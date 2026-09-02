import os

os.environ.setdefault("APP_ENV", "demo")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("LLM_ENABLED", "false")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "")
os.environ.setdefault("SEED_ON_START", "false")
os.environ.setdefault("LOG_LEVEL", "WARNING")

from app.core.config import get_settings

get_settings.cache_clear()
