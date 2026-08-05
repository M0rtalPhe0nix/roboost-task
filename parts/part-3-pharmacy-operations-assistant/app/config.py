"""Runtime settings for the pharmacy operations assistant."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables or a local `.env` file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_model: str = "gemini-3.5-flash-lite"
    operations_data_path: Path = Path("data/operations_data_anonymized.xlsx")
    telegram_bot_token: SecretStr | None = None
    telegram_public_access: bool = False
    telegram_allowed_user_ids: str = ""
    chat_history_messages: int = Field(default=10, ge=1, le=50)
    session_idle_ttl_seconds: int = Field(default=3600, ge=300, le=86400)
    max_active_sessions: int = Field(default=25, ge=1, le=500)
    max_concurrent_messages: int = Field(default=1, ge=1, le=10)
    min_comparison_orders: int = Field(default=50, ge=10)
    min_comparison_days: int = Field(default=14, ge=2)
    min_completeness: float = Field(default=0.90, ge=0.5, le=1.0)
    long_delivery_minutes: float = Field(default=90.0, gt=0)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide immutable settings instance."""

    return Settings()
