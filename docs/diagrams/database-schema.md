# Database Schema (3NF notes)

13 entities: users, addresses, categories, products, carts, cart_items,
orders, order_items, payments, purchase_invoices, warranty_policies,
warranty_registrations, notifications (+ admins for operations).

- 1NF: atomic columns, no repeating groups (items in child tables).
- 2NF: order totals derived server-side; order_items snapshot `unit_price`
  at purchase; cart has no price (rechecked from products at checkout).
- 3NF: product brand/category via FKs; warranty dates computed backend
  from policy months; invoice tax/total stored per order (historical).
- Integrity: FKs with RESTRICT/SET NULL/CASCADE as appropriate;
  `with_for_update()` row locks on cart/product/order during checkout;
  unique order/warranty/invoice numbers generated server-side.
- Money: `NUMERIC(12,2)` everywhere; never trust frontend totals.
- MySQL primary (`mysql+pymysql`); Postgres/SQLite via `DATABASE_URL`.
- Migrations: `alembic.ini` + `migrations/` (baseline `0001_baseline`
  calls idempotent `create_all`); legacy `initialize_database()` kept.
