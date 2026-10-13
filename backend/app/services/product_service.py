from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def create_product(db: Session, data: ProductCreate) -> Product:
    if not db.get(Category, data.category_id):
        raise LookupError("Category not found")
    if db.query(Product).filter(Product.model_number == data.model_number).first():
        raise ValueError("Model number already exists")
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_product(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise LookupError("Product not found")
    return product


def list_products(db: Session) -> list[Product]:
    return db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.id).all()


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    values = data.model_dump(exclude_unset=True)
    if "category_id" in values and not db.get(Category, values["category_id"]):
        raise LookupError("Category not found")
    for key, value in values.items():
        setattr(product, key, value)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Product update conflicts with existing data") from error
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> None:
    product = get_product(db, product_id)
    product.is_active = False
    db.commit()