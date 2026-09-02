from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import HTMLResponse

templates = Jinja2Templates(directory="app/web/templates")


def render(request: Request, name: str, status_code: int = 200, **context) -> HTMLResponse:
    context.setdefault("current_user", getattr(request.state, "user", None))
    context.setdefault("csrf_token", getattr(request.state, "csrf_token", ""))
    context.setdefault("notice", request.query_params.get("notice", ""))
    context.setdefault("error", request.query_params.get("error", ""))
    context.setdefault("title", "AI-наставник 360")
    return templates.TemplateResponse(request, name, context, status_code=status_code)
