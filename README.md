# DRF Shop API

A simple shop API built with Django REST Framework and JWT authentication. It includes:

- User registration, login, token refresh, and profile
- Product listing, creation, update, and delete
- Order creation and per-user order history

## Tech Stack

- Python 3.12
- Django 6
- Django REST Framework
- Simple JWT
- SQLite

## Project Structure

```text
drf_shop_api/
|-- config/
|-- users/
|-- products/
|-- orders/
|-- manage.py
|-- requirements.txt
```

## Setup

1. Clone the repository:

```bash
git clone <your-repo-url>
cd drf_shop_api
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

4. Optional environment variables:

```powershell
Copy-Item .env.example .env
```

This project reads these environment variables if you set them in your shell:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`

5. Apply migrations:

```bash
python manage.py migrate
```

6. Start the server:

```bash
python manage.py runserver
```

Base URL:

```text
http://127.0.0.1:8000/
```

## Step-By-Step API Testing

Open a second terminal after the server is running.

### 1. Register a user

```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"alice\",\"email\":\"alice@example.com\",\"password\":\"StrongPass123\"}"
```

Expected result: `201 Created`

### 2. Log in and get JWT tokens

```bash
curl -X POST http://127.0.0.1:8000/api/users/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"alice\",\"password\":\"StrongPass123\"}"
```

Expected result: JSON with `access` and `refresh`.

Copy the `access` token and use it below.

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

Expected result: `201 Created` with the new product.

### 5. List products

```bash
curl http://127.0.0.1:8000/api/products/
```

Expected result: a list of products. This endpoint is public.

### 6. Update your product

Replace `1` with the real product ID.

```bash
curl -X PATCH http://127.0.0.1:8000/api/products/1/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" ^
  -d "{\"price\":\"79.99\",\"stock\":7}"
```

Expected result: updated product data.

### 7. Create an order

Replace `1` with the product ID you want to order.

```bash
curl -X POST http://127.0.0.1:8000/api/orders/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" ^
  -d "{\"product\":1,\"quantity\":2}"
```

Expected result: `total_price` is calculated automatically.

### 8. List your orders

```bash
curl http://127.0.0.1:8000/api/orders/ ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected result: only your own orders.

### 9. View one order

Replace `1` with the order ID.

```bash
curl http://127.0.0.1:8000/api/orders/1/ ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected result: your selected order if it belongs to you.

### 10. Refresh an access token

```bash
curl -X POST http://127.0.0.1:8000/api/users/token/refresh/ ^
  -H "Content-Type: application/json" ^
  -d "{\"refresh\":\"YOUR_REFRESH_TOKEN\"}"
```

Expected result: a new access token.

## Endpoint Summary

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

### Orders

- `GET /api/orders/`
- `POST /api/orders/`
- `GET /api/orders/<id>/`

## Automated Tests

Run the test suite with:

```bash
python manage.py test
```

The test suite covers:

- user registration, login, and profile access
- product permissions and CRUD-related behavior
- order creation and ownership filtering

## Notes
- For production, set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, and a real `DJANGO_ALLOWED_HOSTS` value.
