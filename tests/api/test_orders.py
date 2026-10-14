from decimal import Decimal

import pytest

from tests.api import schemas
from tests.api.assertions import assert_matches_schema
from tests.api.data import ProductPayload


@pytest.fixture
def product_factory(admin):
    created = []

    def _create(**overrides) -> dict:
        response = admin.post("/products", json=ProductPayload.new(**overrides).to_json())
        assert response.status_code == 201, response.text
        created.append(response.json())
        return response.json()

    yield _create
    for product in created:
        admin.delete(f"/products/{product['id']}")


def order_of(*lines: tuple[dict, int]) -> dict:
    return {"items": [{"product_id": p["id"], "quantity": q} for p, q in lines]}


def test_create_order(viewer, product_factory):
    tote = product_factory(price="12.50", stock=10)
    mug = product_factory(price="3.99", stock=5)

    response = viewer.post("/orders", json=order_of((tote, 2), (mug, 3)))

    assert response.status_code == 201
    order = response.json()
    assert_matches_schema(order, schemas.ORDER)
    assert response.headers["Location"] == f"/orders/{order['id']}"
    assert order["status"] == "created"
    assert Decimal(order["total"]) == Decimal("12.50") * 2 + Decimal("3.99") * 3
    assert {(i["product_id"], i["quantity"], i["unit_price"]) for i in order["items"]} == {
        (tote["id"], 2, "12.50"),
        (mug["id"], 3, "3.99"),
    }


def test_order_decreases_stock(admin, viewer, product_factory):
    product = product_factory(stock=5)

    viewer.post("/orders", json=order_of((product, 2)))

    assert admin.get(f"/products/{product['id']}").json()["stock"] == 3


def test_order_can_use_all_remaining_stock(viewer, admin, product_factory):
    product = product_factory(stock=2)

    response = viewer.post("/orders", json=order_of((product, 2)))

    assert response.status_code == 201
    assert admin.get(f"/products/{product['id']}").json()["stock"] == 0


def test_order_keeps_price_at_time_of_purchase(admin, viewer, product_factory):
    product = product_factory(price="10.00")
    order = viewer.post("/orders", json=order_of((product, 1))).json()

    admin.put(
        f"/products/{product['id']}",
        json={**ProductPayload.new(price="99.00").to_json(), "sku": product["sku"]},
    )

    stored = viewer.get(f"/orders/{order['id']}").json()
    assert stored["items"][0]["unit_price"] == "10.00"
    assert stored["total"] == "10.00"


def test_order_appears_in_own_order_list(viewer, product_factory):
    order = viewer.post("/orders", json=order_of((product_factory(), 1))).json()

    orders = viewer.get("/orders").json()

    assert_matches_schema(orders, {"type": "array", "items": schemas.ORDER})
    assert order["id"] in [o["id"] for o in orders]


def test_order_with_insufficient_stock_returns_409(admin, viewer, product_factory):
    product = product_factory(stock=1)

    response = viewer.post("/orders", json=order_of((product, 2)))

    assert response.status_code == 409
    assert response.json()["detail"] == f"Not enough stock for product {product['id']}"
    assert admin.get(f"/products/{product['id']}").json()["stock"] == 1


def test_failed_order_does_not_change_any_stock(admin, viewer, product_factory):
    """One bad line must roll back the whole order, including lines that were fine."""
    plenty = product_factory(stock=10)
    scarce = product_factory(stock=0)

    response = viewer.post("/orders", json=order_of((plenty, 1), (scarce, 1)))

    assert response.status_code == 409
    assert admin.get(f"/products/{plenty['id']}").json()["stock"] == 10


def test_order_with_unknown_product_returns_404(viewer):
    response = viewer.post("/orders", json={"items": [{"product_id": 999_999, "quantity": 1}]})

    assert response.status_code == 404
    assert response.json()["detail"] == "Product 999999 not found"


def test_order_with_duplicate_product_returns_400(viewer, product_factory):
    product = product_factory()

    response = viewer.post("/orders", json=order_of((product, 1), (product, 2)))

    assert response.status_code == 400
    assert_matches_schema(response.json(), schemas.ERROR)


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"items": []}, id="empty_items"),
        pytest.param({}, id="missing_items"),
        pytest.param({"items": [{"product_id": 1, "quantity": 0}]}, id="zero_quantity"),
        pytest.param({"items": [{"product_id": 1, "quantity": -1}]}, id="negative_quantity"),
        pytest.param({"items": [{"product_id": 1}]}, id="missing_quantity"),
        pytest.param({"items": [{"quantity": 1}]}, id="missing_product_id"),
        pytest.param({"items": [{"product_id": "one", "quantity": 1}]}, id="product_id_string"),
        pytest.param({"items": "all"}, id="items_not_a_list"),
    ],
)
def test_create_order_rejects_invalid_payload(viewer, body):
    response = viewer.post("/orders", json=body)

    assert response.status_code == 422
    assert_matches_schema(response.json(), schemas.VALIDATION_ERROR)


def test_missing_order_returns_404(admin):
    response = admin.get("/orders/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order 999999 not found"
