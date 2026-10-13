import pytest
from playwright.sync_api import Page

from tests.ui.pages.cart_page import CartPage
from tests.ui.pages.checkout_page import CheckoutPage
from tests.ui.pages.inventory_page import InventoryPage
from tests.ui.pages.login_page import LoginPage
from tests.ui.test_data import User, Users

DEFAULT_TIMEOUT_MS = 10_000


def pytest_collection_modifyitems(items):
    for item in items:
        if "tests/ui/" in item.nodeid:
            item.add_marker(pytest.mark.ui)


@pytest.fixture(autouse=True)
def set_timeout(page: Page):
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)


@pytest.fixture
def login_as(page: Page):
    def _login(user: User) -> InventoryPage:
        login = LoginPage(page)
        login.navigate()
        login.login(user.username, user.password)
        inventory_page = InventoryPage(page)
        inventory_page.expect_on_inventory_page()
        return inventory_page

    return _login


@pytest.fixture
def logged_in_page(login_as) -> InventoryPage:
    return login_as(Users.STANDARD)


@pytest.fixture
def cart_page(page: Page) -> CartPage:
    return CartPage(page)


@pytest.fixture
def checkout_page(page: Page) -> CheckoutPage:
    return CheckoutPage(page)
