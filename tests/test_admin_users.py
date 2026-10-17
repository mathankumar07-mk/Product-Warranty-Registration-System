import os
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models.admin import Admin
from app.models.user import User
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
            name="Users Admin",
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


def register_customer(name="Lifecycle Customer"):
    email = f"{name.replace(' ', '.')}.{uuid4().hex}@example.com"
    assert client.post("/auth/register", json={"name": name, "email": email, "password": "password123"}).status_code == 201
    return email


def test_user_search_detail_and_deactivation():
    admin, _ = make_admin()
    email = register_customer()
    found = client.get("/admin/users/search", headers=admin, params={"q": email})
    assert found.status_code == 200
    assert any(u["email"] == email.lower() for u in found.json())
    user_id = next(u["id"] for u in found.json() if u["email"] == email.lower())

    detail = client.get(f"/admin/users/{user_id}", headers=admin)
    assert detail.status_code == 200
    assert set(detail.json().keys()) >= {"orders", "invoices", "warranties", "is_active"}

    assert client.patch(f"/admin/users/{user_id}", headers=admin, json={"is_active": False}).status_code == 200
    assert client.post("/auth/login", json={"email": email, "password": "password123"}).status_code == 401
    assert client.patch(f"/admin/users/{user_id}", headers=admin, json={"is_active": True}).status_code == 200
    assert client.post("/auth/login", json={"email": email, "password": "password123"}).status_code == 200
    assert client.get(f"/admin/users/{user_id}", headers=admin).json()["is_active"] is True


def test_user_delete_guards_history():
    admin, _ = make_admin()
    email = register_customer("History Customer")
    user_id = client.get("/admin/users/search", headers=admin, params={"q": email}).json()[0]["id"]
    # Give the customer an order through the real checkout flow.
    login = client.post("/auth/login", json={"email": email, "password": "password123"}).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    db = TestingSessionLocal()
    try:
        from decimal import Decimal
        from app.models.category import Category
        from app.models.product import Product
        from app.models.cart import Cart
        from app.models.cart_item import CartItem

        category = Category(name=f"Hist Cat {uuid4().hex}")
        db.add(category)
        db.flush()
        product = Product(
            category_id=category.id, name="Hist Product", price=Decimal("10.00"),
            stock_quantity=5, brand="Hist", model_number=f"HIST-{uuid4().hex}",
        )
        db.add(product)
        db.flush()
        me = client.get("/auth/me", headers=headers).json()
        cart = Cart(user_id=me["id"])
        db.add(cart)
        db.flush()
        db.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=1))
        db.commit()
    finally:
        db.close()
    assert client.post("/orders", headers=headers, json={}).status_code == 201
    assert client.delete(f"/admin/users/{user_id}", headers=admin).status_code == 409

    fresh_email = register_customer("Fresh Customer")
    fresh_id = client.get("/admin/users/search", headers=admin, params={"q": fresh_email}).json()[0]["id"]
    assert client.delete(f"/admin/users/{fresh_id}", headers=admin).status_code == 204


def test_admin_guards_and_deactivation():
    admin_headers, admin = make_admin()
    email = f"second.{uuid4().hex}@example.com"
    created = client.post("/admin/admins", headers=admin_headers, json={"name": "Second", "email": email, "password": "password123"})
    assert created.status_code == 201
    second_id = created.json()["id"]
    # Duplicate email is rejected.
    assert client.post("/admin/admins", headers=admin_headers, json={"name": "Dupe", "email": email, "password": "password123"}).status_code == 409
    # Admins cannot deactivate or delete themselves.
    assert client.patch(f"/admin/admins/{admin.id}", headers=admin_headers, json={"is_active": False}).status_code == 409
    assert client.delete(f"/admin/admins/{admin.id}", headers=admin_headers).status_code == 409
    # Deactivating another admin works while a second active admin remains.
    assert client.patch(f"/admin/admins/{second_id}", headers=admin_headers, json={"is_active": False}).status_code == 200
    assert client.post("/auth/login", json={"email": email, "password": "password123"}).status_code == 401
    # A deactivated admin token is rejected with 403, not treated as admin.
    db = TestingSessionLocal()
    try:
        target = db.query(User).filter(User.email == "nobody@example.com").first()
        assert target is None
    finally:
        db.close()
    from app.core.security import create_access_token as make_token

    stale = {"Authorization": f"Bearer {make_token(str(second_id), is_admin=True)}"}
    assert client.get("/admins/me", headers=stale).status_code == 403
    # Cleanup: delete the deactivated admin (another active admin remains).
    assert client.delete(f"/admin/admins/{second_id}", headers=admin_headers).status_code == 204
