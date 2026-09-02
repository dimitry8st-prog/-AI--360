from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.logging import get_logger
from app.core.permissions import Permission, has_permission
from app.core.security import verify_password
from app.db.models.enums import UserStatus
from app.db.models.user import User, UserRole
from app.services.audit_service import record_audit

logger = get_logger("auth")


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    result = await session.execute(
        select(User).options(selectinload(User.user_roles).selectinload(UserRole.role)).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str, organization_id: UUID | None = None) -> User | None:
    stmt = (
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.email == email.strip().lower())
    )
    if organization_id is not None:
        stmt = stmt.where(User.organization_id == organization_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_user_by_telegram(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def authenticate_web(session: AsyncSession, *, email: str, password: str, request_id: str | None) -> User:
    user = await get_user_by_email(session, email)
    if user is None or user.status != UserStatus.ACTIVE.value or not verify_password(password, user.password_hash):
        logger.warning("login_failed", email=email.strip().lower())
        raise UnauthorizedError("Неверный email или пароль")
    logger.info("login_success", email=user.email, roles=sorted(user.role_names))
    await record_audit(
        session,
        organization_id=user.organization_id,
        actor_id=user.id,
        action="auth.login",
        entity_type="user",
        entity_id=user.id,
        request_id=request_id,
    )
    return user


async def bind_telegram(
    session: AsyncSession,
    *,
    email: str,
    telegram_id: int,
    request_id: str | None = None,
) -> User:
    existing = await get_user_by_telegram(session, telegram_id)
    if existing is not None:
        logger.info("telegram_already_bound", telegram_id=telegram_id)
        return existing

    user = await get_user_by_email(session, email)
    if user is None or user.status != UserStatus.ACTIVE.value:
        logger.warning("telegram_bind_unknown_email", email=email.strip().lower())
        raise NotFoundError("Сотрудник с таким email не найден. Обратитесь к администратору.")
    if user.telegram_id and user.telegram_id != telegram_id:
        logger.warning("telegram_bind_conflict", user_id=str(user.id))
        raise ForbiddenError("Этот профиль уже привязан к другому Telegram.")
    user.telegram_id = telegram_id
    logger.info("telegram_bound", user_id=str(user.id), telegram_id=telegram_id)
    await record_audit(
        session,
        organization_id=user.organization_id,
        actor_id=user.id,
        action="auth.telegram_bind",
        entity_type="user",
        entity_id=user.id,
        after={"telegram_id": telegram_id},
        request_id=request_id,
    )
    return user


def actor_can(user: User, permission: Permission) -> bool:
    return has_permission(user.role_names, permission)
