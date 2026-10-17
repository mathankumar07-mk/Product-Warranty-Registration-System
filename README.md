# Mini E-Commerce and Product Warranty Registration System

## Description

A FastAPI backend for product browsing, shopping carts, orders, payments, invoices, and product warranty registration with a React frontend.

## Features

- JWT authentication with bcrypt password hashing
- User and admin authorization
- Product and category management
- Addresses, carts, orders, and sandbox payments
- Invoice records and warranty policy registration
- User notifications
- Admin console (separate `/admin/login`, dashboard, user/admin management,
  orders, payments, invoices, warranties, notifications, reports, audit logs)
- Automatic SQLAlchemy table initialization for the 14 specified tables

## Technology Stack

- Python, FastAPI, Uvicorn
- SQLAlchemy with PostgreSQL and psycopg2
- Pydantic
- JWT with `python-jose`
- React, JavaScript/JSX, HTML, CSS for the frontend

## Folder Structure

The active backend package is the root `app/` package so it runs with `uvicorn app.main:app --reload`. The `backend/` directory preserves the requested project scaffold and environment examples. Frontend files are in `frontend-react/`.

## Database Setup

PostgreSQL is the only supported server database (`postgresql+psycopg2`;
`postgres://` URLs from providers are accepted too). SQLite remains available
for the isolated test suite via `DATABASE_URL`.

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/product_warranty_db
JWT_SECRET_KEY=change-this-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

For local development, copy `.env.example` to `.env`. `DATABASE_URL` overrides
`DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD` (defaults target a local
PostgreSQL at `127.0.0.1:5432`). Set `CORS_ORIGINS` to a comma-separated
list of trusted frontend origins. In production, set `ENVIRONMENT=production`
(or `APP_ENV`) and replace the development JWT secret with a long, random
secret (>=32 chars); the application refuses to start with the default secret.

Migrations: `alembic upgrade head` (baseline `migrations/0001_baseline.py` is
idempotent; app startup also ensures tables exist).

## Installation

```powershell
python -m pip install -r requirements.txt
```

## Run Backend

```powershell
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Swagger documentation is available at `/docs`.

Create the initial administrator from a trusted local shell. The password is
prompted without being echoed; subsequent administrator accounts can be created
with an administrator token through `POST /admins` or `POST /auth/admin/register`.

```powershell
python -m scripts.create_admin
```

To add the sample catalogue after PostgreSQL is configured, run:

```powershell
$env:PYTHONPATH='.'; python scripts/seed_products.py
```

## Run Frontend

```powershell
cd frontend-react
npm install
npm run dev
```

The frontend will be available at `http://127.0.0.1:5173`.

## Admin Console

Administrators sign in at `/admin/login` (customer accounts are rejected there).
Unauthenticated visits to `/admin/*` redirect to `/admin/login`, and expired
admin sessions return there instead of the customer login page. The console
provides a collapsible sidebar with Dashboard, Users, Admin Accounts, Products,
Categories, Orders, Payments, Purchase Invoices, Warranty Policies, Warranty
Registrations, Notifications, Reports & Analytics, Audit Logs, and Settings.

Backend authorization never trusts client roles: every admin endpoint requires a
JWT with `is_admin=true` for an active row in the `admins` table. Deactivated
accounts cannot log in. Admin creation, activation, order/warranty/payment
decisions, and password changes are recorded in the immutable `audit_logs`
table (migration `0006_admin_audit`). The last active administrator cannot be
deactivated or deleted, and customers with historical orders or warranties can
only be deactivated, never deleted.

## API Overview

All paths below also work under `/api/v1` (e.g. `/api/v1/orders`); bare paths
are kept for backward compatibility.

- Health: `/health`, `/ready`
- Authentication: `/auth/register`, `/auth/login` (access + refresh), `/auth/refresh`, `/auth/logout`, `/auth/change-password`, `/auth/forgot-password`, `/auth/reset-password`, `/auth/me`
- Users and addresses: `/users`, `/addresses`
- Categories and products: `/categories`, `/products`
- Cart and orders: `/cart`, `/orders` (orders now expose server-generated `order_number`)
- Payments and invoices: `/payments` (incl. `/webhook`, `/{id}/refund`, `Idempotency-Key`), `/invoices` (incl. `/{id}/download`)
- Warranties: `/warranties` (registrations now expose `warranty_number`; policies have `is_active`; category fallback; external proof → `PENDING_REVIEW`)
- Notifications: `/notifications`
- Admin: `/admin/overview` (totals, recent activity, sales trend, top products),
  `/admin/users/search|/{id}`, `/admin/admins`, `/admin/orders` (customer and
  order-number search) + `/admin/orders/{id}|/export`, `/admin/payments`,
  `/admin/invoices` (+ `/{id}|/{id}/download`), `/admin/notifications`,
  `/admin/registrations/export`, `/admin/reports/summary`, `/admin/audit-logs`,
  `/admin/settings`, `/admin/dashboard`, `/admin/users`, `/admin/orders`,
  `/admin/payments`, `/admin/notifications/broadcast`, `/admins`,
  `/auth/admin/change-password`, `/auth/admin/register`
- Catalogue: `POST /products/import` (admin CSV)
- Database health check: `/database-test`

## Authentication Flow

1. Register a user via `POST /auth/register`
2. Login via `POST /auth/login` to get JWT token
3. Include token in Authorization header: `Authorization: Bearer <token>`
4. Access protected endpoints

## Testing Commands

```powershell
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage (install pytest-cov separately)
pytest --cov=app tests/
```
