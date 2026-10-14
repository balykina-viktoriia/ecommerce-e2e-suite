import pytest
from playwright.sync_api import expect

from tests.ui.test_data import SortOption


@pytest.mark.parametrize(
    ("option", "reverse"),
    [
        pytest.param(SortOption.NAME_A_TO_Z, False, id="name_a_to_z"),
        pytest.param(SortOption.NAME_Z_TO_A, True, id="name_z_to_a"),
    ],
)
def test_sort_by_name(logged_in_page, option, reverse):
    expected = sorted(logged_in_page.names(), reverse=reverse)
    logged_in_page.sort_by(option)
    expect(logged_in_page.item_names).to_have_text(expected)


@pytest.mark.parametrize(
    ("option", "reverse"),
    [
        pytest.param(SortOption.PRICE_LOW_TO_HIGH, False, id="price_low_to_high"),
        pytest.param(SortOption.PRICE_HIGH_TO_LOW, True, id="price_high_to_low"),
    ],
)
def test_sort_by_price(logged_in_page, option, reverse):
    expected = [f"${price}" for price in sorted(logged_in_page.prices(), reverse=reverse)]
    logged_in_page.sort_by(option)
    expect(logged_in_page.item_prices).to_have_text(expected)
