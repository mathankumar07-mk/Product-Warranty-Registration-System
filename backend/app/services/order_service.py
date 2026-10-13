from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.address import Address
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate


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

    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart or not cart.items:
        raise ValueError("Cart is empty")
    total = Decimal("0.00")
    order_items = []
    for item in cart.items:
        product = db.get(Product, item.product_id)
        if not product or not product.is_active:
            raise ValueError(f"Product {item.product_id} no longer available")
        if product.stock_quantity < item.quantity:
            raise ValueError(f"Insufficient stock for {product.name}")
        total += product.price * item.quantity
        order_items.append(OrderItem(product_id=product.id, quantity=item.quantity, unit_price=product.price))
        product.stock_quantity -= item.quantity
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
    db.commit()
    db.refresh(order)
    return order


def get_order(db: Session, user: User, order_id: int) -> Order:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise LookupError("Order not found")
    return order


def list_orders(db: Session, user: User) -> list[Order]:
    return db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()


def update_order_status(db: Session, order_id: int, status: OrderStatus) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise LookupError("Order not found")
    order.status = status
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order