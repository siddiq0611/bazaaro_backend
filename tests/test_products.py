"""
test_products.py — core business logic tests for product management.

WHAT WE'RE TESTING:
  1. Product listing filters (soft-delete, category, search)
  2. Individual product retrieval including 404 cases
  3. Tenant-scoped create / update / delete
  4. Soft-delete semantics (row stays in DB, is_deleted=True)
  5. Category creation and duplicate prevention
"""

import pytest
from shop.main import app
from shop import oauth2, models
from conftest import override_current_user, override_tenant_user


# ── Helper ────────────────────────────────────────────────────────────────────
def get_items(res):
    """
    GET /product now returns a paginated envelope:
        { "items": [...], "total": N, "page": 1, "page_size": 12, "total_pages": N }

    This helper extracts the items list so every test stays readable and any
    future shape changes only need to be fixed here.
    """
    body = res.json()
    # Support both old flat-list responses and the new paginated envelope
    if isinstance(body, list):
        return body
    return body["items"]


# ── GET /product ─────────────────────────────────────────────────────────────
class TestGetAllProducts:

    def test_returns_empty_list_when_no_products(self, client):
        res = client.get("/product")
        assert res.status_code == 200
        # FIX: response is now { items: [], total: 0, ... } — check items is empty
        assert get_items(res) == []

    def test_returns_only_active_products(self, client, db, test_product):
        """
        Soft-deleted products must never appear in the public listing.
        We add one active and one deleted product, then assert only one comes back.
        """
        deleted = models.Product(
            name="Ghost Product",
            description="",
            price=1.0,
            available_quantity=0,
            category_id=test_product.category_id,
            tenant_id=test_product.tenant_id,
            is_deleted=True,
        )
        db.add(deleted)
        db.commit()

        res = client.get("/product")
        # FIX: unwrap paginated envelope before iterating
        names = [p["name"] for p in get_items(res)]

        assert "Test Phone" in names
        assert "Ghost Product" not in names

    def test_filter_by_category_returns_only_matching(
        self, client, db, test_product, test_tenant
    ):
        """Category filter must exclude products from other categories."""
        other_cat = models.Category(name="Clothing")
        db.add(other_cat)
        db.commit()
        db.refresh(other_cat)

        other_product = models.Product(
            name="T-Shirt",
            description="",
            price=29.99,
            available_quantity=20,
            category_id=other_cat.id,
            tenant_id=test_tenant.id,
        )
        db.add(other_product)
        db.commit()

        res = client.get(f"/product?category_id={test_product.category_id}")
        # FIX: unwrap paginated envelope before iterating
        names = [p["name"] for p in get_items(res)]

        assert "Test Phone" in names
        assert "T-Shirt" not in names

    def test_search_by_name_returns_match(self, client, test_product):
        res = client.get("/product?search=Phone")
        assert res.status_code == 200
        # FIX: check items length and items[0], not the envelope itself
        items = get_items(res)
        assert len(items) == 1
        assert items[0]["name"] == "Test Phone"

    def test_search_by_description_returns_match(self, client, test_product):
        res = client.get("/product?search=reliable")  # matches description
        assert res.status_code == 200
        assert len(get_items(res)) >= 1

    def test_search_with_no_match_returns_empty(self, client, test_product):
        res = client.get("/product?search=zzznomatch")
        assert res.status_code == 200
        # FIX: check items list is empty, not the whole envelope
        assert get_items(res) == []

    # ── Extra pagination-specific tests ──────────────────────────────────────

    def test_response_has_pagination_envelope(self, client, test_product):
        """Sanity-check that the envelope fields are all present."""
        res = client.get("/product")
        body = res.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert "page_size" in body
        assert "total_pages" in body

    def test_page_size_limits_returned_items(self, client, db, test_product, test_tenant, test_category):
        """Requesting page_size=1 should return exactly 1 item even when more exist."""
        # Create a second product so there are 2 total
        extra = models.Product(
            name="Extra Product",
            description="",
            price=9.99,
            available_quantity=5,
            category_id=test_category.id,
            tenant_id=test_tenant.id,
        )
        db.add(extra)
        db.commit()

        res = client.get("/product?page=1&page_size=1")
        assert res.status_code == 200
        body = res.json()
        assert len(body["items"]) == 1
        assert body["total"] == 2
        assert body["total_pages"] == 2

    def test_page_two_returns_second_item(self, client, db, test_product, test_tenant, test_category):
        """Page 2 with page_size=1 should return the second product."""
        extra = models.Product(
            name="Extra Product",
            description="",
            price=9.99,
            available_quantity=5,
            category_id=test_category.id,
            tenant_id=test_tenant.id,
        )
        db.add(extra)
        db.commit()

        res = client.get("/product?page=2&page_size=1")
        assert res.status_code == 200
        body = res.json()
        assert len(body["items"]) == 1
        # We got a product, and it's the second one
        assert body["page"] == 2

    def test_total_reflects_filters(self, client, db, test_product, test_tenant, test_category):
        """'total' in the envelope must match only filtered results, not all products."""
        other_cat = models.Category(name="Clothing2")
        db.add(other_cat)
        db.commit()
        db.refresh(other_cat)

        other = models.Product(
            name="Jeans",
            description="",
            price=49.99,
            available_quantity=10,
            category_id=other_cat.id,
            tenant_id=test_tenant.id,
        )
        db.add(other)
        db.commit()

        res = client.get(f"/product?category_id={test_product.category_id}")
        body = res.json()
        assert body["total"] == 1   # only the Electronics product


# ── GET /product/{id} ────────────────────────────────────────────────────────
class TestGetProductById:

    def test_returns_correct_product(self, client, test_product):
        res = client.get(f"/product/{test_product.id}")
        assert res.status_code == 200
        assert res.json()["id"] == test_product.id
        assert res.json()["name"] == "Test Phone"

    def test_nonexistent_id_returns_404(self, client):
        res = client.get("/product/99999")
        assert res.status_code == 404

    def test_soft_deleted_product_returns_404(self, client, db, test_product):
        """
        Even if you know the ID, a deleted product must not be accessible.
        This protects against enumeration of deleted items.
        """
        test_product.is_deleted = True
        db.commit()

        res = client.get(f"/product/{test_product.id}")
        assert res.status_code == 404


# ── POST /product ─────────────────────────────────────────────────────────────
class TestCreateProduct:

    def test_tenant_can_create_product(self, client, test_user, test_tenant, test_category):
        app.dependency_overrides[oauth2.get_tenant_user] = override_tenant_user(
            test_user, test_tenant
        )

        res = client.post("/product", data={
            "name": "New Gadget",
            "description": "Fresh off the line",
            "price": "299.99",
            "available_quantity": "50",
            "category_id": str(test_category.id),
        })

        assert res.status_code == 201
        body = res.json()
        assert body["name"] == "New Gadget"
        assert body["price"] == 299.99
        assert body["available_quantity"] == 50

        app.dependency_overrides.pop(oauth2.get_tenant_user, None)

    def test_created_product_belongs_to_tenant(
        self, client, test_user, test_tenant, test_category
    ):
        app.dependency_overrides[oauth2.get_tenant_user] = override_tenant_user(
            test_user, test_tenant
        )

        res = client.post("/product", data={
            "name": "Brand Item",
            "description": "",
            "price": "50.0",
            "available_quantity": "10",
            "category_id": str(test_category.id),
        })

        assert res.json()["tenant"]["id"] == test_tenant.id
        app.dependency_overrides.pop(oauth2.get_tenant_user, None)

    def test_create_product_invalid_category_returns_404(
        self, client, test_user, test_tenant
    ):
        app.dependency_overrides[oauth2.get_tenant_user] = override_tenant_user(
            test_user, test_tenant
        )

        res = client.post("/product", data={
            "name": "Orphan",
            "description": "",
            "price": "10.0",
            "available_quantity": "1",
            "category_id": "99999",  # doesn't exist
        })

        assert res.status_code == 404
        app.dependency_overrides.pop(oauth2.get_tenant_user, None)

    def test_unauthenticated_create_is_rejected(self, client, test_category):
        """No auth override = the real dependency runs = 401/403."""
        res = client.post("/product", data={
            "name": "Sneaky",
            "description": "",
            "price": "1.0",
            "available_quantity": "1",
            "category_id": str(test_category.id),
        })
        assert res.status_code in (401, 403)


# ── PUT /product/{id} ────────────────────────────────────────────────────────
class TestUpdateProduct:

    def test_tenant_can_update_own_product(
        self, client, db, test_user, test_tenant, test_product
    ):
        app.dependency_overrides[oauth2.get_tenant_user] = override_tenant_user(
            test_user, test_tenant
        )

        res = client.put(f"/product/{test_product.id}", data={
            "name": "Updated Phone",
            "price": "1199.99",
            "description": test_product.description,
            "available_quantity": str(test_product.available_quantity),
            "category_id": str(test_product.category_id),
        })

        assert res.status_code == 202
        assert res.json()["name"] == "Updated Phone"
        assert res.json()["price"] == 1199.99

        app.dependency_overrides.pop(oauth2.get_tenant_user, None)

    def test_tenant_cannot_update_another_tenants_product(
        self, client, db, test_category, test_user, test_tenant, test_product
    ):
        """
        We create a second tenant + product, then try to update it
        using test_tenant's credentials. Must return 404 (not found for that tenant).
        """
        other_user = models.User(
            name="Other",
            email="other@example.com",
            password="x",
            keycloak_id="other-kc-id",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        other_tenant = models.Tenant(
            brand_name="Other Brand",
            domain="otherbrand",
            user_id=other_user.id,
        )
        db.add(other_tenant)
        db.commit()
        db.refresh(other_tenant)

        other_product = models.Product(
            name="Not Yours",
            description="",
            price=100.0,
            available_quantity=5,
            category_id=test_category.id,
            tenant_id=other_tenant.id,
        )
        db.add(other_product)
        db.commit()
        db.refresh(other_product)

        # test_tenant tries to update other_tenant's product
        app.dependency_overrides[oauth2.get_tenant_user] = override_tenant_user(
            test_user, test_tenant
        )

        res = client.put(f"/product/{other_product.id}", data={"name": "Hijacked"})
        assert res.status_code == 404  # not found for this tenant

        app.dependency_overrides.pop(oauth2.get_tenant_user, None)


# ── DELETE /product/{id} — soft delete ───────────────────────────────────────
class TestDeleteProduct:

    def test_delete_sets_is_deleted_flag(self, client, db, test_user, test_tenant, test_product):
        """
        Soft delete: the DB row must remain, but is_deleted becomes True.
        This is critical — real deletion would break order history.
        """
        app.dependency_overrides[oauth2.get_tenant_user] = override_tenant_user(
            test_user, test_tenant
        )

        res = client.delete(f"/product/{test_product.id}")
        assert res.status_code == 204

        db.refresh(test_product)
        assert test_product.is_deleted is True      # row still exists
        assert test_product.available_quantity == 0  # zeroed out

        app.dependency_overrides.pop(oauth2.get_tenant_user, None)

    def test_deleted_product_disappears_from_listing(
        self, client, db, test_user, test_tenant, test_product
    ):
        app.dependency_overrides[oauth2.get_tenant_user] = override_tenant_user(
            test_user, test_tenant
        )
        client.delete(f"/product/{test_product.id}")
        app.dependency_overrides.pop(oauth2.get_tenant_user, None)

        res = client.get("/product")
        # FIX: unwrap paginated envelope before iterating
        names = [p["name"] for p in get_items(res)]
        assert "Test Phone" not in names


# ── POST /product/category ────────────────────────────────────────────────────
class TestCreateCategory:

    def test_create_category_succeeds(self, client, test_user, test_tenant):
        app.dependency_overrides[oauth2.get_tenant_user] = override_tenant_user(
            test_user, test_tenant
        )

        res = client.post("/product/category", json={"name": "Furniture"})
        assert res.status_code == 201
        assert res.json()["name"] == "Furniture"

        app.dependency_overrides.pop(oauth2.get_tenant_user, None)

    def test_duplicate_category_returns_400(self, client, test_user, test_tenant, test_category):
        """
        Category names must be unique. A second creation with the same name
        must be rejected — the repository catches IntegrityError and raises 400.
        """
        app.dependency_overrides[oauth2.get_tenant_user] = override_tenant_user(
            test_user, test_tenant
        )

        # test_category fixture already added "Electronics"
        res = client.post("/product/category", json={"name": "Electronics"})
        assert res.status_code == 400

        app.dependency_overrides.pop(oauth2.get_tenant_user, None)