from decimal import ROUND_HALF_UP, Decimal

import pytest
from playwright.sync_api import Page, expect

from tests.ui.pages.login_page import LoginPage
from tests.ui.test_data import (
    TAX_RATE,
    Customer,
    Customers,
    ErrorMessage,
    InventoryItem,
    Users,
)


def test_checkout_flow(logged_in_page, cart_page, checkout_page):
    inventory_page = logged_in_page

    inventory_page.add_to_cart(InventoryItem.BACKPACK)
    inventory_page.check_shopping_cart_badge(1)
    inventory_page.go_to_cart()

    cart_page.expect_on_cart_page()
    cart_page.check_cart_item()
    cart_page.go_to_checkout()

    checkout_page.expect_on_checkout_page()
    checkout_page.get_your_information(Customers.VALID)
    checkout_page.expect_on_step_two_page()
    checkout_page.finish_checkout()
    checkout_page.checkout_success()


def test_problem_user_flow(login_as, cart_page, checkout_page):
    inventory_page = login_as(Users.PROBLEM)

    inventory_page.add_to_cart(InventoryItem.BACKPACK)
    inventory_page.check_shopping_cart_badge(1)
    inventory_page.go_to_cart()

    cart_page.expect_on_cart_page()
    cart_page.check_cart_item()
    cart_page.go_to_checkout()

    checkout_page.expect_on_checkout_page()
    checkout_page.get_your_information(Customers.VALID)
    expect(checkout_page.error_message).to_have_text(ErrorMessage.LAST_NAME_REQUIRED)


def test_locked_out_user_flow(page: Page):
    login_page = LoginPage(page)
    login_page.navigate()
    login_page.login(Users.LOCKED_OUT.username, Users.LOCKED_OUT.password)
    expect(login_page.error_message).to_have_text(ErrorMessage.LOCKED_OUT)


@pytest.mark.parametrize(
    ("customer", "error"),
    [
        pytest.param(Customer("", "Doe", "12345"), ErrorMessage.FIRST_NAME_REQUIRED, id="no_first"),
        pytest.param(Customer("John", "", "12345"), ErrorMessage.LAST_NAME_REQUIRED, id="no_last"),
        pytest.param(Customer("John", "Doe", ""), ErrorMessage.POSTAL_CODE_REQUIRED, id="no_zip"),
    ],
)
def test_checkout_requires_customer_info(logged_in_page, cart_page, checkout_page, customer, error):
    logged_in_page.add_to_cart(InventoryItem.BACKPACK)
    logged_in_page.go_to_cart()
    cart_page.go_to_checkout()

    checkout_page.get_your_information(customer)
    expect(checkout_page.error_message).to_have_text(error)
    checkout_page.expect_on_checkout_page()


def test_checkout_totals_add_up(logged_in_page, cart_page, checkout_page):
    for item in (InventoryItem.BACKPACK, InventoryItem.BIKE_LIGHT, InventoryItem.ONESIE):
        logged_in_page.add_to_cart(item)
    logged_in_page.go_to_cart()
    cart_page.go_to_checkout()
    checkout_page.get_your_information(Customers.VALID)
    checkout_page.expect_on_step_two_page()

    subtotal = checkout_page.subtotal()
    tax = checkout_page.tax()
    assert subtotal == sum(checkout_page.item_prices())
    assert tax == (subtotal * TAX_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    assert checkout_page.total() == subtotal + tax
