"""Application settings. Secrets never logged; prod rejects default SECRET_KEY."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["demo", "dev", "prod"] = "dev"
    secret_key: str = "replace-with-a-long-random-string"
    database_url: str = "sqlite+aiosqlite:///./mentor360.db"
    redis_url: str = "redis://localhost:6379/0"

    web_host: str = "0.0.0.0"
    web_port: int = 8000
    session_cookie_name: str = "dis_session"
    csrf_cookie_name: str = "dis_csrf"

    telegram_bot_token: str = ""
    telegram_mode: Literal["polling", "webhook"] = "polling"
    telegram_webhook_url: str = ""

    llm_enabled: bool = False
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_mentor_model: str = ""
    llm_examiner_model: str = ""
    llm_timeout: int = 30
    llm_max_retries: int = 1
    llm_temperature_mentor: float = 0.3
    llm_temperature_examiner: float = 0.0
    llm_max_tokens: int = 800

    upload_max_mb: int = 10
    upload_allowed_ext: str = "pdf,txt,md"
    retrieval_top_k: int = 5

    rate_limit_telegram: str = "20/minute"
    rate_limit_web: str = "60/minute"
    exam_default_attempt_limit: int = 2
    pass_score_percent: int = 70

    seed_on_start: bool = False
    log_level: str = "INFO"

    @field_validator("secret_key")
    @classmethod
    def secret_not_default_in_prod(cls, value: str, info):
        env = info.data.get("app_env") if info.data else None
        if env == "prod" and value in {"", "replace-with-a-long-random-string", "change-me"}:
            raise ValueError("SECRET_KEY must be set to a strong value in prod")
        return value

    @property
    def allowed_upload_extensions(self) -> set[str]:
        return {ext.strip().lower().lstrip(".") for ext in self.upload_allowed_ext.split(",") if ext.strip()}

    @property
    def mentor_model(self) -> str:
        return self.llm_mentor_model or self.llm_model

    @property
    def examiner_model(self) -> str:
        return self.llm_examiner_model or self.llm_model

    @property
    def session_secure_cookie(self) -> bool:
        return self.app_env == "prod"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def llm_is_live(self) -> bool:
        return self.llm_enabled and bool(self.llm_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
