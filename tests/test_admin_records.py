import io
import os
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


def make_admin():
    db = TestingSessionLocal()
    try:
        admin = Admin(
            name="Records Admin",
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


def register_and_login(name="Records Customer"):
    email = f"{name.replace(' ', '.')}.{uuid4().hex}@example.com"
    assert client.post("/auth/register", json={"name": name, "email": email, "password": "password123"}).status_code == 201
    login = client.post("/auth/login", json={"email": email, "password": "password123"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, email


def paid_order(headers, price="42.00"):
    db = TestingSessionLocal()
    try:
        category = Category(name=f"Rec Cat {uuid4().hex}")
        db.add(category)
        db.flush()
        product = Product(
            category_id=category.id, name="Rec Product", price=Decimal(price),
            stock_quantity=5, brand="Rec", model_number=f"REC-{uuid4().hex}",
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
    order = client.post("/orders", headers=headers, json={})
    assert order.status_code == 201
    order_id = order.json()["id"]
    payment = client.post("/payments", headers=headers, json={"order_id": order_id, "amount": price, "method": "card"})
    assert payment.status_code == 201
    payment_id = payment.json()["id"]
    assert client.post(f"/payments/{payment_id}/simulate", headers=headers, params={"success": True}).status_code == 200
    return order_id


def test_admin_invoice_flow():
    admin = make_admin()
    headers, _ = register_and_login()
    order_id = paid_order(headers)
    listing = client.get("/admin/invoices", headers=admin, params={"page_size": 20})
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1
    invoice = listing.json()["items"][0]
    assert invoice["customer_email"]
    assert invoice["order_id"] == order_id
    detail = client.get(f"/admin/invoices/{invoice['id']}", headers=admin)
    assert detail.status_code == 200
    assert detail.json()["order"]["items"]
    assert "file_path" not in detail.json() or detail.json()["file_path"] is None
    download = client.get(f"/admin/invoices/{invoice['id']}/download", headers=admin)
    assert download.status_code == 200
    assert download.content.startswith(b"%PDF")
    assert client.get("/admin/invoices/999999", headers=admin).status_code == 404


def test_admin_notification_filters():
    admin = make_admin()
    headers, _ = register_and_login()
    paid_order(headers)  # placing an order emits an order notification
    all_notes = client.get("/admin/notifications", headers=admin, params={"page_size": 50})
    assert all_notes.status_code == 200
    assert all_notes.json()["total"] >= 1
    orders_only = client.get("/admin/notifications", headers=admin, params={"type": "order"})
    assert orders_only.status_code == 200
    assert all(n["type"] == "order" for n in orders_only.json()["items"])
    assert client.get("/admin/notifications", headers=admin, params={"type": "bogus"}).status_code == 400


def test_admin_order_detail_and_auth():
    admin = make_admin()
    headers, _ = register_and_login()
    order_id = paid_order(headers)
    detail = client.get(f"/admin/orders/{order_id}", headers=admin)
    assert detail.status_code == 200
    body = detail.json()
    assert body["customer"]["email"]
    assert len(body["items"]) == 1
    assert len(body["payments"]) == 1
    assert body["invoice"]["invoice_number"].startswith("INV-")
    assert client.get("/admin/orders/999999", headers=admin).status_code == 404
    assert client.get(f"/admin/orders/{order_id}", headers=headers).status_code == 401
    filtered = client.get("/admin/orders", headers=admin, params={"q": body["order_number"][:12]})
    assert filtered.status_code == 200
    assert any(o["id"] == order_id for o in filtered.json())
