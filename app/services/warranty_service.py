from datetime import datetime, timezone, timedelta
from uuid import uuid4
from dateutil.relativedelta import relativedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _generate_warranty_number() -> str:
    return f"WRT-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:8].upper()}"

from app.models.product import Product
from app.models.purchase_invoice import PurchaseInvoice
from app.models.notification import NotificationType
from app.models.warranty_policy import WarrantyPolicy
from app.models.warranty_registration import WarrantyRegistration, WarrantyStatus, PurchaseSource
from app.models.user import User
from app.schemas.warranty import WarrantyPolicyCreate, WarrantyPolicyUpdate
from app.schemas.warranty_registration import WarrantyRegistrationCreate, WarrantyRegistrationUpdate
from app.services.notification_service import add_user_notification
from app.services.email_service import render_warranty_registration_email, send_email


def create_warranty_policy(db: Session, data: WarrantyPolicyCreate) -> WarrantyPolicy:
    if bool(data.product_id) == bool(data.category_id):
        raise ValueError("Exactly one of product_id or category_id must be set")
    if data.product_id:
        from app.models.product import Product as _Product

        product = db.get(_Product, data.product_id)
        if not product:
            raise LookupError("Product not found")
        if not product.is_active:
            raise ValueError("Cannot create a warranty policy for an inactive product")
        if product.warranty_policy:
            raise ValueError("Warranty policy already exists for this product")
    else:
        from app.models.category import Category as _Category

        category = db.get(_Category, data.category_id)
        if not category:
            raise LookupError("Category not found")
        existing = (
            db.query(WarrantyPolicy).filter(WarrantyPolicy.category_id == data.category_id).first()
        )
        if existing:
            raise ValueError("Warranty policy already exists for this category")
    policy = WarrantyPolicy(**data.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def get_applicable_policy(db: Session, product: Product) -> WarrantyPolicy:
    """Product-specific policy first, then active category default."""
    if product.warranty_policy and product.warranty_policy.is_active:
        return product.warranty_policy
    fallback = (
        db.query(WarrantyPolicy)
        .filter(WarrantyPolicy.category_id == product.category_id, WarrantyPolicy.is_active.is_(True))
        .first()
    )
    if not fallback:
        raise LookupError("No warranty policy for this product")
    return fallback


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


def list_warranty_policies(db: Session, is_active: bool | None = None) -> list[WarrantyPolicy]:
    query = db.query(WarrantyPolicy).order_by(WarrantyPolicy.created_at.desc())
    if is_active is not None:
        query = query.filter(WarrantyPolicy.is_active.is_(is_active))
    return query.all()


def search_registrations(
    db: Session, status: str | None = None, product_id: int | None = None
) -> list[WarrantyRegistration]:
    query = db.query(WarrantyRegistration).order_by(WarrantyRegistration.created_at.desc())
    if status is not None:
        query = query.filter(WarrantyRegistration.warranty_status == WarrantyStatus(status))
    if product_id is not None:
        query = query.filter(WarrantyRegistration.product_id == product_id)
    return query.all()


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
    if not policy.is_active:
        raise ValueError("Warranty policy is inactive")
    product = db.get(Product, data.product_id)
    if not product:
        raise LookupError("Product not found")
    if policy.product_id:
        if data.product_id != policy.product_id:
            raise ValueError("Product does not match warranty policy")
    elif policy.category_id:
        if product.category_id != policy.category_id:
            raise ValueError("Product does not match warranty policy category")
    # NOTE: warranty_available is informational/filters only; an active matching
    # policy is the eligibility gate (keeps legacy products registrable).
    
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
    
    # Ensure datetime is timezone-aware for comparison
    if warranty_end_date.tzinfo is None:
        warranty_end_date = warranty_end_date.replace(tzinfo=timezone.utc)
    if warranty_start_date.tzinfo is None:
        warranty_start_date = warranty_start_date.replace(tzinfo=timezone.utc)
    
    # External purchases require proof and start as PENDING_REVIEW.
    is_external = purchase_source != PurchaseSource.COMPANY_WEBSITE
    if is_external and not (data.proof_reference or data.purchase_invoice_id):
        raise ValueError("External purchases require proof_reference or purchase_invoice_id")

    # Determine initial warranty status
    now = datetime.now(timezone.utc)
    if warranty_end_date < now:
        warranty_status = WarrantyStatus.EXPIRED
    elif is_external:
        warranty_status = WarrantyStatus.PENDING_REVIEW
    elif warranty_start_date > now:
        warranty_status = WarrantyStatus.PENDING
    else:
        warranty_status = WarrantyStatus.ACTIVE
    
    existing = db.query(WarrantyRegistration).filter(
        WarrantyRegistration.product_id == data.product_id,
        WarrantyRegistration.serial_number == data.serial_number,
    ).first()
    if existing:
        raise ValueError("Serial number is already registered for this product")
    if data.purchase_invoice_id:
        existing = db.query(WarrantyRegistration).filter(
            WarrantyRegistration.product_id == data.product_id,
            WarrantyRegistration.purchase_invoice_id == data.purchase_invoice_id,
        ).first()
        if existing:
            raise ValueError("Warranty already registered for this product and invoice")
    
    registration = WarrantyRegistration(
        warranty_number=_generate_warranty_number(),
        policy_id=data.policy_id,
        user_id=user_id,
        product_id=data.product_id,
        purchase_invoice_id=data.purchase_invoice_id,
        serial_number=data.serial_number,
        purchase_source=purchase_source,
        proof_reference=data.proof_reference,
        purchase_date=data.purchase_date,
        warranty_start_date=warranty_start_date,
        warranty_end_date=warranty_end_date,
        warranty_status=warranty_status,
    )
    db.add(registration)
    add_user_notification(
        db,
        user_id,
        NotificationType.warranty,
        f"Warranty registered for {product.name}",
        f"Warranty for serial number {registration.serial_number} is {registration.warranty_status.value.lower()}.",
    )
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Warranty is already registered for this product") from error
    db.refresh(registration)
    user = db.get(User, user_id)
    html, text = render_warranty_registration_email(
        user.name,
        product.name,
        registration.serial_number,
        registration.warranty_end_date.isoformat(),
        registration.warranty_status.value,
    )
    import asyncio

    asyncio.run(
        send_email(
            user.email,
            f"Warranty Registered - {product.name}",
            html,
            text,
        )
    )
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
        if key == "warranty_status":
            value = WarrantyStatus(value)
        setattr(registration, key, value)
    registration.updated_at = datetime.now(timezone.utc)
    if "warranty_status" in values:
        add_user_notification(
            db,
            registration.user_id,
            NotificationType.warranty,
            f"Warranty registration #{registration.id} updated",
            f"Your warranty registration is now {registration.warranty_status.value.lower()}.",
        )
    db.commit()
    db.refresh(registration)
    return registration


def check_warranty_validity(db: Session, registration_id: int, user: User | None = None) -> dict:
    registration = get_registration(db, registration_id, user)
    now = datetime.now(timezone.utc)
    
    # Ensure datetime is timezone-aware for comparison
    warranty_end_date = registration.warranty_end_date
    warranty_start_date = registration.warranty_start_date
    if warranty_end_date.tzinfo is None:
        warranty_end_date = warranty_end_date.replace(tzinfo=timezone.utc)
    if warranty_start_date.tzinfo is None:
        warranty_start_date = warranty_start_date.replace(tzinfo=timezone.utc)
    
    is_valid = registration.warranty_status == WarrantyStatus.ACTIVE and now <= warranty_end_date
    
    # Auto-update status based on dates
    if warranty_end_date < now and registration.warranty_status != WarrantyStatus.EXPIRED:
        registration.warranty_status = WarrantyStatus.EXPIRED
        db.commit()
        db.refresh(registration)
        is_valid = False
    elif warranty_start_date > now and registration.warranty_status != WarrantyStatus.PENDING:
        registration.warranty_status = WarrantyStatus.PENDING
        db.commit()
        db.refresh(registration)
        is_valid = False
    elif (
        warranty_start_date <= now <= warranty_end_date
        and registration.warranty_status not in (WarrantyStatus.ACTIVE, WarrantyStatus.PENDING_REVIEW)
    ):
        registration.warranty_status = WarrantyStatus.ACTIVE
        db.commit()
        db.refresh(registration)
        is_valid = True
    
    return {
        "valid": is_valid,
        "warranty_status": registration.warranty_status.value,
        "warranty_start_date": registration.warranty_start_date.isoformat(),
        "warranty_end_date": registration.warranty_end_date.isoformat(),
        "days_remaining": (warranty_end_date - now).days if is_valid else 0,
    }