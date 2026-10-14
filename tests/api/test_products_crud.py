from decimal import Decimal

from tests.api import schemas
from tests.api.assertions import assert_matches_schema
from tests.api.data import ProductPayload


def test_create_product(admin):
    payload = ProductPayload.new(name="Canvas Tote", price="12.50", stock=7)

    response = admin.post("/products", json=payload.to_json())

    assert response.status_code == 201
    body = response.json()
    assert_matches_schema(body, schemas.PRODUCT)
    assert response.headers["Location"] == f"/products/{body['id']}"
    assert {k: body[k] for k in ("sku", "name", "price", "stock")} == payload.to_json()
    assert body["created_at"] == body["updated_at"]
    admin.delete(f"/products/{body['id']}")


def test_get_product_by_id(admin, created_product):
    response = admin.get(f"/products/{created_product['id']}")

    assert response.status_code == 200
    assert_matches_schema(response.json(), schemas.PRODUCT)
    assert response.json() == created_product


def test_viewer_can_read_products(viewer, created_product):
    response = viewer.get(f"/products/{created_product['id']}")

    assert response.status_code == 200
    assert response.json()["sku"] == created_product["sku"]


def test_list_products(admin):
    response = admin.get("/products", params={"limit": 100})

    assert response.status_code == 200
    products = response.json()
    assert_matches_schema(products, schemas.PRODUCT_LIST)
    ids = [p["id"] for p in products]
    assert ids == sorted(ids), "products should be ordered by id"


def test_list_products_pagination(admin):
    first_page = admin.get("/products", params={"limit": 3, "offset": 0}).json()
    second_page = admin.get("/products", params={"limit": 3, "offset": 3}).json()

    assert len(first_page) == 3
    assert len(second_page) == 3
    assert not {p["id"] for p in first_page} & {p["id"] for p in second_page}


def test_update_product(admin, created_product):
    payload = ProductPayload.new(name="Renamed", price="0.99", stock=0)

    response = admin.put(f"/products/{created_product['id']}", json=payload.to_json())

    assert response.status_code == 200
    body = response.json()
    assert_matches_schema(body, schemas.PRODUCT)
    assert {k: body[k] for k in ("sku", "name", "price", "stock")} == payload.to_json()
    assert body["created_at"] == created_product["created_at"]
    assert body["updated_at"] > created_product["updated_at"]


def test_delete_product(admin):
    product = admin.post("/products", json=ProductPayload.new().to_json()).json()

    response = admin.delete(f"/products/{product['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert admin.get(f"/products/{product['id']}").status_code == 404


def test_price_keeps_two_decimal_places(admin):
    payload = ProductPayload.new(price="10")

    body = admin.post("/products", json=payload.to_json()).json()

    assert body["price"] == "10.00"
    assert Decimal(body["price"]) == Decimal(payload.price)
    admin.delete(f"/products/{body['id']}")
