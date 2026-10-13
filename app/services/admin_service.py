from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.admin import Admin
from app.models.user import User
from app.schemas.admin import AdminCreate


def create_admin(db: Session, data: AdminCreate) -> Admin:
    from app.core.security import hash_password
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