from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DBSession, get_current_admin, get_current_user
from app.models.admin import Admin
from app.models.user import User
from app.schemas.invoice import PurchaseInvoiceCreate, PurchaseInvoiceResponse, PurchaseInvoiceUpdate
from app.services import invoice_service

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=PurchaseInvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(data: PurchaseInvoiceCreate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        return invoice_service.create_invoice(db, data.order_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{invoice_id}", response_model=PurchaseInvoiceResponse)
def get_invoice(invoice_id: int, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        return invoice_service.get_invoice(db, invoice_id, current_user)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/order/{order_id}", response_model=PurchaseInvoiceResponse)
def get_invoice_by_order(order_id: int, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        return invoice_service.get_invoice_by_order(db, order_id, current_user)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put("/{invoice_id}", response_model=PurchaseInvoiceResponse)
def update_invoice(invoice_id: int, data: PurchaseInvoiceUpdate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        return invoice_service.update_invoice_file(db, invoice_id, data.file_path or "")
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{invoice_id}/download")
def download_invoice(invoice_id: int, db: DBSession, current_user: User = Depends(get_current_user)):
    import os

    from fastapi.responses import FileResponse

    try:
        invoice = invoice_service.get_invoice(db, invoice_id, current_user)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    if not invoice.file_path or not os.path.isfile(invoice.file_path):
        raise HTTPException(status_code=404, detail="Invoice file not available")
    return FileResponse(invoice.file_path, filename=f"{invoice.invoice_number}.txt")