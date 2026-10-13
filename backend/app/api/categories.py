from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DBSession, get_current_admin
from app.models.admin import Admin
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        return category_service.create_category(db, data)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: DBSession):
    return db.query(Category).order_by(Category.id).all()


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: DBSession):
    try:
        return category_service.get_category(db, category_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, data: CategoryUpdate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        return category_service.update_category(db, category_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        category_service.delete_category(db, category_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error