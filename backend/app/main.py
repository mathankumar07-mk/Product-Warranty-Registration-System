from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    addresses_router,
    admins_router,
    auth_router,
    carts_router,
    categories_router,
    database_test_router,
    invoices_router,
    notifications_router,
    orders_router,
    payments_router,
    products_router,
    users_router,
    warranties_router,
)
from app.core.database import Base, engine
from app.models import (
    Address,
    Admin,
    Cart,
    CartItem,
    Category,
    Notification,
    Order,
    OrderItem,
    Payment,
    Product,
    PurchaseInvoice,
    User,
    WarrantyPolicy,
    WarrantyRegistration,
)


app = FastAPI(
    title="Mini E-Commerce and Product Warranty Registration System"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

for router in (
    auth_router,
    users_router,
    admins_router,
    addresses_router,
    categories_router,
    products_router,
    carts_router,
    orders_router,
    payments_router,
    invoices_router,
    warranties_router,
    notifications_router,
    database_test_router,
):
    app.include_router(router)


@app.get("/")
def root():
    return {"message": "API is running successfully"}