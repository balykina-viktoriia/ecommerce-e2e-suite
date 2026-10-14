import re
import uuid

from tests.api.client import ApiClient
from tests.settings import VIEWER

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def test_json_content_type(admin):
    response = admin.get("/products")

    assert response.headers["Content-Type"] == "application/json"


def test_request_id_is_echoed(admin):
    request_id = str(uuid.uuid4())

    response = admin.get("/products", headers={"X-Request-ID": request_id})

    assert response.headers["X-Request-ID"] == request_id


def test_request_id_is_generated_when_missing(admin):
    first = admin.get("/products").headers["X-Request-ID"]
    second = admin.get("/products").headers["X-Request-ID"]

    assert UUID_RE.match(first)
    assert first != second


def test_request_id_on_error_responses(anonymous):
    response = anonymous.get("/products", headers={"X-Request-ID": "trace-me"})

    assert response.status_code == 401
    assert response.headers["X-Request-ID"] == "trace-me"


def test_unauthorized_response_has_www_authenticate(anonymous):
    response = anonymous.get("/products")

    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_login_sets_http_only_cookie():
    # A fresh client: requests.Session keeps cookies, and the shared `anonymous` client
    # would silently become logged in for every test that runs after this one.
    response = ApiClient().post(
        "/auth/login", json={"username": VIEWER.username, "password": VIEWER.password}
    )

    cookie = response.headers["Set-Cookie"]
    assert cookie.startswith("access_token=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
