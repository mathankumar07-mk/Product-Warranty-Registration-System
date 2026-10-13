from datetime import datetime, timezone

from jose import JWTError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.admin import Admin
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.admin import AdminCreate
from app.schemas.user import UserCreate
from app.services.email_service import render_welcome_email, send_email


def register_user(db: Session, data: UserCreate) -> User:
    if (
        db.query(User).filter(User.email == data.email).first()
        or db.query(Admin).filter(Admin.email == data.email).first()
    ):
        raise ValueError("Email is already registered")
    user = User(name=data.name, email=data.email, password_hash=hash_password(data.password), phone=data.phone)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Email is already registered") from error
    db.refresh(user)

    html, text = render_welcome_email(user.name)
    import asyncio
    asyncio.run(send_email(user.email, "Welcome to Mini E-Commerce!", html, text))

    return user


def authenticate_user(db: Session, email: str, password: str) -> tuple[str, bool]:
    user = db.query(User).filter(User.email == email).first()
    if user and user.is_active and verify_password(password, user.password_hash):
        return create_access_token(str(user.id)), False
    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin and verify_password(password, admin.password_hash):
        return create_access_token(str(admin.id), is_admin=True), True
    raise ValueError("Invalid email or password")


def issue_token_pair(db: Session, subject: str, is_admin: bool) -> tuple[str, str]:
    access = create_access_token(subject, is_admin=is_admin)
    refresh, jti, expires_at = create_refresh_token(subject, is_admin=is_admin)
    db.add(RefreshToken(jti=jti, subject=subject, is_admin=is_admin, expires_at=expires_at))
    db.commit()
    return access, refresh


def rotate_refresh_token(db: Session, refresh_token: str) -> tuple[str, str]:
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
    except (JWTError, ValueError) as error:
        raise ValueError("Invalid refresh token") from error
    record = db.query(RefreshToken).filter(RefreshToken.jti == payload.get("jti")).first()
    if not record or record.revoked:
        raise ValueError("Refresh token has been revoked")
    if record.expires_at.tzinfo is None:
        expiry = record.expires_at.replace(tzinfo=timezone.utc)
    else:
        expiry = record.expires_at
    if expiry < datetime.now(timezone.utc):
        raise ValueError("Refresh token has expired")
    record.revoked = True
    db.commit()
    return issue_token_pair(db, record.subject, record.is_admin)


def revoke_refresh_token(db: Session, refresh_token: str) -> None:
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
    except (JWTError, ValueError) as error:
        raise ValueError("Invalid refresh token") from error
    record = db.query(RefreshToken).filter(RefreshToken.jti == payload.get("jti")).first()
    if not record:
        raise ValueError("Refresh token not found")
    record.revoked = True
    db.commit()


def change_password(db: Session, account: User | Admin, old_password: str, new_password: str) -> None:
    if not verify_password(old_password, account.password_hash):
        raise ValueError("Current password is incorrect")
    account.password_hash = hash_password(new_password)
    db.query(RefreshToken).filter(
        RefreshToken.subject == str(account.id),
        RefreshToken.is_admin == isinstance(account, Admin),
        RefreshToken.revoked.is_(False),
    ).update({"revoked": True})
    db.commit()


def build_password_reset_token(db: Session, email: str) -> tuple[str, bool]:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return create_password_reset_token(str(user.id)), False
    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin:
        return create_password_reset_token(str(admin.id), is_admin=True), True
    raise LookupError("Account not found")


def reset_password_with_token(db: Session, token: str, new_password: str) -> None:
    try:
        payload = decode_token(token, expected_type="reset")
    except (JWTError, ValueError) as error:
        raise ValueError("Invalid or expired reset token") from error
    if payload.get("is_admin"):
        account = db.get(Admin, int(payload["sub"]))
    else:
        account = db.get(User, int(payload["sub"]))
    if not account:
        raise LookupError("Account not found")
    account.password_hash = hash_password(new_password)
    db.query(RefreshToken).filter(
        RefreshToken.subject == str(account.id),
        RefreshToken.is_admin == bool(payload.get("is_admin")),
        RefreshToken.revoked.is_(False),
    ).update({"revoked": True})
    db.commit()


def create_admin(db: Session, data: AdminCreate) -> Admin:
    if (
        db.query(Admin).filter(Admin.email == data.email).first()
        or db.query(User).filter(User.email == data.email).first()
    ):
        raise ValueError("Email is already registered")
    admin = Admin(name=data.name, email=data.email, password_hash=hash_password(data.password))
    db.add(admin)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Email is already registered") from error
    db.refresh(admin)
    return admin