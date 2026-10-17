from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DBSession, get_current_admin, get_current_user
from app.models.admin import Admin
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse, OrderUpdate
from app.services import audit_service, order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(data: OrderCreate, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        return order_service.create_order(db, current_user, data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("", response_model=list[OrderResponse])
def list_orders(db: DBSession, current_user: User = Depends(get_current_user)):
    return order_service.list_orders(db, current_user)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        return order_service.get_order(db, current_user, order_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, data: OrderUpdate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        if data.status:
            previous = db.get(Order, order_id)
            previous_status = previous.status.value if previous and previous.status else None
            updated = order_service.update_order_status(db, order_id, OrderStatus(data.status))
            audit_service.log_admin_action(
                db,
                admin_id=admin.id,
                action="order.status",
                entity_type="order",
                entity_id=order_id,
                details=f"Status {previous_status} -> {updated.status.value}",
            )
            return updated
        raise HTTPException(status_code=400, detail="No valid fields to update")
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error