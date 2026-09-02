import time
import uuid
from collections.abc import Callable

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import get_settings
from app.core.logging import bind_log_context, get_logger, is_health_path, reset_log_context
from app.core.security import generate_csrf_token, try_load_session
from app.services.auth_service import get_user_by_id

logger = get_logger("http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = request.app.state.settings if hasattr(request.app.state, "settings") else get_settings()
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        started = time.perf_counter()
        reset_log_context()
        bind_log_context(request_id=request_id, source="web")

        csrf = request.cookies.get(settings.csrf_cookie_name)
        if not csrf:
            csrf = generate_csrf_token()
            request.state.csrf_set_cookie = csrf
        request.state.csrf_token = csrf
        request.state.user = None

        factory = getattr(request.app.state, "session_factory", None)
        payload = try_load_session(settings, request.cookies.get(settings.session_cookie_name))
        if factory is not None and payload and payload.get("uid"):
            try:
                async with factory() as session:
                    user = await get_user_by_id(session, uuid.UUID(str(payload["uid"])))
                    request.state.user = user
                    if user is not None:
                        bind_log_context(user_id=user.id, organization_id=user.organization_id)
            except Exception:
                logger.warning("session_user_load_failed")

        try:
            response = await call_next(request)
        except Exception:
            logger.exception("http_unhandled_error", method=request.method, path=request.url.path)
            reset_log_context()
            raise

        duration_ms = int((time.perf_counter() - started) * 1000)
        if not is_health_path(request.url.path):
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=duration_ms,
            )
        response.headers["X-Request-ID"] = request_id
        if getattr(request.state, "csrf_set_cookie", None):
            response.set_cookie(settings.csrf_cookie_name, request.state.csrf_set_cookie, **{
                "httponly": False,
                "samesite": "lax",
                "secure": settings.session_secure_cookie,
                "path": "/",
            })
        reset_log_context()
        return response


def login_redirect() -> RedirectResponse:
    return RedirectResponse("/login?error=Требуется+вход", status_code=303)
