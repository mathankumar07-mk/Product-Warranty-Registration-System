from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemUpdate


def get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            cart = db.query(Cart).filter(Cart.user_id == user.id).first()
            if not cart:
                raise
        db.refresh(cart)
    return cart


def get_cart(db: Session, user: User) -> Cart:
    return get_or_create_cart(db, user)


def add_to_cart(db: Session, user: User, data: CartItemCreate) -> CartItem:
    cart = get_or_create_cart(db, user)
    cart = db.query(Cart).filter(Cart.id == cart.id).with_for_update().one()
    product = db.query(Product).filter(Product.id == data.product_id).with_for_update().first()
    if not product or not product.is_active or not product.category.is_active:
        raise LookupError("Product not found")
    if product.stock_quantity < data.quantity:
        raise ValueError("Insufficient stock")
    existing = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == data.product_id).first()
    if existing:
        existing.quantity += data.quantity
        if existing.quantity > product.stock_quantity:
            raise ValueError("Insufficient stock")
        db.commit()
        db.refresh(existing)
        return existing
    item = CartItem(cart_id=cart.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_cart_item(db: Session, user: User, item_id: int, data: CartItemUpdate) -> CartItem:
    cart = get_or_create_cart(db, user)
    cart = db.query(Cart).filter(Cart.id == cart.id).with_for_update().one()
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
        .with_for_update()
        .first()
    )
    if not item:
        raise LookupError("Cart item not found")
    product = db.get(Product, item.product_id)
    if not product or not product.is_active or not product.category.is_active:
        raise LookupError("Product not found")
    if product.stock_quantity < data.quantity:
        raise ValueError("Insufficient stock")
    item.quantity = data.quantity
    db.commit()
    db.refresh(item)
    return item


def remove_from_cart(db: Session, user: User, item_id: int) -> None:
    cart = get_or_create_cart(db, user)
    cart = db.query(Cart).filter(Cart.id == cart.id).with_for_update().one()
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise LookupError("Cart item not found")
    db.delete(item)
    db.commit()


def clear_cart(db: Session, user: User) -> None:
    cart = get_or_create_cart(db, user)
    cart = db.query(Cart).filter(Cart.id == cart.id).with_for_update().one()
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()