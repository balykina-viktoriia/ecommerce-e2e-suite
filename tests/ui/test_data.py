from dataclasses import dataclass
from enum import IntEnum, StrEnum

DEFAULT_PASSWORD = "secret_sauce"


@dataclass(frozen=True)
class User:
    username: str
    password: str = DEFAULT_PASSWORD


@dataclass(frozen=True)
class Customer:
    first_name: str
    last_name: str
    zip_code: str


class Users:
    STANDARD = User("standard_user")
    LOCKED_OUT = User("locked_out_user")
    PROBLEM = User("problem_user")


class Customers:
    VALID = Customer(first_name="John", last_name="Doe", zip_code="12345")


class InventoryItem(IntEnum):
    """Position of the item on the inventory page (default sorting)."""

    BACKPACK = 0
    BIKE_LIGHT = 1
    BOLT_T_SHIRT = 2
    FLEECE_JACKET = 3
    ONESIE = 4
    RED_T_SHIRT = 5


class ErrorMessage(StrEnum):
    LAST_NAME_REQUIRED = "Error: Last Name is required"
    LOCKED_OUT = "Epic sadface: Sorry, this user has been locked out."


class SuccessMessage(StrEnum):
    CHECKOUT_COMPLETE = "Thank you for your order!"
