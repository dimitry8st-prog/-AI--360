from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.core.permissions import Permission, has_permission, require_permission
from app.db.models.course import Course, Enrollment, LearningBlock, Module
from app.db.models.enums import BlockType, CourseStatus, EnrollmentStatus
from app.db.models.user import User
from app.repositories.access import assert_org_scope
from app.services.audit_service import record_audit
from app.services.notification_service import refresh_enrollment_status

logger = get_logger("course")


async def get_course(session: AsyncSession, course_id: UUID) -> Course:
    result = await session.execute(
        select(Course)
        .options(selectinload(Course.modules).selectinload(Module.blocks))
        .where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    if course is None:
        raise NotFoundError("Курс не найден")
    return course


async def list_assigned_courses(session: AsyncSession, user: User) -> list[tuple[Course, Enrollment]]:
    result = await session.execute(
        select(Enrollment, Course)
        .join(Course, Course.id == Enrollment.course_id)
        .options(selectinload(Course.modules))
        .where(Enrollment.user_id == user.id)
        .order_by(Enrollment.assigned_at.desc())
    )
    rows = []
    now = datetime.now(UTC)
    for enrollment, course in result.all():
        refresh_enrollment_status(enrollment, now=now)
        rows.append((course, enrollment))
    logger.info("courses_listed_assigned", count=len(rows))
    return rows


async def list_manageable_courses(session: AsyncSession, user: User) -> list[Course]:
    stmt = (
        select(Course)
        .options(selectinload(Course.modules))
        .where(Course.organization_id == user.organization_id)
        .order_by(Course.created_at.desc())
    )
    if has_permission(user.role_names, Permission.COURSE_MANAGE):
        pass
    elif has_permission(user.role_names, Permission.ENROLLMENT_ASSIGN_TEAM) or has_permission(
        user.role_names, Permission.ENROLLMENT_ASSIGN_ORG
    ):
        stmt = stmt.where(Course.status == CourseStatus.PUBLISHED.value)
    else:
        raise ForbiddenError("Недостаточно прав для просмотра каталога")
    courses = list((await session.execute(stmt)).scalars().unique())
    logger.info("courses_listed_catalog", count=len(courses))
    return courses


async def create_course(
    session: AsyncSession,
    *,
    actor: User,
    title: str,
    description: str,
    passing_score: int,
    request_id: str | None,
) -> Course:
    require_permission(actor.role_names, Permission.COURSE_MANAGE)
    course = Course(
        id=uuid4(),
        organization_id=actor.organization_id,
        title=title.strip(),
        description=description.strip(),
        status=CourseStatus.DRAFT.value,
        version=1,
        owner_id=actor.id,
        passing_score=passing_score,
        require_human_confirmation=False,
    )
    session.add(course)
    await session.flush()
    logger.info("course_created", course_id=str(course.id), title=course.title)
    await record_audit(
        session,
        organization_id=actor.organization_id,
        actor_id=actor.id,
        action="course.create",
        entity_type="course",
        entity_id=course.id,
        after={"title": course.title, "status": course.status},
        request_id=request_id,
    )
    return course


async def publish_course(session: AsyncSession, *, actor: User, course_id: UUID, request_id: str | None) -> Course:
    require_permission(actor.role_names, Permission.COURSE_MANAGE)
    course = await get_course(session, course_id)
    assert_org_scope(actor.organization_id, course.organization_id)
    course.status = CourseStatus.PUBLISHED.value
    course.published_at = datetime.now(UTC)
    logger.info("course_published", course_id=str(course.id))
    await record_audit(
        session,
        organization_id=actor.organization_id,
        actor_id=actor.id,
        action="course.publish",
        entity_type="course",
        entity_id=course.id,
        request_id=request_id,
    )
    return course


async def add_module(
    session: AsyncSession,
    *,
    actor: User,
    course_id: UUID,
    title: str,
    learning_objectives: str,
    estimated_minutes: int,
    explain: str,
    source_label: str,
    recall_prompt: str,
    recall_answer: str,
    example: str,
    check_prompt: str,
    check_options: list[str],
    check_answer: str,
    alt_body: str,
    request_id: str | None,
) -> Module:
    require_permission(actor.role_names, Permission.MODULE_MANAGE)
    course = await get_course(session, course_id)
    assert_org_scope(actor.organization_id, course.organization_id)
    position = len(course.modules) + 1
    module = Module(
        id=uuid4(),
        course_id=course.id,
        title=title.strip(),
        position=position,
        learning_objectives=learning_objectives.strip(),
        estimated_minutes=estimated_minutes,
    )
    session.add(module)
    await session.flush()
    blocks = [
        LearningBlock(
            id=uuid4(),
            module_id=module.id,
            position=1,
            block_type=BlockType.EXPLAIN.value,
            title="Зачем это в работе",
            body=explain.strip(),
        ),
        LearningBlock(
            id=uuid4(),
            module_id=module.id,
            position=2,
            block_type=BlockType.SOURCE.value,
            title="Первоисточник",
            body=explain.strip()[:400],
            source_label=source_label.strip() or "Утверждённый учебный материал курса",
        ),
        LearningBlock(
            id=uuid4(),
            module_id=module.id,
            position=3,
            block_type=BlockType.RECALL.value,
            title="Вспомните",
            prompt=recall_prompt.strip(),
            expected_answer=recall_answer.strip(),
        ),
        LearningBlock(
            id=uuid4(),
            module_id=module.id,
            position=4,
            block_type=BlockType.EXAMPLE.value,
            title="Рабочий пример",
            body=example.strip(),
        ),
        LearningBlock(
            id=uuid4(),
            module_id=module.id,
            position=5,
            block_type=BlockType.CHECK.value,
            title="Проверка понимания",
            prompt=check_prompt.strip(),
            options_json=check_options,
            expected_answer=check_answer.strip(),
            alt_body=alt_body.strip(),
        ),
    ]
    session.add_all(blocks)
    logger.info("module_created", course_id=str(course.id), module_id=str(module.id), position=position)
    await record_audit(
        session,
        organization_id=actor.organization_id,
        actor_id=actor.id,
        action="module.create",
        entity_type="module",
        entity_id=module.id,
        after={"title": module.title, "course_id": str(course.id)},
        request_id=request_id,
    )
    return module


def _can_assign(actor: User, target: User) -> None:
    assert_org_scope(actor.organization_id, target.organization_id)
    if has_permission(actor.role_names, Permission.ENROLLMENT_ASSIGN_ORG):
        return
    if has_permission(actor.role_names, Permission.ENROLLMENT_ASSIGN_TEAM):
        if actor.department_id and actor.department_id == target.department_id:
            return
        raise ForbiddenError("Руководитель может назначать обучение только своей команде")
    raise ForbiddenError("Недостаточно прав для назначения")


async def assign_course(
    session: AsyncSession,
    *,
    actor: User,
    user_id: UUID,
    course_id: UUID,
    deadline: datetime | None,
    request_id: str | None,
) -> Enrollment:
    from app.services.auth_service import get_user_by_id

    target = await get_user_by_id(session, user_id)
    if target is None:
        raise NotFoundError("Сотрудник не найден")
    _can_assign(actor, target)
    course = await get_course(session, course_id)
    assert_org_scope(actor.organization_id, course.organization_id)
    if course.status != CourseStatus.PUBLISHED.value:
        raise ForbiddenError("Назначить можно только опубликованный курс")

    existing = await session.execute(
        select(Enrollment).where(Enrollment.user_id == target.id, Enrollment.course_id == course.id)
    )
    enrollment = existing.scalar_one_or_none()
    if enrollment is None:
        enrollment = Enrollment(
            id=uuid4(),
            user_id=target.id,
            course_id=course.id,
            assigned_by=actor.id,
            assigned_at=datetime.now(UTC),
            deadline=deadline,
            status=EnrollmentStatus.ASSIGNED.value,
        )
        session.add(enrollment)
        logger.info("enrollment_created", user_id=str(target.id), course_id=str(course.id))
    else:
        enrollment.deadline = deadline
        enrollment.assigned_by = actor.id
        if enrollment.status == EnrollmentStatus.CANCELLED.value:
            enrollment.status = EnrollmentStatus.ASSIGNED.value
        logger.info("enrollment_updated", user_id=str(target.id), course_id=str(course.id))
    await record_audit(
        session,
        organization_id=actor.organization_id,
        actor_id=actor.id,
        action="enrollment.assign",
        entity_type="enrollment",
        entity_id=enrollment.id,
        after={"user_id": str(target.id), "course_id": str(course.id)},
        request_id=request_id,
    )
    return enrollment


async def list_org_users(session: AsyncSession, actor: User) -> list[User]:
    if not (
        has_permission(actor.role_names, Permission.ENROLLMENT_ASSIGN_ORG)
        or has_permission(actor.role_names, Permission.ENROLLMENT_ASSIGN_TEAM)
        or has_permission(actor.role_names, Permission.USER_MANAGE)
        or has_permission(actor.role_names, Permission.COURSE_MANAGE)
    ):
        raise ForbiddenError()
    stmt = select(User).where(User.organization_id == actor.organization_id).order_by(User.full_name)
    if has_permission(actor.role_names, Permission.ENROLLMENT_ASSIGN_TEAM) and not has_permission(
        actor.role_names, Permission.ENROLLMENT_ASSIGN_ORG
    ) and not has_permission(actor.role_names, Permission.USER_MANAGE):
        stmt = stmt.where(User.department_id == actor.department_id)
    return list((await session.execute(stmt)).scalars())
