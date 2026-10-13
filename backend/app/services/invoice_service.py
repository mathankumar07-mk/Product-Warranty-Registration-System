from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.payment import Payment, PaymentStatus
from app.models.purchase_invoice import PurchaseInvoice
from app.models.user import User


def generate_invoice_number() -> str:
    return f"INV-{int(datetime.utcnow().timestamp())}"


def create_invoice(db: Session, order_id: int) -> PurchaseInvoice:
    order = db.get(Order, order_id)
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
    db.commit()
    db.refresh(invoice)
    return invoice


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


def update_invoice_file(db: Session, invoice_id: int, file_path: str) -> PurchaseInvoice:
    invoice = get_invoice(db, invoice_id)
    invoice.file_path = file_path
    db.commit()
    db.refresh(invoice)
    return invoice