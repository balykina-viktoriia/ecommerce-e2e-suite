"""Role-based access: every endpoint x every role, plus proof that a refused write
really changed nothing."""

import pytest

from tests.api.data import ProductPayload
from tests.auth.conftest import Role

ADMIN, VIEWER, ANONYMOUS = Role.ADMIN, Role.VIEWER, Role.ANONYMOUS

# (method, path) -> expected status per role. {id} is a fresh product created per test.
PERMISSION_MATRIX = [
    ("GET", "/products", {ADMIN: 200, VIEWER: 200, ANONYMOUS: 401}),
    ("GET", "/products/{id}", {ADMIN: 200, VIEWER: 200, ANONYMOUS: 401}),
    ("POST", "/products", {ADMIN: 201, VIEWER: 403, ANONYMOUS: 401}),
    ("PUT", "/products/{id}", {ADMIN: 200, VIEWER: 403, ANONYMOUS: 401}),
    ("DELETE", "/products/{id}", {ADMIN: 204, VIEWER: 403, ANONYMOUS: 401}),
    ("GET", "/orders", {ADMIN: 200, VIEWER: 200, ANONYMOUS: 401}),
    ("GET", "/auth/me", {ADMIN: 200, VIEWER: 200, ANONYMOUS: 401}),
]

CASES = [
    pytest.param(method, path, role, expected, id=f"{role}-{method}-{path}")
    for method, path, by_role in PERMISSION_MATRIX
    for role, expected in by_role.items()
]


@pytest.fixture
def product(admin_ctx):
    response = admin_ctx.post("/products", data=ProductPayload.new().to_json())
    assert response.status == 201, response.text()
    yield response.json()
    admin_ctx.delete(f"/products/{response.json()['id']}")


@pytest.mark.parametrize(("method", "path", "role", "expected"), CASES)
def test_permission_matrix(context_for, product, method, path, role, expected):
    response = context_for(role).fetch(
        path.format(id=product["id"]),
        method=method,
        data=ProductPayload.new().to_json() if method in ("POST", "PUT") else None,
    )

    assert response.status == expected, response.text()
    if expected == 403:
        assert response.json() == {"detail": "Admin role required"}


def test_viewer_gets_403_on_delete_and_product_survives(viewer_ctx, admin_ctx, product):
    response = viewer_ctx.delete(f"/products/{product['id']}")

    assert response.status == 403
    assert admin_ctx.get(f"/products/{product['id']}").json() == product


def test_viewer_gets_403_on_update_and_product_is_unchanged(viewer_ctx, admin_ctx, product):
    response = viewer_ctx.put(
        f"/products/{product['id']}", data=ProductPayload.new(price="0.01").to_json()
    )

    assert response.status == 403
    assert admin_ctx.get(f"/products/{product['id']}").json() == product


def test_viewer_cannot_see_someone_elses_order(admin_ctx, viewer_ctx, product):
    order = admin_ctx.post(
        "/orders", data={"items": [{"product_id": product["id"], "quantity": 1}]}
    ).json()

    response = viewer_ctx.get(f"/orders/{order['id']}")

    assert response.status == 403
    assert response.json() == {"detail": "You can only view your own orders"}


def test_order_list_is_scoped_to_the_user(admin_ctx, viewer_ctx, product):
    line = {"items": [{"product_id": product["id"], "quantity": 1}]}
    admin_order = admin_ctx.post("/orders", data=line).json()
    viewer_order = viewer_ctx.post("/orders", data=line).json()
    viewer_id = viewer_ctx.get("/auth/me").json()["id"]

    viewer_orders = viewer_ctx.get("/orders").json()
    admin_orders = admin_ctx.get("/orders").json()

    assert {o["user_id"] for o in viewer_orders} == {viewer_id}
    assert viewer_order["id"] in [o["id"] for o in viewer_orders]
    assert admin_order["id"] not in [o["id"] for o in viewer_orders]
    assert {admin_order["id"], viewer_order["id"]} <= {o["id"] for o in admin_orders}
