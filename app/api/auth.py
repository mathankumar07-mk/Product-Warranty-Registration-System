from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DBSession, get_current_admin, get_current_user
from app.core.config import SMTP_USER
from app.models.admin import Admin
from app.models.user import User
from app.schemas.admin import AdminCreate, AdminResponse
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPairResponse,
)
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_service
from app.services.email_service import send_email

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
        # Issue a rotating refresh token alongside the access token.
        from app.services.auth_service import issue_token_pair

        try:
            payload_is_admin = False
            from app.core.security import decode_token

            payload = decode_token(token, expected_type="access")
            payload_is_admin = bool(payload.get("is_admin"))
            _, refresh = issue_token_pair(db, payload.get("sub"), payload_is_admin)
        except Exception:
            refresh = None
        return {"access_token": token, "token_type": "bearer", "refresh_token": refresh}
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error


@router.post("/refresh", response_model=TokenPairResponse)
def refresh(data: RefreshRequest, db: DBSession):
    try:
        access, refresh = auth_service.rotate_refresh_token(db, data.refresh_token)
        return {"access_token": access, "token_type": "bearer", "refresh_token": refresh}
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshRequest, db: DBSession):
    try:
        auth_service.revoke_refresh_token(db, data.refresh_token)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    return None


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: ChangePasswordRequest,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    try:
        auth_service.change_password(db, current_user, data.old_password, data.new_password)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return None


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(data: ForgotPasswordRequest, db: DBSession):
    try:
        token, _ = auth_service.build_password_reset_token(db, data.email)
    except LookupError:
        # Never reveal whether the email exists.
        return {"email_sent": False, "reset_token": None}
    if SMTP_USER:
        import asyncio

        asyncio.run(send_email(data.email, "Password reset", f"<p>Reset token: {token}</p>", f"Reset token: {token}"))
        return {"email_sent": True, "reset_token": None}
    return {"email_sent": False, "reset_token": token}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(data: ResetPasswordRequest, db: DBSession):
    try:
        auth_service.reset_password_with_token(db, data.token, data.new_password)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return None


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/admin/register", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
def register_admin(
    data: AdminCreate,
    db: DBSession,
    admin: Admin = Depends(get_current_admin),
):
    try:
        return auth_service.create_admin(db, data)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
