from sqlalchemy.orm import Session

from app.models.address import Address
from app.models.user import User
from app.schemas.address import AddressCreate, AddressUpdate


def create_address(db: Session, user: User, data: AddressCreate) -> Address:
    if data.is_default:
        db.query(Address).filter(Address.user_id == user.id, Address.is_default.is_(True)).update(
            {Address.is_default: False}
        )
    address = Address(user_id=user.id, **data.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def get_address(db: Session, user: User, address_id: int) -> Address:
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not address:
        raise LookupError("Address not found")
    return address


def list_addresses(db: Session, user: User) -> list[Address]:
    return db.query(Address).filter(Address.user_id == user.id).order_by(Address.id).all()


def update_address(db: Session, user: User, address_id: int, data: AddressUpdate) -> Address:
    address = get_address(db, user, address_id)
    values = data.model_dump(exclude_unset=True)
    if values.get("is_default"):
        db.query(Address).filter(Address.user_id == user.id, Address.is_default.is_(True)).update(
            {Address.is_default: False}
        )
    for key, value in values.items():
        setattr(address, key, value)
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, user: User, address_id: int) -> None:
    address = get_address(db, user, address_id)
    db.delete(address)
    db.commit()