import pytest

from tests.ui.pages.login_page import LoginPage
from tests.ui.test_data import DEFAULT_PASSWORD, ErrorMessage, Users


@pytest.mark.parametrize(
    ("username", "password", "error"),
    [
        pytest.param("", "", ErrorMessage.USERNAME_REQUIRED, id="empty_form"),
        pytest.param("", DEFAULT_PASSWORD, ErrorMessage.USERNAME_REQUIRED, id="no_username"),
        pytest.param(Users.STANDARD.username, "", ErrorMessage.PASSWORD_REQUIRED, id="no_password"),
        pytest.param(
            Users.STANDARD.username, "wrong", ErrorMessage.WRONG_CREDENTIALS, id="wrong_password"
        ),
        pytest.param(
            "no_such_user", DEFAULT_PASSWORD, ErrorMessage.WRONG_CREDENTIALS, id="unknown_user"
        ),
    ],
)
def test_login_rejected(page, username, password, error):
    login_page = LoginPage(page)
    login_page.navigate()
    login_page.login(username, password)
    login_page.expect_error(error)
    login_page.expect_on_login_page()


def test_logout_returns_to_login_page(page, logged_in_page):
    logged_in_page.logout()
    LoginPage(page).expect_on_login_page()


def test_inventory_requires_login(page, logged_in_page):
    logged_in_page.logout()
    page.goto(logged_in_page.URL)
    LoginPage(page).expect_on_login_page()
