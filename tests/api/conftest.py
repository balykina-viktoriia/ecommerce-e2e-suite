import pytest

from tests.api.client import ApiClient, require_shop_api
from tests.api.data import ProductPayload
from tests.settings import ADMIN, VIEWER


@pytest.fixture(scope="session", autouse=True)
def api_is_up():
    require_shop_api()


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
