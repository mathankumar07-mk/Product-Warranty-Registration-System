# Product-Warranty-Registration-System

# Problem Statement

## 1. Title

**Mini E-Commerce and Product Warranty Registration System**

## 2. Domain

**E-Commerce and Warranty Management**

## 3. Who is the user? (2–3 user types, with roles)

### Customer / User

* Register and login
* Browse products
* Add products to cart
* Place orders and make payments
* Register and track product warranty

### Admin

* Manage users
* Manage categories and products
* Manage orders and payments
* Manage warranty policies and registrations
* Manage notifications

## 4. What problem are we solving?

Customers often need to manage their **product purchases and warranty details separately**.
After purchasing a product, maintaining the purchase invoice, purchase source, warranty dates, and warranty status can be difficult.
Manual warranty registration may also cause missing or incorrect information.
This system provides a single platform to manage **product purchasing and warranty registration** efficiently.

## 5. Proposed Solution

The application will provide:

* User registration and login
* JWT authentication
* User dashboard
* Category and product management
* Product listing and product details
* Shopping cart and cart items
* Order and order items
* Payment management
* Purchase invoice
* Warranty policy management
* Warranty registration
* Purchase source tracking
* Warranty start and end dates
* Warranty status tracking
* Notifications
* Admin management

## 6. Core Entities / Database Tables

1. `users`
2. `admins`
3. `addresses`
4. `categories`
5. `products`
6. `carts`
7. `cart_items`
8. `orders`
9. `order_items`
10. `payments`
11. `purchase_invoices`
12. `warranty_policies`
13. `warranty_registrations`
14. `notifications`

## 7. User Roles & Permissions

| Role         | Main Permissions                                                                                                     |
| ------------ | -------------------------------------------------------------------------------------------------------------------- |
| **Customer** | Register, Login, Browse Products, Cart, Order, Payment, Invoice, Warranty Registration, View Warranty, Notifications |
| **Admin**    | Manage Users, Categories, Products, Orders, Payments, Warranty Policies, Warranty Registrations, Notifications       |

## 8. Success Criteria

* User should be able to **register and login securely**.
* User should be able to browse and purchase products.
* User should be able to add products to cart and place an order.
* Payment details should be recorded successfully.
* Purchase invoice should be available to the customer.
* User should be able to register a purchased product warranty.
* System should record **purchase source, warranty start date and end date**.
* User should be able to view the current **warranty status**.
* Admin should be able to manage products and warranty information.

## 9. Out of Scope

* Warranty claim processing
* Claim document management
* Seller/vendor management
* Real bank payment processing
* Product delivery/logistics management
* Live customer support/chat
* Advanced AI recommendation system

## 10. Chosen Track

**Python – FastAPI**

**Frontend:** React + JSX
**Backend:** Python + FastAPI
**Database:** MySQL
**Authentication:** JWT
**API:** REST API / Swagger OpenAPI
**Payment:** Payment Sandbox
**Version Control:** Git + GitHub
