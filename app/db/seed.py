"""Idempotent demo data for stage 2. Fake names only — no real personal data."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.models.course import Course, Enrollment, LearningBlock, Module
from app.db.models.enums import BlockType, CourseStatus, EnrollmentStatus, OrgStatus, UserStatus
from app.db.models.organization import Department, Organization
from app.db.models.user import Role, User, UserRole
from app.db.role_ids import (
    ROLE_ADMIN_ID,
    ROLE_EMPLOYEE_ID,
    ROLE_MANAGER_ID,
    ROLE_METHODIST_ID,
    SYSTEM_ROLES,
)

logger = get_logger("seed")

DEMO_PASSWORD = "DemoPass123!"

DEMO_ORG_ID = UUID("10000000-0000-4000-8000-000000000001")
DEMO_DEPT_ID = UUID("10000000-0000-4000-8000-000000000010")
DEMO_ADMIN_ID = UUID("10000000-0000-4000-8000-000000000021")
DEMO_METHODIST_ID = UUID("10000000-0000-4000-8000-000000000022")
DEMO_MANAGER_ID = UUID("10000000-0000-4000-8000-000000000023")
DEMO_EMPLOYEE_ID = UUID("10000000-0000-4000-8000-000000000024")
DEMO_COURSE_ID = UUID("10000000-0000-4000-8000-000000000031")


def _blocks(module_id: UUID, items: list[dict]) -> list[LearningBlock]:
    result = []
    for index, item in enumerate(items, start=1):
        result.append(
            LearningBlock(
                module_id=module_id,
                position=index,
                block_type=item["type"],
                title=item.get("title", ""),
                body=item.get("body", ""),
                source_label=item.get("source_label", ""),
                prompt=item.get("prompt", ""),
                options_json=item.get("options"),
                expected_answer=item.get("expected", ""),
                alt_body=item.get("alt", ""),
            )
        )
    return result


async def seed_demo(session: AsyncSession) -> None:
    for role_id, name, description in SYSTEM_ROLES:
        if await session.get(Role, role_id) is None:
            session.add(Role(id=role_id, name=name, description=description))
    await session.flush()

    existing = await session.get(Organization, DEMO_ORG_ID)
    if existing is not None:
        logger.info("demo_seed_already_present")
        return

    logger.info("demo_seed_started")
    password_hash = hash_password(DEMO_PASSWORD)
    now = datetime.now(UTC)

    session.add(Organization(id=DEMO_ORG_ID, name="Демо-организация", status=OrgStatus.ACTIVE.value))
    session.add(
        User(
            id=DEMO_ADMIN_ID,
            organization_id=DEMO_ORG_ID,
            email="admin@demo.local",
            full_name="Анна Админова",
            password_hash=password_hash,
            status=UserStatus.ACTIVE.value,
        )
    )
    session.add(
        User(
            id=DEMO_METHODIST_ID,
            organization_id=DEMO_ORG_ID,
            email="methodist@demo.local",
            full_name="Михаил Методистов",
            password_hash=password_hash,
            status=UserStatus.ACTIVE.value,
        )
    )
    session.add(
        User(
            id=DEMO_MANAGER_ID,
            organization_id=DEMO_ORG_ID,
            email="manager@demo.local",
            full_name="Мария Руководителева",
            password_hash=password_hash,
            status=UserStatus.ACTIVE.value,
        )
    )
    session.add(
        User(
            id=DEMO_EMPLOYEE_ID,
            organization_id=DEMO_ORG_ID,
            email="employee@demo.local",
            full_name="Иван Сотрудников",
            password_hash=password_hash,
            status=UserStatus.ACTIVE.value,
        )
    )
    await session.flush()

    session.add(
        Department(
            id=DEMO_DEPT_ID,
            organization_id=DEMO_ORG_ID,
            name="Команда внедрения",
            manager_id=DEMO_MANAGER_ID,
        )
    )
    for user_id in (DEMO_MANAGER_ID, DEMO_EMPLOYEE_ID):
        user = await session.get(User, user_id)
        if user:
            user.department_id = DEMO_DEPT_ID

    session.add_all(
        [
            UserRole(user_id=DEMO_ADMIN_ID, role_id=ROLE_ADMIN_ID, organization_id=DEMO_ORG_ID),
            UserRole(user_id=DEMO_METHODIST_ID, role_id=ROLE_METHODIST_ID, organization_id=DEMO_ORG_ID),
            UserRole(user_id=DEMO_MANAGER_ID, role_id=ROLE_MANAGER_ID, organization_id=DEMO_ORG_ID),
            UserRole(user_id=DEMO_EMPLOYEE_ID, role_id=ROLE_EMPLOYEE_ID, organization_id=DEMO_ORG_ID),
        ]
    )

    course = Course(
        id=DEMO_COURSE_ID,
        organization_id=DEMO_ORG_ID,
        title="Командная работа и коммуникация",
        description=(
            "Короткий корпоративный курс: команда как система, каналы коммуникации и обратная связь SBI. "
            "Итоговая квалификация этим курсом не подтверждается."
        ),
        status=CourseStatus.PUBLISHED.value,
        version=1,
        owner_id=DEMO_METHODIST_ID,
        passing_score=70,
        require_human_confirmation=False,
        published_at=now,
    )
    session.add(course)
    await session.flush()

    modules_spec = [
        {
            "id": UUID("10000000-0000-4000-8000-000000000041"),
            "title": "Команда как система",
            "objectives": "Понять, что результат зависит от связей между ролями, а не только от личных усилий.",
            "blocks": [
                {
                    "type": BlockType.EXPLAIN.value,
                    "title": "Зачем это в работе",
                    "body": (
                        "Команда — система ролей, договорённостей и потоков информации. "
                        "Если один человек «тянет всё», система хрупкая: при отпуске или сбое работа останавливается."
                    ),
                },
                {
                    "type": BlockType.SOURCE.value,
                    "title": "Первоисточник",
                    "source_label": "Учебный модуль 1. Команда как система, ред. 2026",
                    "body": "Утверждённый материал: команда описывается через цели, роли, правила взаимодействия и обратную связь.",
                },
                {
                    "type": BlockType.RECALL.value,
                    "title": "Вспомните",
                    "prompt": "Назовите два элемента, без которых команда перестаёт быть системой.",
                    "expected": "роли и договорённости",
                },
                {
                    "type": BlockType.EXAMPLE.value,
                    "title": "Рабочий пример",
                    "body": (
                        "Смена передаёт заявку без владельца. Через день никто не знает статус. "
                        "Системное решение — явная роль «владелец заявки» и канал статуса, а не «пусть кто-нибудь глянет»."
                    ),
                },
                {
                    "type": BlockType.CHECK.value,
                    "title": "Проверка понимания",
                    "prompt": "Что делает команду системой, а не набором людей?",
                    "options": [
                        "Связи между ролями, целями и правилами",
                        "Максимальная загрузка каждого сотрудника",
                        "Ежедневные отчёты руководителю без договорённостей",
                    ],
                    "expected": "Связи между ролями, целями и правилами",
                    "alt": "Подумайте не о «хороших людях», а о том, как роли связаны: кто за что отвечает и как передаётся информация.",
                },
            ],
        },
        {
            "id": UUID("10000000-0000-4000-8000-000000000042"),
            "title": "Уровни и каналы коммуникации",
            "objectives": "Выбирать канал по задаче: срочность, сложность, необходимость следа.",
            "blocks": [
                {
                    "type": BlockType.EXPLAIN.value,
                    "title": "Зачем это в работе",
                    "body": (
                        "Сообщение в общем чате не заменяет решение, которое должно остаться в регламенте. "
                        "Сложный конфликт редко решается стикером. Канал должен соответствовать ставке разговора."
                    ),
                },
                {
                    "type": BlockType.SOURCE.value,
                    "title": "Первоисточник",
                    "source_label": "Учебный модуль 2. Каналы коммуникации, ред. 2026",
                    "body": "Синхронный канал — для уточнения. Асинхронный с фиксацией — для решений и поручений.",
                },
                {
                    "type": BlockType.RECALL.value,
                    "title": "Вспомните",
                    "prompt": "Когда лучше письменный канал с фиксацией, а не голосовой звонок?",
                    "expected": "когда нужно сохранить решение или поручение",
                },
                {
                    "type": BlockType.EXAMPLE.value,
                    "title": "Рабочий пример",
                    "body": "Согласовали срок в созвоне и не записали. Через неделю спор «кто что обещал». След в задаче снимает спор.",
                },
                {
                    "type": BlockType.CHECK.value,
                    "title": "Проверка понимания",
                    "prompt": "Какой канал уместен для фиксации решения по инциденту?",
                    "options": [
                        "Запись в утверждённом журнале или задаче",
                        "Только личные сообщения без копии",
                        "Устный разговор в коридоре",
                    ],
                    "expected": "Запись в утверждённом журнале или задаче",
                    "alt": "Если решение должно быть проверяемым, ему нужен след. Голос удобен для уточнения, но не заменяет фиксацию.",
                },
            ],
        },
        {
            "id": UUID("10000000-0000-4000-8000-000000000043"),
            "title": "Обратная связь SBI",
            "objectives": "Давать обратную связь по факту поведения, без ярлыков.",
            "blocks": [
                {
                    "type": BlockType.EXPLAIN.value,
                    "title": "Зачем это в работе",
                    "body": (
                        "SBI: Situation — момент, Behavior — наблюдаемое действие, Impact — влияние на работу. "
                        "Так проще услышать замечание и не спорить о личности."
                    ),
                },
                {
                    "type": BlockType.SOURCE.value,
                    "title": "Первоисточник",
                    "source_label": "Учебный модуль 5. Обратная связь SBI, ред. 2026",
                    "body": "Формула SBI описывает ситуацию, поведение и влияние. Оценки характера в модель не входят.",
                },
                {
                    "type": BlockType.RECALL.value,
                    "title": "Вспомните",
                    "prompt": "Расшифруйте буквы S, B и I в модели обратной связи.",
                    "expected": "situation behavior impact",
                },
                {
                    "type": BlockType.EXAMPLE.value,
                    "title": "Рабочий пример",
                    "body": (
                        "Не: «ты безответственный». "
                        "Да: «На стендапе вчера (S) отчёт по инциденту не был озвучен (B), смена не знала статус клиента (I)»."
                    ),
                },
                {
                    "type": BlockType.CHECK.value,
                    "title": "Проверка понимания",
                    "prompt": "Какая фраза ближе к SBI?",
                    "options": [
                        "На планёрке в 10:00 ты перебил коллегу, из-за этого решение не зафиксировали",
                        "Ты всегда всех перебиваешь, так нельзя",
                        "Надо быть командным игроком",
                    ],
                    "expected": "На планёрке в 10:00 ты перебил коллегу, из-за этого решение не зафиксировали",
                    "alt": "Уберите ярлык («всегда», «безответственный») и оставьте момент, действие и следствие.",
                },
            ],
        },
    ]

    for index, spec in enumerate(modules_spec, start=1):
        module = Module(
            id=spec["id"],
            course_id=DEMO_COURSE_ID,
            title=spec["title"],
            position=index,
            learning_objectives=spec["objectives"],
            estimated_minutes=8,
        )
        session.add(module)
        session.add_all(_blocks(spec["id"], spec["blocks"]))

    session.add(
        Enrollment(
            id=UUID("10000000-0000-4000-8000-000000000051"),
            user_id=DEMO_EMPLOYEE_ID,
            course_id=DEMO_COURSE_ID,
            assigned_by=DEMO_MANAGER_ID,
            assigned_at=now,
            deadline=now + timedelta(days=14),
            status=EnrollmentStatus.ASSIGNED.value,
        )
    )
    await session.flush()
    logger.info("demo_seed_finished", course_id=str(DEMO_COURSE_ID), employee="employee@demo.local")


async def seed_if_enabled(session: AsyncSession, enabled: bool) -> None:
    if not enabled:
        logger.info("demo_seed_skipped")
        return
    await seed_demo(session)


async def org_exists(session: AsyncSession) -> bool:
    result = await session.execute(select(Organization.id).limit(1))
    return result.scalar_one_or_none() is not None


async def _cli() -> None:
    from app.core.config import get_settings
    from app.core.logging import setup_logging
    from app.db.session import dispose_engine, init_engine

    settings = get_settings()
    setup_logging(settings.log_level)
    factory = init_engine(settings)
    async with factory() as session:
        await seed_demo(session)
        await session.commit()
    await dispose_engine()


if __name__ == "__main__":
    import asyncio

    asyncio.run(_cli())
