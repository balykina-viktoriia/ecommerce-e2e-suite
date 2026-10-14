"""SQL the tests use to read state. Kept in one place so tests read like specifications."""

from psycopg import Connection


def product_by_id(db: Connection, product_id: int) -> dict | None:
    return db.execute("SELECT * FROM products WHERE id = %s", (product_id,)).fetchone()


def products_by_sku(db: Connection, sku: str) -> list[dict]:
    return db.execute("SELECT * FROM products WHERE sku = %s", (sku,)).fetchall()


def order_by_id(db: Connection, order_id: int) -> dict | None:
    return db.execute("SELECT * FROM orders WHERE id = %s", (order_id,)).fetchone()


def order_items(db: Connection, order_id: int) -> list[dict]:
    return db.execute(
        "SELECT * FROM order_items WHERE order_id = %s ORDER BY product_id", (order_id,)
    ).fetchall()


def order_items_for_product(db: Connection, product_id: int) -> list[dict]:
    return db.execute("SELECT * FROM order_items WHERE product_id = %s", (product_id,)).fetchall()


def db_now(db: Connection):
    return db.execute("SELECT now() AS now").fetchone()["now"]
