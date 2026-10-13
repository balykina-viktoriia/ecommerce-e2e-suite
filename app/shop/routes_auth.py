from fastapi import APIRouter, Depends, HTTPException, Response, status
from psycopg import Connection

from shop.db import get_conn
from shop.schemas import LoginIn, TokenOut, UserOut
from shop.security import (
    COOKIE_NAME,
    TOKEN_TTL_SECONDS,
    create_token,
    current_user,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, response: Response, conn: Connection = Depends(get_conn)):
    user = conn.execute(
        "SELECT id, password_hash, role FROM users WHERE username = %s", (body.username,)
    ).fetchone()
    if user is None or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
        )
    token = create_token(user["id"], user["role"])
    response.set_cookie(
        COOKIE_NAME, token, max_age=TOKEN_TTL_SECONDS, httponly=True, samesite="lax"
    )
    return {"access_token": token, "role": user["role"]}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(current_user)):
    return user
