from pathlib import Path

import pytest

from tests.api.client import ApiClient
from tests.api.data import ProductPayload
from tests.settings import ADMIN, VIEWER

TESTS_DIR = Path(__file__).parent


def pytest_collection_modifyitems(items):
    """Mark every test with the name of its layer folder, so `pytest -m api` selects a layer."""
    for item in items:
        layer = Path(item.path).relative_to(TESTS_DIR).parts[0]
        item.add_marker(getattr(pytest.mark, layer))


# API clients shared by the API and database layers. They are created lazily, so UI-only
# runs never touch the shop app.


@pytest.fixture(scope="session")
def anonymous() -> ApiClient:
    return ApiClient()


@pytest.fixture(scope="session")
def admin() -> ApiClient:
    return ApiClient.logged_in(ADMIN)


@pytest.fixture(scope="session")
def viewer() -> ApiClient:
    return ApiClient.logged_in(VIEWER)


@pytest.fixture
def created_product(admin):
    """A fresh product, deleted after the test. Deleting a product that ended up in an order
    returns 409, which is fine: the row stays, and its SKU is unique anyway."""
    payload = ProductPayload.new()
    response = admin.post("/products", json=payload.to_json())
    assert response.status_code == 201, response.text
    product = response.json()
    yield product
    admin.delete(f"/products/{product['id']}")
