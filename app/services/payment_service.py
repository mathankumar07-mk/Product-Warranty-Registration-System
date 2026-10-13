from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.notification import NotificationType
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.services.email_service import render_payment_confirmation_email, send_email
from app.services.invoice_service import create_invoice
from app.services.notification_service import add_user_notification
from app.schemas.payment import PaymentCreate, PaymentUpdate


def create_payment(db: Session, user: User, data: PaymentCreate) -> Payment:
    order = db.query(Order).filter(Order.id == data.order_id).with_for_update().first()
    if not order or order.user_id != user.id:
        raise LookupError("Order not found")
    if data.amount != order.total_amount:
        raise ValueError("Payment amount must match the order total")
    if order.status != OrderStatus.pending:
        raise ValueError("Order is not awaiting payment")
    pending_payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id, Payment.status == PaymentStatus.pending)
        .first()
    )
    if pending_payment:
        return pending_payment
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
    previous_status = payment.status
    values = data.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(payment, key, value)
    payment.updated_at = datetime.now(timezone.utc)
    if payment.status == PaymentStatus.completed:
        order = db.get(Order, payment.order_id)
        if order:
            order.status = OrderStatus.confirmed
            db.flush()
            if previous_status != PaymentStatus.completed:
                add_user_notification(
                    db,
                    order.user_id,
                    NotificationType.payment,
                    f"Payment confirmed for order #{order.id}",
                    f"Your payment of ${payment.amount:.2f} was successful.",
                )
            if not order.invoice:
                create_invoice(db, order.id, commit=False)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Payment update conflicts with existing data") from error
    db.refresh(payment)
    return payment


def simulate_payment(db: Session, user: User, payment_id: int, success: bool = True) -> Payment:
    payment = get_payment(db, payment_id, user)
    if payment.status != PaymentStatus.pending:
        if (success and payment.status == PaymentStatus.completed) or (
            not success and payment.status == PaymentStatus.failed
        ):
            return payment
        raise ValueError("Payment is no longer pending")
    order = None
    if success:
        order = db.query(Order).filter(Order.id == payment.order_id).with_for_update().first()
        if not order or order.status != OrderStatus.pending:
            raise ValueError("Order is not awaiting payment")

    payment.status = PaymentStatus.completed if success else PaymentStatus.failed
    payment.transaction_id = f"TXN-{payment.id}-{int(datetime.now(timezone.utc).timestamp())}"
    payment.updated_at = datetime.now(timezone.utc)
    confirmation_email = None
    if success:
        if order:
            order.status = OrderStatus.confirmed
            db.flush()
            add_user_notification(
                db,
                user.id,
                NotificationType.payment,
                f"Payment confirmed for order #{order.id}",
                f"Your payment of ${payment.amount:.2f} was successful.",
            )
            if not order.invoice:
                create_invoice(db, order.id, commit=False)
            confirmation_email = render_payment_confirmation_email(
                user.name,
                order.id,
                str(payment.amount),
                payment.method.value,
                payment.transaction_id,
            )
    else:
        add_user_notification(
            db,
            user.id,
            NotificationType.payment,
            f"Payment failed for order #{payment.order_id}",
            "Your payment was not completed. You can try another payment.",
        )
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Payment could not be completed due to a conflicting transaction") from error
    db.refresh(payment)
    if confirmation_email and order:
        import asyncio

        html, text = confirmation_email
        asyncio.run(send_email(user.email, f"Payment Confirmed - Order #{order.id}", html, text))
    return payment