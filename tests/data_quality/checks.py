"""Data-quality checks over the shop dataset, grouped by the six classic dimensions.

Each check returns the offending rows, not just a boolean, so a failure shows *what* is wrong.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from enum import StrEnum

import pandas as pd

from tests.data_quality.dataset import ShopDataset

ORDER_STATUSES = {"created", "paid", "cancelled"}
ROLES = {"admin", "viewer"}
SKU_PATTERN = r"[A-Z0-9-]{3,32}"
CLOCK_SKEW = timedelta(minutes=1)
MAX_DATA_AGE = timedelta(hours=24)


class Dimension(StrEnum):
    VALIDITY = "validity"
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    TIMELINESS = "timeliness"
    CONSISTENCY = "consistency"
    UNIQUENESS = "uniqueness"


@dataclass(frozen=True)
class CheckResult:
    dimension: Dimension
    name: str
    checked: int
    failed: pd.DataFrame

    @property
    def passed(self) -> bool:
        return self.failed.empty

    @property
    def pass_rate(self) -> float:
        return 1.0 if self.checked == 0 else 1 - len(self.failed) / self.checked

    def describe(self) -> str:
        sample = self.failed.head(5).to_string(index=False)
        return (
            f"[{self.dimension}] {self.name}: {len(self.failed)} of {self.checked} rows failed\n"
            f"{sample}"
        )


Check = Callable[[ShopDataset, pd.Timestamp], CheckResult]
CHECKS: list[Check] = []


def check(dimension: Dimension):
    """Register a check under its function name and the given dimension."""

    def register(fn):
        def run(ds: ShopDataset, now: pd.Timestamp) -> CheckResult:
            checked, failed = fn(ds, now)
            return CheckResult(dimension, fn.__name__, checked, failed)

        run.__name__ = fn.__name__
        run.__doc__ = fn.__doc__
        CHECKS.append(run)
        return run

    return register


def _has_more_than_two_decimals(value) -> bool:
    return value is not None and Decimal(value).as_tuple().exponent < -2


# --- Validity: values have the right type, format and range ---------------------------


@check(Dimension.VALIDITY)
def order_status_is_known(ds, now):
    return len(ds.orders), ds.orders[~ds.orders["status"].isin(ORDER_STATUSES)]


@check(Dimension.VALIDITY)
def user_role_is_known(ds, now):
    return len(ds.users), ds.users[~ds.users["role"].isin(ROLES)]


@check(Dimension.VALIDITY)
def sku_has_valid_format(ds, now):
    valid = ds.products["sku"].astype("string").str.fullmatch(SKU_PATTERN).fillna(False)
    return len(ds.products), ds.products[~valid.astype(bool)]


@check(Dimension.VALIDITY)
def product_price_and_stock_in_range(ds, now):
    p = ds.products
    bad = (
        (p["price"].map(lambda v: v is not None and v < 0))
        | p["price"].map(_has_more_than_two_decimals)
        | (p["stock"] < 0)
    )
    return len(p), p[bad]


@check(Dimension.VALIDITY)
def order_line_quantity_and_price_in_range(ds, now):
    i = ds.order_items
    bad = (
        (i["quantity"] <= 0)
        | i["unit_price"].map(lambda v: v is not None and v < 0)
        | i["unit_price"].map(_has_more_than_two_decimals)
    )
    return len(i), i[bad]


# --- Completeness: required values and related records are present -------------------

REQUIRED = {
    "users": ["id", "username", "role", "created_at"],
    "products": ["id", "sku", "name", "price", "stock", "created_at", "updated_at"],
    "orders": ["id", "user_id", "status", "total", "created_at"],
    "order_items": ["order_id", "product_id", "quantity", "unit_price"],
}


@check(Dimension.COMPLETENESS)
def required_fields_are_filled(ds, now):
    missing, checked = [], 0
    for table, columns in REQUIRED.items():
        frame = getattr(ds, table)
        checked += len(frame)
        blank = frame[columns].isna().any(axis=1)
        if "name" in columns:
            blank |= frame["name"].astype("string").str.strip().eq("").fillna(False)
        missing.append(frame[blank].assign(table=table))
    return checked, pd.concat(missing, ignore_index=True)


@check(Dimension.COMPLETENESS)
def every_order_has_lines(ds, now):
    return len(ds.orders), ds.orders[~ds.orders["id"].isin(ds.order_items["order_id"])]


# --- Accuracy: values agree with the source of truth they are derived from ------------


@check(Dimension.ACCURACY)
def order_total_equals_sum_of_lines(ds, now):
    lines = ds.order_items.assign(amount=ds.order_items["quantity"] * ds.order_items["unit_price"])
    computed = lines.groupby("order_id")["amount"].sum().rename("computed_total")
    joined = ds.orders.join(computed, on="id", how="inner")
    return len(joined), joined[joined["total"] != joined["computed_total"]]


# --- Timeliness: timestamps are plausible and the data is recent ----------------------


@check(Dimension.TIMELINESS)
def no_timestamps_in_the_future(ds, now):
    limit = now + CLOCK_SKEW
    rows = [
        frame[frame[column] > limit].assign(table=table, column=column)
        for table, frame, column in (
            ("users", ds.users, "created_at"),
            ("products", ds.products, "created_at"),
            ("products", ds.products, "updated_at"),
            ("orders", ds.orders, "created_at"),
        )
    ]
    checked = len(ds.users) + 2 * len(ds.products) + len(ds.orders)
    return checked, pd.concat(rows, ignore_index=True)


@check(Dimension.TIMELINESS)
def order_is_not_older_than_its_products(ds, now):
    lines = ds.order_items.merge(
        ds.orders[["id", "created_at"]].rename(columns={"id": "order_id"}), on="order_id"
    ).merge(
        ds.products[["id", "created_at"]].rename(
            columns={"id": "product_id", "created_at": "product_created_at"}
        ),
        on="product_id",
    )
    return len(lines), lines[lines["created_at"] < lines["product_created_at"]]


@check(Dimension.TIMELINESS)
def latest_order_is_recent(ds, now):
    """Freshness: the newest order is younger than MAX_DATA_AGE (a stale feed fails)."""
    if ds.orders.empty:
        return 1, pd.DataFrame({"problem": ["no orders at all"]})
    latest = ds.orders["created_at"].max()
    stale = pd.DataFrame({"latest_order": [latest], "age": [now - latest]})
    return 1, stale[stale["age"] > MAX_DATA_AGE]


# --- Consistency: related records and fields agree with each other --------------------


@check(Dimension.CONSISTENCY)
def order_lines_reference_existing_rows(ds, now):
    i = ds.order_items
    orphan = ~i["order_id"].isin(ds.orders["id"]) | ~i["product_id"].isin(ds.products["id"])
    return len(i), i[orphan]


@check(Dimension.CONSISTENCY)
def orders_reference_existing_users(ds, now):
    return len(ds.orders), ds.orders[~ds.orders["user_id"].isin(ds.users["id"])]


@check(Dimension.CONSISTENCY)
def product_updated_not_before_created(ds, now):
    p = ds.products
    return len(p), p[p["updated_at"] < p["created_at"]]


# --- Uniqueness: keys identify exactly one record --------------------------------------

KEYS = {
    "users": [["id"], ["username"]],
    "products": [["id"], ["sku"]],
    "orders": [["id"]],
    "order_items": [["order_id", "product_id"]],
}


@check(Dimension.UNIQUENESS)
def keys_are_unique(ds, now):
    duplicates, checked = [], 0
    for table, keys in KEYS.items():
        frame = getattr(ds, table)
        for key in keys:
            checked += len(frame)
            dupes = frame[frame.duplicated(subset=key, keep=False)]
            duplicates.append(dupes.assign(table=table, key=",".join(key)))
    return checked, pd.concat(duplicates, ignore_index=True)


def run_all(ds: ShopDataset, now: pd.Timestamp) -> list[CheckResult]:
    return [run(ds, now) for run in CHECKS]
