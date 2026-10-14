import json

import pytest

from tests.auth.conftest import Role
from tests.settings import ADMIN, API_BASE_URL, VIEWER


@pytest.mark.parametrize("role", [Role.ADMIN, Role.VIEWER])
def test_storage_state_holds_secure_session_cookie(storage_states, role):
    cookies = json.loads(storage_states[role].read_text())["cookies"]

    assert [c["name"] for c in cookies] == ["access_token"]
    cookie = cookies[0]
    assert cookie["httpOnly"] is True
    assert cookie["sameSite"] == "Lax"
    assert cookie["expires"] > 0, "session cookie should have an expiry"


@pytest.mark.parametrize(
    ("role", "username"),
    [(Role.ADMIN, ADMIN.username), (Role.VIEWER, VIEWER.username)],
)
def test_context_from_storage_state_is_signed_in(context_for, role, username):
    response = context_for(role).get("/auth/me")

    assert response.status == 200
    assert response.json()["username"] == username
    assert response.json()["role"] == role


def test_anonymous_context_is_not_signed_in(context_for):
    response = context_for(Role.ANONYMOUS).get("/auth/me")

    assert response.status == 401


def test_logout_clears_the_session(playwright):
    context = playwright.request.new_context(base_url=API_BASE_URL)
    context.post("/auth/login", data={"username": VIEWER.username, "password": VIEWER.password})
    assert context.get("/auth/me").status == 200

    assert context.post("/auth/logout").status == 204

    assert context.get("/auth/me").status == 401
    assert context.storage_state()["cookies"] == []
    context.dispose()
