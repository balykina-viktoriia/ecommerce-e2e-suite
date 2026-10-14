import hashlib
import hmac
import os
import secrets
import time

import jwt
from fastapi import Depends, HTTPException, Request, status
from psycopg import Connection

from shop.db import get_conn

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 60 * 60
COOKIE_NAME = "access_token"
PBKDF2_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    salt, expected = password_hash.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS)
    return hmac.compare_digest(digest.hex(), expected)


def create_token(user_id: int, role: str) -> str:
    now = int(time.time())
    payload = {"sub": str(user_id), "role": role, "iat": now, "exp": now + TOKEN_TTL_SECONDS}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _token_from_request(request: Request) -> str | None:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header.removeprefix("Bearer ")
    return request.cookies.get(COOKIE_NAME)


def current_user(request: Request, conn: Connection = Depends(get_conn)) -> dict:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = _token_from_request(request)
    if token is None:
        raise unauthorized
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise unauthorized from None
    user = conn.execute(
        "SELECT id, username, role FROM users WHERE id = %s", (int(payload["sub"]),)
    ).fetchone()
    if user is None:
        raise unauthorized
    return user


def require_admin(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user
