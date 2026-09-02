from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.exceptions import AppError, UnauthorizedError
from app.core.logging import get_logger, setup_logging
from app.db.seed import seed_if_enabled
from app.db.session import dispose_engine, init_engine
from app.web.middleware import RequestContextMiddleware
from app.web.routes import api_router

logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.log_level)
    app.state.settings = settings
    session_factory = init_engine(settings)
    app.state.session_factory = session_factory
    client = redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    try:
        await client.ping()
        app.state.redis = client
        logger.info("redis_connected")
    except Exception:
        await client.aclose()
        app.state.redis = None
        logger.warning("redis_unavailable")

    async with session_factory() as session:
        await seed_if_enabled(session, settings.seed_on_start)
        await session.commit()

    logger.info("app_started", env=settings.app_env, llm_enabled=settings.llm_is_live)
    yield
    if app.state.redis is not None:
        await app.state.redis.aclose()
    await dispose_engine()
    logger.info("app_stopped")


def create_app() -> FastAPI:
    application = FastAPI(
        title="AI-наставник 360",
        description="Корпоративное обучение, практика и независимый контроль знаний. ДИС не принимает кадровые решения.",
        version="0.2.0",
        lifespan=lifespan,
    )
    application.add_middleware(RequestContextMiddleware)

    @application.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError):
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            return RedirectResponse("/login?error=Требуется+вход", status_code=303)
        return JSONResponse({"error": exc.code, "message": exc.message}, status_code=exc.status_code)

    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.warning("app_error", code=exc.code, message=exc.message, path=request.url.path)
        accept = request.headers.get("accept", "")
        if "text/html" in accept and exc.status_code in {401, 403, 404}:
            return RedirectResponse(f"/dashboard?error={exc.message}", status_code=303)
        return JSONResponse({"error": exc.code, "message": exc.message}, status_code=exc.status_code)

    application.mount("/static", StaticFiles(directory="app/web/static"), name="static")
    application.include_router(api_router)
    return application


app = create_app()
