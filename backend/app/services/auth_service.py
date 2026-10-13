from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.admin import Admin
from app.models.user import User
from app.schemas.admin import AdminCreate
from app.schemas.user import UserCreate


def register_user(db: Session, data: UserCreate) -> User:
    if db.query(User).filter(User.email == data.email).first():
        raise ValueError("Email is already registered")
    user = User(name=data.name, email=data.email, password_hash=hash_password(data.password), phone=data.phone, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> tuple[str, bool]:
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, user.password_hash):
        return create_access_token(str(user.id)), False
    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin and verify_password(password, admin.password_hash):
        return create_access_token(str(admin.id), is_admin=True), True
    raise ValueError("Invalid email or password")


def create_admin(db: Session, data: AdminCreate) -> Admin:
    if db.query(Admin).filter(Admin.email == data.email).first():
        raise ValueError("Admin email is already registered")
    admin = Admin(name=data.name, email=data.email, password_hash=hash_password(data.password))
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin