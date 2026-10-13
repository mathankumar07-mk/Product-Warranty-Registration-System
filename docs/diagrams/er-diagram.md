# ER Diagram (3NF)

```mermaid
erDiagram
  USERS ||--o{ ADDRESSES : has
  USERS ||--o{ CARTS : owns
  CARTS ||--o{ CART_ITEMS : contains
  PRODUCTS ||--o{ CART_ITEMS : listed-in
  CATEGORIES ||--o{ PRODUCTS : groups
  USERS ||--o{ ORDERS : places
  ORDERS ||--o{ ORDER_ITEMS : has
  PRODUCTS ||--o{ ORDER_ITEMS : sold-as
  ORDERS ||--o{ PAYMENTS : paid-by
  ORDERS ||--o| PURCHASE_INVOICES : invoiced-as
  PRODUCTS ||--o| WARRANTY_POLICIES : covered-by
  WARRANTY_POLICIES ||--o{ WARRANTY_REGISTRATIONS : governs
  USERS ||--o{ WARRANTY_REGISTRATIONS : registers
  PRODUCTS ||--o{ WARRANTY_REGISTRATIONS : covers
  PURCHASE_INVOICES ||--o{ WARRANTY_REGISTRATIONS : proves
  USERS ||--o{ NOTIFICATIONS : receives
  USERS ||--o{ ADMINS : manages
```

Keys: all tables use integer PK `id`. Money uses `NUMERIC(12,2)`.
Unique: `users.email`, `admins.email`, `products.model_number`,
`orders.order_number`, `payments.transaction_id`, `purchase_invoices.invoice_number`,
`warranty_registrations.warranty_number`,
`(warranty_registrations.product_id, serial_number)`.
