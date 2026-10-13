from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DBSession, get_current_admin, get_current_user
from app.models.admin import Admin
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DBSession):
    try:
        return auth_service.register_user(db, data)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: DBSession):
    try:
        token, _ = auth_service.authenticate_user(db, data.email, data.password)
        return {"access_token": token, "token_type": "bearer"}
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/admin/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_admin(data: UserCreate, db: DBSession):
    try:
        return auth_service.create_admin(db, data)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error