from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.payment import Payment, PaymentStatus
from app.models.purchase_invoice import PurchaseInvoice
from app.models.user import User


def generate_invoice_number() -> str:
    return f"INV-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:8].upper()}"


def create_invoice(
    db: Session,
    order_id: int,
    *,
    commit: bool = True,
) -> PurchaseInvoice:
    order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
    if not order:
        raise LookupError("Order not found")
    if order.invoice:
        raise ValueError("Invoice already exists for this order")
    completed_payments = (
        db.query(Payment)
        .filter(Payment.order_id == order_id, Payment.status == PaymentStatus.completed)
        .all()
    )
    paid_amount = sum(p.amount for p in completed_payments)
    if paid_amount < order.total_amount:
        raise ValueError("Order not fully paid")
    invoice = PurchaseInvoice(
        order_id=order_id,
        invoice_number=generate_invoice_number(),
        total_amount=order.total_amount,
        tax_amount=Decimal("0.00"),
    )
    db.add(invoice)
    db.flush()
    invoice.file_path = _write_invoice_file(invoice, order)
    if commit:
        db.commit()
        db.refresh(invoice)
    return invoice


def _write_invoice_file(invoice: PurchaseInvoice, order: Order) -> str:
    import os

    from app.core.config import UPLOAD_DIR
    from app.services.invoice_pdf import render_invoice_pdf

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, f"{invoice.invoice_number}.pdf")
    title = [
        f"Invoice {invoice.invoice_number}",
        f"Order #{order.id} (Order No: {order.order_number or order.id})",
        f"Date: {invoice.created_at.isoformat()}",
    ]
    items = [
        f"Product {item.product_id} x{item.quantity} @ {item.unit_price} = "
        f"{item.unit_price * item.quantity}"
        for item in order.items
    ]
    totals = [f"Tax: {invoice.tax_amount}", f"Total: {invoice.total_amount}"]
    with open(path, "wb") as fh:
        fh.write(render_invoice_pdf(title, items, totals))
    return path


def list_user_invoices(db: Session, user: User) -> list[PurchaseInvoice]:
    return (
        db.query(PurchaseInvoice)
        .join(Order)
        .filter(Order.user_id == user.id)
        .order_by(PurchaseInvoice.created_at.desc())
        .all()
    )


def get_invoice(db: Session, invoice_id: int, user: User | None = None) -> PurchaseInvoice:
    invoice = db.get(PurchaseInvoice, invoice_id)
    if not invoice or (user and invoice.order.user_id != user.id):
        raise LookupError("Invoice not found")
    return invoice


def get_invoice_by_order(db: Session, order_id: int, user: User | None = None) -> PurchaseInvoice:
    query = db.query(PurchaseInvoice).join(Order).filter(PurchaseInvoice.order_id == order_id)
    if user:
        query = query.filter(Order.user_id == user.id)
    invoice = query.first()
    if not invoice:
        raise LookupError("Invoice not found")
    return invoice


def get_invoice_by_number(db: Session, invoice_number: str, user: User | None = None) -> PurchaseInvoice:
    """Resolve a human-readable invoice number (e.g. INV-20261013-E6324947)
    to its internal record. Ownership-scoped: other customers' invoices
    read as not found."""
    query = db.query(PurchaseInvoice).join(Order).filter(PurchaseInvoice.invoice_number == invoice_number)
    if user:
        query = query.filter(Order.user_id == user.id)
    invoice = query.first()
    if not invoice:
        raise LookupError("Invoice not found")
    return invoice


def update_invoice_file(db: Session, invoice_id: int, file_path: str) -> PurchaseInvoice:
    invoice = get_invoice(db, invoice_id)
    invoice.file_path = file_path
    db.commit()
    db.refresh(invoice)
    return invoice