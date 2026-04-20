# DRF Shop API

A Django REST Framework shop API with JWT authentication, user-owned products, and stock-aware order creation.

## Features

- User registration, login, token refresh, and authenticated profile access
- Custom user model with unique email addresses
- Public product listing and product detail endpoints
- Authenticated product creation with automatic product ownership
- Owner-only product update and delete permissions
- Order creation for authenticated users
- Automatic order `total_price` calculation
- Automatic product stock reduction when an order is created
- Order validation for out-of-stock products, oversized quantities, and non-positive quantities
- Order `status` tracking with a default value of `pending`
- Per-user order history for normal users
- Full order visibility for staff and superusers

## Tech Stack

- Python 3.12
- Django 6.0.4
- Django REST Framework 3.17.1
- Simple JWT 5.5.1
- SQLite
- `python-dotenv` for local environment loading

## Project Structure

```text
shop_api/
|-- config/
|-- users/
|-- products/
|-- orders/
|-- manage.py
|-- requirements.txt
|-- README.md
```

## Setup

1. Clone the repository:

```bash
git clone <your-repo-url>
cd shop_api
```

2. Create and activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a local `.env` file:

```powershell
Copy-Item .env.example .env
```

Example `.env` values:

```env
DJANGO_SECRET_KEY=change-me-before-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

The project loads `.env` automatically from the repository root.

5. Apply migrations:

```bash
python manage.py migrate
```

6. Start the development server:

```bash
python manage.py runserver
```

Base URL:

```text
http://127.0.0.1:8000/
```

## Authentication

The API uses JWT bearer tokens via Simple JWT.

- Access token lifetime: 30 minutes
- Refresh token lifetime: 1 day
- Auth header format: `Authorization: Bearer <access_token>`

## API Overview

### Users

- `POST /api/users/register/`
- `POST /api/users/login/`
- `POST /api/users/token/refresh/`
- `GET /api/users/profile/`

### Products

- `GET /api/products/`
- `POST /api/products/`
- `GET /api/products/<id>/`
- `PATCH /api/products/<id>/`
- `DELETE /api/products/<id>/`

Behavior:

- Anyone can list and retrieve products.
- Only authenticated users can create products.
- The authenticated user is saved automatically as the product owner.
- Only the owner of a product can update or delete it.
- The `user` field in product responses is read-only and returns the owner username.

### Orders

- `GET /api/orders/`
- `POST /api/orders/`
- `GET /api/orders/<id>/`

Behavior:

- Only authenticated users can create and view orders.
- Normal users can only list and retrieve their own orders.
- Staff and superusers can list and retrieve all orders.
- `total_price` is calculated automatically from `product.price * quantity`.
- `status` is read-only in the API and defaults to `pending`.
- Product stock is reduced automatically when an order is created.

Validation:

- Quantity must be greater than `0`.
- Orders are rejected if the product is out of stock.
- Orders are rejected if the requested quantity is greater than available stock.

## Step-By-Step API Testing

Open a second terminal after the server is running.

### 1. Register a user

```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"alice\",\"email\":\"alice@example.com\",\"password\":\"StrongPass123\"}"
```

Expected result: `201 Created`

Example response:

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com"
}
```

### 2. Log in and get JWT tokens

```bash
curl -X POST http://127.0.0.1:8000/api/users/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"alice\",\"password\":\"StrongPass123\"}"
```

Expected result: JSON with `access` and `refresh`.

### 3. View the logged-in user profile

```bash
curl http://127.0.0.1:8000/api/users/profile/ ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected result: your user details.

### 4. Create a product

```bash
curl -X POST http://127.0.0.1:8000/api/products/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" ^
  -d "{\"name\":\"Keyboard\",\"description\":\"Mechanical keyboard\",\"price\":\"89.99\",\"stock\":10}"
```

Expected result: `201 Created`

Example response:

```json
{
  "id": 1,
  "user": "alice",
  "name": "Keyboard",
  "description": "Mechanical keyboard",
  "price": "89.99",
  "stock": 10,
  "created_at": "2026-04-20T08:00:00Z"
}
```

### 5. List products

```bash
curl http://127.0.0.1:8000/api/products/
```

Expected result: a public list of products ordered by newest first.

### 6. Update your product

Replace `1` with the real product ID.

```bash
curl -X PATCH http://127.0.0.1:8000/api/products/1/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" ^
  -d "{\"price\":\"79.99\",\"stock\":7}"
```

Expected result: updated product data.

If a different authenticated user tries to update this product, the API returns `403 Forbidden`.

### 7. Create an order

Replace `1` with the product ID you want to order.

```bash
curl -X POST http://127.0.0.1:8000/api/orders/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" ^
  -d "{\"product\":1,\"quantity\":2}"
```

Expected result: `201 Created`

Example response:

```json
{
  "id": 1,
  "user": "alice",
  "product": 1,
  "quantity": 2,
  "status": "pending",
  "total_price": "159.98",
  "ordered_at": "2026-04-20T08:05:00Z"
}
```

Notes:

- `status` is assigned automatically.
- `total_price` is calculated automatically.
- The product's stock is reduced after the order is created.

### 8. List your orders

```bash
curl http://127.0.0.1:8000/api/orders/ ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected result:

- Normal users see only their own orders.
- Staff users see all orders.

### 9. View one order

Replace `1` with the order ID.

```bash
curl http://127.0.0.1:8000/api/orders/1/ ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected result:

- Normal users can retrieve only their own orders.
- Staff users can retrieve any order.
- A normal user trying to access someone else's order gets `404 Not Found`.

### 10. Refresh an access token

```bash
curl -X POST http://127.0.0.1:8000/api/users/token/refresh/ ^
  -H "Content-Type: application/json" ^
  -d "{\"refresh\":\"YOUR_REFRESH_TOKEN\"}"
```

Expected result: a new access token.

## Common Error Cases

### Unauthenticated product creation

`POST /api/products/` without a bearer token returns `401 Unauthorized`.

### Out-of-stock order

If the selected product has `stock = 0`, the API returns `400 Bad Request`.

Example response:

```json
{
  "product": "This product is out of stock."
}
```

### Quantity greater than available stock

If requested quantity exceeds stock, the API returns `400 Bad Request`.

Example response:

```json
{
  "quantity": "Only 5 item(s) available in stock."
}
```

### Zero or negative quantity

If quantity is `0` or less, the API returns `400 Bad Request`.

Example response:

```json
{
  "quantity": [
    "Quantity must be greater than 0."
  ]
}
```

## Automated Tests

Run the full test suite with:

```bash
python manage.py test
```

The current test suite covers:

- user registration, login, and profile protection
- public product listing and retrieval
- authenticated product creation
- owner-only product updates
- order creation with automatic status and total price
- stock reduction after ordering
- order validation for stock and quantity rules
- user-only order visibility
- admin access to all orders

## Notes

- The project includes Django's browsable API login routes at `GET /api-auth/`.
- The default database is SQLite at `db.sqlite3`.
- If `.env` is missing, Django falls back to safe local defaults from [config/settings.py](/c:/Users/dell/Desktop/Learn/drf_shop_api/config/settings.py).
- For production, set a real `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=False`, and configure `DJANGO_ALLOWED_HOSTS` properly.
