from fastapi import APIRouter, Depends

from app.core.dependencies import DBSession, get_current_user
from app.models.user import User
from app.schemas.address import AddressCreate, AddressResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(data: UserUpdate, db: DBSession, current_user: User = Depends(get_current_user)):
    return user_service.update_user(db, current_user, data)


@router.get("/me/addresses", response_model=list[AddressResponse])
def list_my_addresses(db: DBSession, current_user: User = Depends(get_current_user)):
    return user_service.list_addresses(db, current_user)


@router.post("/me/addresses", response_model=AddressResponse, status_code=201)
def create_my_address(
    data: AddressCreate,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    return user_service.create_address(db, current_user, data)