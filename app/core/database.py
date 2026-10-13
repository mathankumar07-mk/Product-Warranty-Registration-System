from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def _normalize_database_url(raw: str) -> str:
    url = (raw or "").strip()
    if url.startswith("mysql://"):
        # Default to the pure-Python driver when no driver is specified.
        return "mysql+pymysql://" + url[len("mysql://") :]
    return url


def _build_database_url() -> str:
    import os

    database_url = _normalize_database_url(os.getenv("DATABASE_URL", ""))
    if database_url:
        return database_url

    # Backward compatibility: existing deployments use Postgres defaults
    # (port 5432 / user postgres). Keep that driver; new installs default to MySQL.
    legacy_postgres = str(DB_PORT) == "5432" or DB_USER == "postgres"
    driver = "postgresql+psycopg2" if legacy_postgres else "mysql+pymysql"
    return URL.create(
        driver,
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
    ).render_as_string(hide_password=False)


DATABASE_URL = _build_database_url()
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs: dict = {"connect_args": {"check_same_thread": False}}
else:
    engine_kwargs = {"pool_pre_ping": True}
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def initialize_database() -> None:
    import app.models  # noqa: F401  (register all models)

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
