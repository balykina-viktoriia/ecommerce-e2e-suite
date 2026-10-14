import pytest

from tests.ui.test_data import InventoryItem, Users


@pytest.mark.parametrize(
    "user",
    [
        pytest.param(Users.STANDARD, id="standard_user"),
        pytest.param(
            Users.PROBLEM,
            id="problem_user",
            marks=pytest.mark.xfail(
                reason="Known saucedemo defect: problem_user cannot add the Fleece Jacket",
                strict=True,
            ),
        ),
    ],
)
def test_add_multiple_items(login_as, user):
    inventory_page = login_as(user)

    inventory_page.add_to_cart(InventoryItem.BIKE_LIGHT)
    inventory_page.add_to_cart(InventoryItem.FLEECE_JACKET)
    inventory_page.check_shopping_cart_badge(2)


def test_remove_multiple_items(logged_in_page):
    inventory_page = logged_in_page

    inventory_page.add_to_cart(InventoryItem.BIKE_LIGHT)
    inventory_page.add_to_cart(InventoryItem.FLEECE_JACKET)
    inventory_page.check_shopping_cart_badge(2)

    inventory_page.remove_from_cart(InventoryItem.BIKE_LIGHT)
    inventory_page.remove_from_cart(InventoryItem.FLEECE_JACKET)
    inventory_page.empty_shopping_cart_badge()
