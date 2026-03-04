"""
conftest.py — shared fixtures for all backend tests.

HOW IT WORKS:
- Uses an in-memory SQLite DB so tests never touch your real shop.db
- Mocks Keycloak so tests run without a live Keycloak server
- Each test function gets a fresh DB (scope="function"), preventing bleed-over
- Dependency overrides swap out get_db with the test session
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from shop.main import app
from shop.database import Base, get_db
from shop import models

# ── In-memory test database ──────────────────────────────────────────────────
TEST_DB_URL = "sqlite:///./test_shop.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ── Database fixture (fresh schema per test) ─────────────────────────────────
@pytest.fixture(scope="function")
def db():
    """
    Provides a clean DB session for each test.
    Tables are created before and dropped after every test function.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ── TestClient fixture (wires test DB into FastAPI) ──────────────────────────
@pytest.fixture(scope="function")
def client(db):
    """
    Returns a TestClient whose requests use the test DB session.
    Dependency overrides are cleared after each test.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Keycloak mock (regular user) ─────────────────────────────────────────────
@pytest.fixture
def mock_keycloak_user():
    """
    Patches keycloak_openid so verify_keycloak_token returns a regular user token.
    Use this fixture in any test that calls an authenticated endpoint.
    """
    token_payload = {
        "sub": "keycloak-uuid-user",
        "email": "user@example.com",
        "name": "Test User",
        "realm_access": {"roles": ["user"]},
    }
    with patch("shop.keycloak_config.keycloak_openid") as mock_oid:
        mock_oid.public_key.return_value = "mock_public_key"
        mock_oid.decode_token.return_value = token_payload
        yield mock_oid


# ── Keycloak mock (admin user) ───────────────────────────────────────────────
@pytest.fixture
def mock_keycloak_admin():
    """
    Patches keycloak_openid to return an admin-role token.
    Also patches keycloak_admin for admin-specific checks.
    """
    token_payload = {
        "sub": "keycloak-uuid-admin",
        "email": "admin@example.com",
        "name": "Admin User",
        "realm_access": {"roles": ["admin", "user"]},
    }
    with patch("shop.keycloak_config.keycloak_openid") as mock_oid, \
         patch("shop.keycloak_config.keycloak_admin") as mock_kadmin:
        mock_oid.public_key.return_value = "mock_public_key"
        mock_oid.decode_token.return_value = token_payload
        mock_kadmin.get_realm_roles_of_user.return_value = [
            {"name": "admin"}, {"name": "user"}
        ]
        yield mock_oid, mock_kadmin


# ── Reusable domain object fixtures ─────────────────────────────────────────
@pytest.fixture
def test_user(db):
    """A plain user already committed to the test DB."""
    user = models.User(
        name="Test User",
        email="user@example.com",
        password="hashed_password",
        keycloak_id="keycloak-uuid-user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_tenant(db, test_user):
    """A tenant owned by test_user."""
    tenant = models.Tenant(
        brand_name="Test Brand",
        domain="testbrand",
        user_id=test_user.id,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def test_category(db):
    """A product category."""
    cat = models.Category(name="Electronics")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@pytest.fixture
def test_product(db, test_tenant, test_category):
    """An in-stock product with 10 units."""
    product = models.Product(
        name="Test Phone",
        description="A reliable test product",
        price=999.99,
        available_quantity=10,
        category_id=test_category.id,
        tenant_id=test_tenant.id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# ── Auth dependency helpers ──────────────────────────────────────────────────
def override_current_user(user):
    """
    Returns a dependency override function that injects `user`
    as the authenticated user — bypassing all Keycloak token logic.

    Usage in a test:
        from shop import oauth2
        app.dependency_overrides[oauth2.get_current_user] = override_current_user(test_user)
    """
    def _override():
        return user
    return _override


def override_tenant_user(user, tenant):
    """
    Returns a dependency override for get_tenant_user,
    which normally checks that the user owns a tenant.
    """
    def _override():
        return {"user": user, "tenant": tenant}
    return _override