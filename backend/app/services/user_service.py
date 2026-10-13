from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.address import AddressCreate
from app.schemas.user import UserUpdate


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def list_addresses(db: Session, user: User) -> list:
    from app.models.address import Address
    return db.query(Address).filter(Address.user_id == user.id).order_by(Address.id).all()


def create_address(db: Session, user: User, data: AddressCreate):
    from app.services import address_service

    return address_service.create_address(db, user, data)