from fastapi import APIRouter, Depends, status

from app.core.dependencies import DBSession, get_current_admin
from app.models.admin import Admin
from app.schemas.admin import AdminCreate, AdminResponse
from app.services import admin_service

router = APIRouter(prefix="/admins", tags=["admins"])


@router.get("/me", response_model=AdminResponse)
def get_me(admin: Admin = Depends(get_current_admin)):
    return admin


@router.post("", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
def create_admin(data: AdminCreate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        return admin_service.create_admin(db, data)
    except ValueError as error:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail=str(error)) from error