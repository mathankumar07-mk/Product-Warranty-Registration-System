import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models.admin import Admin
from app.models.category import Category
from app.models.product import Product
from app.models.cart import Cart
from app.models.cart_item import CartItem
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
            name="Actions Admin",
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


def register_and_login(name="Actions Customer"):
    email = f"{name.replace(' ', '.')}.{uuid4().hex}@example.com"
    assert client.post("/auth/register", json={"name": name, "email": email, "password": "password123"}).status_code == 201
    login = client.post("/auth/login", json={"email": email, "password": "password123"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, email


def make_product(price="30.00"):
    db = TestingSessionLocal()
    try:
        category = Category(name=f"Act Cat {uuid4().hex}")
        db.add(category)
        db.flush()
        product = Product(
            category_id=category.id, name="Act Product", price=Decimal(price),
            stock_quantity=5, brand="Act", model_number=f"ACT-{uuid4().hex}",
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product.id, category.id
    finally:
        db.close()


def place_order(headers, product_id):
    db = TestingSessionLocal()
    try:
        me = client.get("/auth/me", headers=headers).json()
        cart = db.query(Cart).filter(Cart.user_id == me["id"]).first()
        if cart is None:
            cart = Cart(user_id=me["id"])
            db.add(cart)
            db.flush()
        db.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=1))
        db.commit()
    finally:
        db.close()
    order = client.post("/orders", headers=headers, json={})
    assert order.status_code == 201
    return order.json()


def test_admin_order_filters_and_csv_export():
    admin, _ = make_admin()
    headers, _ = register_and_login()
    product_id, _ = make_product()
    order = place_order(headers, product_id)
    by_user = client.get("/admin/orders", headers=admin, params={"user_id": order["user_id"]})
    assert by_user.status_code == 200
    assert all(o["user_id"] == order["user_id"] for o in by_user.json())
    by_number = client.get("/admin/orders", headers=admin, params={"q": order["order_number"][:12]})
    assert by_number.status_code == 200
    assert any(o["id"] == order["id"] for o in by_number.json())
    export = client.get("/admin/orders/export", headers=admin)
    assert export.status_code == 200
    assert "text/csv" in export.headers["content-type"]
    assert export.headers["content-disposition"].endswith("orders.csv")
    lines = export.text.strip().splitlines()
    assert lines[0].startswith("id,order_number,")
    assert any(str(order["id"]) in line for line in lines[1:])


def test_admin_password_change_flow():
    admin_headers, admin = make_admin(password="oldpassword123")
    assert client.post("/auth/admin/change-password", headers=admin_headers, json={"old_password": "wrong", "new_password": "newpassword123"}).status_code == 400
    assert client.post("/auth/admin/change-password", headers=admin_headers, json={"old_password": "oldpassword123", "new_password": "newpassword123"}).status_code == 204
    assert client.post("/auth/login", json={"email": admin.email, "password": "oldpassword123"}).status_code == 401
    assert client.post("/auth/login", json={"email": admin.email, "password": "newpassword123"}).status_code == 200
    customer, _ = register_and_login("Pw Customer")
    assert client.post("/auth/admin/change-password", headers=customer, json={"old_password": "password123", "new_password": "newpassword123"}).status_code == 401


def test_admin_actions_are_audited():
    admin, _ = make_admin()
    headers, _ = register_and_login("Audit Customer")
    assert client.post("/auth/admin/change-password", headers=admin, json={"old_password": "password123", "new_password": "password1234"}).status_code == 204
    product_id, _ = make_product()
    order = place_order(headers, product_id)
    # Cancel the order (pending -> cancelled needs no payment).
    assert client.put(f"/orders/{order['id']}", headers=admin, json={"status": "cancelled"}).status_code == 200
    # Full payment flow then refund.
    order2 = place_order(headers, product_id)
    payment = client.post("/payments", headers=headers, json={"order_id": order2["id"], "amount": "30.00", "method": "card"})
    assert payment.status_code == 201
    payment_id = payment.json()["id"]
    assert client.post(f"/payments/{payment_id}/simulate", headers=headers, params={"success": True}).status_code == 200
    assert client.post(f"/payments/{payment_id}/refund", headers=admin).status_code == 200
    # Warranty decision flow.
    policy = client.post("/warranties/policies", headers=admin, json={"product_id": product_id, "warranty_period_months": 12, "terms": "Standard"})
    assert policy.status_code == 201
    purchase = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    reg = client.post(
        "/warranties/register",
        headers=headers,
        json={
            "policy_id": policy.json()["id"], "product_id": product_id,
            "serial_number": f"SN-{uuid4().hex[:12]}", "purchase_source": "Company Website",
            "purchase_date": purchase,
        },
    )
    assert reg.status_code == 201
    assert client.put(f"/warranties/registrations/{reg.json()['id']}", headers=admin, json={"warranty_status": "EXPIRED"}).status_code == 200
    reg_export = client.get("/admin/registrations/export", headers=admin)
    assert reg_export.status_code == 200
    assert reg_export.text.splitlines()[0].startswith("id,warranty_number,")
    logs = client.get("/admin/audit-logs", headers=admin, params={"page_size": 50}).json()
    actions = {entry["action"] for entry in logs}
    assert {"order.status", "payment.refund", "warranty.decision", "admin.change-password"} <= actions
