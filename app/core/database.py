from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def _normalize_database_url(raw: str) -> str:
    url = (raw or "").strip()
    if url.startswith("postgres://"):
        # Providers such as Railway expose ``postgres://``; SQLAlchemy
        # expects the ``postgresql://`` scheme.
        return "postgresql://" + url[len("postgres://") :]
    return url


# PostgreSQL is the only supported server database. SQLite URLs are accepted
# solely for the isolated automated test suite.
SUPPORTED_SCHEMES = ("postgresql", "postgresql+psycopg", "postgresql+psycopg2", "sqlite")


def _build_database_url() -> str:
    import os

    database_url = _normalize_database_url(os.getenv("DATABASE_URL", ""))
    if database_url:
        scheme = database_url.split("://", 1)[0]
        if scheme not in SUPPORTED_SCHEMES:
            raise RuntimeError(
                f"Unsupported DATABASE_URL scheme {scheme!r}: only PostgreSQL "
                "(and SQLite for tests) is supported"
            )
        return database_url

    # Local development default: local PostgreSQL (override with DATABASE_URL).
    return URL.create(
        "postgresql+psycopg2",
        username=DB_USER or None,
        password=DB_PASSWORD or None,
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
