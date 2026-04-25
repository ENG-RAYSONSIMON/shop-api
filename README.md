# DRF Shop API

A Django REST Framework shop API with JWT authentication, user-owned products, cart management, and atomic checkout.

## Features

- User registration, login, token refresh, and authenticated profile access
- Custom user model with unique email addresses
- Public product listing and product detail endpoints
- Authenticated product creation with automatic product ownership
- Owner-only product update and delete permissions
- Per-user shopping cart with add, update, remove, and view operations
- Atomic checkout flow that converts cart items into order + order line items
- Automatic order total calculation from immutable line-item purchase prices
- Automatic stock reduction at checkout with row locking to avoid race conditions
- Order `status` tracking with default value `pending`
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

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. (Optional) Create a local `.env` file:

```env
DJANGO_SECRET_KEY=change-me-before-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

5. Apply migrations:

```bash
python manage.py migrate
```

6. Start the development server:

```bash
python manage.py runserver
```

Base URL: `http://127.0.0.1:8000/`

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

### Cart

- `GET /api/orders/cart/` — view your cart
- `POST /api/orders/cart/items/` — add a product to cart (increments quantity if already present)
- `PATCH /api/orders/cart/items/<id>/` — update cart item quantity
- `DELETE /api/orders/cart/items/<id>/` — remove cart item

Add item payload:

```json
{
  "product": 1,
  "quantity": 2
}
```

Cart response shape:

```json
{
  "id": 1,
  "user": "alice",
  "items": [
    {
      "id": 1,
      "product": 1,
      "product_name": "Keyboard",
      "unit_price": "89.99",
      "quantity": 2,
      "line_total": "179.98"
    }
  ],
  "total": "179.98",
  "created_at": "2026-04-25T10:00:00Z",
  "updated_at": "2026-04-25T10:05:00Z"
}
```

### Checkout

- `POST /api/orders/checkout/`

Behavior:

- Requires authentication.
- Rejects empty carts.
- Locks product rows using `select_for_update()`.
- Validates stock at checkout time.
- Creates one `Order` + multiple `OrderItem` rows.
- Deducts product stock atomically.
- Clears the cart after successful checkout.

### Orders

- `GET /api/orders/`
- `GET /api/orders/<id>/`

Behavior:

- Normal users can list/retrieve only their own orders.
- Staff and superusers can list/retrieve all orders.
- Order responses include nested order items.
- `status` is read-only in API responses and defaults to `pending`.

Order response shape:

```json
{
  "id": 12,
  "user": "alice",
  "status": "pending",
  "total_price": "214.97",
  "ordered_at": "2026-04-25T10:10:00Z",
  "updated_at": "2026-04-25T10:10:00Z",
  "items": [
    {
      "id": 100,
      "product": 1,
      "product_name": "Keyboard",
      "price_at_purchase": "89.99",
      "quantity": 2,
      "line_total": "179.98"
    },
    {
      "id": 101,
      "product": 5,
      "product_name": "Mouse",
      "price_at_purchase": "34.99",
      "quantity": 1,
      "line_total": "34.99"
    }
  ]
}
```

## Step-by-Step API Testing (quick flow)

1. Register + login, then set `ACCESS_TOKEN`.
2. Create products as an authenticated owner.
3. Add products to cart.
4. View cart.
5. Checkout.
6. List orders and inspect nested items.

Example commands:

```bash
# 1) Register
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"StrongPass123"}'

# 2) Login
curl -X POST http://127.0.0.1:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"StrongPass123"}'

# 3) Add to cart
curl -X POST http://127.0.0.1:8000/api/orders/cart/items/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -d '{"product":1,"quantity":2}'

# 4) View cart
curl http://127.0.0.1:8000/api/orders/cart/ \
  -H "Authorization: Bearer ACCESS_TOKEN"

# 5) Checkout
curl -X POST http://127.0.0.1:8000/api/orders/checkout/ \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# 6) List orders
curl http://127.0.0.1:8000/api/orders/ \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

## Common Error Cases

- `POST /api/orders/cart/items/` with quantity greater than stock returns `400`.
- `PATCH /api/orders/cart/items/<id>/` with invalid quantity returns `400`.
- `POST /api/orders/checkout/` with empty cart returns `400`.
- `POST /api/orders/checkout/` when stock changed and is insufficient returns `400`.
- Unauthorized access to protected endpoints returns `401`.

## Automated Tests

Run the full test suite:

```bash
python manage.py test
```

Or orders tests only:

```bash
python manage.py test orders
```

## Notes

- Browsable API login routes are available at `GET /api-auth/`.
- The default database is SQLite at `db.sqlite3`.
- If `.env` is missing, Django falls back to local defaults in `config/settings.py`.
- For production, set a real `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=False`, and configure `DJANGO_ALLOWED_HOSTS` correctly.
