# API Contract (summary)

Base: bare paths (legacy) + `/api/v1` aliases. Auth: `Bearer <JWT>`.

- Health: `GET /health`, `GET /ready` (+ `/api/v1/...`).
- Auth: `POST /auth/register|/login` (login returns access + refresh),
  `POST /auth/refresh|/logout`, `POST /auth/change-password`,
  `POST /auth/forgot-password|/reset-password`, `GET /auth/me`,
  `POST /auth/admin/register` (admin).
- Users/addresses: `GET|PUT /users/me`, `GET|POST /users/me/addresses`.
- Admins: `POST /admins` (admin); dashboard `GET /admin/dashboard` (admin).
- Categories/products: CRUD (admin write, public read); products support
  `search, category_id, brand, min/max_price, sort, page, page_size`.
- Cart: `GET /cart`, `POST /cart/items`, `PUT|DELETE /cart/items/{id}`,
  `DELETE /cart`.
- Orders: `POST /orders` (checkout from cart), `GET /orders`,
  `GET /orders/{id}`, `PUT /orders/{id}` (admin status; 409 on bad transition
  or unpaid confirm).
- Payments (sandbox-labelled gateway abstraction in `payment_gateway.py`):
  `POST /payments` (`Idempotency-Key` header supported), `GET /payments?order_id=`,
  `GET /payments/{id}`, `PUT /payments/{id}` (admin, guarded transitions only),
  `POST /payments/{id}/simulate?success=`, `POST /payments/{id}/refund` (admin),
  `POST /payments/webhook` (signature-verified).
- Invoices: `POST /invoices` (admin), `GET /invoices/{id}`,
  `GET /invoices/order/{order_id}`, `GET /invoices/{id}/download`,
  `PUT /invoices/{id}` (admin). Files auto-generated under `UPLOAD_DIR`.
- Warranties: policies `POST /warranties/policies` (admin, product- or
  category-scoped), `GET /warranties/policies[?is_active=]`,
  `GET /warranties/policies/{id}|/product/{product_id}`,
  `PUT /warranties/policies/{id}` (admin); selection is product-specific
  before category default.
  registrations `POST /warranties/register` (external sources require
  `proof_reference` or invoice; start as `PENDING_REVIEW`),
  `GET /warranties/registrations|/{id}|/{id}/validity`,
  `GET /warranties/registrations/search` (admin, `status`/`product_id`),
  `PUT /warranties/registrations/{id}` (admin).
- Notifications: `GET /notifications?unread_only=`,
  `PUT /notifications/read-all`, `PUT /notifications/{id}/read`.
- Admin: `GET /admin/dashboard|/users|/orders[?status=]|/payments` (paginated),
  `POST /admin/notifications/broadcast`.
- Catalogue: `POST /products/import` (admin, multipart CSV).
- Infra: `GET /database-test`, `GET /` root.

Errors: 400 validation, 401 auth, 404 missing/not-owned, 409 conflict.
