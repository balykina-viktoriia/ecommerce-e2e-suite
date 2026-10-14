"""Test the tests: a check that never fails proves nothing. Each case breaks the clean
dataset in one specific way and expects the matching check to flag exactly those rows."""

from datetime import timedelta
from decimal import Decimal

import pandas as pd
import pytest

from tests.data_quality import checks
from tests.data_quality.checks import CHECKS, Dimension, run_all


def set_value(table: str, row: int, **values):
    """Breaker: overwrite cells of one row. Callables get (dataset, now) and return the value."""

    def breaker(ds, now):
        frame = getattr(ds, table).copy()
        for column, value in values.items():
            frame[column] = frame[column].astype(object)
            frame.at[row, column] = value(ds, now) if callable(value) else value
        return ds.with_changes(**{table: frame})

    return breaker


def drop_lines_of_order(order_id: int):
    def breaker(ds, now):
        return ds.with_changes(order_items=ds.order_items[ds.order_items["order_id"] != order_id])

    return breaker


def age_all_orders(by: timedelta):
    def breaker(ds, now):
        return ds.with_changes(orders=ds.orders.assign(created_at=now - by))

    return breaker


def duplicate_first_line(ds, now):
    return ds.with_changes(order_items=pd.concat([ds.order_items, ds.order_items.head(1)]))


DAY = timedelta(days=1)

# (check, breaker, rows the check should flag)
DEFECTS = [
    # validity
    (checks.order_status_is_known, set_value("orders", 0, status="shipped"), 1),
    (checks.user_role_is_known, set_value("users", 1, role="root"), 1),
    (checks.sku_has_valid_format, set_value("products", 0, sku="bag 001"), 1),
    (checks.product_price_and_stock_in_range, set_value("products", 1, price=Decimal("-1")), 1),
    (checks.product_price_and_stock_in_range, set_value("products", 1, price=Decimal("9.999")), 1),
    (checks.product_price_and_stock_in_range, set_value("products", 2, stock=-3), 1),
    (checks.order_line_quantity_and_price_in_range, set_value("order_items", 0, quantity=0), 1),
    # completeness
    (checks.required_fields_are_filled, set_value("products", 0, price=None), 1),
    (checks.required_fields_are_filled, set_value("products", 2, name="  "), 1),
    (checks.required_fields_are_filled, set_value("orders", 1, user_id=None), 1),
    (checks.every_order_has_lines, drop_lines_of_order(101), 1),
    # accuracy
    (checks.order_total_equals_sum_of_lines, set_value("orders", 0, total=Decimal("69.98")), 1),
    # timeliness
    (
        checks.no_timestamps_in_the_future,
        set_value("orders", 0, created_at=lambda ds, now: now + DAY),
        1,
    ),
    (
        checks.order_is_not_older_than_its_products,
        set_value("products", 0, created_at=lambda ds, now: now),
        1,
    ),
    (checks.latest_order_is_recent, age_all_orders(3 * DAY), 1),
    # consistency
    (checks.order_lines_reference_existing_rows, set_value("order_items", 2, product_id=999), 1),
    (checks.orders_reference_existing_users, set_value("orders", 1, user_id=42), 1),
    (
        checks.product_updated_not_before_created,
        set_value("products", 1, updated_at=lambda ds, now: ds.products.at[1, "created_at"] - DAY),
        1,
    ),
    # uniqueness: both copies of a duplicate are reported
    (checks.keys_are_unique, set_value("products", 1, sku="BAG-001"), 2),
    (checks.keys_are_unique, duplicate_first_line, 2),
]

# Defects that, by nature, also show up in a second dimension. Anything else is a bug in a
# check: one broken value should not light up the whole report.
ALLOWED_SPILLOVER = {
    # A zero quantity also changes what the order total should be.
    "order_line_quantity_and_price_in_range": {Dimension.ACCURACY},
    # An order with no user_id also points at a user that does not exist.
    "required_fields_are_filled": {Dimension.CONSISTENCY},
    # A product created "now" is also created after it was last updated.
    "order_is_not_older_than_its_products": {Dimension.CONSISTENCY},
    # A duplicated order line is counted twice in the computed total.
    "keys_are_unique": {Dimension.ACCURACY},
}

CASES = [
    pytest.param(check, breaker, expected, id=f"{check.__name__}-{i}")
    for i, (check, breaker, expected) in enumerate(DEFECTS)
]


def test_clean_dataset_passes_every_check(clean_dataset, now):
    failures = [r.describe() for r in run_all(clean_dataset, now) if not r.passed]

    assert not failures, "\n\n".join(failures)


def test_every_dimension_has_checks(clean_dataset, now):
    assert {r.dimension for r in run_all(clean_dataset, now)} == set(Dimension)


def test_every_check_has_a_defect_case():
    assert {c.__name__ for c in CHECKS} == {check.__name__ for check, _, _ in DEFECTS}


@pytest.mark.parametrize(("check", "breaker", "expected"), CASES)
def test_check_flags_injected_defect(clean_dataset, now, check, breaker, expected):
    result = check(breaker(clean_dataset, now), now)

    assert not result.passed
    assert len(result.failed) == expected, result.describe()


@pytest.mark.parametrize(("check", "breaker", "expected"), CASES)
def test_defect_trips_only_its_own_dimension(clean_dataset, now, check, breaker, expected):
    own = check(clean_dataset, now).dimension

    results = run_all(breaker(clean_dataset, now), now)

    tripped = {r.dimension for r in results if not r.passed}
    assert tripped <= {own} | ALLOWED_SPILLOVER.get(check.__name__, set())
