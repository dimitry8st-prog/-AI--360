from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.core.exceptions import ForbiddenError
from app.core.security import hash_password
from app.db.base import Base
from app.db.models import Organization, Role, User, UserRole
from app.db.role_ids import ROLE_EMPLOYEE_ID, SYSTEM_ROLES
from app.repositories.access import assert_org_scope
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


@pytest.mark.asyncio
async def test_org_user_and_role_persist(session: AsyncSession):
    org = Organization(id=uuid4(), name="Демо", status="active")
    session.add(org)
    for role_id, name, description in SYSTEM_ROLES:
        session.add(Role(id=role_id, name=name, description=description))
    user = User(
        id=uuid4(),
        organization_id=org.id,
        email="employee@demo.local",
        full_name="Иван Демо",
        password_hash=hash_password("demo-pass-123"),
        status="active",
    )
    session.add(user)
    await session.flush()
    session.add(
        UserRole(
            id=uuid4(),
            user_id=user.id,
            role_id=ROLE_EMPLOYEE_ID,
            organization_id=org.id,
            created_at=datetime.now(UTC),
        )
    )
    await session.commit()
    loaded = await session.get(User, user.id)
    assert loaded is not None
    assert loaded.email == "employee@demo.local"
    assert loaded.organization_id == org.id


def test_repository_blocks_cross_org():
    org_a, org_b = uuid4(), uuid4()
    assert_org_scope(org_a, org_a)
    with pytest.raises(ForbiddenError):
        assert_org_scope(org_a, org_b)
