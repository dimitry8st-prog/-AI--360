from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.logging import get_logger
from app.core.rate_limit import allow_request
from app.core.security import dump_session, session_cookie_kwargs
from app.db.models.user import User
from app.services.auth_service import authenticate_web
from app.web.deps import csrf_from_form, current_user_optional, get_db, request_id_of
from app.web.templating import render

router = APIRouter(tags=["auth"])
logger = get_logger("web.auth")


@router.get("/login")
async def login_form(request: Request):
    if current_user_optional(request):
        return RedirectResponse("/dashboard", status_code=303)
    return render(request, "login.html", title="Вход")


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_db),
    _: str = Depends(csrf_from_form),
):
    redis = getattr(request.app.state, "redis", None)
    settings = request.app.state.settings
    ip = request.client.host if request.client else "unknown"
    if not await allow_request(redis, key=f"login:{ip}", spec=settings.rate_limit_web):
        return render(request, "login.html", title="Вход", error="Слишком много попыток входа", status_code=429)
    try:
        user = await authenticate_web(
            session, email=email, password=password, request_id=request_id_of(request)
        )
    except UnauthorizedError:
        return render(request, "login.html", title="Вход", error="Неверный email или пароль", status_code=401)

    token = dump_session(settings, {"uid": str(user.id)})
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(settings.session_cookie_name, token, **session_cookie_kwargs(settings))
    logger.info("web_login_cookie_set")
    return response


@router.post("/logout")
async def logout(
    request: Request,
    _user: User | None = Depends(current_user_optional),
    _: str = Depends(csrf_from_form),
):
    settings = get_settings()
    logger.info("logout")
    response = RedirectResponse("/login?notice=Вы+вышли", status_code=303)
    response.delete_cookie(settings.session_cookie_name, path="/")
    return response
