import os
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "product_warranty_db")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "postgres")

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core import database as database_module
from app.core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.main import app
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.purchase_invoice import PurchaseInvoice
from app.models.category import Category
from app.models.product import Product
from app.models.warranty_policy import WarrantyPolicy
from app.models.address import Address
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.user import User
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


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "API is running successfully"


def test_registration_and_login():
    response = client.post("/auth/register", json={"name": "Test User", "email": "test@example.com", "password": "password123"})
    assert response.status_code in {201, 409}
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"


def test_protected_endpoint_requires_authentication():
    response = client.get("/users/me")
    assert response.status_code == 401


def test_malformed_token_subject_is_rejected():
    token = jwt.encode(
        {"sub": "not-an-id", "is_admin": False},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_database_url_escapes_reserved_password_characters(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(database_module, "DB_HOST", "localhost")
    monkeypatch.setattr(database_module, "DB_PORT", "5432")
    monkeypatch.setattr(database_module, "DB_NAME", "warranty")
    monkeypatch.setattr(database_module, "DB_USER", "store_user")
    monkeypatch.setattr(database_module, "DB_PASSWORD", "pass:/@word")

    parsed_url = make_url(database_module._build_database_url())
    assert parsed_url.password == "pass:/@word"
    assert parsed_url.database == "warranty"


def test_admin_registration_requires_admin_authentication():
    response = client.post(
        "/auth/admin/register",
        json={"name": "Unexpected Admin", "email": "unexpected@example.com", "password": "password123"},
    )
    assert response.status_code == 401


def test_password_length_is_limited_to_bcrypt_supported_bytes():
    response = client.post(
        "/auth/register",
        json={
            "name": "Long Password",
            "email": f"{uuid4().hex}@example.com",
            "password": "😀" * 19,
        },
    )
    assert response.status_code == 422


def test_disabled_users_cannot_reuse_tokens_or_sign_in():
    headers = register_and_login("Disabled Account")
    user_id = client.get("/auth/me", headers=headers).json()["id"]

    db = TestingSessionLocal()
    try:
        user = db.get(User, user_id)
        user.is_active = False
        db.commit()
        email = user.email
    finally:
        db.close()

    assert client.get("/auth/me", headers=headers).status_code == 401
    assert client.post(
        "/auth/login",
        json={"email": email, "password": "password123"},
    ).status_code == 401


def register_and_login(name: str):
    email = f"{uuid4().hex}@example.com"
    client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": "password123"},
    )
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_user_can_create_address():
    headers = register_and_login("Address Owner")
    response = client.post(
        "/users/me/addresses",
        headers=headers,
        json={
            "label": "Home",
            "line1": "1 Main Street",
            "city": "Austin",
            "state": "TX",
            "postal_code": "78701",
            "country": "US",
        },
    )
    assert response.status_code == 201
    assert response.json()["label"] == "Home"


def test_admin_address_operations_use_the_requested_user():
    first_user_headers = register_and_login("First Address User")
    target_user_headers = register_and_login("Target Address User")
    target_user_id = client.get("/auth/me", headers=target_user_headers).json()["id"]

    db = TestingSessionLocal()
    try:
        admin = Admin(
            name="Address Admin",
            email=f"{uuid4().hex}@admin.example.com",
            password_hash=hash_password("password123"),
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        headers = {
            "Authorization": f"Bearer {create_access_token(str(admin.id), is_admin=True)}"
        }
    finally:
        db.close()

    response = client.post(
        "/addresses",
        headers=headers,
        json={
            "user_id": target_user_id,
            "label": "Target home",
            "line1": "2 Main Street",
            "city": "Austin",
            "state": "TX",
            "postal_code": "78701",
            "country": "US",
        },
    )
    assert response.status_code == 201
    address_id = response.json()["id"]
    assert response.json()["user_id"] == target_user_id
    assert client.get("/users/me/addresses", headers=first_user_headers).json() == []

    update = client.put(
        f"/addresses/{address_id}",
        headers=headers,
        json={"label": "Updated target home"},
    )
    assert update.status_code == 200
    assert update.json()["label"] == "Updated target home"


def test_order_creation_decrements_stock_clears_cart_and_notifies_user():
    headers = register_and_login("Checkout User")
    user_id = client.get("/auth/me", headers=headers).json()["id"]
    db = TestingSessionLocal()
    try:
        category = Category(name=f"Checkout Category {uuid4().hex}")
        db.add(category)
        db.flush()
        product = Product(
            category_id=category.id,
            name="Checkout Product",
            price=Decimal("12.50"),
            stock_quantity=3,
            brand="Checkout Brand",
            model_number=f"CHECKOUT-{uuid4().hex}",
        )
        db.add(product)
        db.flush()
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.flush()
        db.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=2))
        db.commit()
        product_id = product.id
    finally:
        db.close()

    response = client.post("/orders", headers=headers, json={})
    assert response.status_code == 201
    assert response.json()["total_amount"] == "25.00"
    assert client.get("/cart", headers=headers).json()["items"] == []
    db = TestingSessionLocal()
    try:
        assert db.get(Product, product_id).stock_quantity == 1
    finally:
        db.close()
    notifications = client.get("/notifications", headers=headers).json()
    assert any(notification["type"] == "order" for notification in notifications)


def test_admin_cannot_confirm_unpaid_order_and_cancellation_restores_stock():
    user_headers = register_and_login("Order Transition User")
    user_id = client.get("/auth/me", headers=user_headers).json()["id"]
    db = TestingSessionLocal()
    try:
        category = Category(name=f"Transition Category {uuid4().hex}")
        db.add(category)
        db.flush()
        product = Product(
            category_id=category.id,
            name="Transition Product",
            price=Decimal("18.00"),
            stock_quantity=4,
            brand="Transition Brand",
            model_number=f"TRANSITION-{uuid4().hex}",
        )
        db.add(product)
        db.flush()
        order = Order(user_id=user_id, total_amount=Decimal("18.00"))
        db.add(order)
        db.flush()
        db.add(OrderItem(order_id=order.id, product_id=product.id, quantity=2, unit_price=Decimal("18.00")))
        db.commit()
        order_id = order.id
        product_id = product.id
        admin = Admin(
            name="Transition Admin",
            email=f"{uuid4().hex}@admin.example.com",
            password_hash=hash_password("password123"),
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        admin_headers = {
            "Authorization": f"Bearer {create_access_token(str(admin.id), is_admin=True)}"
        }
    finally:
        db.close()

    unpaid_confirmation = client.put(
        f"/orders/{order_id}",
        headers=admin_headers,
        json={"status": "confirmed"},
    )
    assert unpaid_confirmation.status_code == 409

    cancellation = client.put(
        f"/orders/{order_id}",
        headers=admin_headers,
        json={"status": "cancelled"},
    )
    assert cancellation.status_code == 200
    db = TestingSessionLocal()
    try:
        assert db.get(Product, product_id).stock_quantity == 6
    finally:
        db.close()


def test_product_listing_returns_pagination_and_validates_filters():
    db = TestingSessionLocal()
    try:
        category = Category(name=f"Browse Category {uuid4().hex}")
        db.add(category)
        db.flush()
        db.add(
            Product(
                category_id=category.id,
                name="Browse Product",
                price=Decimal("19.99"),
                stock_quantity=2,
                brand="Browse Brand",
                model_number=f"BROWSE-{uuid4().hex}",
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.get("/products", params={"min_price": "10", "max_price": "20"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["page"] == 1
    assert len(payload["products"]) == 1

    assert client.get("/products", params={"sort": "category"}).status_code == 422
    assert client.get("/products", params={"min_price": "20", "max_price": "10"}).status_code == 422


def test_payment_endpoints_only_expose_owned_orders():
    owner_headers = register_and_login("Payment Owner")
    other_headers = register_and_login("Other User")
    owner_id = client.get("/auth/me", headers=owner_headers).json()["id"]

    db = TestingSessionLocal()
    try:
        order = Order(user_id=owner_id, total_amount=Decimal("10.00"))
        db.add(order)
        db.flush()
        payment = Payment(order_id=order.id, amount=Decimal("10.00"), method="card")
        db.add(payment)
        db.commit()
        db.refresh(payment)
        payment_id = payment.id
        order_id = order.id
    finally:
        db.close()

    assert client.get(f"/payments/{payment_id}", headers=other_headers).status_code == 404
    assert client.get(f"/payments?order_id={order_id}", headers=other_headers).status_code == 404


def test_invoice_endpoints_only_expose_owned_orders():
    owner_headers = register_and_login("Invoice Owner")
    other_headers = register_and_login("Other Invoice User")
    owner_id = client.get("/auth/me", headers=owner_headers).json()["id"]

    db = TestingSessionLocal()
    try:
        order = Order(user_id=owner_id, total_amount=Decimal("25.00"))
        db.add(order)
        db.flush()
        invoice = PurchaseInvoice(
            order_id=order.id,
            invoice_number=f"INV-TEST-{uuid4().hex}",
            total_amount=Decimal("25.00"),
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        invoice_id = invoice.id
        order_id = order.id
    finally:
        db.close()

    assert client.get(f"/invoices/{invoice_id}", headers=other_headers).status_code == 404
    assert client.get(f"/invoices/order/{order_id}", headers=other_headers).status_code == 404


def test_warranty_registration_validates_policy_and_owner():
    owner_headers = register_and_login("Warranty Owner")
    other_headers = register_and_login("Other Warranty User")
    owner_id = client.get("/auth/me", headers=owner_headers).json()["id"]

    db = TestingSessionLocal()
    try:
        category = Category(name=f"Warranty Category {uuid4().hex}")
        db.add(category)
        db.flush()
        first_product = Product(
            category_id=category.id,
            name="Warranty Product One",
            price=Decimal("10.00"),
            stock_quantity=5,
            brand="Test Brand",
            model_number=f"MODEL-{uuid4().hex}",
        )
        second_product = Product(
            category_id=category.id,
            name="Warranty Product Two",
            price=Decimal("20.00"),
            stock_quantity=5,
            brand="Test Brand",
            model_number=f"MODEL-{uuid4().hex}",
        )
        db.add_all([first_product, second_product])
        db.flush()
        policy = WarrantyPolicy(product_id=first_product.id, warranty_period_months=12, terms="Test terms")
        db.add(policy)
        db.commit()
        db.refresh(policy)
        policy_id = policy.id
        first_product_id = first_product.id
        second_product_id = second_product.id
    finally:
        db.close()

    mismatch = client.post(
        "/warranties/register",
        headers=owner_headers,
        json={
            "policy_id": policy_id,
            "product_id": second_product_id,
            "serial_number": "SERIAL-MISMATCH",
            "purchase_source": "Company Website",
            "purchase_date": "2024-01-15T10:00:00",
        },
    )
    assert mismatch.status_code == 409

    registration = client.post(
        "/warranties/register",
        headers=owner_headers,
        json={
            "policy_id": policy_id,
            "product_id": first_product_id,
            "serial_number": "SERIAL-OWNER",
            "purchase_source": "Company Website",
            "purchase_date": "2024-01-15T10:00:00",
        },
    )
    assert registration.status_code == 201
    registration_id = registration.json()["id"]
    # Check that response contains new fields
    assert "warranty_start_date" in registration.json()
    assert "warranty_end_date" in registration.json()
    assert "warranty_status" in registration.json()
    notifications = client.get("/notifications", headers=owner_headers).json()
    assert any(notification["type"] == "warranty" for notification in notifications)

    assert client.get(
        f"/warranties/registrations/{registration_id}",
        headers=other_headers,
    ).status_code == 404
    assert client.get(
        f"/warranties/registrations/{registration_id}/validity",
        headers=other_headers,
    ).status_code == 404
    assert client.get(
        f"/warranties/registrations/{registration_id}/validity",
        headers=other_headers,
    ).status_code == 404


def test_order_rejects_another_users_address():
    owner_headers = register_and_login("Order Owner")
    other_headers = register_and_login("Address Owner")
    owner_id = client.get("/auth/me", headers=owner_headers).json()["id"]
    other_id = client.get("/auth/me", headers=other_headers).json()["id"]

    db = TestingSessionLocal()
    try:
        category = Category(name=f"Order Category {uuid4().hex}")
        db.add(category)
        db.flush()
        product = Product(
            category_id=category.id,
            name="Order Product",
            price=Decimal("15.00"),
            stock_quantity=2,
            brand="Test Brand",
            model_number=f"ORDER-{uuid4().hex}",
        )
        address = Address(
            user_id=other_id,
            label="Other Home",
            line1="2 Main Street",
            city="Austin",
            state="TX",
            postal_code="78701",
            country="US",
        )
        db.add_all([product, address])
        db.flush()
        db.add(Cart(user_id=owner_id))
        db.flush()
        db.add(CartItem(cart_id=db.query(Cart).filter(Cart.user_id == owner_id).one().id, product_id=product.id, quantity=1))
        db.commit()
        address_id = address.id
    finally:
        db.close()

    response = client.post(
        "/orders",
        headers=owner_headers,
        json={"shipping_address_id": address_id, "billing_address_id": address_id},
    )
    assert response.status_code == 400


def test_payment_amount_must_match_order_total():
    owner_headers = register_and_login("Payment Amount Owner")
    owner_id = client.get("/auth/me", headers=owner_headers).json()["id"]

    db = TestingSessionLocal()
    try:
        order = Order(user_id=owner_id, total_amount=Decimal("25.00"))
        db.add(order)
        db.commit()
        db.refresh(order)
        order_id = order.id
    finally:
        db.close()

    response = client.post(
        "/payments",
        headers=owner_headers,
        json={"order_id": order_id, "amount": "1.00", "method": "card"},
    )
    assert response.status_code == 400


def test_successful_payment_creates_invoice():
    owner_headers = register_and_login("Invoice Creation Owner")
    owner_id = client.get("/auth/me", headers=owner_headers).json()["id"]

    db = TestingSessionLocal()
    try:
        order = Order(user_id=owner_id, total_amount=Decimal("30.00"))
        db.add(order)
        db.flush()
        payment = Payment(
            order_id=order.id,
            amount=Decimal("30.00"),
            method="card",
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        payment_id = payment.id
        order_id = order.id
    finally:
        db.close()

    response = client.post(
        f"/payments/{payment_id}/simulate",
        headers=owner_headers,
    )
    assert response.status_code == 200
    invoice = client.get(f"/invoices/order/{order_id}", headers=owner_headers)
    assert invoice.status_code == 200
    assert invoice.json()["total_amount"] == "30.00"
    notifications = client.get("/notifications", headers=owner_headers).json()
    assert any(notification["type"] == "payment" for notification in notifications)


def test_warranty_registration_with_purchase_invoice():
    """Test warranty registration with purchase invoice validation"""
    owner_headers = register_and_login("Warranty Invoice Owner")
    owner_id = client.get("/auth/me", headers=owner_headers).json()["id"]

    db = TestingSessionLocal()
    try:
        category = Category(name=f"Warranty Invoice Category {uuid4().hex}")
        db.add(category)
        db.flush()
        product = Product(
            category_id=category.id,
            name="Warranty Invoice Product",
            price=Decimal("100.00"),
            stock_quantity=10,
            brand="Test Brand",
            model_number=f"MODEL-INV-{uuid4().hex}",
        )
        db.add(product)
        db.flush()
        policy = WarrantyPolicy(product_id=product.id, warranty_period_months=24, terms="Test terms for invoice")
        db.add(policy)
        
        # Create order with this product
        order = Order(user_id=owner_id, total_amount=Decimal("100.00"))
        db.add(order)
        db.flush()
        order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=1, unit_price=Decimal("100.00"))
        db.add(order_item)
        db.flush()
        
        # Create invoice
        invoice = PurchaseInvoice(
            order_id=order.id,
            invoice_number=f"INV-TEST-{uuid4().hex}",
            total_amount=Decimal("100.00"),
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        invoice_id = invoice.id
        product_id = product.id
        policy_id = policy.id
    finally:
        db.close()

    # Register warranty with invoice
    registration = client.post(
        "/warranties/register",
        headers=owner_headers,
        json={
            "policy_id": policy_id,
            "product_id": product_id,
            "serial_number": "SERIAL-INV-001",
            "purchase_source": "Company Website",
            "purchase_date": "2024-01-15T10:00:00",
            "purchase_invoice_id": invoice_id,
        },
    )
    assert registration.status_code == 201
    assert registration.json()["purchase_invoice_id"] == invoice_id
    assert registration.json()["warranty_status"] in ["PENDING", "ACTIVE", "EXPIRED"]


def test_warranty_registration_duplicate_prevention():
    """Test that duplicate warranty registration for same product and invoice is prevented"""
    owner_headers = register_and_login("Warranty Duplicate Owner")
    owner_id = client.get("/auth/me", headers=owner_headers).json()["id"]

    db = TestingSessionLocal()
    try:
        category = Category(name=f"Warranty Dup Category {uuid4().hex}")
        db.add(category)
        db.flush()
        product = Product(
            category_id=category.id,
            name="Warranty Dup Product",
            price=Decimal("50.00"),
            stock_quantity=5,
            brand="Test Brand",
            model_number=f"MODEL-DUP-{uuid4().hex}",
        )
        db.add(product)
        db.flush()
        policy = WarrantyPolicy(product_id=product.id, warranty_period_months=12, terms="Test terms")
        db.add(policy)
        
        order = Order(user_id=owner_id, total_amount=Decimal("50.00"))
        db.add(order)
        db.flush()
        order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=1, unit_price=Decimal("50.00"))
        db.add(order_item)
        db.flush()
        
        invoice = PurchaseInvoice(
            order_id=order.id,
            invoice_number=f"INV-DUP-{uuid4().hex}",
            total_amount=Decimal("50.00"),
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        invoice_id = invoice.id
        product_id = product.id
        policy_id = policy.id
    finally:
        db.close()

    # First registration
    reg1 = client.post(
        "/warranties/register",
        headers=owner_headers,
        json={
            "policy_id": policy_id,
            "product_id": product_id,
            "serial_number": "SERIAL-DUP-001",
            "purchase_source": "Company Website",
            "purchase_date": "2024-01-15T10:00:00",
            "purchase_invoice_id": invoice_id,
        },
    )
    assert reg1.status_code == 201

    # Second registration with same product and invoice should fail
    reg2 = client.post(
        "/warranties/register",
        headers=owner_headers,
        json={
            "policy_id": policy_id,
            "product_id": product_id,
            "serial_number": "SERIAL-DUP-002",
            "purchase_source": "Amazon",
            "purchase_date": "2024-01-15T10:00:00",
            "purchase_invoice_id": invoice_id,
        },
    )
    assert reg2.status_code == 409
    assert "already registered" in reg2.json()["detail"]


def test_warranty_validity_check():
    """Test warranty validity endpoint"""
    owner_headers = register_and_login("Warranty Validity Owner")
    owner_id = client.get("/auth/me", headers=owner_headers).json()["id"]

    db = TestingSessionLocal()
    try:
        category = Category(name=f"Warranty Validity Category {uuid4().hex}")
        db.add(category)
        db.flush()
        product = Product(
            category_id=category.id,
            name="Warranty Validity Product",
            price=Decimal("75.00"),
            stock_quantity=5,
            brand="Test Brand",
            model_number=f"MODEL-VAL-{uuid4().hex}",
        )
        db.add(product)
        db.flush()
        policy = WarrantyPolicy(product_id=product.id, warranty_period_months=12, terms="Test terms")
        db.add(policy)
        db.commit()
        db.refresh(policy)
        product_id = product.id
        policy_id = policy.id
    finally:
        db.close()

    # Register warranty with recent purchase date (should be ACTIVE)
    registration = client.post(
        "/warranties/register",
        headers=owner_headers,
        json={
            "policy_id": policy_id,
            "product_id": product_id,
            "serial_number": "SERIAL-VAL-001",
            "purchase_source": "Company Website",
            "purchase_date": "2024-01-15T10:00:00",
        },
    )
    assert registration.status_code == 201
    registration_id = registration.json()["id"]

    # Check validity
    validity = client.get(
        f"/warranties/registrations/{registration_id}/validity",
        headers=owner_headers,
    )
    assert validity.status_code == 200
    assert "valid" in validity.json()
    assert "warranty_status" in validity.json()
    assert "warranty_start_date" in validity.json()
    assert "warranty_end_date" in validity.json()
    assert "days_remaining" in validity.json()
