from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DBSession, get_current_admin, get_current_user
from app.models.admin import Admin
from app.models.user import User
from app.schemas.warranty import WarrantyPolicyCreate, WarrantyPolicyResponse, WarrantyPolicyUpdate
from app.schemas.warranty_registration import WarrantyRegistrationCreate, WarrantyRegistrationResponse, WarrantyRegistrationUpdate
from app.services import audit_service, warranty_service

router = APIRouter(prefix="/warranties", tags=["warranties"])


@router.post("/policies", response_model=WarrantyPolicyResponse, status_code=status.HTTP_201_CREATED)
def create_policy(data: WarrantyPolicyCreate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        return warranty_service.create_warranty_policy(db, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/policies", response_model=list[WarrantyPolicyResponse])
def list_policies(db: DBSession, is_active: bool | None = None):
    return warranty_service.list_warranty_policies(db, is_active)


@router.get("/policies/{policy_id}", response_model=WarrantyPolicyResponse)
def get_policy(policy_id: int, db: DBSession):
    try:
        return warranty_service.get_warranty_policy(db, policy_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/policies/product/{product_id}", response_model=WarrantyPolicyResponse)
def get_policy_by_product(product_id: int, db: DBSession):
    try:
        return warranty_service.get_warranty_policy_by_product(db, product_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put("/policies/{policy_id}", response_model=WarrantyPolicyResponse)
def update_policy(policy_id: int, data: WarrantyPolicyUpdate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        return warranty_service.update_warranty_policy(db, policy_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/register", response_model=WarrantyRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_warranty(data: WarrantyRegistrationCreate, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        return warranty_service.register_warranty(db, current_user.id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/registrations", response_model=list[WarrantyRegistrationResponse])
def list_my_registrations(
    db: DBSession, current_user: User = Depends(get_current_user), status: str | None = None
):
    try:
        warranty_status = warranty_service.WarrantyStatus(status) if status is not None else None
    except ValueError as error:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}") from error
    return warranty_service.list_user_registrations(db, current_user.id, warranty_status)


@router.get("/registrations/search", response_model=list[WarrantyRegistrationResponse])
def search_registrations(
    db: DBSession,
    admin: Admin = Depends(get_current_admin),
    status: str | None = None,
    product_id: int | None = None,
):
    return warranty_service.search_registrations(db, status, product_id)


@router.get("/registrations/{registration_id}", response_model=WarrantyRegistrationResponse)
def get_registration(registration_id: int, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        return warranty_service.get_registration(db, registration_id, current_user)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put("/registrations/{registration_id}", response_model=WarrantyRegistrationResponse)
def update_registration(registration_id: int, data: WarrantyRegistrationUpdate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        updated = warranty_service.update_registration_status(db, registration_id, data)
        audit_service.log_admin_action(
            db,
            admin_id=admin.id,
            action="warranty.decision",
            entity_type="warranty_registration",
            entity_id=registration_id,
            details=f"Status -> {updated.warranty_status.value}",
        )
        return updated
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/registrations/{registration_id}/validity")
def check_validity(registration_id: int, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        return warranty_service.check_warranty_validity(db, registration_id, current_user)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error