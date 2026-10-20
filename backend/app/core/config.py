"""Victory Crest One - Application Configuration
Environment-based settings with fallback defaults, secret management, and database configuration.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
import re


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "Victory Crest One"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Server Bindings
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000

    # PostgreSQL Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/victory_crest_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 10

    # SQLite Local / Offline Database
    LOCAL_DB_PATH: str = "local_data/victory_crest_local.db"

    # Security
    SECRET_KEY: str = "victory-crest-one-dev-secret-key-change-in-production-2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Integrations (Optional)
    AI_ASSISTANT_ENABLED: bool = False
    AI_API_KEY: Optional[str] = None
    PAYMENT_SANDBOX_MODE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def is_postgres(self) -> bool:
        return self.DATABASE_URL.startswith("postgresql")

    @property
    def masked_database_url(self) -> str:
        """Return database URL with password masked for safe diagnostic display and logs."""
        try:
            return re.sub(r":([^@]+)@", r":****@", self.DATABASE_URL)
        except Exception:
            return "postgresql://****:****@localhost/..."


settings = Settings()
