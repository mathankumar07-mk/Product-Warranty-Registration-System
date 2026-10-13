from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DBSession, get_current_admin
from app.models.admin import Admin
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate
from app.services import address_service

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(data: AddressCreate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    from app.models.user import User
    # Admin can create addresses for any user - for now use first user
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    try:
        return address_service.create_address(db, user, data)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("", response_model=list[AddressResponse])
def list_addresses(db: DBSession, admin: Admin = Depends(get_current_admin)):
    from app.models.address import Address
    return db.query(Address).order_by(Address.id).all()


@router.get("/{address_id}", response_model=AddressResponse)
def get_address(address_id: int, db: DBSession, admin: Admin = Depends(get_current_admin)):
    from app.models.address import Address
    address = db.get(Address, address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


@router.put("/{address_id}", response_model=AddressResponse)
def update_address(address_id: int, data: AddressUpdate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    from app.models.user import User
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    try:
        return address_service.update_address(db, user, address_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: int, db: DBSession, admin: Admin = Depends(get_current_admin)):
    from app.models.user import User
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    try:
        address_service.delete_address(db, user, address_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error