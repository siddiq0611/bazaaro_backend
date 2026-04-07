# 🛒 Bazaaro — Backend API

A multi-tenant e-commerce REST API built with **FastAPI**, **SQLAlchemy**, and **Keycloak** for authentication and role management.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM | [SQLAlchemy](https://www.sqlalchemy.org/) |
| Database | SQLite (dev) |
| Auth | [Keycloak](https://www.keycloak.org/) via `python-keycloak` |
| Validation | Pydantic v2 |
| File Serving | FastAPI `StaticFiles` |
| Testing | Pytest |
| Server | Uvicorn |

---

## 📁 Project Structure

```
.
├── conftest.py                  # Root-level pytest config
├── requirements.txt
├── shop/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, middleware, router registration
│   ├── database.py              # SQLAlchemy engine & session
│   ├── models.py                # ORM models (User, Tenant, Product, Order, etc.)
│   ├── schemas.py               # Pydantic request/response schemas
│   ├── oauth2.py                # Keycloak token verification & role guards
│   ├── keycloak_config.py       # Keycloak admin & OIDC client setup
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── cart.py
│   │   ├── favorite.py
│   │   ├── order.py
│   │   ├── product.py
│   │   ├── tenant.py
│   │   └── user.py
│   └── routers/
│       ├── __init__.py
│       ├── authentication.py    # /signup, /login, /logout
│       ├── cart.py              # /cart
│       ├── favorite.py          # /favorite
│       ├── order.py             # /order
│       ├── product.py           # /product
│       ├── tenant.py            # /tenant
│       └── user.py              # /user
└── tests/
    ├── conftest.py
    ├── test_favorites.py
    ├── test_orders.py
    └── test_products.py
```

---

## ⚙️ Prerequisites

- Python 3.10+
- A running [Keycloak](https://www.keycloak.org/downloads) instance (v21+ recommended)
- Keycloak realm configured with:
  - A client (confidential, with client secret)
  - Realm roles: `customer`, `tenant`, `admin`
  - An admin user in the `master` realm

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/bazaaro-backend.git
cd bazaaro-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root directory:

```env
# Keycloak
KEYCLOAK_SERVER_URL=http://localhost:8080/
KEYCLOAK_REALM=bazaaro
KEYCLOAK_CLIENT_ID=bazaaro-client
KEYCLOAK_CLIENT_SECRET=your-client-secret-here

# Keycloak admin credentials (master realm)
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=admin
```

### 5. Run the development server

```bash
uvicorn shop.main:app --reload
```

The API will be available at **http://localhost:8000**

Interactive docs: **http://localhost:8000/docs**

---

## 📦 Static Files

Product images are stored in `static/images/` and served at `/static/images/<filename>`. This directory is created automatically on startup.

---

## 🔐 Authentication & Roles

All protected routes require a `Bearer` token issued by Keycloak.

| Role | Access |
|---|---|
| `customer` | Browse products, manage cart, place orders, add favourites |
| `tenant` | All customer permissions + manage own products |
| `admin` | All permissions + manage users, tenants, and tenant requests |

### Auth Flow

1. **Sign up** — `POST /signup` creates a Keycloak user, assigns the `customer` role, and returns a JWT.
2. **Log in** — `POST /login` (form data: `username`, `password`) authenticates via Keycloak and returns a JWT.
3. All subsequent requests pass the JWT as `Authorization: Bearer <token>`.

---

## 🗂️ API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/signup` | Register a new user |
| POST | `/login` | Login (form data) |
| POST | `/logout` | Logout (client-side token removal) |

### Products
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/product` | Public | List all products (paginated, filterable) |
| GET | `/product/{id}` | Public | Get a single product |
| GET | `/product/category` | Public | List all categories |
| GET | `/product/store/{domain}` | Public | Products by store domain |
| GET | `/product/my-products` | Tenant | List own products |
| POST | `/product` | Tenant | Create a product |
| PUT | `/product/{id}` | Tenant | Update a product |
| DELETE | `/product/{id}` | Tenant | Soft-delete a product |
| POST | `/product/category` | Tenant | Create a category |

### Orders
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/order` | Customer | Place an order |
| GET | `/order` | Customer | Get own order history |

### Cart
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/cart` | Customer | Get current cart |
| PUT | `/cart/item` | Customer | Add or update item quantity |
| DELETE | `/cart/item/{product_id}` | Customer | Remove a specific item |
| DELETE | `/cart` | Customer | Clear the entire cart |

### Favourites
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/favorite` | Customer | Get favourited products |
| POST | `/favorite` | Customer | Add a product to favourites |
| DELETE | `/favorite/{product_id}` | Customer | Remove from favourites |

### Tenants
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/tenant/request` | Customer | Apply to become a tenant |
| GET | `/tenant/request/me` | Customer | View own application status |
| GET | `/tenant/requests` | Admin | View all pending requests |
| PUT | `/tenant/request/{id}/accept` | Admin | Accept a tenant request |
| PUT | `/tenant/request/{id}/decline` | Admin | Decline a tenant request |
| POST | `/tenant` | Admin | Create a tenant directly |
| GET | `/tenant` | Admin | List all tenants |
| GET | `/tenant/{id}` | Customer | Get a specific tenant |
| DELETE | `/tenant/{id}` | Admin | Soft-delete a tenant |

### Users
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/user/me` | Customer | Get own profile |
| GET | `/user/{id}` | Admin | Get user by ID |
| GET | `/user/` | Admin | List all users |

---

## 🧪 Running Tests

```bash
pytest tests/
```

---

## 🗃️ Database

The project uses **SQLite** by default (`shop.db` in the root). Tables are created automatically on startup via:

```python
models.Base.metadata.create_all(engine)
```

To switch to PostgreSQL, update `SQLALCHAMY_DATABASE_URL` in `shop/database.py`:

```python
SQLALCHAMY_DATABASE_URL = "postgresql://user:password@localhost/bazaaro"
```

And remove the `connect_args` from the engine creation.

---

## 🌐 CORS

The API allows requests from `http://localhost:5173` by default (the Vite dev server). Update `allow_origins` in `shop/main.py` for production deployments.

---

## 📋 Requirements

Key dependencies from `requirements.txt`:

```
fastapi
uvicorn[standard]
sqlalchemy
python-multipart
python-dotenv
python-keycloak
pydantic[email]
pytest
httpx
```