from playwright.sync_api import expect

from tests.ui.pages.base_page import BasePage


class CartPage(BasePage):
    URL = "/cart.html"

    @property
    def cart_item(self):
        return self.page.locator("[data-test='cart-list'] [data-test='inventory-item-name']")

    @property
    def checkout_button(self):
        return self.page.get_by_role("button", name="Checkout")

    def expect_on_cart_page(self):
        expect(self.page).to_have_url(self.URL)

    def check_cart_item(self):
        expect(self.cart_item).to_be_visible()

    def go_to_checkout(self):
        self.checkout_button.click()
