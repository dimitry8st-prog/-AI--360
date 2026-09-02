from collections.abc import AsyncIterator

from fastapi import Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.logging import get_logger
from app.core.security import verify_csrf
from app.db.models.user import User

logger = get_logger("web")


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def csrf_from_form(request: Request, csrf_token: str = Form(...)) -> str:
    settings = request.app.state.settings
    cookie = request.cookies.get(settings.csrf_cookie_name)
    if not verify_csrf(settings, cookie, csrf_token):
        logger.warning("csrf_rejected", path=request.url.path)
        raise ForbiddenError("Сессия формы устарела. Обновите страницу.")
    return csrf_token


def current_user_optional(request: Request) -> User | None:
    return getattr(request.state, "user", None)


def require_login(request: Request) -> User:
    user = current_user_optional(request)
    if user is None:
        raise UnauthorizedError("Требуется вход")
    return user


def request_id_of(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)
