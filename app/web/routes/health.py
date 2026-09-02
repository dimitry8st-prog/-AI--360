from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.ai.providers import get_llm_provider
from app.schemas.common import HealthStatus, ReadinessStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    return HealthStatus(status="ok")


@router.get("/health/live", response_model=HealthStatus)
async def live() -> HealthStatus:
    return HealthStatus(status="ok")


@router.get("/health/ready")
async def ready(request: Request):
    database = "ok"
    redis_status = "ok"
    settings = request.app.state.settings
    try:
        async with request.app.state.session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        database = "error"

    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is None:
        redis_status = "error"
    else:
        try:
            await redis_client.ping()
        except Exception:
            redis_status = "error"

    llm = "live" if settings.llm_is_live else "stub"
    provider = get_llm_provider(settings)
    if not provider.available and settings.llm_enabled:
        llm = "unavailable"

    payload = ReadinessStatus(
        status="ok" if database == "ok" and redis_status == "ok" else "degraded",
        database=database,
        redis=redis_status,
        llm=llm,
    )
    code = 200 if payload.status == "ok" else 503
    return JSONResponse(payload.model_dump(), status_code=code)
