from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    SECRET_KEY: str = "super-secret-development-key-change-in-production-min-32-chars-long"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres_dev_password"
    POSTGRES_DB: str = "adaptive_edu_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "sqlite+aiosqlite:///adaptive_edu_dev.db"
    DATABASE_SYNC_URL: str = "sqlite:///adaptive_edu_dev.db"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "curriculum-documents"

    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

if settings.ENVIRONMENT.lower() == "production" and "super-secret-development-key" in settings.SECRET_KEY:
    raise ValueError("CRITICAL SECURITY ERROR: Default SECRET_KEY detected in production environment! Must be overridden via environment variable.")

