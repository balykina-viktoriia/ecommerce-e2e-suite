import pytest

from tests.api.client import require_shop_api


@pytest.fixture(scope="session", autouse=True)
def api_is_up():
    require_shop_api()
