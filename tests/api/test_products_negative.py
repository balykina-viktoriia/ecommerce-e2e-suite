import pytest

from tests.api import schemas
from tests.api.assertions import assert_matches_schema
from tests.api.data import ProductPayload

MISSING_ID = 999_999


def valid_product(**overrides) -> dict:
    return {**ProductPayload.new().to_json(), **overrides}


def without(field: str) -> dict:
    payload = valid_product()
    del payload[field]
    return payload


INVALID_PAYLOADS = [
    pytest.param(without("sku"), "sku", id="missing_sku"),
    pytest.param(without("name"), "name", id="missing_name"),
    pytest.param(without("price"), "price", id="missing_price"),
    pytest.param(without("stock"), "stock", id="missing_stock"),
    pytest.param(valid_product(sku="ab"), "sku", id="sku_too_short"),
    pytest.param(valid_product(sku="lower-case"), "sku", id="sku_lowercase"),
    pytest.param(valid_product(sku="A" * 33), "sku", id="sku_too_long"),
    pytest.param(valid_product(name=""), "name", id="empty_name"),
    pytest.param(valid_product(name="x" * 121), "name", id="name_too_long"),
    pytest.param(valid_product(price="-0.01"), "price", id="negative_price"),
    pytest.param(valid_product(price="1.999"), "price", id="price_three_decimals"),
    pytest.param(valid_product(price="free"), "price", id="price_not_a_number"),
    pytest.param(valid_product(price="100000000.00"), "price", id="price_too_large"),
    pytest.param(valid_product(stock=-1), "stock", id="negative_stock"),
    pytest.param(valid_product(stock=1.5), "stock", id="fractional_stock"),
    pytest.param(valid_product(color="red"), "color", id="unknown_field"),
]


@pytest.mark.parametrize(("payload", "field"), INVALID_PAYLOADS)
def test_create_product_rejects_invalid_payload(admin, payload, field):
    response = admin.post("/products", json=payload)

    assert response.status_code == 422
    assert_matches_schema(response.json(), schemas.VALIDATION_ERROR)
    assert field in [error["loc"][-1] for error in response.json()["detail"]]


@pytest.mark.parametrize(("payload", "field"), INVALID_PAYLOADS[:4])
def test_update_product_rejects_invalid_payload(admin, created_product, payload, field):
    response = admin.put(f"/products/{created_product['id']}", json=payload)

    assert response.status_code == 422
    assert admin.get(f"/products/{created_product['id']}").json() == created_product


def test_create_product_rejects_malformed_json(admin):
    response = admin.post(
        "/products", data="{not json", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "json_invalid"


def test_create_product_rejects_empty_body(admin):
    response = admin.post("/products")

    assert response.status_code == 422


def test_create_product_rejects_duplicate_sku(admin, created_product):
    response = admin.post("/products", json=valid_product(sku=created_product["sku"]))

    assert response.status_code == 409
    assert_matches_schema(response.json(), schemas.ERROR)
    assert created_product["sku"] in response.json()["detail"]


def test_update_product_rejects_duplicate_sku(admin, created_product):
    other = admin.post("/products", json=valid_product()).json()

    response = admin.put(f"/products/{other['id']}", json=valid_product(sku=created_product["sku"]))

    assert response.status_code == 409
    admin.delete(f"/products/{other['id']}")


@pytest.mark.parametrize(
    ("method", "body"),
    [
        pytest.param("get", None, id="get"),
        pytest.param("put", valid_product(), id="put"),
        pytest.param("delete", None, id="delete"),
    ],
)
def test_missing_product_returns_404(admin, method, body):
    response = getattr(admin, method)(f"/products/{MISSING_ID}", json=body)

    assert response.status_code == 404
    assert_matches_schema(response.json(), schemas.ERROR)
    assert response.json()["detail"] == f"Product {MISSING_ID} not found"


@pytest.mark.parametrize("product_id", ["abc", "1.5", "-"])
def test_non_integer_product_id_returns_422(admin, product_id):
    assert admin.get(f"/products/{product_id}").status_code == 422


def test_unknown_route_returns_404(admin):
    assert admin.get("/no-such-endpoint").status_code == 404


def test_wrong_method_returns_405(admin):
    response = admin.request("PATCH", "/products/1", json={})

    assert response.status_code == 405


@pytest.mark.xfail(
    reason="Known defect: Allow on /products/{id} lists only GET, though PUT and DELETE exist",
    strict=True,
)
def test_405_lists_all_allowed_methods(admin):
    response = admin.request("PATCH", "/products/1", json={})

    assert set(response.headers["Allow"].split(", ")) == {"GET", "PUT", "DELETE"}


@pytest.mark.parametrize(
    "params",
    [
        pytest.param({"limit": 0}, id="limit_zero"),
        pytest.param({"limit": 101}, id="limit_over_max"),
        pytest.param({"limit": "ten"}, id="limit_not_a_number"),
        pytest.param({"offset": -1}, id="negative_offset"),
    ],
)
def test_list_products_rejects_bad_pagination(admin, params):
    response = admin.get("/products", params=params)

    assert response.status_code == 422
    assert_matches_schema(response.json(), schemas.VALIDATION_ERROR)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/products"),
        ("get", "/products/1"),
        ("post", "/products"),
        ("put", "/products/1"),
        ("delete", "/products/1"),
        ("get", "/orders"),
        ("post", "/orders"),
    ],
)
def test_endpoints_require_authentication(anonymous, method, path):
    response = getattr(anonymous, method)(path, json=valid_product())

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
