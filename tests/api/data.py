import uuid
from dataclasses import asdict, dataclass


def unique_sku() -> str:
    """SKUs are unique in the DB, so every test gets its own to stay independent in parallel."""
    return f"T-{uuid.uuid4().hex[:12].upper()}"


@dataclass
class ProductPayload:
    sku: str
    name: str = "Test Product"
    price: str = "19.99"
    stock: int = 10

    @classmethod
    def new(cls, **overrides) -> "ProductPayload":
        return cls(sku=unique_sku(), **overrides)

    def to_json(self) -> dict:
        return asdict(self)
