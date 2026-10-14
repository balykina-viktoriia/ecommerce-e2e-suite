import psycopg
import pytest
from psycopg.rows import dict_row

from tests.api.client import require_shop_api
from tests.settings import DATABASE_URL, VIEWER


@pytest.fixture(scope="session", autouse=True)
def api_is_up():
    require_shop_api()


@pytest.fixture(scope="session")
def db():
    """Read-mostly connection straight to PostgreSQL, bypassing the API.

    Autocommit, so every query sees what the API has committed so far.
    """
    try:
        conn = psycopg.connect(DATABASE_URL, autocommit=True, row_factory=dict_row)
    except psycopg.OperationalError as error:
        pytest.exit(f"Database is not reachable at {DATABASE_URL} ({error})", returncode=1)
    yield conn
    conn.close()


@pytest.fixture
def rollback_db():
    """A connection whose changes are always rolled back: for poking at constraints."""
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        yield conn
        conn.rollback()


@pytest.fixture(scope="session")
def viewer_id(db) -> int:
    return db.execute("SELECT id FROM users WHERE username = %s", (VIEWER.username,)).fetchone()[
        "id"
    ]
