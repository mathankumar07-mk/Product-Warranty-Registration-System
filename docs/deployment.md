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
7. Frontend: `cd frontend-react && npm install && npm run dev`
   (-> http://127.0.0.1:5173; admin console at `/admin/login`).
   For production builds set `VITE_API_URL` (see
   `frontend-react/.env.example`) before `npm run build`.

## Environment variables

Backend (see `.env.example`): `APP_NAME`, `APP_ENV`, `DEBUG`, `DATABASE_URL`,
`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `JWT_SECRET_KEY`
(>=32 random chars in production), `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`,
`CORS_ORIGINS` (comma-separated trusted frontend origins), `FRONTEND_URL`,
`UPLOAD_DIR`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`,
`SMTP_TLS`, `EMAIL_FROM`, `EMAIL_FROM_NAME`. Never commit `.env` or real
secrets; the `.gitignore` excludes `.env`, `*.db`, uploads, and build output.

Frontend: `VITE_API_URL` (backend base URL, e.g. `http://127.0.0.1:8000`
locally or the deployed API URL in production).

## Database migrations

Migrations are additive only (no data loss): run `alembic upgrade head` before
starting the app on a fresh or upgraded database. The current head is `0006_admin_audit` (`audit_logs`
table + `admins.is_active` backfill). Render runs migrations automatically via
`preDeployCommand`; the Docker image runs them on container start. Verify with
`pytest tests/test_migrations.py`, which exercises the 0006
downgrade/upgrade cycle and the application's graceful fallback when the
audit table is absent.

## Tests

`pytest` (isolated SQLite via `DATABASE_URL` override in tests).

## Render

See `render.yaml` (web service, Python 3.12, `uvicorn app.main:app`).
Set env: `DATABASE_URL`, `JWT_SECRET_KEY` (>=32 chars), `CORS_ORIGINS`,
`FRONTEND_URL`. No auto-deploy on commit.
