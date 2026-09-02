from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, Update

from app.core.logging import bind_log_context, get_logger, reset_log_context
from app.core.rate_limit import allow_request
from app.services.auth_service import get_user_by_telegram

logger = get_logger("bot.auth")


def telegram_user_of(event: TelegramObject, data: dict[str, Any]):
    user = data.get("event_from_user")
    if user is not None:
        return user
    if isinstance(event, Update):
        if event.message:
            return event.message.from_user
        if event.callback_query:
            return event.callback_query.from_user
    return getattr(event, "from_user", None)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        reset_log_context()
        bind_log_context(source="telegram")
        telegram_user = telegram_user_of(event, data)
        session = data.get("session")
        data["db_user"] = None
        if telegram_user is not None:
            bind_log_context(telegram_id=telegram_user.id)
            if session is not None:
                user = await get_user_by_telegram(session, telegram_user.id)
                data["db_user"] = user
                if user is not None:
                    bind_log_context(user_id=user.id, organization_id=user.organization_id)
        try:
            return await handler(event, data)
        finally:
            reset_log_context()


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, redis, spec: str):
        self.redis = redis
        self.spec = spec

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_user = telegram_user_of(event, data)
        key = f"tg:{getattr(telegram_user, 'id', 'anon')}"
        if not await allow_request(self.redis, key=key, spec=self.spec):
            if isinstance(event, Message):
                await event.answer("Слишком много сообщений. Подождите минуту.")
            return None
        return await handler(event, data)
