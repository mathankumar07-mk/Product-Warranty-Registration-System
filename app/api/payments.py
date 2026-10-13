from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.core.dependencies import DBSession, get_current_admin, get_current_user
from app.models.admin import Admin
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentUpdate
from app.services import payment_service
from app.services.payment_gateway import get_gateway

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    data: PaymentCreate,
    db: DBSession,
    current_user: User = Depends(get_current_user),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    try:
        return payment_service.create_payment(db, current_user, data, idempotency_key)
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


@router.post("/webhook", response_model=PaymentResponse)
async def payment_webhook(
    request: Request,
    db: DBSession,
    signature: str = Header(default="", alias="X-Webhook-Signature"),
):
    body = await request.body()
    if not get_gateway().verify_webhook(body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    try:
        payload = await request.json()
        return payment_service.handle_webhook(
            db,
            int(payload["payment_id"]),
            str(payload["status"]),
            payload.get("transaction_id"),
        )
    except (KeyError, ValueError, TypeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
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
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


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
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment(payment_id: int, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        return payment_service.refund_payment(db, payment_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
