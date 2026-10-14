from decimal import Decimal

from playwright.sync_api import Page


def parse_money(text: str) -> Decimal:
    """'Item total: $39.98' or '$29.99' -> Decimal('39.98')."""
    return Decimal(text.rsplit("$", 1)[1])


class BasePage:
    def __init__(self, page: Page):
        self.page = page
