from app.api.addresses import router as addresses_router
from app.api.admin_dashboard import router as admin_dashboard_router
from app.api.admins import router as admins_router
from app.api.auth import router as auth_router
from app.api.carts import router as carts_router
from app.api.categories import router as categories_router
from app.api.database_test import router as database_test_router
from app.api.health import router as health_router
from app.api.invoices import router as invoices_router
from app.api.notifications import router as notifications_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.products import router as products_router
from app.api.users import router as users_router
from app.api.warranties import router as warranties_router

__all__ = [
    "addresses_router",
    "admin_dashboard_router",
    "admins_router",
    "auth_router",
    "carts_router",
    "categories_router",
    "database_test_router",
    "health_router",
    "invoices_router",
    "notifications_router",
    "orders_router",
    "payments_router",
    "products_router",
    "users_router",
    "warranties_router",
]