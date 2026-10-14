from playwright.sync_api import expect

from tests.ui.pages.base_page import BasePage


class LoginPage(BasePage):
    URL = "/"

    @property
    def username_input(self):
        return self.page.get_by_placeholder("Username")

    @property
    def password_input(self):
        return self.page.get_by_placeholder("Password")

    @property
    def login_button(self):
        return self.page.get_by_role("button", name="Login")

    @property
    def error_message(self):
        return self.page.locator("[data-test='error']")

    def navigate(self):
        # Don't wait for the load event: it also waits for third-party fonts, which
        # sometimes stall for seconds. Assertions wait for the elements they need anyway.
        self.page.goto(self.URL, wait_until="domcontentloaded")

    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def expect_on_login_page(self):
        expect(self.page).to_have_url(self.URL)
        expect(self.login_button).to_be_visible()

    def expect_error(self, message: str):
        expect(self.error_message).to_have_text(message)
