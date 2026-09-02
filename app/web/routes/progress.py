from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.services.learning_service import own_progress_payload
from app.web.deps import get_db, require_login
from app.web.templating import render

router = APIRouter(tags=["progress"])


@router.get("/progress")
async def progress_page(
    request: Request,
    user: User = Depends(require_login),
    session: AsyncSession = Depends(get_db),
):
    rows = await own_progress_payload(session, user)
    return render(request, "progress.html", title="Прогресс", rows=rows)
