"""The database is the last line of defence: its constraints must reject bad rows even if
the API lets one through. Every change here is rolled back."""

import pytest
from psycopg import errors

from tests.api.data import unique_sku
from tests.settings import ADMIN, VIEWER


def insert_product(conn, **overrides):
    values = {"sku": unique_sku(), "name": "x", "price": "1.00", "stock": 1, **overrides}
    conn.execute(
        "INSERT INTO products (sku, name, price, stock) "
        "VALUES (%(sku)s, %(name)s, %(price)s, %(stock)s)",
        values,
    )


@pytest.mark.parametrize(
    ("overrides", "error"),
    [
        pytest.param({"price": "-0.01"}, errors.CheckViolation, id="negative_price"),
        pytest.param({"stock": -1}, errors.CheckViolation, id="negative_stock"),
        pytest.param({"name": None}, errors.NotNullViolation, id="null_name"),
        pytest.param({"price": None}, errors.NotNullViolation, id="null_price"),
        pytest.param({"sku": "BAG-001"}, errors.UniqueViolation, id="duplicate_seed_sku"),
        pytest.param({"price": "100000000.00"}, errors.NumericValueOutOfRange, id="price_overflow"),
    ],
)
def test_products_table_rejects_bad_rows(rollback_db, overrides, error):
    with pytest.raises(error):
        insert_product(rollback_db, **overrides)


def test_price_is_rounded_to_cents_by_the_column_type(rollback_db):
    sku = unique_sku()
    insert_product(rollback_db, sku=sku, price="1.005")

    price = rollback_db.execute("SELECT price FROM products WHERE sku = %s", (sku,)).fetchone()
    assert str(price["price"]) == "1.01"


def test_order_item_must_reference_existing_product(rollback_db):
    order_id = rollback_db.execute(
        "INSERT INTO orders (user_id, total) SELECT id, 0 FROM users LIMIT 1 RETURNING id"
    ).fetchone()["id"]

    with pytest.raises(errors.ForeignKeyViolation):
        rollback_db.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
            "VALUES (%s, 999999, 1, 1.00)",
            (order_id,),
        )


def test_order_status_is_limited_to_known_values(rollback_db):
    with pytest.raises(errors.CheckViolation):
        rollback_db.execute(
            "INSERT INTO orders (user_id, total, status) SELECT id, 0, 'shipped' FROM users LIMIT 1"
        )


@pytest.mark.parametrize("account", [ADMIN, VIEWER], ids=["admin", "viewer"])
def test_passwords_are_stored_salted_and_hashed(db, account):
    row = db.execute(
        "SELECT password_hash FROM users WHERE username = %s", (account.username,)
    ).fetchone()

    assert account.password not in row["password_hash"]
    salt, digest = row["password_hash"].split("$")
    assert len(salt) == 32, "16-byte random salt, hex encoded"
    assert len(digest) == 64, "SHA-256 digest, hex encoded"
