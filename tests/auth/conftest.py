from enum import StrEnum
from pathlib import Path

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from tests.api.client import require_shop_api
from tests.settings import ADMIN, API_BASE_URL, VIEWER, Credentials


class Role(StrEnum):
    ADMIN = "admin"
    VIEWER = "viewer"
    ANONYMOUS = "anonymous"


CREDENTIALS: dict[Role, Credentials] = {Role.ADMIN: ADMIN, Role.VIEWER: VIEWER}


@pytest.fixture(scope="session", autouse=True)
def api_is_up():
    require_shop_api()


@pytest.fixture(scope="session")
def storage_states(playwright: Playwright, tmp_path_factory) -> dict[Role, Path]:
    """Log in once per role and save the session cookie to a storageState file.

    Every test then starts an already-authenticated context from the file instead of
    logging in again, which is the standard Playwright pattern for multi-role suites.
    """
    folder = tmp_path_factory.mktemp("auth")
    states = {}
    for role, credentials in CREDENTIALS.items():
        context = playwright.request.new_context(base_url=API_BASE_URL)
        response = context.post(
            "/auth/login",
            data={"username": credentials.username, "password": credentials.password},
        )
        assert response.ok, response.text()
        states[role] = folder / f"{role}.json"
        context.storage_state(path=states[role])
        context.dispose()
    return states


@pytest.fixture
def context_for(playwright: Playwright, storage_states):
    """Factory: an API request context signed in as the given role (or anonymous)."""
    contexts: list[APIRequestContext] = []

    def _context(role: Role) -> APIRequestContext:
        state = storage_states.get(role)
        context = playwright.request.new_context(base_url=API_BASE_URL, storage_state=state)
        contexts.append(context)
        return context

    yield _context
    for context in contexts:
        context.dispose()


@pytest.fixture
def admin_ctx(context_for) -> APIRequestContext:
    return context_for(Role.ADMIN)


@pytest.fixture
def viewer_ctx(context_for) -> APIRequestContext:
    return context_for(Role.VIEWER)
