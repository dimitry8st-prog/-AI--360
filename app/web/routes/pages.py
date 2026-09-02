from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers import get_llm_provider
from app.db.models.user import User
from app.services.learning_service import own_progress_payload
from app.web.deps import get_db, require_login
from app.web.templating import render

router = APIRouter(tags=["pages"])


@router.get("/")
async def index(request: Request):
    settings = request.app.state.settings
    provider = get_llm_provider(settings)
    return render(
        request,
        "index.html",
        app_env=settings.app_env,
        llm_mode=provider.name,
        telegram_ready=bool(settings.telegram_bot_token),
    )


@router.get("/dashboard")
async def dashboard(
    request: Request,
    user: User = Depends(require_login),
    session: AsyncSession = Depends(get_db),
):
    progress = []
    try:
        progress = await own_progress_payload(session, user)
    except Exception:
        progress = []
    return render(request, "dashboard.html", title="Панель", progress=progress, roles=sorted(user.role_names))
