"""Extended admin endpoints: overview, users, admins, invoices, notifications, reports, audit, settings.

All handlers require an active admin JWT (``get_current_admin`` verifies
``is_admin`` claim + active status server-side; never trusts client roles).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_

from app.api.deps import DBSession, get_current_admin
from app.models.admin import Admin
from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.notification import Notification, NotificationType
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.payment import Payment, PaymentStatus
from app.models.product import Product
from app.models.purchase_invoice import PurchaseInvoice
from app.models.user import User
from app.models.warranty_policy import WarrantyPolicy
from app.models.warranty_registration import WarrantyRegistration, WarrantyStatus
from app.schemas.admin import AdminCreate, AdminResponse
from app.schemas.user import UserResponse
from app.services import admin_service, audit_service

router = APIRouter(prefix="/admin", tags=["admin-extended"])


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value)


def _money(value) -> str:
    if value is None:
        return "0.00"
    return str(value)


class UserStatusUpdate(BaseModel):
    is_active: bool


class AdminStatusUpdate(BaseModel):
    is_active: bool


class AuditLogResponse(BaseModel):
    id: int
    admin_id: int | None
    action: str
    entity_type: str | None
    entity_id: str | None
    details: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


def _active_admin_count(db: DBSession) -> int:
    try:
        return int(db.query(func.count(Admin.id)).filter(Admin.is_active.is_(True)).scalar() or 0)
    except Exception:
        # Column missing on databases created before migration 0006.
        return int(db.query(func.count(Admin.id)).scalar() or 0)


def _ensure_not_last_active_admin(db: DBSession, target: Admin) -> None:
    if not getattr(target, "is_active", True):
        return  # already inactive; deactivating again is harmless
    if _active_admin_count(db) <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot deactivate or remove the last active administrator",
        )


# ---------------------------------------------------------------- overview ---

@router.get("/overview")
def overview(db: DBSession, admin: Admin = Depends(get_current_admin)) -> dict:
    total_customers = int(db.query(func.count(User.id)).scalar() or 0)
    active_products = int(db.query(func.count(Product.id)).filter(Product.is_active.is_(True)).scalar() or 0)
    total_categories = int(db.query(func.count(Category.id)).scalar() or 0)
    total_orders = int(db.query(func.count(Order.id)).scalar() or 0)

    orders_by_status: dict[str, int] = {}
    for st in OrderStatus:
        orders_by_status[st.value] = int(
            db.query(func.count(Order.id)).filter(Order.status == st).scalar() or 0
        )

    payments_by_status: dict[str, dict] = {}
    total_paid = Decimal("0.00")
    for st in PaymentStatus:
        count = int(db.query(func.count(Payment.id)).filter(Payment.status == st).scalar() or 0)
        amount = (
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.status == st)
            .scalar()
            or Decimal("0.00")
        )
        payments_by_status[st.value] = {"count": count, "amount": _money(amount)}
        if st == PaymentStatus.completed:
            total_paid = Decimal(str(amount))

    total_registrations = int(db.query(func.count(WarrantyRegistration.id)).scalar() or 0)
    warranties_by_status: dict[str, int] = {}
    for st in WarrantyStatus:
        warranties_by_status[st.value] = int(
            db.query(func.count(WarrantyRegistration.id))
            .filter(WarrantyRegistration.warranty_status == st)
            .scalar()
            or 0
        )
    now = datetime.now(timezone.utc)
    soon = now + timedelta(days=30)
    expiring_soon = int(
        db.query(func.count(WarrantyRegistration.id))
        .filter(
            WarrantyRegistration.warranty_status == WarrantyStatus.ACTIVE,
            WarrantyRegistration.warranty_end_date <= soon,
            WarrantyRegistration.warranty_end_date >= now,
        )
        .scalar()
        or 0
    )

    recent_orders = (
        db.query(Order).order_by(Order.created_at.desc()).limit(5).all()
    )
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    recent_warranties = (
        db.query(WarrantyRegistration).order_by(WarrantyRegistration.created_at.desc()).limit(5).all()
    )

    # Sales trend: last 14 days, aggregated in Python (dialect-agnostic).
    since = now - timedelta(days=14)
    recent_paid_orders = (
        db.query(Order).filter(Order.created_at >= since).order_by(Order.created_at.asc()).all()
    )
    trend: dict[str, dict] = {}
    for i in range(14, -1, -1):
        day = (now - timedelta(days=i)).date().isoformat()
        trend[day] = {"orders": 0, "revenue": "0.00", "_total": Decimal("0.00")}
    for o in recent_paid_orders:
        day = o.created_at.date().isoformat() if o.created_at else None
        if day in trend:
            trend[day]["orders"] += 1
            trend[day]["_total"] = trend[day]["_total"] + Decimal(str(o.total_amount or 0))
    sales_trend = [
        {"date": day, "orders": v["orders"], "revenue": str(v["_total"])}
        for day, v in sorted(trend.items())
    ]

    # Product performance: top 5 by quantity sold (non-cancelled orders).
    top_rows = (
        db.query(
            Product.id,
            Product.name,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("units"),
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status != OrderStatus.cancelled)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )
    top_products = [
        {"product_id": r[0], "name": r[1], "units_sold": int(r[2] or 0), "revenue": _money(r[3])}
        for r in top_rows
    ]

    return {
        "totals": {
            "customers": total_customers,
            "active_products": active_products,
            "categories": total_categories,
            "orders": total_orders,
            "warranty_registrations": total_registrations,
            "total_paid": _money(total_paid),
        },
        "orders_by_status": orders_by_status,
        "payments_by_status": payments_by_status,
        "warranties_by_status": warranties_by_status,
        "expiring_soon_warranties": expiring_soon,
        "recent_orders": [
            {
                "id": o.id,
                "order_number": o.order_number,
                "user_id": o.user_id,
                "status": o.status.value if o.status else None,
                "total_amount": _money(o.total_amount),
                "created_at": _iso(o.created_at),
            }
            for o in recent_orders
        ],
        "recent_users": [
            {"id": u.id, "name": u.name, "email": u.email, "created_at": _iso(u.created_at)}
            for u in recent_users
        ],
        "recent_warranties": [
            {
                "id": w.id,
                "warranty_number": w.warranty_number,
                "status": w.warranty_status.value if w.warranty_status else None,
                "created_at": _iso(w.created_at),
            }
            for w in recent_warranties
        ],
        "sales_trend": sales_trend,
        "top_products": top_products,
    }


# ------------------------------------------------------------------ admins ---

@router.get("/admins", response_model=list[AdminResponse])
def list_admins(db: DBSession, admin: Admin = Depends(get_current_admin)):
    return db.query(Admin).order_by(Admin.created_at.asc()).all()


@router.post("/admins", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
def create_admin_endpoint(data: AdminCreate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        created = admin_service.create_admin(db, data)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    audit_service.log_admin_action(
        db,
        admin_id=admin.id,
        action="admin.create",
        entity_type="admin",
        entity_id=created.id,
        details=f"Created admin {created.email}",
    )
    return created


@router.patch("/admins/{admin_id}", response_model=AdminResponse)
def update_admin_status(
    admin_id: int, data: AdminStatusUpdate, db: DBSession, admin: Admin = Depends(get_current_admin)
):
    target = db.get(Admin, admin_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    if not data.is_active:
        if target.id == admin.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admins cannot deactivate their own account")
        _ensure_not_last_active_admin(db, target)
    target.is_active = data.is_active
    db.commit()
    db.refresh(target)
    audit_service.log_admin_action(
        db,
        admin_id=admin.id,
        action="admin.deactivate" if not data.is_active else "admin.activate",
        entity_type="admin",
        entity_id=target.id,
        details=f"Set is_active={data.is_active} for {target.email}",
    )
    return target


@router.delete("/admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin(admin_id: int, db: DBSession, admin: Admin = Depends(get_current_admin)):
    target = db.get(Admin, admin_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    if target.id == admin.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admins cannot delete their own account")
    _ensure_not_last_active_admin(db, target)
    email = target.email
    db.delete(target)
    db.commit()
    audit_service.log_admin_action(
        db,
        admin_id=admin.id,
        action="admin.delete",
        entity_type="admin",
        entity_id=admin_id,
        details=f"Deleted admin {email}",
    )
    return None


# ------------------------------------------------------------------- users ---

@router.get("/users/search", response_model=list[UserResponse])
def search_users(
    db: DBSession,
    admin: Admin = Depends(get_current_admin),
    q: str | None = Query(default=None, max_length=120),
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    query = db.query(User)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(User.name.ilike(like), User.email.ilike(like), User.phone.ilike(like)))
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))
    return (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


@router.get("/users/{user_id}")
def get_user_detail(user_id: int, db: DBSession, admin: Admin = Depends(get_current_admin)) -> dict:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).limit(20).all()
    invoices = (
        db.query(PurchaseInvoice)
        .join(Order, PurchaseInvoice.order_id == Order.id)
        .filter(Order.user_id == user_id)
        .order_by(PurchaseInvoice.created_at.desc())
        .limit(20)
        .all()
    )
    warranties = (
        db.query(WarrantyRegistration)
        .filter(WarrantyRegistration.user_id == user_id)
        .order_by(WarrantyRegistration.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "is_active": user.is_active,
        "created_at": _iso(user.created_at),
        "orders": [
            {
                "id": o.id,
                "order_number": o.order_number,
                "status": o.status.value if o.status else None,
                "total_amount": _money(o.total_amount),
                "created_at": _iso(o.created_at),
            }
            for o in orders
        ],
        "invoices": [
            {
                "id": i.id,
                "invoice_number": i.invoice_number,
                "order_id": i.order_id,
                "total_amount": _money(i.total_amount),
                "created_at": _iso(i.created_at),
            }
            for i in invoices
        ],
        "warranties": [
            {
                "id": w.id,
                "warranty_number": w.warranty_number,
                "product_id": w.product_id,
                "status": w.warranty_status.value if w.warranty_status else None,
                "warranty_end_date": _iso(w.warranty_end_date),
            }
            for w in warranties
        ],
    }


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user_status(
    user_id: int, data: UserStatusUpdate, db: DBSession, admin: Admin = Depends(get_current_admin)
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    audit_service.log_admin_action(
        db,
        admin_id=admin.id,
        action="user.deactivate" if not data.is_active else "user.activate",
        entity_type="user",
        entity_id=user.id,
        details=f"Set is_active={data.is_active} for {user.email}",
    )
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: DBSession, admin: Admin = Depends(get_current_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    order_count = int(db.query(func.count(Order.id)).filter(Order.user_id == user_id).scalar() or 0)
    warranty_count = int(
        db.query(func.count(WarrantyRegistration.id)).filter(WarrantyRegistration.user_id == user_id).scalar() or 0
    )
    if order_count or warranty_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete customer with historical orders or warranties; deactivate instead to preserve records",
        )
    email = user.email
    db.delete(user)
    db.commit()
    audit_service.log_admin_action(
        db,
        admin_id=admin.id,
        action="user.delete",
        entity_type="user",
        entity_id=user_id,
        details=f"Deleted customer {email}",
    )
    return None


# ------------------------------------------------------------------ orders ---

def _csv_cell(value) -> str:
    text = "" if value is None else str(value)
    if text[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


@router.get("/orders/export")
def export_orders_csv(
    db: DBSession,
    admin: Admin = Depends(get_current_admin),
    status: str | None = None,
):
    import csv
    import io

    from fastapi.responses import StreamingResponse

    query = db.query(Order).order_by(Order.created_at.desc())
    if status is not None:
        query = query.filter(Order.status == OrderStatus(status))
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "order_number", "user_id", "customer_email", "status", "total_amount", "created_at"])
    for order in query.all():
        writer.writerow(
            [
                _csv_cell(order.id),
                _csv_cell(order.order_number),
                _csv_cell(order.user_id),
                _csv_cell(order.user.email if order.user else None),
                _csv_cell(order.status.value if order.status else None),
                _csv_cell(order.total_amount),
                _csv_cell(_iso(order.created_at)),
            ]
        )
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=orders.csv"},
    )


@router.get("/registrations/export")
def export_registrations_csv(
    db: DBSession,
    admin: Admin = Depends(get_current_admin),
    status: str | None = None,
):
    import csv
    import io

    from fastapi.responses import StreamingResponse

    query = db.query(WarrantyRegistration).order_by(WarrantyRegistration.created_at.desc())
    if status is not None:
        try:
            query = query.filter(WarrantyRegistration.warranty_status == WarrantyStatus(status))
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {status}") from error
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["id", "warranty_number", "user_id", "product_id", "serial_number", "status", "purchase_date", "warranty_end_date"]
    )
    for reg in query.all():
        writer.writerow(
            [
                _csv_cell(reg.id),
                _csv_cell(reg.warranty_number),
                _csv_cell(reg.user_id),
                _csv_cell(reg.product_id),
                _csv_cell(reg.serial_number),
                _csv_cell(reg.warranty_status.value if reg.warranty_status else None),
                _csv_cell(_iso(reg.purchase_date)),
                _csv_cell(_iso(reg.warranty_end_date)),
            ]
        )
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=warranty-registrations.csv"},
    )


@router.get("/orders/{order_id}")
def get_order_admin(order_id: int, db: DBSession, admin: Admin = Depends(get_current_admin)) -> dict:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    customer = order.user
    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status.value if order.status else None,
        "total_amount": _money(order.total_amount),
        "created_at": _iso(order.created_at),
        "updated_at": _iso(order.updated_at),
        "customer": (
            {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
            }
            if customer
            else None
        ),
        "items": [
            {
                "id": it.id,
                "product_id": it.product_id,
                "product_name": it.product.name if it.product else None,
                "quantity": it.quantity,
                "unit_price": _money(it.unit_price),
            }
            for it in order.items
        ],
        "payments": [
            {
                "id": p.id,
                "amount": _money(p.amount),
                "status": p.status.value if p.status else None,
                "method": p.method.value if hasattr(p.method, "value") else p.method,
                "transaction_id": p.transaction_id,
                "created_at": _iso(p.created_at),
            }
            for p in order.payments
        ],
        "invoice": (
            {
                "id": order.invoice.id,
                "invoice_number": order.invoice.invoice_number,
                "total_amount": _money(order.invoice.total_amount),
            }
            if order.invoice
            else None
        ),
    }


# ---------------------------------------------------------------- invoices ---

@router.get("/invoices")
def list_invoices_admin(
    db: DBSession,
    admin: Admin = Depends(get_current_admin),
    q: str | None = Query(default=None, max_length=120),
    order_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    query = db.query(PurchaseInvoice).order_by(PurchaseInvoice.created_at.desc())
    if order_id is not None:
        query = query.filter(PurchaseInvoice.order_id == order_id)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(PurchaseInvoice.invoice_number.ilike(like))
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "items": [
            {
                "id": i.id,
                "invoice_number": i.invoice_number,
                "order_id": i.order_id,
                "user_id": i.order.user_id if i.order else None,
                "customer_email": i.order.user.email if i.order and i.order.user else None,
                "total_amount": _money(i.total_amount),
                "tax_amount": _money(i.tax_amount),
                "created_at": _iso(i.created_at),
            }
            for i in rows
        ],
    }


@router.get("/invoices/{invoice_id}")
def get_invoice_admin(invoice_id: int, db: DBSession, admin: Admin = Depends(get_current_admin)) -> dict:
    invoice = db.get(PurchaseInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    order = invoice.order
    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "order_id": invoice.order_id,
        "total_amount": _money(invoice.total_amount),
        "tax_amount": _money(invoice.tax_amount),
        "file_path": None,  # never leak server paths
        "created_at": _iso(invoice.created_at),
        "order": (
            {
                "id": order.id,
                "order_number": order.order_number,
                "user_id": order.user_id,
                "status": order.status.value if order.status else None,
                "total_amount": _money(order.total_amount),
                "items": [
                    {"product_id": it.product_id, "quantity": it.quantity, "unit_price": _money(it.unit_price)}
                    for it in order.items
                ],
            }
            if order
            else None
        ),
    }


@router.get("/invoices/{invoice_id}/download")
def download_invoice_admin(invoice_id: int, db: DBSession, admin: Admin = Depends(get_current_admin)):
    import mimetypes
    import os

    invoice = db.get(PurchaseInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if not invoice.file_path or not os.path.isfile(invoice.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice file not available")
    filename = os.path.basename(invoice.file_path)
    media_type, _ = mimetypes.guess_type(filename)
    return FileResponse(invoice.file_path, filename=filename, media_type=media_type or "application/octet-stream")


# ------------------------------------------------------------- notifications ---

@router.get("/notifications")
def list_notifications_admin(
    db: DBSession,
    admin: Admin = Depends(get_current_admin),
    type: str | None = Query(default=None),
    is_read: bool | None = None,
    user_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    query = db.query(Notification).order_by(Notification.created_at.desc())
    if type:
        try:
            query = query.filter(Notification.type == NotificationType(type))
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid type: {type}") from error
    if is_read is not None:
        query = query.filter(Notification.is_read.is_(is_read))
    if user_id is not None:
        query = query.filter(Notification.user_id == user_id)
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "items": [
            {
                "id": n.id,
                "user_id": n.user_id,
                "type": n.type.value if n.type else None,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": _iso(n.created_at),
            }
            for n in rows
        ],
    }


# ----------------------------------------------------------------- reports ---

@router.get("/reports/summary")
def reports_summary(db: DBSession, admin: Admin = Depends(get_current_admin)) -> dict:
    overview_data = overview(db, admin)
    # Category breakdown: products per category + active policies.
    categories = db.query(Category).order_by(Category.name.asc()).all()
    category_rows = []
    for c in categories:
        product_count = int(db.query(func.count(Product.id)).filter(Product.category_id == c.id).scalar() or 0)
        category_rows.append({"id": c.id, "name": c.name, "products": product_count})
    # Payment method breakdown (safe fields only).
    method_rows = (
        db.query(Payment.method, func.count(Payment.id), func.coalesce(func.sum(Payment.amount), 0))
        .group_by(Payment.method)
        .all()
    )
    return {
        "overview": {
            "totals": overview_data["totals"],
            "orders_by_status": overview_data["orders_by_status"],
            "payments_by_status": overview_data["payments_by_status"],
            "warranties_by_status": overview_data["warranties_by_status"],
        },
        "sales_trend": overview_data["sales_trend"],
        "top_products": overview_data["top_products"],
        "categories": category_rows,
        "payment_methods": [
            {"method": str(m[0].value) if hasattr(m[0], "value") else str(m[0]), "count": int(m[1] or 0), "amount": _money(m[2])}
            for m in method_rows
        ],
        "policy_count": int(db.query(func.count(WarrantyPolicy.id)).scalar() or 0),
    }


# --------------------------------------------------------------- audit logs ---

@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs_endpoint(
    db: DBSession,
    admin: Admin = Depends(get_current_admin),
    action: str | None = None,
    entity_type: str | None = None,
    admin_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    try:
        return audit_service.list_audit_logs(
            db, action=action, entity_type=entity_type, admin_id=admin_id, page=page, page_size=page_size
        )
    except Exception as error:
        # Table missing when migration 0006 has not run yet.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audit logs unavailable: run migrations (0006_audit_logs)",
        ) from error


# ---------------------------------------------------------------- settings ---

@router.get("/settings")
def get_settings(db: DBSession, admin: Admin = Depends(get_current_admin)) -> dict:
    from app.core import config as app_config

    def _safe_db_dialect() -> str:
        raw = getattr(app_config, "DATABASE_URL_RAW", "") or ""
        if "://" in raw:
            return raw.split("://", 1)[0]
        return "sqlite" if "sqlite" in raw.lower() else "configured"

    return {
        "app_name": getattr(app_config, "APP_NAME", "Mini E-Commerce"),
        "environment": getattr(app_config, "APP_ENV", "development"),
        "frontend_url": getattr(app_config, "FRONTEND_URL", ""),
        "cors_origins": getattr(app_config, "CORS_ORIGINS", []),
        "jwt_algorithm": getattr(app_config, "JWT_ALGORITHM", "HS256"),
        "access_token_expire_minutes": getattr(app_config, "ACCESS_TOKEN_EXPIRE_MINUTES", 60),
        "db_dialect": _safe_db_dialect(),
        "smtp_configured": bool(getattr(app_config, "SMTP_USER", "")),
        "email_from": getattr(app_config, "EMAIL_FROM", ""),
        "payment_note": "Simulated/manual payments only; no live gateway charges. See /payments webhook + simulate endpoints.",
    }
