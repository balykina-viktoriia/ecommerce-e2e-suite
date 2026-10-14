from decimal import Decimal

from playwright.sync_api import expect

from tests.ui.pages.base_page import BasePage, parse_money
from tests.ui.test_data import Customer, SuccessMessage


class CheckoutPage(BasePage):
    URL = "/checkout-step-one.html"
    CHECKOUT_URL = "/checkout-step-two.html"
    COMPLETE_URL = "/checkout-complete.html"

    @property
    def first_name_input(self):
        return self.page.get_by_placeholder("First Name")

    @property
    def last_name_input(self):
        return self.page.get_by_placeholder("Last Name")

    @property
    def zip_code_input(self):
        return self.page.get_by_placeholder("Zip/Postal Code")

    @property
    def continue_button(self):
        return self.page.get_by_role("button", name="Continue")

    @property
    def finish_button(self):
        return self.page.get_by_role("button", name="Finish")

    @property
    def complete_page(self):
        return self.page.locator("[data-test='complete-header']")

    @property
    def summary_item_prices(self):
        return self.page.locator("[data-test='cart-list'] [data-test='inventory-item-price']")

    @property
    def subtotal_label(self):
        return self.page.locator("[data-test='subtotal-label']")

    @property
    def tax_label(self):
        return self.page.locator("[data-test='tax-label']")

    @property
    def total_label(self):
        return self.page.locator("[data-test='total-label']")

    @property
    def error_message(self):
        return self.page.locator("[data-test='error']")

    def expect_on_checkout_page(self):
        expect(self.page).to_have_url(self.URL)

    def get_your_information(self, customer: Customer):
        self.first_name_input.fill(customer.first_name)
        self.last_name_input.fill(customer.last_name)
        self.zip_code_input.fill(customer.zip_code)
        self.continue_button.click()

    def expect_on_step_two_page(self):
        expect(self.page).to_have_url(self.CHECKOUT_URL)

    def item_prices(self) -> list[Decimal]:
        return [parse_money(text) for text in self.summary_item_prices.all_text_contents()]

    def subtotal(self) -> Decimal:
        return parse_money(self.subtotal_label.inner_text())

    def tax(self) -> Decimal:
        return parse_money(self.tax_label.inner_text())

    def total(self) -> Decimal:
        return parse_money(self.total_label.inner_text())

    def finish_checkout(self):
        self.finish_button.click()

    def checkout_success(self):
        expect(self.page).to_have_url(self.COMPLETE_URL)
        expect(self.complete_page).to_have_text(SuccessMessage.CHECKOUT_COMPLETE)
