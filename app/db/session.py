from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings
from app.db.base import Base

engine: AsyncEngine | None = None
SessionFactory: async_sessionmaker[AsyncSession] | None = None


def create_engine(settings: Settings | None = None) -> AsyncEngine:
    settings = settings or get_settings()
    connect_args = {}
    if settings.is_sqlite:
        connect_args = {"check_same_thread": False}
    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


def init_engine(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    global engine, SessionFactory
    settings = settings or get_settings()
    engine = create_engine(settings)
    SessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return SessionFactory


async def dispose_engine() -> None:
    global engine, SessionFactory
    if engine is not None:
        await engine.dispose()
    engine = None
    SessionFactory = None


async def get_session() -> AsyncIterator[AsyncSession]:
    if SessionFactory is None:
        init_engine()
    assert SessionFactory is not None
    async with SessionFactory() as session:
        yield session


async def create_all_tables(bind: AsyncEngine | None = None) -> None:
    """Used in tests. Production uses Alembic."""
    target = bind or engine
    if target is None:
        raise RuntimeError("Engine is not initialized")
    async with target.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
