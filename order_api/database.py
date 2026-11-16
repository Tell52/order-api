"""Small SQLite operations; each operation commits and closes its connection."""

import sqlite3
from contextlib import closing
from pathlib import Path


def initialize_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL CHECK (product_id IN (1, 2, 3)),
                quantity INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 10),
                unit_price INTEGER NOT NULL CHECK (unit_price > 0),
                total_amount INTEGER NOT NULL CHECK (total_amount = quantity * unit_price)
            ) STRICT
        """)


def create_order(path: Path, product_id: int, quantity: int, unit_price: int) -> dict:
    total_amount = quantity * unit_price
    with closing(sqlite3.connect(path)) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO orders (product_id, quantity, unit_price, total_amount) VALUES (?, ?, ?, ?)",
            (product_id, quantity, unit_price, total_amount),
        )
        order_id = cursor.lastrowid
    return dict(order_id=order_id, product_id=product_id, quantity=quantity,
                unit_price=unit_price, total_amount=total_amount)


def get_order(path: Path, order_id: int) -> dict | None:
    with closing(sqlite3.connect(path)) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
    return dict(row) if row else None
