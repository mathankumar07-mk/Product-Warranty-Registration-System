from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.user import User
from app.services.invoice_service import create_invoice
from app.schemas.payment import PaymentCreate, PaymentUpdate


def create_payment(db: Session, user: User, data: PaymentCreate) -> Payment:
    order = db.get(Order, data.order_id)
    if not order or order.user_id != user.id:
        raise LookupError("Order not found")
    if data.amount != order.total_amount:
        raise ValueError("Payment amount must match the order total")
    payment = Payment(
        order_id=data.order_id,
        amount=data.amount,
        method=data.method,
        status=PaymentStatus.pending,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_payment(db: Session, payment_id: int, user: User | None = None) -> Payment:
    payment = db.get(Payment, payment_id)
    if not payment or (user and payment.order.user_id != user.id):
        raise LookupError("Payment not found")
    return payment


def list_payments_for_order(db: Session, user: User, order_id: int) -> list[Payment]:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise LookupError("Order not found")
    return db.query(Payment).filter(Payment.order_id == order_id).order_by(Payment.created_at).all()


def update_payment(db: Session, payment_id: int, data: PaymentUpdate) -> Payment:
    payment = get_payment(db, payment_id)
    values = data.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(payment, key, value)
    payment.updated_at = datetime.utcnow()
    if payment.status == PaymentStatus.completed:
        order = db.get(Order, payment.order_id)
        if order:
            order.status = "confirmed"
    db.commit()
    db.refresh(payment)
    return payment


def simulate_payment(db: Session, user: User, payment_id: int, success: bool = True) -> Payment:
    payment = get_payment(db, payment_id, user)
    payment.status = PaymentStatus.completed if success else PaymentStatus.failed
    payment.transaction_id = f"TXN-{payment.id}-{int(datetime.utcnow().timestamp())}"
    payment.updated_at = datetime.utcnow()
    if success:
        order = db.get(Order, payment.order_id)
        if order:
            order.status = "confirmed"
            db.flush()
            if not order.invoice:
                create_invoice(db, order.id)
    db.commit()
    db.refresh(payment)
    return payment