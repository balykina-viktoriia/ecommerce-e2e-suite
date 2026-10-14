# E-commerce E2E Test Suite

An end-to-end test suite for an e-commerce flow, built layer by layer: UI, API, auth, database and data quality.

## Layers

| Layer | What it covers | Status |
|---|---|---|
| UI | Playwright + Page Object Model against [saucedemo](https://www.saucedemo.com), typed test data: login (positive and negative), logout, sorting, cart, checkout validation and totals | done |
| API | `requests` tests: CRUD, JSON Schema contracts, headers, and negative cases (400, 401, 404, 405, 409, 422) | done |
| Auth | Playwright `storageState` per role, a role x endpoint permission matrix (viewer gets 403 on delete, and the row survives), order ownership, forged and expired JWTs | done |
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

The API layer needs the shop app running (see above). Run one layer with a marker, in parallel:

```bash
pytest -m ui -n 4
```

## Troubleshooting

UI tests time out on `Page.goto` now and then, while the API layers are fine: check the IPv6 route to saucedemo. On one home network a third of IPv6 requests stalled for 5-12 seconds while IPv4 answered in 0.1 s:

```bash
for v in 4 6; do curl -$v -s -o /dev/null -m 12 -w "IPv$v %{time_total}s\n" https://www.saucedemo.com/; done
```

GitHub Actions runners and Docker containers use IPv4 by default, so CI is not affected.

## Known issues

Defects the suite found are kept as `xfail(strict=True)` tests: they document the bug, and turn red once it is fixed so the marker gets removed.

| Where | Defect |
|---|---|
| saucedemo | `problem_user` cannot add the Fleece Jacket to the cart |
| shop API | `405` on `/products/{id}` returns `Allow: GET`, although `PUT` and `DELETE` exist |

## Structure

```
tests/ui/pages/      # page objects
tests/ui/test_data.py  # typed test data (dataclasses, enums)
tests/ui/            # UI tests and fixtures
tests/api/           # API tests, client, JSON schemas, payload factory
tests/auth/          # storageState fixtures, permission matrix, token tests
tests/settings.py    # API URL and test accounts (env vars, defaults match .env.example)
app/                 # shop API (FastAPI)
db/init.sql          # database schema and seed data
docker-compose.yml   # app + database
pyproject.toml       # pytest and ruff configuration
```
