from sqlalchemy.exc import IntegrityError
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def create_product(db: Session, data: ProductCreate) -> Product:
    category = db.get(Category, data.category_id)
    if not category:
        raise LookupError("Category not found")
    if not category.is_active:
        raise ValueError("Cannot add a product to an inactive category")
    if db.query(Product).filter(Product.model_number == data.model_number).first():
        raise ValueError("Model number already exists")
    product = Product(**data.model_dump())
    db.add(product)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Product model number already exists") from error
    db.refresh(product)
    return product


def get_product(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise LookupError("Product not found")
    return product


def list_products(
    db: Session,
    search: str | None = None,
    category_id: int | None = None,
    brand: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    warranty_available: bool | None = None,
    in_stock_only: bool = False,
    sort: str = "id",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Product], int]:
    query = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Product.is_active.is_(True), Category.is_active.is_(True))
    )

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.brand.ilike(search_term),
                Product.model_number.ilike(search_term),
                Product.description.ilike(search_term),
            )
        )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if warranty_available is not None:
        query = query.filter(Product.warranty_available.is_(warranty_available))

    if in_stock_only:
        query = query.filter(Product.stock_quantity > 0)

    total = query.count()

    descending = sort.startswith("-")
    sort_field = sort[1:] if descending else sort
    sort_column = {
        "id": Product.id,
        "name": Product.name,
        "price": Product.price,
        "created_at": Product.created_at,
        "brand": Product.brand,
    }.get(sort_field)
    if sort_column is None:
        raise ValueError("Unsupported product sort field")

    if descending:
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    offset = (page - 1) * page_size
    products = query.offset(offset).limit(page_size).all()

    return products, total


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    values = data.model_dump(exclude_unset=True)
    if "category_id" in values:
        category = db.get(Category, values["category_id"])
        if not category:
            raise LookupError("Category not found")
        if not category.is_active:
            raise ValueError("Cannot move a product to an inactive category")
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


def get_brands(db: Session) -> list[str]:
    brands = (
        db.query(Product.brand)
        .join(Category, Product.category_id == Category.id)
        .filter(Product.is_active.is_(True), Category.is_active.is_(True))
        .distinct()
        .all()
    )
    return [b[0] for b in brands if b[0]]