from decimal import Decimal

from playwright.sync_api import expect

from tests.ui.pages.base_page import BasePage, parse_money
from tests.ui.test_data import SortOption


class InventoryPage(BasePage):
    URL = "/inventory.html"

    @property
    def items(self):
        return self.page.locator("[data-test='inventory-item']")

    @property
    def cart_badge(self):
        return self.page.locator("[data-test='shopping-cart-badge']")

    @property
    def cart_link(self):
        return self.page.locator("[data-test='shopping-cart-link']")

    @property
    def sort_dropdown(self):
        return self.page.locator("[data-test='product-sort-container']")

    @property
    def item_names(self):
        return self.page.locator("[data-test='inventory-item-name']")

    @property
    def item_prices(self):
        return self.page.locator("[data-test='inventory-item-price']")

    @property
    def menu_button(self):
        return self.page.get_by_role("button", name="Open Menu")

    @property
    def logout_link(self):
        return self.page.locator("[data-test='logout-sidebar-link']")

    # Buttons are looked up inside the item card: "Add to cart" turns into "Remove" after a
    # click, so indexing a list of all add-to-cart buttons would point at a different item.
    def add_to_cart(self, index: int):
        self.items.nth(index).get_by_role("button", name="Add to cart").click()

    def remove_from_cart(self, index: int):
        self.items.nth(index).get_by_role("button", name="Remove").click()

    def check_shopping_cart_badge(self, items_number: int):
        expect(self.cart_badge).to_have_text(str(items_number))

    def empty_shopping_cart_badge(self):
        expect(self.cart_badge).not_to_be_visible()

    def go_to_cart(self):
        self.cart_link.click()

    def sort_by(self, option: SortOption):
        self.sort_dropdown.select_option(option)

    def expect_items_loaded(self):
        # The URL changes before the list renders, so wait for it before reading text.
        expect(self.item_names.first).to_be_visible()

    def names(self) -> list[str]:
        self.expect_items_loaded()
        return self.item_names.all_text_contents()

    def prices(self) -> list[Decimal]:
        self.expect_items_loaded()
        return [parse_money(text) for text in self.item_prices.all_text_contents()]

    def logout(self):
        self.menu_button.click()
        self.logout_link.click()

    def expect_on_inventory_page(self):
        expect(self.page).to_have_url(self.URL)
