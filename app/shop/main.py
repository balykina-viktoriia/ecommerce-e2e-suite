import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from shop import routes_auth, routes_orders, routes_products
from shop.db import pool
from shop.security import hash_password


def seed_users() -> None:
    """Create the two built-in accounts on first start. Passwords come from the environment."""
    accounts = [
        (os.environ["ADMIN_USERNAME"], os.environ["ADMIN_PASSWORD"], "admin"),
        (os.environ["VIEWER_USERNAME"], os.environ["VIEWER_PASSWORD"], "viewer"),
    ]
    with pool.connection() as conn:
        for username, password, role in accounts:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) "
                "ON CONFLICT (username) DO NOTHING",
                (username, hash_password(password), role),
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open(wait=True)
    seed_users()
    yield
    pool.close()


app = FastAPI(title="Shop API", version="1.0.0", lifespan=lifespan)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Echo the caller's X-Request-ID, or generate one, so a request can be traced in logs."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health", tags=["health"])
def health():
    with pool.connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


app.include_router(routes_auth.router)
app.include_router(routes_products.router)
app.include_router(routes_orders.router)
