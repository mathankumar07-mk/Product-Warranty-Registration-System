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

MySQL is the primary database (`mysql+pymysql`). PostgreSQL and SQLite remain
supported via `DATABASE_URL` for backward compatibility and isolated tests.

```env
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/product_warranty_db
JWT_SECRET_KEY=change-this-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

For local development, copy `.env.example` to `.env`. `DATABASE_URL` overrides
`DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD` (legacy Postgres defaults still
use the `postgresql+psycopg2` driver when `DB_PORT=5432`/`DB_USER=postgres`).
SQLite example: `sqlite:///./local.db`. Set `CORS_ORIGINS` to a comma-separated
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
python scripts/seed_products.py
```

## Run Frontend

```powershell
cd frontend-react
npm install
npm run dev
```

The frontend will be available at `http://127.0.0.1:5173`.

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
- Admin: `/admin/dashboard`, `/admin/users`, `/admin/orders`, `/admin/payments`, `/admin/notifications/broadcast`, `/admins`
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
