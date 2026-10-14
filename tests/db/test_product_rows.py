"""After every API write, read the row straight from PostgreSQL and check it."""

from datetime import timedelta
from decimal import Decimal

from tests.api.data import ProductPayload
from tests.db import queries

RECENT = timedelta(seconds=30)


def test_created_product_is_stored_exactly(admin, db):
    payload = ProductPayload.new(name="Linen Shirt", price="34.90", stock=12)

    body = admin.post("/products", json=payload.to_json()).json()

    row = queries.product_by_id(db, body["id"])
    assert row is not None
    assert row["sku"] == payload.sku
    assert row["name"] == payload.name
    assert row["price"] == Decimal("34.90")  # NUMERIC, compared exactly, no float rounding
    assert row["stock"] == 12
    assert row["created_at"] == row["updated_at"]
    assert queries.db_now(db) - row["created_at"] < RECENT
    admin.delete(f"/products/{body['id']}")


def test_api_response_matches_the_row(admin, db, created_product):
    row = queries.product_by_id(db, created_product["id"])

    assert created_product["price"] == f"{row['price']:.2f}"
    assert created_product["created_at"] == row["created_at"].isoformat().replace("+00:00", "Z")


def test_update_changes_the_row_and_bumps_updated_at(admin, db, created_product):
    before = queries.product_by_id(db, created_product["id"])
    payload = ProductPayload.new(name="Updated", price="1.05", stock=0)

    admin.put(f"/products/{created_product['id']}", json=payload.to_json())

    after = queries.product_by_id(db, created_product["id"])
    assert (after["sku"], after["name"], after["price"], after["stock"]) == (
        payload.sku,
        "Updated",
        Decimal("1.05"),
        0,
    )
    assert after["created_at"] == before["created_at"]
    assert after["updated_at"] > before["updated_at"]


def test_delete_removes_the_row(admin, db):
    product = admin.post("/products", json=ProductPayload.new().to_json()).json()

    admin.delete(f"/products/{product['id']}")

    assert queries.product_by_id(db, product["id"]) is None


def test_rejected_create_writes_nothing(admin, db):
    payload = ProductPayload.new(price="-5.00")

    assert admin.post("/products", json=payload.to_json()).status_code == 422

    assert queries.products_by_sku(db, payload.sku) == []


def test_duplicate_sku_keeps_a_single_row(admin, db, created_product):
    payload = ProductPayload.new(name="Impostor")
    payload.sku = created_product["sku"]

    assert admin.post("/products", json=payload.to_json()).status_code == 409

    rows = queries.products_by_sku(db, created_product["sku"])
    assert len(rows) == 1
    assert rows[0]["name"] == created_product["name"]


def test_forbidden_delete_leaves_the_row(viewer, db, created_product):
    before = queries.product_by_id(db, created_product["id"])

    assert viewer.delete(f"/products/{created_product['id']}").status_code == 403

    assert queries.product_by_id(db, created_product["id"]) == before


def test_delete_of_ordered_product_is_refused_and_row_kept(admin, viewer, db, created_product):
    viewer.post("/orders", json={"items": [{"product_id": created_product["id"], "quantity": 1}]})

    assert admin.delete(f"/products/{created_product['id']}").status_code == 409

    assert queries.product_by_id(db, created_product["id"]) is not None
