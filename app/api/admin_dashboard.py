"""Admin-only dashboard and inspection endpoints (thin handlers)."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func

from app.api.deps import DBSession, get_current_admin
from app.models.admin import Admin
from app.models.notification import NotificationType
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.product import Product
from app.models.user import User
from app.models.warranty_registration import WarrantyRegistration, WarrantyStatus
from app.schemas.order import OrderResponse
from app.schemas.payment import PaymentResponse
from app.schemas.user import UserResponse
from app.services.notification_service import add_user_notification

router = APIRouter(prefix="/admin", tags=["admin"])


class BroadcastRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=1000)


@router.get("/dashboard")
def dashboard(db: DBSession, admin: Admin = Depends(get_current_admin)) -> dict:
    users = db.query(func.count(User.id)).scalar() or 0
    orders = db.query(func.count(Order.id)).scalar() or 0
    revenue = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status == PaymentStatus.completed)
        .scalar()
        or Decimal("0.00")
    )
    pending_warranties = (
        db.query(func.count(WarrantyRegistration.id))
        .filter(WarrantyRegistration.warranty_status == WarrantyStatus.PENDING)
        .scalar()
        or 0
    )
    low_stock = (
        db.query(func.count(Product.id)).filter(Product.stock_quantity <= 5).scalar() or 0
    )
    return {
        "users": int(users),
        "orders": int(orders),
        "revenue": str(revenue),
        "pending_warranties": int(pending_warranties),
        "low_stock_products": int(low_stock),
    }


@router.get("/users", response_model=list[UserResponse])
def list_users(db: DBSession, admin: Admin = Depends(get_current_admin), page: int = 1, page_size: int = 20):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    return (
        db.query(User)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


@router.get("/orders", response_model=list[OrderResponse])
def list_all_orders(
    db: DBSession,
    admin: Admin = Depends(get_current_admin),
    status: str | None = None,
    user_id: int | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    query = db.query(Order).order_by(Order.created_at.desc())
    if status is not None:
        query = query.filter(Order.status == OrderStatus(status))
    if user_id is not None:
        query = query.filter(Order.user_id == user_id)
    if q:
        query = query.filter(Order.order_number.ilike(f"%{q.strip()}%"))
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    return query.offset((page - 1) * page_size).limit(page_size).all()


@router.get("/payments", response_model=list[PaymentResponse])
def list_all_payments(db: DBSession, admin: Admin = Depends(get_current_admin), page: int = 1, page_size: int = 20):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    return (
        db.query(Payment)
        .order_by(Payment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


@router.post("/notifications/broadcast", response_model=dict)
def broadcast(data: BroadcastRequest, db: DBSession, admin: Admin = Depends(get_current_admin)):
    user_ids = [row[0] for row in db.query(User.id).filter(User.is_active.is_(True)).all()]
    for user_id in user_ids:
        add_user_notification(db, user_id, NotificationType.order, data.title, data.message)
    db.commit()
    return {"recipients": len(user_ids)}
