from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from decimal import Decimal

from app.core.dependencies import DBSession, get_current_admin
from app.models.admin import Admin
from app.schemas.product import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate
from app.services import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        return product_service.create_product(db, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("", response_model=ProductListResponse)
def list_products(
    db: DBSession,
    search: str | None = Query(None, description="Search by name, brand, model number, or description"),
    category_id: int | None = Query(None, ge=1, description="Filter by category ID"),
    brand: str | None = Query(None, description="Filter by brand"),
    min_price: Decimal | None = Query(None, description="Minimum price", ge=0),
    max_price: Decimal | None = Query(None, description="Maximum price", ge=0),
    warranty_available: bool | None = Query(None, description="Filter by warranty availability"),
    in_stock_only: bool = Query(False, description="Show only in-stock products"),
    sort: str = Query("id", pattern="^-?(id|name|price|created_at|brand)$", description="Sort field with optional '-' for descending"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="min_price must not exceed max_price")
    products, total = product_service.list_products(
        db,
        search=search,
        category_id=category_id,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        warranty_available=warranty_available,
        in_stock_only=in_stock_only,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return {
        "products": products,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/import", response_model=dict)
def import_products(
    db: DBSession, admin: Admin = Depends(get_current_admin), file: UploadFile = File(...)
):
    """Validated CSV catalogue import.

    Columns: name, model_number, price, stock_quantity, brand, category_id,
    plus optional description, image_url, warranty_available (true/false).
    Rows with duplicate model numbers are skipped; invalid rows are reported.
    """
    import csv
    import io

    try:
        text = file.file.read().decode("utf-8-sig")
    except Exception as error:
        raise HTTPException(status_code=400, detail="Could not read uploaded file") from error
    reader = csv.DictReader(io.StringIO(text))
    required = {"name", "model_number", "price", "brand", "category_id"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain columns: {sorted(required)}",
        )
    created, skipped, errors = 0, 0, []
    for line_no, row in enumerate(reader, start=2):
        try:
            data = ProductCreate(
                category_id=int(row["category_id"]),
                name=row["name"].strip(),
                description=(row.get("description") or None),
                price=Decimal(str(row["price"])),
                stock_quantity=int(row.get("stock_quantity") or 0),
                brand=row["brand"].strip(),
                model_number=row["model_number"].strip(),
                image_url=(row.get("image_url") or None),
                warranty_available=str(row.get("warranty_available") or "").lower()
                in {"true", "1", "yes"},
            )
            product_service.create_product(db, data)
            created += 1
        except ValueError as error:
            if "already exists" in str(error):
                skipped += 1
            else:
                errors.append({"row": line_no, "error": str(error)})
        except Exception as error:
            errors.append({"row": line_no, "error": str(error)})
    return {"created": created, "skipped": skipped, "errors": errors}


@router.get("/brands", response_model=list[str])
def get_brands(db: DBSession):
    return product_service.get_brands(db)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: DBSession):
    try:
        product = product_service.get_product(db, product_id)
        if not product.is_active or not product.category.is_active:
            raise LookupError("Product not found")
        return product
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductUpdate, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        return product_service.update_product(db, product_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: DBSession, admin: Admin = Depends(get_current_admin)):
    try:
        product_service.delete_product(db, product_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error