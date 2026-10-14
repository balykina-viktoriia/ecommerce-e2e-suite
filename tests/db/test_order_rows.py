from decimal import Decimal

import pytest

from tests.api.data import ProductPayload
from tests.db import queries


@pytest.fixture
def two_products(admin):
    products = [
        admin.post("/products", json=ProductPayload.new(price=p, stock=s).to_json()).json()
        for p, s in (("12.50", 10), ("3.99", 5))
    ]
    yield products
    for product in products:
        admin.delete(f"/products/{product['id']}")


def test_order_rows_are_written(viewer, db, viewer_id, two_products):
    tote, mug = two_products

    order = viewer.post(
        "/orders",
        json={
            "items": [
                {"product_id": tote["id"], "quantity": 2},
                {"product_id": mug["id"], "quantity": 3},
            ]
        },
    ).json()

    row = queries.order_by_id(db, order["id"])
    assert row["user_id"] == viewer_id
    assert row["status"] == "created"
    assert row["total"] == Decimal("36.97")

    items = queries.order_items(db, order["id"])
    assert [(i["product_id"], i["quantity"], i["unit_price"]) for i in items] == sorted(
        [(tote["id"], 2, Decimal("12.50")), (mug["id"], 3, Decimal("3.99"))]
    )


def test_order_total_equals_sum_of_its_lines_in_sql(viewer, db, two_products):
    order = viewer.post(
        "/orders",
        json={"items": [{"product_id": p["id"], "quantity": 3} for p in two_products]},
    ).json()

    check = db.execute(
        """
        SELECT o.total, SUM(i.quantity * i.unit_price) AS lines_total
        FROM orders o JOIN order_items i ON i.order_id = o.id
        WHERE o.id = %s
        GROUP BY o.total
        """,
        (order["id"],),
    ).fetchone()
    assert check["total"] == check["lines_total"]


def test_order_decrements_stock_in_the_table(viewer, db, two_products):
    tote, _ = two_products

    viewer.post("/orders", json={"items": [{"product_id": tote["id"], "quantity": 4}]})

    assert queries.product_by_id(db, tote["id"])["stock"] == 6


def test_failed_order_leaves_no_rows_and_no_stock_change(viewer, db, two_products):
    tote, mug = two_products

    response = viewer.post(
        "/orders",
        json={
            "items": [
                {"product_id": tote["id"], "quantity": 1},
                {"product_id": mug["id"], "quantity": 99},
            ]
        },
    )

    assert response.status_code == 409
    assert queries.order_items_for_product(db, tote["id"]) == []
    assert queries.product_by_id(db, tote["id"])["stock"] == 10
    assert queries.product_by_id(db, mug["id"])["stock"] == 5
