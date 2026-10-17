import os
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models.admin import Admin
from app.core.security import create_access_token, hash_password

test_engine = create_engine("sqlite:///./test_api.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def make_admin(password="password123"):
    db = TestingSessionLocal()
    try:
        admin = Admin(
            name="Overview Admin",
            email=f"{uuid4().hex}@admin.example.com",
            password_hash=hash_password(password),
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return {"Authorization": f"Bearer {create_access_token(str(admin.id), is_admin=True)}"}, admin
    finally:
        db.close()


def register_customer(name="Overview Customer"):
    email = f"{name.replace(' ', '.')}.{uuid4().hex}@example.com"
    assert client.post("/auth/register", json={"name": name, "email": email, "password": "password123"}).status_code == 201
    login = client.post("/auth/login", json={"email": email, "password": "password123"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_overview_shape_and_auth():
    admin, _ = make_admin()
    customer = register_customer()
    response = client.get("/admin/overview", headers=admin)
    assert response.status_code == 200
    body = response.json()
    assert set(body["totals"]) >= {"customers", "active_products", "categories", "orders", "warranty_registrations", "total_paid"}
    assert body["totals"]["customers"] >= 1
    assert len(body["sales_trend"]) == 15
    assert set(body.keys()) >= {"orders_by_status", "payments_by_status", "warranties_by_status", "recent_orders", "recent_users", "recent_warranties", "top_products"}
    # Customer tokens and anonymous callers are rejected.
    assert client.get("/admin/overview", headers=customer).status_code == 401
    assert client.get("/admin/overview").status_code == 401


def test_reports_and_settings_expose_no_secrets():
    admin, _ = make_admin()
    reports = client.get("/admin/reports/summary", headers=admin)
    assert reports.status_code == 200
    assert set(reports.json().keys()) >= {"overview", "sales_trend", "top_products", "categories", "payment_methods", "policy_count"}
    settings = client.get("/admin/settings", headers=admin)
    assert settings.status_code == 200
    text = settings.text.lower()
    assert "jwt_secret_key" not in text
    assert "smtp_password" not in text
    assert "db_password" not in text
    assert "password_hash" not in text
    assert settings.json()["db_dialect"]


def test_audit_log_records_admin_creation():
    admin, _ = make_admin()
    email = f"sub.{uuid4().hex}@example.com"
    created = client.post("/admin/admins", headers=admin, json={"name": "Sub", "email": email, "password": "password123"})
    assert created.status_code == 201
    logs = client.get("/admin/audit-logs", headers=admin)
    assert logs.status_code == 200
    actions = [entry["action"] for entry in logs.json()]
    assert "admin.create" in actions
    entry = next(e for e in logs.json() if e["action"] == "admin.create")
    assert entry["entity_type"] == "admin"
    assert entry["admin_id"] is not None
