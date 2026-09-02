"""Password hashing, session signing, CSRF tokens. No JWT in MVP."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import Settings

SESSION_MAX_AGE_SECONDS = 60 * 60 * 12
CSRF_MAX_AGE_SECONDS = 60 * 60 * 8


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key, salt="dis-session")


def dump_session(settings: Settings, payload: dict[str, Any]) -> str:
    data = {**payload, "iat": datetime.now(UTC).isoformat()}
    return _serializer(settings).dumps(data)


def load_session(settings: Settings, token: str) -> dict[str, Any]:
    return _serializer(settings).loads(token, max_age=SESSION_MAX_AGE_SECONDS)


def try_load_session(settings: Settings, token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        return load_session(settings, token)
    except (BadSignature, SignatureExpired):
        return None


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_signature(settings: Settings, token: str) -> str:
    return hmac.new(settings.secret_key.encode(), token.encode(), hashlib.sha256).hexdigest()


def verify_csrf(settings: Settings, cookie_token: str | None, form_token: str | None) -> bool:
    if not cookie_token or not form_token:
        return False
    return hmac.compare_digest(cookie_token, form_token)


def session_cookie_kwargs(settings: Settings) -> dict[str, Any]:
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.session_secure_cookie,
        "max_age": SESSION_MAX_AGE_SECONDS,
        "path": "/",
    }


def csrf_cookie_kwargs(settings: Settings) -> dict[str, Any]:
    return {
        "httponly": False,
        "samesite": "lax",
        "secure": settings.session_secure_cookie,
        "max_age": CSRF_MAX_AGE_SECONDS,
        "path": "/",
    }


def expires_at(minutes: int) -> datetime:
    return datetime.now(UTC) + timedelta(minutes=minutes)
