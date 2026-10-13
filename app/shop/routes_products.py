from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from shop.db import get_conn
from shop.schemas import ProductIn, ProductOut
from shop.security import current_user, require_admin

router = APIRouter(prefix="/products", tags=["products"])

COLUMNS = "id, sku, name, price, stock, created_at, updated_at"


def _not_found(product_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {product_id} not found"
    )


def _sku_conflict(sku: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail=f"Product with sku {sku} already exists"
    )


@router.get("", response_model=list[ProductOut], dependencies=[Depends(current_user)])
def list_products(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_conn),
):
    return conn.execute(
        f"SELECT {COLUMNS} FROM products ORDER BY id LIMIT %s OFFSET %s", (limit, offset)
    ).fetchall()


@router.get("/{product_id}", response_model=ProductOut, dependencies=[Depends(current_user)])
def get_product(product_id: int, conn: Connection = Depends(get_conn)):
    product = conn.execute(
        f"SELECT {COLUMNS} FROM products WHERE id = %s", (product_id,)
    ).fetchone()
    if product is None:
        raise _not_found(product_id)
    return product


@router.post(
    "",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_product(body: ProductIn, response: Response, conn: Connection = Depends(get_conn)):
    try:
        product = conn.execute(
            f"INSERT INTO products (sku, name, price, stock) VALUES (%s, %s, %s, %s) "
            f"RETURNING {COLUMNS}",
            (body.sku, body.name, body.price, body.stock),
        ).fetchone()
    except UniqueViolation:
        raise _sku_conflict(body.sku) from None
    response.headers["Location"] = f"/products/{product['id']}"
    return product


@router.put("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_admin)])
def update_product(product_id: int, body: ProductIn, conn: Connection = Depends(get_conn)):
    try:
        product = conn.execute(
            f"UPDATE products SET sku = %s, name = %s, price = %s, stock = %s, updated_at = now() "
            f"WHERE id = %s RETURNING {COLUMNS}",
            (body.sku, body.name, body.price, body.stock, product_id),
        ).fetchone()
    except UniqueViolation:
        raise _sku_conflict(body.sku) from None
    if product is None:
        raise _not_found(product_id)
    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_product(product_id: int, conn: Connection = Depends(get_conn)):
    try:
        deleted = conn.execute(
            "DELETE FROM products WHERE id = %s RETURNING id", (product_id,)
        ).fetchone()
    except ForeignKeyViolation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product {product_id} is used in orders and cannot be deleted",
        ) from None
    if deleted is None:
        raise _not_found(product_id)
