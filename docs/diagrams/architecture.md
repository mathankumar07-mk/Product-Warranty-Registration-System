# Architecture

FastAPI (thin routers) -> services (business logic) -> SQLAlchemy 2.x models.
Shared `app/core` for settings (`pydantic-settings`), DB engine/session,
JWT auth, logging, exceptions.

```mermaid
flowchart LR
  FE[Frontend] --> API[FastAPI routers<br/>/auth /products /orders ...<br/>+ /api/v1 aliases]
  API --> SVC[Services<br/>cart/order/payment/warranty]
  SVC --> DB[(PostgreSQL only<br/>SQLite for tests)]
  SVC --> NOTIF[Notifications + optional SMTP]
  API --> HEALTH[/health /ready<br/>public]
```

Versioning: legacy bare paths keep working; new clients should use `/api/v1/*`.
Admin: `GET /admin/dashboard` (revenue from completed payments only).
