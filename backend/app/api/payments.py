from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DBSession, get_current_admin, get_current_user
from app.models.admin import Admin
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentUpdate
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(data: PaymentCreate, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        return payment_service.create_payment(db, current_user, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("", response_model=list[PaymentResponse])
def list_payments(order_id: int, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        return payment_service.list_payments_for_order(db, current_user, order_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        return payment_service.get_payment(db, payment_id, current_user)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment(payment_id: int, data: PaymentUpdate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        return payment_service.update_payment(db, payment_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{payment_id}/simulate", response_model=PaymentResponse)
def simulate_payment(
    payment_id: int,
    db: DBSession,
    current_user: User = Depends(get_current_user),
    success: bool = True,
):
    try:
        return payment_service.simulate_payment(db, current_user, payment_id, success)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error