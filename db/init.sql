-- Schema and seed data for the shop database.
-- Runs once, when the Postgres container starts with an empty data volume.

CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('admin', 'viewer')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE products (
    id         SERIAL PRIMARY KEY,
    sku        TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    price      NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    stock      INTEGER NOT NULL CHECK (stock >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users (id),
    status     TEXT NOT NULL DEFAULT 'created' CHECK (status IN ('created', 'paid', 'cancelled')),
    total      NUMERIC(12, 2) NOT NULL CHECK (total >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE order_items (
    order_id   INTEGER NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products (id),
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    PRIMARY KEY (order_id, product_id)
);

INSERT INTO products (sku, name, price, stock) VALUES
    ('BAG-001', 'Backpack',            29.99, 50),
    ('LGT-001', 'Bike Light',           9.99, 120),
    ('TSH-001', 'Bolt T-Shirt',        15.99, 80),
    ('JKT-001', 'Fleece Jacket',       49.99, 25),
    ('ONS-001', 'Onesie',               7.99, 200),
    ('TSH-002', 'Red T-Shirt',         15.99, 60),
    ('CAP-001', 'Baseball Cap',        12.50, 0),
    ('BTL-001', 'Water Bottle',         5.00, 300);
