# Ganymede API — Core Configuration

"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Application
    APP_NAME: str = "Ganymede"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://ganymede:ganymede@localhost:5432/ganymede"

    # File storage
    STORAGE_PATH: str = "/data/storage"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100 MB

    # Allowed MIME types for upload
    ALLOWED_MIME_TYPES: list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
    ]

    # Parser versions (recorded in provenance)
    PYMUPDF_PARSER_VERSION: str = "1.26.5"
    PYTHON_DOCX_PARSER_VERSION: str = "1.2.0"
    TESSERACT_OCR_VERSION: str = "5.5.3"

    # Security
    SECRET_KEY: str = "dev-secret-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
