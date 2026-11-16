"""HTTP contract, a fixed synthetic catalog, and the application factory."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path as PathParameter
from pydantic import BaseModel, ConfigDict, Field

from order_api.database import create_order, get_order, initialize_database


# Whole THB only. These are synthetic products, not a live price feed.
CATALOG = {
    1: {"name": "Notebook", "unit_price": 50},
    2: {"name": "Desk lamp", "unit_price": 350},
    3: {"name": "Water bottle", "unit_price": 120},
}


class OrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: Annotated[int, Field(strict=True, gt=0)]
    quantity: Annotated[int, Field(strict=True, ge=1, le=10)]


class OrderResponse(BaseModel):
    order_id: int
    product_id: int
    quantity: int
    unit_price: int
    total_amount: int


def create_app(database_path: str | Path | None = None) -> FastAPI:
    """Use a file-backed database; each test supplies its own temporary file."""
    db_path = Path(database_path or os.getenv("ORDER_DB_PATH", "data/orders.sqlite3"))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize_database(db_path)
        yield

    app = FastAPI(title="Order API", lifespan=lifespan)
    app.state.database_path = db_path

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/orders", status_code=201, response_model=OrderResponse)
    def post_order(request: OrderRequest):
        product = CATALOG.get(request.product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return create_order(db_path, request.product_id, request.quantity, product["unit_price"])

    @app.get("/orders/{order_id}", response_model=OrderResponse)
    def read_order(order_id: Annotated[int, PathParameter(gt=0)]):
        # SQLite INTEGER is signed 64-bit. Larger positive IDs cannot exist.
        order = None if order_id > 2**63 - 1 else get_order(db_path, order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    return app
