from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

# Money is serialized as a string ("29.99") so clients never lose precision to floats.
Price = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginIn(StrictModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    role: Literal["admin", "viewer"]


class UserOut(BaseModel):
    id: int
    username: str
    role: Literal["admin", "viewer"]


class ProductIn(StrictModel):
    sku: str = Field(pattern=r"^[A-Z0-9-]{3,32}$")
    name: str = Field(min_length=1, max_length=120)
    price: Price
    stock: int = Field(ge=0)


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    price: Decimal
    stock: int
    created_at: datetime
    updated_at: datetime


class OrderItemIn(StrictModel):
    product_id: int
    quantity: int = Field(ge=1)


class OrderIn(StrictModel):
    items: list[OrderItemIn] = Field(min_length=1)


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal


class OrderOut(BaseModel):
    id: int
    user_id: int
    status: Literal["created", "paid", "cancelled"]
    total: Decimal
    created_at: datetime
    items: list[OrderItemOut]
