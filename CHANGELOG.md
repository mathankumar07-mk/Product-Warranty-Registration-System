# Changelog

## Unreleased (PostgreSQL only)

- Database: PostgreSQL is now the only supported server database; MySQL
  support (`pymysql`, `mysql://` handling, MySQL-first defaults) removed.
  `postgres://` URLs are normalized to `postgresql://`; anything outside
  PostgreSQL/SQLite-test is rejected with a clear error at startup.

## Unreleased (admin console completion)

- Admin console: separate `/admin/login` with server-verified admin check,
  collapsible sidebar layout, deep-link redirect preservation, and
  `/admin/login` routing for expired admin sessions.
- Admin APIs: `/admin/overview`, `/admin/users/search|/{id}`, `/admin/admins`
  (last-admin guards), `/admin/orders` search filters, `/admin/orders/{id}`,
  CSV exports, `/admin/invoices`, `/admin/notifications`,
  `/admin/reports/summary`, `/admin/settings`, `/auth/admin/change-password`.
- Audit trail: immutable `audit_logs` table (migration `0006_admin_audit`)
  recording admin/order/warranty/payment decisions with graceful 503 fallback.
- Validation: email normalization, case-insensitive category uniqueness,
  warranty duration cap (120 months), `is_active` in user responses.
- Tests: `test_admin_overview|_users|_records`, `test_validation`,
  `test_admin_actions`, `test_migrations` (0006 cycle + fallback).
- Frontend: shared pagination, CSV export buttons, print stylesheet, layout
  landmarks, oxlint unused-binding cleanup.

## Unreleased (backend completion)

- Auth: refresh-token rotation + revocation (`RefreshToken` table),
  `POST /auth/refresh|/logout`, `POST /auth/change-password`,
  `POST /auth/forgot-password|/reset-password` (reset token returned
  directly only when SMTP is unconfigured; never claims email sent).
- Payments: `payment_gateway.py` abstraction (labelled sandbox adapter),
  signature-verified `POST /payments/webhook`, `POST /payments/{id}/refund`
  (admin), guarded status transitions, `Idempotency-Key` header support.
- Invoices: auto-generated text file under `UPLOAD_DIR` plus
  `GET /invoices/{id}/download` (owner-only).
- Warranties: category-scoped policies with product-first selection order,
  `GET /warranties/policies` list, external-purchase proof workflow
  (`proof_reference`, `PENDING_REVIEW`), `GET /warranties/registrations/search`.
- Admin: paginated `GET /admin/users|/orders|/payments`, broadcast
  `POST /admin/notifications/broadcast`; catalogue `POST /products/import` CSV.
- Migration `0002_extended_backend` (idempotent); 6 new tests in
  `tests/test_extended.py`.
- Postgres hardening: `0003_reconcile_columns` (backfill missing columns),
  `0004_relax_vestigial_columns` (orphan NOT NULLs), `0005_relax_model_nullable`
  (e.g. payments.transaction_id); `notifications.is_read` Integer → Boolean
  with True/False service writes.
- Frontend: server-side category filter, paginated product unwrapping,
  warranty form fields/status display, invoice download, real policy months,
  login redirect-back, refresh-token retry, forgot-password + account pages,
  admin section with `GET /admins/me` role detection.
- Audit fixes: `VITE_API_URL` env for API base (`frontend-react/.env.example`),
  `/dashboard` alias route, real stdlib-generated PDF invoices
  (`invoice_pdf.py`, Content-Disposition + CORS expose), invoice filename from
  stored path, Home hero free of fake product/stats claims.

## Previous

- Fix `PUT /orders/{id}` to return 409 (not 500) on illegal transition / unpaid confirm.
- Fix `PUT /notifications/read-all` route shadowing by defining static route first.
- Add `GET /health` and `GET /ready` (+ `/api/v1` aliases) without removing legacy paths.
- Add `/api/v1/*` dual-mount compatibility layer (`app/api/v1/api.py`) and `app/api/deps.py`.
- Add `app/core/exceptions.py` and `app/core/logging.py`.
- Add admin dashboard `GET /admin/dashboard` (revenue from completed payments only).
- Migrate config to `pydantic-settings` with legacy constant exports; add
  `APP_NAME/APP_ENV/DEBUG/FRONTEND_URL`; document MySQL-first `DATABASE_URL`.
- Support `mysql+pymysql` (primary) while keeping Postgres/SQLite compat.
- Additive schema: `orders.order_number/idempotency_key`,
  `payments.idempotency_key`, `warranty_policies.is_active/updated_at`,
  `warranty_registrations.warranty_number` (server-generated).
- Add Alembic (`alembic.ini`, `migrations/` baseline) and docs
  (`er-diagram`, `architecture`, `database-schema`, `api-contract`, `deployment`).
- Harden `.gitignore`; update `requirements.txt` (`pydantic-settings`,
  `pymysql`, `alembic`).
