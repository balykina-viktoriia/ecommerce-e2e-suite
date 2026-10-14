import pytest
import requests

from tests.settings import API_BASE_URL, Credentials

DEFAULT_TIMEOUT_SECONDS = 10


class ApiClient:
    """Thin wrapper over requests.Session: base URL, timeout and bearer token in one place.

    Methods return the raw Response so tests can assert on status codes and headers.
    """

    def __init__(self, base_url: str = API_BASE_URL, token: str | None = None):
        self.base_url = base_url
        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    @classmethod
    def logged_in(cls, credentials: Credentials) -> "ApiClient":
        client = cls()
        response = client.post(
            "/auth/login",
            json={"username": credentials.username, "password": credentials.password},
        )
        response.raise_for_status()
        return cls(token=response.json()["access_token"])

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT_SECONDS)
        return self.session.request(method, f"{self.base_url}{path}", **kwargs)

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.request("DELETE", path, **kwargs)


def require_shop_api() -> None:
    """Stop the run with a clear message instead of a hundred connection errors."""
    try:
        ApiClient().get("/health").raise_for_status()
    except requests.RequestException as error:
        pytest.exit(
            f"Shop API is not reachable at {API_BASE_URL} ({error}). "
            "Start it with: docker compose up -d --build --wait",
            returncode=1,
        )
