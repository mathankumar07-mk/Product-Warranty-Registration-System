from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.schemas.admin import AdminCreate


def create_admin(db: Session, data: AdminCreate) -> Admin:
    from app.core.security import hash_password
    if db.query(Admin).filter(Admin.email == data.email).first():
        raise ValueError("Admin email already registered")
    admin = Admin(name=data.name, email=data.email, password_hash=hash_password(data.password))
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin