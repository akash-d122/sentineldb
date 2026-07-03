"""Application settings loaded from environment variables."""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    ENV: Literal["development", "production", "testing"] = "development"

    # Database
    POSTGRES_PASSWORD: str = "change_me_postgres"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    # Redis / Celery
    REDIS_PASSWORD: str = "change_me_redis"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # LLM
    GOOGLE_API_KEY: str = ""
    LITELLM_MODEL: str = "gemini/gemini-2.5-flash-lite"

    # CORS – default to local dev servers; restrict to real frontend URL in production
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Security
    WEBHOOK_SECRET: str = ""

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://sentinel_app:{self.POSTGRES_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/sentineldb"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"


settings = Settings()
