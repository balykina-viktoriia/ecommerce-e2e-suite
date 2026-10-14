"""Login and token handling: wrong credentials, and tokens that must not be accepted."""

import time

import jwt
import pytest

from tests.auth.conftest import Role
from tests.settings import ADMIN, JWT_SECRET, VIEWER


def forge(payload: dict, secret: str = JWT_SECRET, algorithm: str = "HS256") -> str:
    now = int(time.time())
    return jwt.encode({"iat": now, "exp": now + 600, **payload}, secret, algorithm=algorithm)


def me(playwright_request, token: str):
    return playwright_request.get("/auth/me", headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
def anon(context_for):
    return context_for(Role.ANONYMOUS)


@pytest.fixture
def viewer_id(viewer_ctx) -> int:
    return viewer_ctx.get("/auth/me").json()["id"]


@pytest.mark.parametrize(
    ("username", "password"),
    [
        pytest.param(VIEWER.username, "wrong-password", id="wrong_password"),
        pytest.param("no-such-user", VIEWER.password, id="unknown_user"),
        pytest.param(VIEWER.username.upper(), VIEWER.password, id="username_is_case_sensitive"),
        pytest.param(ADMIN.username, VIEWER.password, id="another_users_password"),
    ],
)
def test_login_rejects_wrong_credentials(anon, username, password):
    response = anon.post("/auth/login", data={"username": username, "password": password})

    assert response.status == 401
    # Same message for unknown user and wrong password: no hint which usernames exist.
    assert response.json() == {"detail": "Invalid username or password"}
    assert "set-cookie" not in response.headers


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({}, id="empty"),
        pytest.param({"username": VIEWER.username}, id="no_password"),
        pytest.param({"username": "", "password": ""}, id="blank_fields"),
    ],
)
def test_login_rejects_incomplete_body(anon, body):
    assert anon.post("/auth/login", data=body).status == 422


def test_valid_forged_token_is_accepted(anon, viewer_id):
    """Control case: proves the forging helper is right, so the rejections below are real."""
    assert me(anon, forge({"sub": str(viewer_id), "role": "viewer"})).status == 200


def test_expired_token_is_rejected(anon, viewer_id):
    token = forge({"sub": str(viewer_id), "role": "viewer", "exp": int(time.time()) - 1})

    assert me(anon, token).status == 401


def test_token_signed_with_another_secret_is_rejected(anon, viewer_id):
    token = forge({"sub": str(viewer_id), "role": "viewer"}, secret="x" * 40)

    assert me(anon, token).status == 401


def test_unsigned_token_is_rejected(anon, viewer_id):
    token = forge({"sub": str(viewer_id), "role": "admin"}, secret="", algorithm="none")

    assert me(anon, token).status == 401


def test_tampered_token_is_rejected(anon, viewer_ctx):
    token = viewer_ctx.storage_state()["cookies"][0]["value"]
    header, payload, signature = token.split(".")
    tampered = f"{header}.{payload}.{signature[::-1]}"

    assert me(anon, tampered).status == 401


def test_role_claim_in_token_does_not_grant_admin(anon, viewer_id):
    """The server takes the role from the database, not from the token."""
    token = forge({"sub": str(viewer_id), "role": "admin"})

    response = anon.delete("/products/1", headers={"Authorization": f"Bearer {token}"})

    assert response.status == 403


def test_token_for_deleted_or_unknown_user_is_rejected(anon):
    assert me(anon, forge({"sub": "999999", "role": "admin"})).status == 401


@pytest.mark.parametrize(
    "header",
    [
        pytest.param("Bearer", id="bearer_without_token"),
        pytest.param("Bearer not.a.jwt", id="garbage_token"),
        pytest.param("Basic dmlld2VyOnZpZXdlci1wYXNz", id="basic_auth"),
    ],
)
def test_malformed_authorization_header_is_rejected(anon, header):
    assert anon.get("/auth/me", headers={"Authorization": header}).status == 401
