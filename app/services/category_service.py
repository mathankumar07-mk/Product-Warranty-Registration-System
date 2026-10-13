from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def create_category(db: Session, data: CategoryCreate) -> Category:
    if db.query(Category).filter(Category.name == data.name).first():
        raise ValueError("Category already exists")
    category = Category(**data.model_dump())
    db.add(category)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Category already exists") from error
    db.refresh(category)
    return category


def get_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if not category:
        raise LookupError("Category not found")
    return category


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    category = get_category(db, category_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Category update conflicts with existing data") from error
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    db.delete(category)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Category cannot be deleted while it has products") from error