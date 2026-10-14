"""Where the shop app runs and which accounts to use. Defaults match .env.example."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://shop:shop@localhost:5433/shop")

ADMIN = Credentials(os.getenv("ADMIN_USERNAME", "admin"), os.getenv("ADMIN_PASSWORD", "admin-pass"))
VIEWER = Credentials(
    os.getenv("VIEWER_USERNAME", "viewer"), os.getenv("VIEWER_PASSWORD", "viewer-pass")
)
