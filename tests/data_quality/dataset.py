from dataclasses import dataclass, replace

import pandas as pd
import psycopg
from psycopg import IsolationLevel

TABLES = {
    "users": "SELECT id, username, role, created_at FROM users",
    "products": "SELECT id, sku, name, price, stock, created_at, updated_at FROM products",
    "orders": "SELECT id, user_id, status, total, created_at FROM orders",
    "order_items": "SELECT order_id, product_id, quantity, unit_price FROM order_items",
}


@dataclass(frozen=True)
class ShopDataset:
    """The shop's tables as DataFrames. Money stays as Decimal, so sums are exact."""

    users: pd.DataFrame
    products: pd.DataFrame
    orders: pd.DataFrame
    order_items: pd.DataFrame

    @classmethod
    def from_database(cls, url: str) -> "ShopDataset":
        # One read-only REPEATABLE READ transaction = one consistent snapshot. Without it, a
        # product created by a parallel test between two SELECTs would look like an orphan.
        with psycopg.connect(url) as conn:
            conn.isolation_level = IsolationLevel.REPEATABLE_READ
            conn.read_only = True
            frames = {}
            for name, sql in TABLES.items():
                cursor = conn.execute(sql)
                columns = [c.name for c in cursor.description]
                frames[name] = pd.DataFrame(cursor.fetchall(), columns=columns)
        return cls(**frames)

    def with_changes(self, **frames: pd.DataFrame) -> "ShopDataset":
        return replace(self, **frames)
