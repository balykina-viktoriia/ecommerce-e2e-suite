from fastapi import APIRouter, Depends, HTTPException, Response, status
from psycopg import Connection

from shop.db import get_conn
from shop.schemas import OrderIn, OrderOut
from shop.security import current_user

router = APIRouter(prefix="/orders", tags=["orders"])


def _load_orders(conn: Connection, where: str, params: tuple) -> list[dict]:
    orders = conn.execute(
        f"SELECT id, user_id, status, total, created_at FROM orders WHERE {where} ORDER BY id",
        params,
    ).fetchall()
    for order in orders:
        order["items"] = conn.execute(
            "SELECT product_id, quantity, unit_price FROM order_items "
            "WHERE order_id = %s ORDER BY product_id",
            (order["id"],),
        ).fetchall()
    return orders


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    body: OrderIn,
    response: Response,
    user: dict = Depends(current_user),
    conn: Connection = Depends(get_conn),
):
    product_ids = [item.product_id for item in body.items]
    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Each product may appear only once in an order",
        )

    # Lock the product rows so two concurrent orders cannot oversell the same stock.
    products = {
        row["id"]: row
        for row in conn.execute(
            "SELECT id, price, stock FROM products WHERE id = ANY(%s) ORDER BY id FOR UPDATE",
            (product_ids,),
        ).fetchall()
    }
    total = 0
    for item in body.items:
        product = products.get(item.product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found",
            )
        if product["stock"] < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Not enough stock for product {item.product_id}",
            )
        total += product["price"] * item.quantity

    order_id = conn.execute(
        "INSERT INTO orders (user_id, total) VALUES (%s, %s) RETURNING id", (user["id"], total)
    ).fetchone()["id"]
    for item in body.items:
        conn.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
            "VALUES (%s, %s, %s, %s)",
            (order_id, item.product_id, item.quantity, products[item.product_id]["price"]),
        )
        conn.execute(
            "UPDATE products SET stock = stock - %s, updated_at = now() WHERE id = %s",
            (item.quantity, item.product_id),
        )

    response.headers["Location"] = f"/orders/{order_id}"
    return _load_orders(conn, "id = %s", (order_id,))[0]


@router.get("", response_model=list[OrderOut])
def list_orders(user: dict = Depends(current_user), conn: Connection = Depends(get_conn)):
    if user["role"] == "admin":
        return _load_orders(conn, "TRUE", ())
    return _load_orders(conn, "user_id = %s", (user["id"],))


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int, user: dict = Depends(current_user), conn: Connection = Depends(get_conn)
):
    orders = _load_orders(conn, "id = %s", (order_id,))
    if not orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found"
        )
    order = orders[0]
    if user["role"] != "admin" and order["user_id"] != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own orders"
        )
    return order
