# E-commerce E2E Test Suite

An end-to-end test suite for an e-commerce flow, built layer by layer: UI, API, auth, database and data quality.

## Layers

| Layer | What it covers | Status |
|---|---|---|
| UI | Playwright + Page Object Model against [saucedemo](https://www.saucedemo.com), typed test data: login (positive and negative), logout, sorting, cart, checkout validation and totals | done |
| API | CRUD, schema validation, headers, negative cases | planned |
| Auth | `storageState`, multiple roles, permission checks | planned |
| Database | Assert on the row in the DB after an API write | planned |
| Data quality | Checks on the six data-quality dimensions | planned |

## System under test

The UI layer runs against the public saucedemo site. It has no API or database, so the other layers run against a small shop service that lives in this repository:

- `app/` is a FastAPI service with products, orders and two roles (`admin`, `viewer`). Login returns a JWT and also sets it as an HttpOnly cookie.
- `db/init.sql` is the PostgreSQL schema and seed data.
- `docker-compose.yml` starts both.

```bash
docker compose up -d --build --wait
```

The API is then at http://localhost:8000 (interactive docs at `/docs`) and PostgreSQL at `localhost:5433`. The default accounts and ports are listed in [`.env.example`](.env.example); they exist only in the local containers.

Stop and wipe the data:

```bash
docker compose down -v
```

| Method | Path | Who | Notes |
|---|---|---|---|
| POST | `/auth/login` | anyone | 401 on wrong credentials |
| GET | `/auth/me` | signed in | |
| GET | `/products`, `/products/{id}` | signed in | `limit` 1–100, `offset` |
| POST | `/products` | admin | 409 on duplicate `sku` |
| PUT | `/products/{id}` | admin | |
| DELETE | `/products/{id}` | admin | 403 for viewer, 409 if used in an order |
| POST | `/orders` | signed in | 400 duplicate product, 404 unknown product, 409 not enough stock |
| GET | `/orders`, `/orders/{id}` | signed in | viewers see only their own orders |

## Run the tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
pytest
```

Run one layer with a marker, in parallel:

```bash
pytest -m ui -n 4
```

## Structure

```
tests/ui/pages/      # page objects
tests/ui/test_data.py  # typed test data (dataclasses, enums)
tests/ui/            # UI tests and fixtures
app/                 # shop API (FastAPI)
db/init.sql          # database schema and seed data
docker-compose.yml   # app + database
pyproject.toml       # pytest and ruff configuration
```
