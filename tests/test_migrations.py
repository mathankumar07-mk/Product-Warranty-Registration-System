import os
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models.admin import Admin
from app.core.security import create_access_token, hash_password

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIG_DB = "sqlite:///./test_mig_tmp.db"
MIG_FILE = os.path.join(ROOT, "test_mig_tmp.db")


def _alembic_config():
    cfg = Config(os.path.join(ROOT, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(ROOT, "migrations"))
    return cfg


def _temp_engine():
    return create_engine(MIG_DB, connect_args={"check_same_thread": False})


import pytest  # noqa: E402


@pytest.fixture()
def migrated_database(monkeypatch):
    for suffix in ("", "-journal", "-wal", "-shm"):
        try:
            os.remove(MIG_FILE + suffix)
        except OSError:
            pass
    monkeypatch.setenv("DATABASE_URL", MIG_DB)
    engine = _temp_engine()
    Base.metadata.create_all(bind=engine)
    command.stamp(_alembic_config(), "head")
    yield engine
    engine.dispose()
    for suffix in ("", "-journal", "-wal", "-shm"):
        try:
            os.remove(MIG_FILE + suffix)
        except OSError:
            pass


def _admin_headers(engine):
    session = sessionmaker(bind=engine)()
    try:
        admin = Admin(
            name="Mig Admin",
            email=f"{uuid4().hex}@admin.example.com",
            password_hash=hash_password("password123"),
            is_active=True,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        return {"Authorization": f"Bearer {create_access_token(str(admin.id), is_admin=True)}"}
    finally:
        session.close()


def test_migration_0006_downgrade_upgrade_cycle(migrated_database):
    engine = migrated_database
    assert inspect(engine).has_table("audit_logs")
    assert "is_active" in {c["name"] for c in inspect(engine).get_columns("admins")}

    command.downgrade(_alembic_config(), "-1")
    assert not inspect(engine).has_table("audit_logs")

    # The app degrades gracefully when the table is missing: 503 with guidance.
    try:
        sessions = []

        def override():
            session = sessionmaker(bind=engine)()
            sessions.append(session)
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override
        client = TestClient(app)
        headers = _admin_headers(engine)
        degraded = client.get("/admin/audit-logs", headers=headers)
        assert degraded.status_code == 503
        assert "migrations" in degraded.json()["detail"].lower()

        command.upgrade(_alembic_config(), "head")
        assert inspect(engine).has_table("audit_logs")
        recovered = client.get("/admin/audit-logs", headers=headers)
        assert recovered.status_code == 200
        assert isinstance(recovered.json(), list)
    finally:
        app.dependency_overrides.pop(get_db, None)
