"""Structured logging with secret masking and request context."""

import logging
import re
import sys
from typing import Any
from uuid import UUID

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars, merge_contextvars

_SECRET_KEYS = {
    "password",
    "password_hash",
    "secret",
    "secret_key",
    "token",
    "telegram_bot_token",
    "api_key",
    "llm_api_key",
    "authorization",
    "cookie",
    "csrf",
    "csrf_token",
    "correct_answer",
    "check_answer",
}

_TOKEN_RE = re.compile(r"(sk-|ghp_|xox[baprs]-)[A-Za-z0-9_\-]{8,}")

HEALTH_PATHS = ("/health", "/health/live", "/health/ready")


def _mask_value(value: Any) -> Any:
    if isinstance(value, str):
        if len(value) > 8:
            masked = _TOKEN_RE.sub("***", value)
            if masked != value:
                return masked
        return value
    if isinstance(value, dict):
        return _mask_event_dict(value)
    if isinstance(value, list):
        return [_mask_value(item) for item in value]
    return value


def _mask_event_dict(event: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for key, value in event.items():
        lowered = key.lower()
        if lowered in _SECRET_KEYS or any(
            part in lowered for part in ("token", "secret", "password", "api_key", "csrf")
        ):
            masked[key] = "***"
        else:
            masked[key] = _mask_value(value)
    return masked


def _censor(_, __, event_dict: dict[str, Any]) -> dict[str, Any]:
    return _mask_event_dict(event_dict)


def setup_logging(level: int | str = logging.INFO) -> None:
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )
    logging.getLogger("uvicorn.access").disabled = True
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _censor,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None):
    return structlog.get_logger(name)


def bind_log_context(
    *,
    request_id: str | None = None,
    user_id: UUID | str | None = None,
    organization_id: UUID | str | None = None,
    source: str | None = None,
    telegram_id: int | None = None,
) -> None:
    payload: dict[str, Any] = {}
    if request_id:
        payload["request_id"] = request_id
    if user_id is not None:
        payload["user_id"] = str(user_id)
    if organization_id is not None:
        payload["organization_id"] = str(organization_id)
    if source:
        payload["source"] = source
    if telegram_id is not None:
        payload["telegram_id"] = telegram_id
    if payload:
        bind_contextvars(**payload)


def reset_log_context() -> None:
    clear_contextvars()


def is_health_path(path: str) -> bool:
    return path in HEALTH_PATHS or path.startswith("/static")
