# E-commerce E2E Test Suite

An end-to-end test suite for an e-commerce flow, built layer by layer: UI, API, auth, database and data quality.

## Layers

| Layer | What it covers | Status |
|---|---|---|
| UI | Playwright + Page Object Model against [saucedemo](https://www.saucedemo.com), typed test data | done |
| API | CRUD, schema validation, headers, negative cases | planned |
| Auth | `storageState`, multiple roles, permission checks | planned |
| Database | Assert on the row in the DB after an API write | planned |
| Data quality | Checks on the six data-quality dimensions | planned |

## Run locally

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
pyproject.toml       # pytest and ruff configuration
```
