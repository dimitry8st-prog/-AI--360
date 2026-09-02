from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.core.permissions import Permission, require_permission
from app.db.models.course import (
    Course,
    Enrollment,
    LearningBlock,
    LearningSession,
    Module,
    ModuleCompletion,
)
from app.db.models.enums import BlockType, EnrollmentStatus, SessionState
from app.db.models.user import User
from app.repositories.access import assert_org_scope
from app.services.audit_service import record_audit
from app.services.course_service import get_course
from app.services.progress_service import calc_module_progress

logger = get_logger("learning")

REPEAT_AFTER_ERRORS = 2


@dataclass
class BlockView:
    session_id: UUID
    course_id: UUID
    module_id: UUID
    module_title: str
    block: LearningBlock
    progress_percent: int
    is_last_in_module: bool
    course_completed: bool = False
    feedback: str | None = None
    reveal_check: bool = False


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def answers_match(expected: str, given: str) -> bool:
    if not expected:
        return True
    left, right = _normalize(expected), _normalize(given)
    return left == right or left in right or right in left


async def _enrollment_for(session: AsyncSession, user_id: UUID, course_id: UUID) -> Enrollment:
    result = await session.execute(
        select(Enrollment).where(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
    )
    enrollment = result.scalar_one_or_none()
    if enrollment is None:
        raise ForbiddenError("Курс не назначен")
    return enrollment


async def _completed_module_ids(session: AsyncSession, user_id: UUID, course: Course) -> set[UUID]:
    module_ids = [module.id for module in course.modules]
    if not module_ids:
        return set()
    result = await session.execute(
        select(ModuleCompletion.module_id).where(
            ModuleCompletion.user_id == user_id,
            ModuleCompletion.module_id.in_(module_ids),
            ModuleCompletion.completed_at.is_not(None),
        )
    )
    return set(result.scalars().all())


async def progress_for_course(session: AsyncSession, user: User, course: Course) -> dict:
    completed = await _completed_module_ids(session, user.id, course)
    total = len(course.modules)
    percent = calc_module_progress(completed_modules=len(completed), total_modules=total)
    module_ids = [item.id for item in course.modules]
    needs_repeat: list[UUID] = []
    if module_ids:
        repeats = await session.execute(
            select(ModuleCompletion.module_id).where(
                ModuleCompletion.user_id == user.id,
                ModuleCompletion.needs_repeat.is_(True),
                ModuleCompletion.module_id.in_(module_ids),
            )
        )
        needs_repeat = list(repeats.scalars().all())
    return {
        "percent": percent,
        "completed_modules": len(completed),
        "total_modules": total,
        "needs_repeat": needs_repeat,
    }


async def start_or_resume(
    session: AsyncSession,
    *,
    user: User,
    course_id: UUID,
    request_id: str | None = None,
) -> LearningSession:
    require_permission(user.role_names, Permission.COURSE_VIEW_ASSIGNED)
    enrollment = await _enrollment_for(session, user.id, course_id)
    course = await get_course(session, course_id)
    assert_org_scope(user.organization_id, course.organization_id)
    if not course.modules:
        raise NotFoundError("В курсе нет модулей")

    result = await session.execute(
        select(LearningSession)
        .where(
            LearningSession.user_id == user.id,
            LearningSession.course_id == course_id,
            LearningSession.state != SessionState.COMPLETED.value,
        )
        .order_by(LearningSession.last_activity_at.desc())
    )
    learning = result.scalars().first()
    now = datetime.now(UTC)
    created = False
    if learning is None:
        first_module = sorted(course.modules, key=lambda item: item.position)[0]
        learning = LearningSession(
            id=uuid4(),
            user_id=user.id,
            course_id=course.id,
            module_id=first_module.id,
            state=SessionState.STARTED.value,
            started_at=now,
            last_activity_at=now,
            current_step=0,
        )
        session.add(learning)
        created = True
        logger.info("learning_session_started", session_id=str(learning.id), course_id=str(course.id))
        await record_audit(
            session,
            organization_id=user.organization_id,
            actor_id=user.id,
            action="learning.session_start",
            entity_type="learning_session",
            entity_id=learning.id,
            after={"course_id": str(course.id), "module_id": str(first_module.id)},
            request_id=request_id,
        )
    else:
        logger.info("learning_session_resumed", session_id=str(learning.id), step=learning.current_step)

    if enrollment.status in {EnrollmentStatus.ASSIGNED.value, EnrollmentStatus.OVERDUE.value}:
        if enrollment.status != EnrollmentStatus.OVERDUE.value:
            enrollment.status = EnrollmentStatus.IN_PROGRESS.value
    learning.state = SessionState.IN_PROGRESS.value
    learning.last_activity_at = now
    if created:
        await session.flush()
    return learning


async def latest_session(session: AsyncSession, user: User) -> LearningSession | None:
    result = await session.execute(
        select(LearningSession)
        .where(LearningSession.user_id == user.id)
        .order_by(LearningSession.last_activity_at.desc())
    )
    return result.scalars().first()


async def get_session(session: AsyncSession, session_id: UUID, user: User) -> LearningSession:
    result = await session.execute(select(LearningSession).where(LearningSession.id == session_id))
    learning = result.scalar_one_or_none()
    if learning is None:
        raise NotFoundError("Учебная сессия не найдена")
    if learning.user_id != user.id:
        raise ForbiddenError("Нельзя открыть чужую учебную сессию")
    return learning


async def _module_with_blocks(session: AsyncSession, module_id: UUID) -> Module:
    result = await session.execute(
        select(Module).options(selectinload(Module.blocks)).where(Module.id == module_id)
    )
    module = result.scalar_one_or_none()
    if module is None:
        raise NotFoundError("Модуль не найден")
    return module


async def current_view(session: AsyncSession, learning: LearningSession, user: User) -> BlockView | None:
    course = await get_course(session, learning.course_id)
    progress = await progress_for_course(session, user, course)
    if progress["percent"] >= 100 and learning.state == SessionState.COMPLETED.value:
        return None
    if learning.module_id is None:
        return None
    module = await _module_with_blocks(session, learning.module_id)
    blocks = sorted(module.blocks, key=lambda item: item.position)
    if not blocks:
        raise NotFoundError("В модуле нет учебных блоков")
    step = min(max(learning.current_step, 0), len(blocks) - 1)
    block = blocks[step]
    return BlockView(
        session_id=learning.id,
        course_id=course.id,
        module_id=module.id,
        module_title=module.title,
        block=block,
        progress_percent=progress["percent"],
        is_last_in_module=step == len(blocks) - 1,
        course_completed=progress["percent"] >= 100,
    )


async def _save_step(learning: LearningSession) -> None:
    learning.last_activity_at = datetime.now(UTC)
    learning.state = SessionState.IN_PROGRESS.value
    logger.info(
        "learning_progress_saved",
        session_id=str(learning.id),
        module_id=str(learning.module_id),
        step=learning.current_step,
    )


async def _completion_row(session: AsyncSession, user_id: UUID, module_id: UUID) -> ModuleCompletion:
    result = await session.execute(
        select(ModuleCompletion).where(
            ModuleCompletion.user_id == user_id, ModuleCompletion.module_id == module_id
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = ModuleCompletion(
            id=uuid4(),
            user_id=user_id,
            module_id=module_id,
            error_count=0,
            needs_repeat=False,
        )
        session.add(row)
        await session.flush()
    return row


async def _advance_or_complete(
    session: AsyncSession, *, user: User, learning: LearningSession, request_id: str | None
) -> BlockView | None:
    module = await _module_with_blocks(session, learning.module_id)  # type: ignore[arg-type]
    blocks = sorted(module.blocks, key=lambda item: item.position)
    if learning.current_step < len(blocks) - 1:
        learning.current_step += 1
        await _save_step(learning)
        return await current_view(session, learning, user)

    completion = await _completion_row(session, user.id, module.id)
    completion.completed_at = datetime.now(UTC)
    logger.info("module_completed", module_id=str(module.id), errors=completion.error_count)

    course = await get_course(session, learning.course_id)
    remaining = [item for item in sorted(course.modules, key=lambda m: m.position) if item.id != module.id]
    completed_ids = await _completed_module_ids(session, user.id, course)
    completed_ids.add(module.id)
    next_module = next((item for item in remaining if item.id not in completed_ids), None)
    if next_module is None:
        learning.state = SessionState.COMPLETED.value
        learning.completed_at = datetime.now(UTC)
        enrollment = await _enrollment_for(session, user.id, course.id)
        enrollment.status = EnrollmentStatus.COMPLETED.value
        logger.info("course_completed", course_id=str(course.id), session_id=str(learning.id))
        await record_audit(
            session,
            organization_id=user.organization_id,
            actor_id=user.id,
            action="learning.course_complete",
            entity_type="course",
            entity_id=course.id,
            request_id=request_id,
        )
        view = await current_view(session, learning, user)
        if view:
            view.course_completed = True
        return view

    learning.module_id = next_module.id
    learning.current_step = 0
    await _save_step(learning)
    logger.info("module_advanced", next_module_id=str(next_module.id))
    return await current_view(session, learning, user)


async def advance_content_block(
    session: AsyncSession, *, user: User, session_id: UUID, request_id: str | None = None
) -> BlockView | None:
    learning = await get_session(session, session_id, user)
    view = await current_view(session, learning, user)
    if view is None:
        return None
    if view.block.block_type in {BlockType.RECALL.value, BlockType.CHECK.value}:
        return view
    return await _advance_or_complete(session, user=user, learning=learning, request_id=request_id)


async def submit_recall(
    session: AsyncSession,
    *,
    user: User,
    session_id: UUID,
    answer: str,
    request_id: str | None = None,
) -> BlockView:
    learning = await get_session(session, session_id, user)
    view = await current_view(session, learning, user)
    if view is None or view.block.block_type != BlockType.RECALL.value:
        raise ForbiddenError("Сейчас ожидается другой шаг")
    logger.info("recall_submitted", session_id=str(learning.id), empty=not answer.strip())
    next_view = await _advance_or_complete(session, user=user, learning=learning, request_id=request_id)
    if next_view is None:
        raise NotFoundError("Следующий шаг не найден")
    expected = view.block.expected_answer
    next_view.feedback = (
        f"Спасибо. Краткий ориентир: {expected}" if expected else "Ответ сохранён. Идём дальше."
    )
    return next_view


async def submit_check(
    session: AsyncSession,
    *,
    user: User,
    session_id: UUID,
    answer: str,
    request_id: str | None = None,
) -> BlockView:
    learning = await get_session(session, session_id, user)
    view = await current_view(session, learning, user)
    if view is None or view.block.block_type != BlockType.CHECK.value:
        raise ForbiddenError("Сейчас ожидается проверка понимания")

    completion = await _completion_row(session, user.id, view.module_id)
    ok = answers_match(view.block.expected_answer, answer)
    if ok:
        logger.info("check_passed", session_id=str(learning.id), module_id=str(view.module_id))
        next_view = await _advance_or_complete(session, user=user, learning=learning, request_id=request_id)
        if next_view is None:
            view.course_completed = True
            view.feedback = "Модуль пройден. ДИС не выставляет квалификацию — это только обучение."
            return view
        next_view.feedback = "Верно. Идём дальше."
        return next_view

    completion.error_count += 1
    if completion.error_count >= REPEAT_AFTER_ERRORS:
        completion.needs_repeat = True
        logger.info(
            "check_failed_repeat_assigned",
            session_id=str(learning.id),
            module_id=str(view.module_id),
            errors=completion.error_count,
        )
        next_view = await _advance_or_complete(session, user=user, learning=learning, request_id=request_id)
        if next_view is None:
            view.feedback = "Тема назначена на повторение. Правильный ориентир показан, квалификацию это не подтверждает."
            view.reveal_check = True
            return view
        next_view.feedback = (
            "Пока ошибка повторяется, я назначил тему на повторение. "
            f"Ориентир: {view.block.expected_answer}"
        )
        return next_view

    logger.info("check_failed", session_id=str(learning.id), errors=completion.error_count)
    view.feedback = view.block.alt_body or "Попробуем иначе. Прочитайте объяснение ещё раз и ответьте снова."
    await _save_step(learning)
    return view


async def own_progress_payload(session: AsyncSession, user: User) -> list[dict]:
    require_permission(user.role_names, Permission.PROGRESS_VIEW_OWN)
    from app.services.course_service import list_assigned_courses

    rows = []
    for course, enrollment in await list_assigned_courses(session, user):
        progress = await progress_for_course(session, user, course)
        rows.append(
            {
                "course_id": course.id,
                "title": course.title,
                "status": enrollment.status,
                "deadline": enrollment.deadline,
                **progress,
            }
        )
    logger.info("progress_viewed_own", courses=len(rows))
    return rows
