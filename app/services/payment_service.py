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


def create_payment(
    db: Session, user: User, data: PaymentCreate, idempotency_key: str | None = None
) -> Payment:
    order = db.query(Order).filter(Order.id == data.order_id).with_for_update().first()
    if not order or order.user_id != user.id:
        raise LookupError("Order not found")
    if data.amount != order.total_amount:
        raise ValueError("Payment amount must match the order total")
    if order.status != OrderStatus.pending:
        raise ValueError("Order is not awaiting payment")
    if idempotency_key:
        existing = (
            db.query(Payment).filter(Payment.idempotency_key == idempotency_key).first()
        )
        if existing:
            if existing.order_id != order.id:
                raise ValueError("Idempotency key already used for another order")
            return existing
    pending_payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id, Payment.status == PaymentStatus.pending)
        .first()
    )
    if pending_payment:
        if idempotency_key and not pending_payment.idempotency_key:
            pending_payment.idempotency_key = idempotency_key
            db.commit()
            db.refresh(pending_payment)
        return pending_payment
    payment = Payment(
        order_id=data.order_id,
        amount=data.amount,
        method=data.method,
        status=PaymentStatus.pending,
        idempotency_key=idempotency_key,
    )
    db.add(payment)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if idempotency_key:
            existing = (
                db.query(Payment).filter(Payment.idempotency_key == idempotency_key).first()
            )
            if existing:
                return existing
        raise ValueError("Duplicate payment request") from error
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


_ALLOWED_TRANSITIONS = {
    PaymentStatus.pending: {PaymentStatus.completed, PaymentStatus.failed},
    PaymentStatus.completed: {PaymentStatus.refunded},
    PaymentStatus.failed: set(),
    PaymentStatus.refunded: set(),
}


def update_payment(db: Session, payment_id: int, data: PaymentUpdate) -> Payment:
    payment = get_payment(db, payment_id)
    previous_status = payment.status
    values = data.model_dump(exclude_unset=True)
    if "status" in values and values["status"] is not None:
        target = PaymentStatus(values["status"])
        if target != payment.status and target not in _ALLOWED_TRANSITIONS[payment.status]:
            raise ValueError(
                f"Payment cannot transition from {payment.status.value} to {target.value}"
            )
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


def refund_payment(db: Session, payment_id: int) -> Payment:
    from app.services.payment_gateway import get_gateway

    payment = get_payment(db, payment_id)
    if payment.status != PaymentStatus.completed:
        raise ValueError("Only completed payments can be refunded")
    gateway = get_gateway()
    if not gateway.refund(payment.transaction_id or f"PAY-{payment.id}", payment.amount):
        raise ValueError("Gateway refused the refund")
    payment.status = PaymentStatus.refunded
    payment.updated_at = datetime.now(timezone.utc)
    order = db.get(Order, payment.order_id)
    if order:
        add_user_notification(
            db,
            order.user_id,
            NotificationType.payment,
            f"Payment refunded for order #{order.id}",
            f"Your payment of ${payment.amount:.2f} was refunded via {gateway.name}.",
        )
    db.commit()
    db.refresh(payment)
    return payment


def handle_webhook(db: Session, payment_id: int, status: str, transaction_id: str | None) -> Payment:
    payment = get_payment(db, payment_id)
    target = PaymentStatus(status)
    if target == PaymentStatus.completed and payment.status == PaymentStatus.pending:
        payment.status = PaymentStatus.completed
        if transaction_id:
            payment.transaction_id = transaction_id
        payment.updated_at = datetime.now(timezone.utc)
        order = db.get(Order, payment.order_id)
        if order:
            order.status = OrderStatus.confirmed
            db.flush()
            add_user_notification(
                db,
                order.user_id,
                NotificationType.payment,
                f"Payment confirmed for order #{order.id}",
                f"Your payment of ${payment.amount:.2f} was successful.",
            )
            if not order.invoice:
                create_invoice(db, order.id, commit=False)
    elif target == PaymentStatus.failed and payment.status == PaymentStatus.pending:
        payment.status = PaymentStatus.failed
        payment.updated_at = datetime.now(timezone.utc)
    else:
        raise ValueError("Webhook status cannot be applied to this payment")
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Webhook conflicts with existing data") from error
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