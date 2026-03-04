"""
test_favorites.py — core business logic tests for the favorites feature.

WHAT WE'RE TESTING:
  1. A user can add a product to favorites
  2. Adding the same product twice is rejected (duplicate prevention)
  3. A user can remove a product from favorites
  4. Removing a product that isn't favorited returns 404
  5. A user only sees their own favorites (isolation)
  6. Favoriting a non-existent product returns 404
"""

import pytest
from shop.main import app
from shop import oauth2, models
# ADD this instead
from conftest import override_current_user, override_tenant_user


@pytest.fixture(autouse=True)
def inject_user_auth(test_user):
    """Auto-inject the test user for every test in this file."""
    app.dependency_overrides[oauth2.get_current_user] = override_current_user(test_user)
    yield
    app.dependency_overrides.pop(oauth2.get_current_user, None)


class TestAddFavorite:

    def test_add_favorite_returns_201(self, client, test_product):
        res = client.post("/favorite", json={"product_id": test_product.id})
        assert res.status_code == 201

    def test_add_favorite_response_contains_product_id(self, client, test_product):
        res = client.post("/favorite", json={"product_id": test_product.id})
        assert res.json()["product_id"] == test_product.id

    def test_add_nonexistent_product_returns_404(self, client):
        """
        Favoriting a product that doesn't exist must be caught immediately.
        The repository checks the product exists before inserting.
        """
        res = client.post("/favorite", json={"product_id": 99999})
        assert res.status_code == 404

    def test_duplicate_favorite_returns_400(self, client, test_product):
        """
        The favorites table has a logical uniqueness constraint enforced
        in the repository layer. A second add must be rejected, not silently
        inserted as a duplicate row.
        """
        client.post("/favorite", json={"product_id": test_product.id})
        res = client.post("/favorite", json={"product_id": test_product.id})
        assert res.status_code == 400

    def test_duplicate_favorite_error_message_is_clear(self, client, test_product):
        client.post("/favorite", json={"product_id": test_product.id})
        res = client.post("/favorite", json={"product_id": test_product.id})
        assert "already" in res.json()["detail"].lower()


class TestRemoveFavorite:

    def test_remove_existing_favorite_returns_200(self, client, test_product):
        client.post("/favorite", json={"product_id": test_product.id})
        res = client.delete(f"/favorite/{test_product.id}")
        assert res.status_code == 200

    def test_removed_favorite_no_longer_in_list(self, client, test_product):
        client.post("/favorite", json={"product_id": test_product.id})
        client.delete(f"/favorite/{test_product.id}")

        res = client.get("/favorite")
        assert res.status_code == 200
        assert res.json() == []

    def test_remove_non_favorited_product_returns_404(self, client, test_product):
        """
        Trying to remove a product that was never favorited must return 404,
        not silently succeed. The repository must check existence first.
        """
        res = client.delete(f"/favorite/{test_product.id}")
        assert res.status_code == 404


class TestGetFavorites:

    def test_empty_favorites_returns_empty_list(self, client):
        res = client.get("/favorite")
        assert res.status_code == 200
        assert res.json() == []

    def test_returns_all_user_favorites(self, client, db, test_product, test_tenant, test_category):
        """Add two products to favorites and confirm both appear."""
        product2 = models.Product(
            name="Second Product",
            description="",
            price=49.99,
            available_quantity=3,
            category_id=test_category.id,
            tenant_id=test_tenant.id,
        )
        db.add(product2)
        db.commit()
        db.refresh(product2)

        client.post("/favorite", json={"product_id": test_product.id})
        client.post("/favorite", json={"product_id": product2.id})

        res = client.get("/favorite")
        assert res.status_code == 200
        assert len(res.json()) == 2

    def test_user_favorites_are_isolated(self, client, db, test_product):
        """
        One user's favorites must not appear in another user's list.
        We create a second user, add a favorite as them directly via the DB,
        then assert the first user's GET /favorite is still empty.
        """
        other_user = models.User(
            name="Other User",
            email="other@example.com",
            password="x",
            keycloak_id="other-kc-id",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # Directly insert a favorite for other_user (not via API)
        fav = models.FavoriteProduct(
            user_id=other_user.id,
            product_id=test_product.id,
        )
        db.add(fav)
        db.commit()

        # test_user (injected by autouse fixture) should see nothing
        res = client.get("/favorite")
        assert res.status_code == 200
        assert res.json() == []