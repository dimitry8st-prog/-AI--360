from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.core.exceptions import ForbiddenError
from app.core.security import hash_password
from app.db.base import Base
from app.db.models import (
    Course,
    Enrollment,
    LearningBlock,
    Module,
    Organization,
    Role,
    User,
    UserRole,
)
from app.db.models.enums import BlockType, CourseStatus, EnrollmentStatus, UserStatus
from app.db.role_ids import ROLE_EMPLOYEE_ID, ROLE_MANAGER_ID, ROLE_METHODIST_ID, SYSTEM_ROLES
from app.services.course_service import assign_course, create_course, get_course
from app.services.learning_service import (
    answers_match,
    current_view,
    progress_for_course,
    start_or_resume,
    submit_check,
    submit_recall,
)
from app.services.progress_service import calc_module_progress
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as db:
        yield db
    await engine.dispose()


async def _bootstrap(session: AsyncSession):
    org = Organization(id=uuid4(), name="Орг А", status="active")
    session.add(org)
    for role_id, name, description in SYSTEM_ROLES:
        session.add(Role(id=role_id, name=name, description=description))
    await session.flush()
    password = hash_password("DemoPass123!")
    methodist = User(
        id=uuid4(),
        organization_id=org.id,
        email="methodist@a.local",
        full_name="Методист",
        password_hash=password,
        status=UserStatus.ACTIVE.value,
    )
    manager = User(
        id=uuid4(),
        organization_id=org.id,
        email="manager@a.local",
        full_name="Руководитель",
        password_hash=password,
        status=UserStatus.ACTIVE.value,
    )
    employee = User(
        id=uuid4(),
        organization_id=org.id,
        email="employee@a.local",
        full_name="Сотрудник",
        password_hash=password,
        status=UserStatus.ACTIVE.value,
    )
    stranger_org = Organization(id=uuid4(), name="Орг Б", status="active")
    session.add_all([methodist, manager, employee, stranger_org])
    await session.flush()
    session.add_all(
        [
            UserRole(user_id=methodist.id, role_id=ROLE_METHODIST_ID, organization_id=org.id),
            UserRole(user_id=manager.id, role_id=ROLE_MANAGER_ID, organization_id=org.id),
            UserRole(user_id=employee.id, role_id=ROLE_EMPLOYEE_ID, organization_id=org.id),
        ]
    )
    await session.flush()
    from app.services.auth_service import get_user_by_id

    methodist = await get_user_by_id(session, methodist.id)
    manager = await get_user_by_id(session, manager.id)
    employee = await get_user_by_id(session, employee.id)
    return org, methodist, manager, employee, stranger_org


async def _published_course(session, methodist, employee, manager) -> Course:
    course = await create_course(
        session,
        actor=methodist,
        title="Демо-курс",
        description="Описание",
        passing_score=70,
        request_id="test",
    )
    module = Module(
        id=uuid4(),
        course_id=course.id,
        title="Модуль 1",
        position=1,
        learning_objectives="Понять правило",
        estimated_minutes=5,
    )
    session.add(module)
    await session.flush()
    session.add_all(
        [
            LearningBlock(
                module_id=module.id,
                position=1,
                block_type=BlockType.EXPLAIN.value,
                title="Объяснение",
                body="Команда — система ролей.",
            ),
            LearningBlock(
                module_id=module.id,
                position=2,
                block_type=BlockType.SOURCE.value,
                title="Источник",
                source_label="Модуль 1, ред. 2026",
                body="Утверждённый текст",
            ),
            LearningBlock(
                module_id=module.id,
                position=3,
                block_type=BlockType.RECALL.value,
                title="Вспомните",
                prompt="Что такое команда как система?",
                expected_answer="роли",
            ),
            LearningBlock(
                module_id=module.id,
                position=4,
                block_type=BlockType.EXAMPLE.value,
                title="Пример",
                body="Назначьте владельца заявки.",
            ),
            LearningBlock(
                module_id=module.id,
                position=5,
                block_type=BlockType.CHECK.value,
                title="Проверка",
                prompt="Что делает команду системой?",
                options_json=["Связи ролей", "Хаос"],
                expected_answer="Связи ролей",
                alt_body="Подумайте о связях между ролями.",
            ),
        ]
    )
    course.status = CourseStatus.PUBLISHED.value
    course.published_at = datetime.now(UTC)
    await session.flush()
    session.add(
        Enrollment(
            id=uuid4(),
            user_id=employee.id,
            course_id=course.id,
            assigned_by=manager.id,
            assigned_at=datetime.now(UTC),
            status=EnrollmentStatus.ASSIGNED.value,
        )
    )
    await session.flush()
    return await get_course(session, course.id)


@pytest.mark.asyncio
async def test_employee_cannot_create_course(session: AsyncSession):
    _org, _methodist, _manager, employee, _other = await _bootstrap(session)
    with pytest.raises(ForbiddenError):
        await create_course(
            session, actor=employee, title="X", description="", passing_score=70, request_id="t"
        )


@pytest.mark.asyncio
async def test_manager_cannot_assign_other_org(session: AsyncSession):
    org, methodist, manager, employee, other_org = await _bootstrap(session)
    outsider = User(
        id=uuid4(),
        organization_id=other_org.id,
        email="out@b.local",
        full_name="Чужой",
        password_hash=hash_password("DemoPass123!"),
        status=UserStatus.ACTIVE.value,
    )
    session.add(outsider)
    await session.flush()
    course = await create_course(
        session, actor=methodist, title="Курс", description="", passing_score=70, request_id="t"
    )
    course.status = CourseStatus.PUBLISHED.value
    with pytest.raises(ForbiddenError, match="другой организации"):
        await assign_course(
            session, actor=manager, user_id=outsider.id, course_id=course.id, deadline=None, request_id="t"
        )


@pytest.mark.asyncio
async def test_learning_session_progress_persists(session: AsyncSession):
    _org, methodist, manager, employee, _other = await _bootstrap(session)
    course = await _published_course(session, methodist, employee, manager)
    learning = await start_or_resume(session, user=employee, course_id=course.id, request_id="t")
    view = await current_view(session, learning, employee)
    assert view is not None
    assert view.block.block_type == BlockType.EXPLAIN.value
    first_id = learning.id
    step_after_start = learning.current_step

    resumed = await start_or_resume(session, user=employee, course_id=course.id)
    assert resumed.id == first_id
    assert resumed.current_step == step_after_start
    progress = await progress_for_course(session, employee, course)
    assert progress["percent"] == 0


@pytest.mark.asyncio
async def test_module_flow_and_progress(session: AsyncSession):
    _org, methodist, manager, employee, _other = await _bootstrap(session)
    course = await _published_course(session, methodist, employee, manager)
    learning = await start_or_resume(session, user=employee, course_id=course.id)
    from app.services.learning_service import advance_content_block

    view = await advance_content_block(session, user=employee, session_id=learning.id)
    assert view.block.block_type == BlockType.SOURCE.value
    view = await advance_content_block(session, user=employee, session_id=learning.id)
    assert view.block.block_type == BlockType.RECALL.value
    view = await submit_recall(session, user=employee, session_id=learning.id, answer="роли и договорённости")
    assert view.block.block_type == BlockType.EXAMPLE.value
    view = await advance_content_block(session, user=employee, session_id=learning.id)
    assert view.block.block_type == BlockType.CHECK.value
    assert "correct_answer" not in (view.block.body or "")
    view = await submit_check(session, user=employee, session_id=learning.id, answer="Хаос")
    assert view.block.block_type == BlockType.CHECK.value
    assert view.feedback
    view = await submit_check(session, user=employee, session_id=learning.id, answer="Связи ролей")
    progress = await progress_for_course(session, employee, course)
    assert progress["percent"] == 100
    assert calc_module_progress(completed_modules=1, total_modules=1) == 100


def test_answers_match_is_lenient():
    assert answers_match("роли", "Роли и договорённости")
    assert not answers_match("связи ролей", "хаос")
