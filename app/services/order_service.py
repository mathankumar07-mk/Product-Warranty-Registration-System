from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.address import Address
from app.models.notification import NotificationType
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.payment import Payment, PaymentStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate
from app.services.email_service import render_order_confirmation_email, send_email
from app.services.notification_service import add_user_notification


def create_order(db: Session, user: User, data: OrderCreate) -> Order:
    address_ids = {address_id for address_id in (data.shipping_address_id, data.billing_address_id) if address_id}
    if address_ids:
        owned_address_ids = {
            address_id
            for (address_id,) in db.query(Address.id)
            .filter(Address.id.in_(address_ids), Address.user_id == user.id)
            .all()
        }
        if owned_address_ids != address_ids:
            raise ValueError("Selected address does not belong to the current user")

    cart = db.query(Cart).filter(Cart.user_id == user.id).with_for_update().first()
    if not cart or not cart.items:
        raise ValueError("Cart is empty")
    total = Decimal("0.00")
    order_items = []
    products = []
    for item in cart.items:
        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .with_for_update()
            .first()
        )
        if not product or not product.is_active or not product.category.is_active:
            raise ValueError(f"Product {item.product_id} no longer available")
        if product.stock_quantity < item.quantity:
            raise ValueError(f"Insufficient stock for {product.name}")
        total += product.price * item.quantity
        order_items.append(OrderItem(product_id=product.id, quantity=item.quantity, unit_price=product.price))
        products.append((product, item.quantity))
    for product, quantity in products:
        product.stock_quantity -= quantity
    order = Order(
        user_id=user.id,
        total_amount=total,
        shipping_address_id=data.shipping_address_id,
        billing_address_id=data.billing_address_id,
        status=OrderStatus.pending,
    )
    db.add(order)
    db.flush()
    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    add_user_notification(
        db,
        user.id,
        NotificationType.order,
        f"Order #{order.id} placed",
        f"Your order has been placed for ${total:.2f}.",
    )
    db.commit()
    db.refresh(order)

    # Send order confirmation email
    items = [{"name": oi.product.name, "quantity": oi.quantity, "price": str(oi.unit_price)} for oi in order.items]
    html, text = render_order_confirmation_email(user.name, order.id, str(total), items)
    import asyncio
    asyncio.run(send_email(user.email, f"Order Confirmation - #{order.id}", html, text))

    return order


def get_order(db: Session, user: User, order_id: int) -> Order:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise LookupError("Order not found")
    return order


def list_orders(db: Session, user: User) -> list[Order]:
    return db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()


def update_order_status(db: Session, order_id: int, status: OrderStatus) -> Order:
    order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
    if not order:
        raise LookupError("Order not found")
    if status == order.status:
        return order

    allowed_transitions = {
        OrderStatus.pending: {OrderStatus.confirmed, OrderStatus.cancelled},
        OrderStatus.confirmed: {OrderStatus.shipped},
        OrderStatus.shipped: {OrderStatus.delivered},
        OrderStatus.delivered: set(),
        OrderStatus.cancelled: set(),
    }
    if status not in allowed_transitions[order.status]:
        raise ValueError(f"Order cannot transition from {order.status.value} to {status.value}")

    if status == OrderStatus.confirmed:
        paid_amount = sum(
            (
                payment.amount
                for payment in db.query(Payment)
                .filter(Payment.order_id == order.id, Payment.status == PaymentStatus.completed)
                .all()
            ),
            Decimal("0.00"),
        )
        if paid_amount < order.total_amount:
            raise ValueError("An order cannot be confirmed before it is fully paid")

    if status == OrderStatus.cancelled:
        for item in order.items:
            product = (
                db.query(Product)
                .filter(Product.id == item.product_id)
                .with_for_update()
                .first()
            )
            if product:
                product.stock_quantity += item.quantity

    order.status = status
    order.updated_at = datetime.now(timezone.utc)
    add_user_notification(
        db,
        order.user_id,
        NotificationType.order,
        f"Order #{order.id} updated",
        f"Your order status is now {status.value}.",
    )
    db.commit()
    db.refresh(order)
    return order