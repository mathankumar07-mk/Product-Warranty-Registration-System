import os

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "product_warranty_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
if ENVIRONMENT in {"production", "prod"} and JWT_SECRET_KEY == "change-this-secret-key":
    raise ValueError("JWT_SECRET_KEY must be configured in production")
if ENVIRONMENT in {"production", "prod"} and len(JWT_SECRET_KEY) < 32:
    raise ValueError("JWT_SECRET_KEY must contain at least 32 characters in production")
if ACCESS_TOKEN_EXPIRE_MINUTES < 1:
    raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "backend/uploads/invoices")

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_TLS = os.getenv("SMTP_TLS", "true").lower() == "true"
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@example.com")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Mini E-Commerce")