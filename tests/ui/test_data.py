from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum, StrEnum

DEFAULT_PASSWORD = "secret_sauce"
TAX_RATE = Decimal("0.08")


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


class SortOption(StrEnum):
    """Values of the sort dropdown on the inventory page."""

    NAME_A_TO_Z = "az"
    NAME_Z_TO_A = "za"
    PRICE_LOW_TO_HIGH = "lohi"
    PRICE_HIGH_TO_LOW = "hilo"


class ErrorMessage(StrEnum):
    USERNAME_REQUIRED = "Epic sadface: Username is required"
    PASSWORD_REQUIRED = "Epic sadface: Password is required"
    WRONG_CREDENTIALS = "Epic sadface: Username and password do not match any user in this service"
    LOCKED_OUT = "Epic sadface: Sorry, this user has been locked out."
    FIRST_NAME_REQUIRED = "Error: First Name is required"
    LAST_NAME_REQUIRED = "Error: Last Name is required"
    POSTAL_CODE_REQUIRED = "Error: Postal Code is required"


class SuccessMessage(StrEnum):
    CHECKOUT_COMPLETE = "Thank you for your order!"
