"""JSON Schemas for API responses. additionalProperties is false, so a new or renamed
field fails the contract test instead of slipping through."""

MONEY = {"type": "string", "pattern": r"^\d+\.\d{2}$"}
TIMESTAMP = {"type": "string", "format": "date-time"}

PRODUCT = {
    "type": "object",
    "required": ["id", "sku", "name", "price", "stock", "created_at", "updated_at"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "sku": {"type": "string", "pattern": r"^[A-Z0-9-]{3,32}$"},
        "name": {"type": "string", "minLength": 1, "maxLength": 120},
        "price": MONEY,
        "stock": {"type": "integer", "minimum": 0},
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    },
}

PRODUCT_LIST = {"type": "array", "items": PRODUCT}

ORDER = {
    "type": "object",
    "required": ["id", "user_id", "status", "total", "created_at", "items"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "user_id": {"type": "integer", "minimum": 1},
        "status": {"enum": ["created", "paid", "cancelled"]},
        "total": MONEY,
        "created_at": TIMESTAMP,
        "items": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["product_id", "quantity", "unit_price"],
                "additionalProperties": False,
                "properties": {
                    "product_id": {"type": "integer"},
                    "quantity": {"type": "integer", "minimum": 1},
                    "unit_price": MONEY,
                },
            },
        },
    },
}

ERROR = {
    "type": "object",
    "required": ["detail"],
    "properties": {"detail": {"type": "string"}},
}

VALIDATION_ERROR = {
    "type": "object",
    "required": ["detail"],
    "properties": {
        "detail": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "object", "required": ["loc", "msg", "type"]},
        }
    },
}
