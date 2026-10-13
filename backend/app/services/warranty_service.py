from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.purchase_invoice import PurchaseInvoice
from app.models.warranty_policy import WarrantyPolicy
from app.models.warranty_registration import WarrantyRegistration, WarrantyStatus, PurchaseSource
from app.models.user import User
from app.schemas.warranty import WarrantyPolicyCreate, WarrantyPolicyUpdate
from app.schemas.warranty_registration import WarrantyRegistrationCreate, WarrantyRegistrationUpdate


def create_warranty_policy(db: Session, data: WarrantyPolicyCreate) -> WarrantyPolicy:
    product = db.get(Product, data.product_id)
    if not product:
        raise LookupError("Product not found")
    if product.warranty_policy:
        raise ValueError("Warranty policy already exists for this product")
    policy = WarrantyPolicy(**data.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def get_warranty_policy(db: Session, policy_id: int) -> WarrantyPolicy:
    policy = db.get(WarrantyPolicy, policy_id)
    if not policy:
        raise LookupError("Warranty policy not found")
    return policy


def get_warranty_policy_by_product(db: Session, product_id: int) -> WarrantyPolicy:
    policy = db.query(WarrantyPolicy).filter(WarrantyPolicy.product_id == product_id).first()
    if not policy:
        raise LookupError("No warranty policy for this product")
    return policy


def update_warranty_policy(db: Session, policy_id: int, data: WarrantyPolicyUpdate) -> WarrantyPolicy:
    policy = get_warranty_policy(db, policy_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(policy, key, value)
    db.commit()
    db.refresh(policy)
    return policy


def register_warranty(db: Session, user_id: int, data: WarrantyRegistrationCreate) -> WarrantyRegistration:
    policy = db.get(WarrantyPolicy, data.policy_id)
    if not policy:
        raise LookupError("Warranty policy not found")
    product = db.get(Product, data.product_id)
    if not product:
        raise LookupError("Product not found")
    if data.product_id != policy.product_id:
        raise ValueError("Product does not match warranty policy")
    
    # Validate purchase invoice belongs to user and order
    if data.purchase_invoice_id:
        invoice = db.get(PurchaseInvoice, data.purchase_invoice_id)
        if not invoice or invoice.order.user_id != user_id:
            raise LookupError("Purchase invoice not found")
        # Validate the order contains this product
        order_has_product = any(item.product_id == data.product_id for item in invoice.order.items)
        if not order_has_product:
            raise ValueError("Purchase invoice does not contain the specified product")
    
    # Validate purchase_source
    try:
        purchase_source = PurchaseSource(data.purchase_source)
    except ValueError:
        valid_sources = [s.value for s in PurchaseSource]
        raise ValueError(f"Invalid purchase_source. Valid options: {valid_sources}")
    
    # Calculate warranty dates
    warranty_start_date = data.purchase_date
    warranty_end_date = warranty_start_date + relativedelta(months=policy.warranty_period_months)
    
    # Determine initial warranty status
    now = datetime.utcnow()
    if warranty_end_date < now:
        warranty_status = WarrantyStatus.EXPIRED
    elif warranty_start_date > now:
        warranty_status = WarrantyStatus.PENDING
    else:
        warranty_status = WarrantyStatus.ACTIVE
    
    # Check for duplicate registration (same product, same user, same invoice)
    if data.purchase_invoice_id:
        existing = db.query(WarrantyRegistration).filter(
            WarrantyRegistration.user_id == user_id,
            WarrantyRegistration.product_id == data.product_id,
            WarrantyRegistration.purchase_invoice_id == data.purchase_invoice_id
        ).first()
        if existing:
            raise ValueError("Warranty already registered for this product and invoice")
    
    registration = WarrantyRegistration(
        policy_id=data.policy_id,
        user_id=user_id,
        product_id=data.product_id,
        purchase_invoice_id=data.purchase_invoice_id,
        serial_number=data.serial_number,
        purchase_source=purchase_source,
        purchase_date=data.purchase_date,
        warranty_start_date=warranty_start_date,
        warranty_end_date=warranty_end_date,
        warranty_status=warranty_status,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return registration


def get_registration(db: Session, registration_id: int, user: User | None = None) -> WarrantyRegistration:
    registration = db.get(WarrantyRegistration, registration_id)
    if not registration or (user and registration.user_id != user.id):
        raise LookupError("Warranty registration not found")
    return registration


def list_user_registrations(db: Session, user_id: int) -> list[WarrantyRegistration]:
    return db.query(WarrantyRegistration).filter(WarrantyRegistration.user_id == user_id).order_by(WarrantyRegistration.created_at.desc()).all()


def update_registration_status(db: Session, registration_id: int, data: WarrantyRegistrationUpdate) -> WarrantyRegistration:
    registration = get_registration(db, registration_id)
    values = data.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(registration, key, value)
    registration.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(registration)
    return registration


def check_warranty_validity(db: Session, registration_id: int, user: User | None = None) -> dict:
    registration = get_registration(db, registration_id, user)
    now = datetime.utcnow()
    
    is_valid = registration.warranty_status == WarrantyStatus.ACTIVE and now <= registration.warranty_end_date
    
    # Auto-update status based on dates
    if registration.warranty_end_date < now and registration.warranty_status != WarrantyStatus.EXPIRED:
        registration.warranty_status = WarrantyStatus.EXPIRED
        db.commit()
        db.refresh(registration)
        is_valid = False
    elif registration.warranty_start_date > now and registration.warranty_status != WarrantyStatus.PENDING:
        registration.warranty_status = WarrantyStatus.PENDING
        db.commit()
        db.refresh(registration)
        is_valid = False
    elif registration.warranty_start_date <= now <= registration.warranty_end_date and registration.warranty_status != WarrantyStatus.ACTIVE:
        registration.warranty_status = WarrantyStatus.ACTIVE
        db.commit()
        db.refresh(registration)
        is_valid = True
    
    return {
        "valid": is_valid,
        "warranty_status": registration.warranty_status.value,
        "warranty_start_date": registration.warranty_start_date.isoformat(),
        "warranty_end_date": registration.warranty_end_date.isoformat(),
        "days_remaining": (registration.warranty_end_date - now).days if is_valid else 0,
    }