from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def _name_taken(db: Session, name: str, exclude_id: int | None = None) -> bool:
    query = db.query(Category).filter(func.lower(Category.name) == name.strip().lower())
    if exclude_id is not None:
        query = query.filter(Category.id != exclude_id)
    return db.query(query.exists()).scalar()


def create_category(db: Session, data: CategoryCreate) -> Category:
    name = data.name.strip()
    if not name:
        raise ValueError("Category name must not be blank")
    if _name_taken(db, name):
        raise ValueError("Category already exists")
    category = Category(name=name, description=data.description)
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
    values = data.model_dump(exclude_unset=True)
    if "name" in values and values["name"] is not None:
        name = values["name"].strip()
        if not name:
            raise ValueError("Category name must not be blank")
        if _name_taken(db, name, exclude_id=category_id):
            raise ValueError("Category already exists")
        values["name"] = name
    for key, value in values.items():
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