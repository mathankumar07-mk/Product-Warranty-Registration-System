from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import CORS_ORIGINS

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
from app.core.database import initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Mini E-Commerce and Product Warranty Registration System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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