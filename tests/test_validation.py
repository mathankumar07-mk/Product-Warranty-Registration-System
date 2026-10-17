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


def make_admin():
    db = TestingSessionLocal()
    try:
        admin = Admin(
            name="Validation Admin",
            email=f"{uuid4().hex}@admin.example.com",
            password_hash=hash_password("password123"),
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return {"Authorization": f"Bearer {create_access_token(str(admin.id), is_admin=True)}"}
    finally:
        db.close()


def test_email_is_normalized_and_unique():
    mixed = f"MiXeD.{uuid4().hex}@Example.COM"
    assert client.post("/auth/register", json={"name": "Mixed Case", "email": mixed, "password": "password123"}).status_code == 201
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {client.post('/auth/login', json={'email': mixed.upper(), 'password': 'password123'}).json()['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == mixed.lower()
    assert me.json()["is_active"] is True
    # Same address in different case is a duplicate.
    assert client.post("/auth/register", json={"name": "Dupe", "email": mixed.lower(), "password": "password123"}).status_code == 409
    # Blank names are rejected.
    assert client.post("/auth/register", json={"name": "   ", "email": f"blank.{uuid4().hex}@example.com", "password": "password123"}).status_code == 409


def test_admin_email_is_normalized():
    admin = make_admin()
    mixed = f"SuB.{uuid4().hex}@Example.COM"
    created = client.post("/admin/admins", headers=admin, json={"name": "Sub Admin", "email": mixed, "password": "password123"})
    assert created.status_code == 201
    assert created.json()["email"] == mixed.lower()


def test_category_names_are_case_insensitive_unique():
    admin = make_admin()
    first = client.post("/categories", headers=admin, json={"name": "Gadgets", "description": "x"})
    assert first.status_code == 201
    first_id = first.json()["id"]
    assert client.post("/categories", headers=admin, json={"name": "gadgets", "description": "y"}).status_code == 409
    other = client.post("/categories", headers=admin, json={"name": "Widgets", "description": "z"})
    assert other.status_code == 201
    other_id = other.json()["id"]
    # Renaming onto another category (any case) conflicts.
    assert client.put(f"/categories/{other_id}", headers=admin, json={"name": "GADGETS"}).status_code == 409
    # Renaming to itself in a different case is allowed.
    assert client.put(f"/categories/{first_id}", headers=admin, json={"name": "GADGETS"}).status_code == 200


def test_warranty_duration_bounds():
    admin = make_admin()
    db = TestingSessionLocal()
    try:
        from app.models.category import Category

        category = Category(name=f"Val Cat {uuid4().hex}")
        db.add(category)
        db.commit()
        db.refresh(category)
        category_id = category.id
    finally:
        db.close()
    assert client.post("/warranties/policies", headers=admin, json={"category_id": category_id, "warranty_period_months": 0, "terms": "t"}).status_code == 422
    assert client.post("/warranties/policies", headers=admin, json={"category_id": category_id, "warranty_period_months": 121, "terms": "t"}).status_code == 422
    ok = client.post("/warranties/policies", headers=admin, json={"category_id": category_id, "warranty_period_months": 120, "terms": "ten years"})
    assert ok.status_code == 201
