from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DBSession, get_current_admin
from app.models.admin import Admin
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        return product_service.create_product(db, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("", response_model=list[ProductResponse])
def list_products(db: DBSession):
    return product_service.list_products(db)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: DBSession):
    try:
        return product_service.get_product(db, product_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductUpdate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        return product_service.update_product(db, product_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        product_service.delete_product(db, product_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error