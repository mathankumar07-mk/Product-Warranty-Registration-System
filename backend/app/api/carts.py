from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DBSession, get_current_user
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemResponse, CartItemUpdate, CartResponse
from app.services import cart_service

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartResponse)
def get_cart(db: DBSession, current_user: User = Depends(get_current_user)):
    return cart_service.get_cart(db, current_user)


@router.post("/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(data: CartItemCreate, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        return cart_service.add_to_cart(db, current_user, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.put("/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(item_id: int, data: CartItemUpdate, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        return cart_service.update_cart_item(db, current_user, item_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(item_id: int, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        cart_service.remove_from_cart(db, current_user, item_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(db: DBSession, current_user: User = Depends(get_current_user)):
    cart_service.clear_cart(db, current_user)