import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from app.bot.handlers.learning import router as learning_router
from app.bot.middlewares.auth import RateLimitMiddleware, UserMiddleware
from app.bot.middlewares.db import DbSessionMiddleware, LoggingMiddleware
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.session import dispose_engine, init_engine

logger = get_logger("bot")


async def _idle_without_token() -> None:
    logger.warning("telegram_token_missing", hint="Задайте TELEGRAM_BOT_TOKEN, контейнер ожидает")
    await asyncio.Event().wait()


async def run_bot() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    if not settings.telegram_bot_token:
        await _idle_without_token()
        return

    session_factory = init_engine(settings)
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    await redis_client.ping()
    storage = RedisStorage(redis=redis_client)
    bot = Bot(
        settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher(storage=storage)
    dispatcher.update.outer_middleware(LoggingMiddleware())
    dispatcher.update.outer_middleware(DbSessionMiddleware(session_factory))
    dispatcher.update.outer_middleware(UserMiddleware())
    dispatcher.update.outer_middleware(RateLimitMiddleware(redis_client, settings.rate_limit_telegram))
    dispatcher.include_router(learning_router)
    logger.info("bot_polling_started")
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await redis_client.aclose()
        await dispose_engine()
        logger.info("bot_stopped")


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
