"""Mandatory ``/api/v1`` router.

The project historically exposes bare prefixes (``/auth`` …). To satisfy
the reference architecture without breaking the existing frontend and
tests, the same routers are mounted a second time under ``/api/v1``.
New code should use the versioned paths; old paths keep working.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api import (
    addresses_router,
    admin_dashboard_router,
    admin_extended_router,
    admins_router,
    auth_router,
    carts_router,
    categories_router,
    database_test_router,
    health_router,
    invoices_router,
    notifications_router,
    orders_router,
    payments_router,
    products_router,
    users_router,
    warranties_router,
)

v1_router = APIRouter(prefix="/api/v1")

for _router in (
    auth_router,
    users_router,
    admins_router,
    admin_dashboard_router,
    admin_extended_router,
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
    health_router,
):
    v1_router.include_router(_router)

__all__ = ["v1_router"]
