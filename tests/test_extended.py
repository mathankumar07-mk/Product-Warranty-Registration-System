import io
import os
from decimal import Decimal
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models.category import Category
from app.models.product import Product
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


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def register_and_login(name: str):
    email = f"{name.replace(' ', '.')}.{uuid4().hex}@example.com"
    password = "password123"
    assert client.post("/auth/register", json={"name": name, "email": email, "password": password}).status_code == 201
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, login.json(), email, password


def make_admin():
    db = TestingSessionLocal()
    try:
        admin = Admin(name="Ext Admin", email=f"{uuid4().hex}@admin.example.com", password_hash=hash_password("password123"))
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return {"Authorization": f"Bearer {create_access_token(str(admin.id), is_admin=True)}"}
    finally:
        db.close()


def make_product(price="25.00", stock=5):
    db = TestingSessionLocal()
    try:
        category = Category(name=f"Ext Cat {uuid4().hex}")
        db.add(category)
        db.flush()
        product = Product(
            category_id=category.id,
            name="Ext Product",
            price=Decimal(price),
            stock_quantity=stock,
            brand="ExtBrand",
            model_number=f"EXT-{uuid4().hex}",
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product.id, category.id
    finally:
        db.close()


def checkout_setup(headers, price="25.00"):
    product_id, _ = make_product(price=price)
    db = TestingSessionLocal()
    try:
        from app.models.user import User
        from app.models.cart import Cart
        from app.models.cart_item import CartItem

        me = client.get("/auth/me", headers=headers).json()
        cart = Cart(user_id=me["id"])
        db.add(cart)
        db.flush()
        db.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=1))
        db.commit()
    finally:
        db.close()
    order = client.post("/orders", headers=headers, json={})
    assert order.status_code == 201
    return order.json()["id"], Decimal(price)


def test_refresh_rotation_and_logout():
    headers, login, _, _ = register_and_login("Refresh User")
    refresh = login["refresh_token"]
    assert refresh
    rotated = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != refresh
    # Old refresh token is revoked
    assert client.post("/auth/refresh", json={"refresh_token": refresh}).status_code == 401
    # Logout revokes the new one
    assert client.post("/auth/logout", json={"refresh_token": rotated.json()["refresh_token"]}).status_code == 204
    assert client.post("/auth/refresh", json={"refresh_token": rotated.json()["refresh_token"]}).status_code == 401


def test_change_password_and_reset_flow():
    headers, _, email, _ = register_and_login("Password User")
    assert client.post("/auth/change-password", headers=headers, json={"old_password": "password123", "new_password": "newpassword123"}).status_code == 204
    assert client.post("/auth/login", json={"email": email, "password": "password123"}).status_code == 401
    assert client.post("/auth/login", json={"email": email, "password": "newpassword123"}).status_code == 200
    forgot = client.post("/auth/forgot-password", json={"email": email})
    assert forgot.status_code == 200
    token = forgot.json()["reset_token"]
    assert token  # no SMTP configured in tests
    assert client.post("/auth/reset-password", json={"token": token, "new_password": "resetpassword123"}).status_code == 204
    assert client.post("/auth/login", json={"email": email, "password": "resetpassword123"}).status_code == 200


def test_payment_idempotency_and_transitions():
    headers, _, _, _ = register_and_login("Idempotency User")
    order_id, total = checkout_setup(headers)
    body = {"order_id": order_id, "amount": str(total), "method": "card"}
    first = client.post("/payments", headers={**headers, "Idempotency-Key": "key-123"}, json=body)
    assert first.status_code == 201
    second = client.post("/payments", headers={**headers, "Idempotency-Key": "key-123"}, json=body)
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    payment_id = first.json()["id"]
    # Illegal transition pending -> refunded
    assert client.put(f"/payments/{payment_id}", headers=make_admin(), json={"status": "refunded"}).status_code == 400
    # Simulate success then refund
    assert client.post(f"/payments/{payment_id}/simulate", headers=headers, params={"success": True}).status_code == 200
    refund = client.post(f"/payments/{payment_id}/refund", headers=make_admin())
    assert refund.status_code == 200
    assert refund.json()["status"] == "refunded"


def test_webhook_and_invoice_download():
    headers, _, _, _ = register_and_login("Webhook User")
    other, _, _, _ = register_and_login("Webhook Other")
    order_id, total = checkout_setup(headers)
    payment = client.post("/payments", headers=headers, json={"order_id": order_id, "amount": str(total), "method": "upi"}).json()
    payload = {"payment_id": payment["id"], "status": "completed", "transaction_id": "WEBHOOK-1"}
    import json as jsonlib

    raw = jsonlib.dumps(payload).encode()
    bad = client.post("/payments/webhook", content=raw, headers={"X-Webhook-Signature": "wrong", "Content-Type": "application/json"})
    assert bad.status_code == 401
    ok = client.post("/payments/webhook", content=raw, headers={"X-Webhook-Signature": "sandbox", "Content-Type": "application/json"})
    assert ok.status_code == 200
    invoice = client.get(f"/invoices/order/{order_id}", headers=headers)
    assert invoice.status_code == 200
    download = client.get(f"/invoices/{invoice.json()['id']}/download", headers=headers)
    assert download.status_code == 200
    assert client.get(f"/invoices/{invoice.json()['id']}/download", headers=other).status_code == 404


def test_category_policy_fallback_and_external_proof():
    headers, _, _, _ = register_and_login("Policy User")
    admin = make_admin()
    product_id, category_id = make_product()
    cat_policy = client.post(
        "/warranties/policies",
        headers=admin,
        json={"category_id": category_id, "warranty_period_months": 12, "terms": "Category default"},
    )
    assert cat_policy.status_code == 201
    assert client.get("/warranties/policies").status_code == 200
    from datetime import datetime, timedelta, timezone

    recent = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    base = {
        "policy_id": cat_policy.json()["id"],
        "product_id": product_id,
        "serial_number": f"EXT-{uuid4().hex}",
        "purchase_date": recent,
    }
    # External source without proof is rejected
    denied = client.post("/warranties/register", headers=headers, json={**base, "purchase_source": "Amazon"})
    assert denied.status_code == 409
    # With proof it registers as PENDING_REVIEW
    reg = client.post(
        "/warranties/register",
        headers=headers,
        json={**base, "serial_number": f"EXT-{uuid4().hex}", "purchase_source": "Amazon", "proof_reference": "INV-PROOF-1"},
    )
    assert reg.status_code == 201
    assert reg.json()["warranty_status"] == "PENDING_REVIEW"
    assert reg.json()["warranty_number"]
    # Admin search sees it
    search = client.get("/warranties/registrations/search", headers=admin, params={"status": "PENDING_REVIEW"})
    assert search.status_code == 200
    assert any(r["id"] == reg.json()["id"] for r in search.json())


def test_admin_lists_broadcast_and_csv_import():
    headers, _, _, _ = register_and_login("Admin List User")
    admin = make_admin()
    assert client.get("/admin/dashboard", headers=admin).status_code == 200
    assert client.get("/admin/users", headers=admin).status_code == 200
    assert client.get("/admin/orders", headers=admin).status_code == 200
    assert client.get("/admin/payments", headers=admin).status_code == 200
    assert client.get("/admin/users", headers=headers).status_code == 401
    cast = client.post("/admin/notifications/broadcast", headers=admin, json={"title": "Hello", "message": "World"})
    assert cast.status_code == 200
    assert cast.json()["recipients"] >= 1
    assert any(n["title"] == "Hello" for n in client.get("/notifications", headers=headers).json())
    _, category_id = make_product()
    csv_text = (
        "name,model_number,price,stock_quantity,brand,category_id\n"
        f"CSV One,CSV-{uuid4().hex},19.99,3,CSVBrand,{category_id}\n"
        f"CSV Bad,CSV-{uuid4().hex},not-a-price,3,CSVBrand,{category_id}\n"
    )
    imported = client.post(
        "/products/import",
        headers=admin,
        files={"file": ("catalog.csv", io.BytesIO(csv_text.encode()), "text/csv")},
    )
    assert imported.status_code == 200
    assert imported.json()["created"] == 1
    assert len(imported.json()["errors"]) == 1
