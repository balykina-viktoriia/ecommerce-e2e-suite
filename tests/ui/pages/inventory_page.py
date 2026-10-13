from playwright.sync_api import expect

from tests.ui.pages.base_page import BasePage


class InventoryPage(BasePage):
    URL = "/inventory.html"

    @property
    def add_to_cart_buttons(self):
        return self.page.locator("[data-test*='add-to-cart']")

    @property
    def remove_buttons(self):
        return self.page.locator("[data-test*='remove']")

    @property
    def cart_badge(self):
        return self.page.locator("[data-test='shopping-cart-badge']")

    @property
    def cart_link(self):
        return self.page.locator("[data-test='shopping-cart-link']")

    def add_to_cart(self, index: int):
        self.add_to_cart_buttons.nth(index).click()

    def remove_from_cart(self, index: int):
        self.remove_buttons.nth(index).click()

    def check_shopping_cart_badge(self, items_number: int):
        expect(self.cart_badge).to_have_text(str(items_number))

    def empty_shopping_cart_badge(self):
        expect(self.cart_badge).not_to_be_visible()

    def go_to_cart(self):
        self.cart_link.click()

    def expect_on_inventory_page(self):
        expect(self.page).to_have_url(self.URL)
