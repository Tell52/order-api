import sqlite3
from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from order_api.app import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "orders.sqlite3")) as test_client:
        yield test_client


def stored_count(client):
    with closing(sqlite3.connect(client.app.state.database_path)) as connection:
        return connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("product_id,quantity,unit_price", [
    (1, 1, 50), (1, 10, 50), (2, 3, 350), (3, 2, 120),
])
def test_create_and_read(client, product_id, quantity, unit_price):
    response = client.post("/orders", json={"product_id": product_id, "quantity": quantity})
    assert response.status_code == 201
    assert response.json() == {
        "order_id": 1, "product_id": product_id, "quantity": quantity,
        "unit_price": unit_price, "total_amount": quantity * unit_price,
    }
    read = client.get("/orders/1")
    assert read.status_code == 200
    assert read.json() == response.json()
    assert stored_count(client) == 1


INVALID_REQUESTS = [
    ("quantity-zero", {"product_id": 1, "quantity": 0}),
    ("quantity-eleven", {"product_id": 1, "quantity": 11}),
    ("quantity-negative", {"product_id": 1, "quantity": -1}),
    ("quantity-string", {"product_id": 1, "quantity": "2"}),
    ("quantity-true", {"product_id": 1, "quantity": True}),
    ("quantity-false", {"product_id": 1, "quantity": False}),
    ("quantity-fraction", {"product_id": 1, "quantity": 1.5}),
    ("quantity-integral-float", {"product_id": 1, "quantity": 2.0}),
    ("quantity-null", {"product_id": 1, "quantity": None}),
    ("product-zero", {"product_id": 0, "quantity": 1}),
    ("product-negative", {"product_id": -1, "quantity": 1}),
    ("product-string", {"product_id": "1", "quantity": 1}),
    ("product-true", {"product_id": True, "quantity": 1}),
    ("product-false", {"product_id": False, "quantity": 1}),
    ("product-fraction", {"product_id": 1.5, "quantity": 1}),
    ("product-integral-float", {"product_id": 1.0, "quantity": 1}),
    ("product-null", {"product_id": None, "quantity": 1}),
    ("missing-quantity", {"product_id": 1}),
    ("missing-product", {"quantity": 1}),
    ("missing-both", {}),
    ("price-tampering", {"product_id": 1, "quantity": 1, "price": 1}),
    ("unit-price-tampering", {"product_id": 1, "quantity": 1, "unit_price": 1}),
    ("total-tampering", {"product_id": 1, "quantity": 1, "total_amount": 1}),
    ("total-alias-tampering", {"product_id": 1, "quantity": 1, "total": 1}),
    ("other-extra-field", {"product_id": 1, "quantity": 1, "note": "hello"}),
    ("array-body", [1, 2]),
    ("string-body", "hello"),
]


@pytest.mark.parametrize("case,payload", INVALID_REQUESTS, ids=[row[0] for row in INVALID_REQUESTS])
def test_invalid_request_leaves_orders_unchanged(client, case, payload):
    assert client.post("/orders", json={"product_id": 2, "quantity": 1}).status_code == 201
    before = stored_count(client)
    response = client.post("/orders", json=payload)
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert stored_count(client) == before
    assert client.get("/orders/1").json()["total_amount"] == 350


@pytest.mark.parametrize("body", ['{"product_id":1,', '', 'null'])
def test_malformed_or_empty_body(client, body):
    response = client.post("/orders", content=body, headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert stored_count(client) == 0


@pytest.mark.parametrize("product_id", [999, 2**80])
def test_unknown_product(client, product_id):
    response = client.post("/orders", json={"product_id": product_id, "quantity": 1})
    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}
    assert stored_count(client) == 0


@pytest.mark.parametrize("order_id", [999, 2**80])
def test_unknown_order(client, order_id):
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Order not found"}
    assert stored_count(client) == 0


@pytest.mark.parametrize("order_id", ["0", "-1", "hello", "1.5"])
def test_invalid_order_path(client, order_id):
    assert client.get(f"/orders/{order_id}").status_code == 422
    assert stored_count(client) == 0


def test_persistence_after_reopen(tmp_path):
    path = tmp_path / "persistent.sqlite3"
    with TestClient(create_app(path)) as first:
        response = first.post("/orders", json={"product_id": 3, "quantity": 10})
        assert response.status_code == 201
        expected = response.json()
    with TestClient(create_app(path)) as reopened:
        assert reopened.get("/orders/1").json() == expected
        second = reopened.post("/orders", json={"product_id": 1, "quantity": 1})
        assert second.status_code == 201
        assert second.json()["order_id"] == 2
        assert stored_count(reopened) == 2


def test_environment_database_path(tmp_path, monkeypatch):
    path = tmp_path / "nested" / "configured.sqlite3"
    monkeypatch.setenv("ORDER_DB_PATH", str(path))
    with TestClient(create_app()) as client:
        assert client.post("/orders", json={"product_id": 1, "quantity": 1}).status_code == 201
    assert path.is_file()
