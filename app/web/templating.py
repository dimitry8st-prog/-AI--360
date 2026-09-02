from pathlib import Path

from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import HTMLResponse

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

_STATUS_TONES = {
    "published": "ok",
    "completed": "ok",
    "passed": "ok",
    "active": "ok",
    "assigned": "info",
    "in_progress": "info",
    "draft": "muted",
    "archived": "muted",
    "needs_repeat": "warn",
    "needs_review": "warn",
    "failed": "danger",
}


def status_tone(status: str | None) -> str:
    return _STATUS_TONES.get((status or "").lower(), "muted")


def nav_is_active(current: str, href: str) -> bool:
    if href == "/":
        return current == "/"
    return current == href or current.startswith(href.rstrip("/") + "/")


templates.env.globals["status_tone"] = status_tone
templates.env.globals["nav_is_active"] = nav_is_active


def render(request: Request, name: str, status_code: int = 200, **context) -> HTMLResponse:
    context.setdefault("current_user", getattr(request.state, "user", None))
    context.setdefault("csrf_token", getattr(request.state, "csrf_token", ""))
    context.setdefault("notice", request.query_params.get("notice", ""))
    context.setdefault("error", request.query_params.get("error", ""))
    context.setdefault("title", "AI-наставник 360")
    return templates.TemplateResponse(request, name, context, status_code=status_code)
