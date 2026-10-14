"""Run every data-quality check against a snapshot of the live shop database."""

from pathlib import Path

import pytest

from tests.data_quality.checks import CHECKS, CheckResult, run_all

REPORT = Path("reports/data_quality.md")


@pytest.fixture(scope="module")
def results(shop_dataset, now) -> dict[str, CheckResult]:
    results = run_all(shop_dataset, now)
    write_report(results, shop_dataset)
    return {r.name: r for r in results}


@pytest.mark.parametrize("name", [c.__name__ for c in CHECKS])
def test_shop_data_passes(results, name):
    result = results[name]

    assert result.passed, result.describe()


def test_dataset_is_big_enough_to_mean_something(shop_dataset, seeded_orders):
    assert len(shop_dataset.orders) >= seeded_orders
    assert len(shop_dataset.order_items) >= seeded_orders


def write_report(results: list[CheckResult], dataset) -> None:
    """A Markdown summary, uploaded by CI as an artifact next to the HTML test report."""
    lines = [
        "# Data quality report",
        "",
        f"Rows: {len(dataset.users)} users, {len(dataset.products)} products, "
        f"{len(dataset.orders)} orders, {len(dataset.order_items)} order lines.",
        "",
        "| Dimension | Check | Rows checked | Failed | Pass rate |",
        "|---|---|---:|---:|---:|",
    ]
    for r in results:
        status = "✅" if r.passed else "❌"
        lines.append(
            f"| {r.dimension} | {status} `{r.name}` | {r.checked} | {len(r.failed)} "
            f"| {r.pass_rate:.1%} |"
        )
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
