import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pandas as pd
import pytest

from tests.api.client import require_shop_api
from tests.api.data import ProductPayload
from tests.data_quality.dataset import ShopDataset
from tests.settings import DATABASE_URL

SEED_PRODUCTS = 6
SEED_ORDERS = 60


@pytest.fixture(scope="session")
def now() -> pd.Timestamp:
    return pd.Timestamp(datetime.now(UTC))


@pytest.fixture
def clean_dataset(now) -> ShopDataset:
    """A small, hand-made, correct dataset. Defect tests break one thing at a time in it."""
    t = now - timedelta(hours=1)
    users = pd.DataFrame(
        {
            "id": [1, 2],
            "username": ["admin", "viewer"],
            "role": ["admin", "viewer"],
            "created_at": [t - timedelta(days=30)] * 2,
        }
    )
    products = pd.DataFrame(
        {
            "id": [10, 11, 12],
            "sku": ["BAG-001", "LGT-001", "CAP-001"],
            "name": ["Backpack", "Bike Light", "Cap"],
            "price": [Decimal("29.99"), Decimal("9.99"), Decimal("12.50")],
            "stock": [50, 0, 7],
            "created_at": [t - timedelta(days=10)] * 3,
            "updated_at": [t - timedelta(days=1)] * 3,
        }
    )
    orders = pd.DataFrame(
        {
            "id": [100, 101],
            "user_id": [2, 1],
            "status": ["created", "paid"],
            "total": [Decimal("69.97"), Decimal("12.50")],
            "created_at": [t, t + timedelta(minutes=5)],
        }
    )
    order_items = pd.DataFrame(
        {
            "order_id": [100, 100, 101],
            "product_id": [10, 11, 12],
            "quantity": [2, 1, 1],
            "unit_price": [Decimal("29.99"), Decimal("9.99"), Decimal("12.50")],
        }
    )
    return ShopDataset(users, products, orders, order_items)


@pytest.fixture(scope="session")
def seeded_orders(admin, viewer) -> int:
    """Create a realistic batch of orders through the API, so the dataset is worth checking.

    Seeded random generator: the same run always produces the same shape of data.
    """
    require_shop_api()
    rng = random.Random(42)
    products = []
    for _ in range(SEED_PRODUCTS):
        price = Decimal(rng.randint(100, 9999)) / 100
        payload = ProductPayload.new(name="Seeded item", price=f"{price:.2f}", stock=10_000)
        products.append(admin.post("/products", json=payload.to_json()).json())
    for _ in range(SEED_ORDERS):
        client = rng.choice([admin, viewer])
        lines = rng.sample(products, k=rng.randint(1, 3))
        items = [{"product_id": p["id"], "quantity": rng.randint(1, 5)} for p in lines]
        response = client.post("/orders", json={"items": items})
        assert response.status_code == 201, response.text
    return SEED_ORDERS


@pytest.fixture(scope="session")
def shop_dataset(seeded_orders) -> ShopDataset:
    return ShopDataset.from_database(DATABASE_URL)
