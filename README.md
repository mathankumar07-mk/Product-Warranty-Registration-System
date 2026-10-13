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

The project is configured for PostgreSQL using the values in the root `.env` file:

```env
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=product_warranty_db
DB_USER=postgres
DB_PASSWORD=postgres
JWT_SECRET_KEY=change-this-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

For local development, copy `.env.example` to `.env`. Set `DATABASE_URL` to override
the PostgreSQL connection, for example `sqlite:///./local.db`. Set `CORS_ORIGINS`
to a comma-separated list of trusted frontend origins. In production, set
`ENVIRONMENT=production` and replace the development JWT secret with a long,
random secret; the application refuses to start with the default JWT secret.

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

- Authentication: `/auth/register`, `/auth/login`, `/auth/me`
- Users and addresses: `/users`, `/addresses`
- Categories and products: `/categories`, `/products`
- Cart and orders: `/cart`, `/orders`
- Payments and invoices: `/payments`, `/invoices`
- Warranties: `/warranties`
- Notifications: `/notifications`
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
