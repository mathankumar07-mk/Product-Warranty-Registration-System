"""Application configuration (pydantic-settings with legacy constant exports).

Existing modules import module-level constants (``from app.core.config import X``).
New code may import ``settings``. Both stay in sync. PostgreSQL is the only
supported server database; SQLite remains available for the isolated test
suite via ``DATABASE_URL``.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Mini E-Commerce and Product Warranty Registration System"
    APP_ENV: str = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "product_warranty_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
    )
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "backend/uploads/invoices")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() == "true"
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@example.com")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "Mini E-Commerce")


settings = Settings()

# Legacy module-level exports (kept for backward compatibility).
APP_NAME = settings.APP_NAME
APP_ENV = settings.APP_ENV
ENVIRONMENT = settings.APP_ENV.lower()
DEBUG = settings.DEBUG
DB_HOST = settings.DB_HOST
DB_PORT = settings.DB_PORT
DB_NAME = settings.DB_NAME
DB_USER = settings.DB_USER
DB_PASSWORD = settings.DB_PASSWORD
DATABASE_URL_RAW = settings.DATABASE_URL
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
FRONTEND_URL = settings.FRONTEND_URL
UPLOAD_DIR = settings.UPLOAD_DIR
SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT
SMTP_USER = settings.SMTP_USER
SMTP_PASSWORD = settings.SMTP_PASSWORD
SMTP_TLS = settings.SMTP_TLS
EMAIL_FROM = settings.EMAIL_FROM
EMAIL_FROM_NAME = settings.EMAIL_FROM_NAME

if ENVIRONMENT in {"production", "prod"} and JWT_SECRET_KEY == "change-this-secret-key":
    raise ValueError("JWT_SECRET_KEY must be configured in production")
if ENVIRONMENT in {"production", "prod"} and len(JWT_SECRET_KEY) < 32:
    raise ValueError("JWT_SECRET_KEY must contain at least 32 characters in production")
if ACCESS_TOKEN_EXPIRE_MINUTES < 1:
    raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")

CORS_ORIGINS = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
