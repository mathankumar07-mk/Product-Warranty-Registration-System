# Deployment

## Local (MySQL primary)

1. `cp .env.example .env` and set `DATABASE_URL`
   (e.g. `mysql+pymysql://root:pw@127.0.0.1:3306/product_warranty_db`)
   or `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD`.
2. `python -m pip install -r requirements.txt`
3. `alembic upgrade head` (or rely on app startup `create_all`).
4. `uvicorn app.main:app --reload` -> http://127.0.0.1:8000 (`/docs`).
5. `python -m scripts.create_admin` for first admin (local shell only).
6. `python scripts/seed_products.py` for sample catalogue.

## Tests

`pytest` (isolated SQLite via `DATABASE_URL` override in tests).

## Render

See `render.yaml` (web service, Python 3.12, `uvicorn app.main:app`).
Set env: `DATABASE_URL`, `JWT_SECRET_KEY` (>=32 chars), `CORS_ORIGINS`,
`FRONTEND_URL`. No auto-deploy on commit.
