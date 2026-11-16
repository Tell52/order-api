# Order API

A small local order service with explicit request validation and API testing evidence.
It demonstrates boundary tests, invalid-input tests, server-calculated prices, and SQLite persistence.
The catalog and all example orders are synthetic. Amounts are integers in whole THB.

| Product ID | Name | Unit price (THB) |
| --- | --- | ---: |
| 1 | Notebook | 50 |
| 2 | Desk lamp | 350 |
| 3 | Water bottle | 120 |

## Quick start

Python 3.13 is used in CI; locally tested with Python 3.13.5 on Windows 11.
Run commands from this repository's root. No database server or credentials are needed.

Windows PowerShell (activation is not required):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn order_api.app:create_app --factory --host 127.0.0.1 --port 8000
```

POSIX shell:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn order_api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Open [interactive API documentation](http://127.0.0.1:8000/docs) while the server is running.
Stop with Ctrl+C. The default database is `data/orders.sqlite3`; restarting keeps existing orders.
Set a different path **before** starting the server:

```powershell
$env:ORDER_DB_PATH = 'data/practice.sqlite3'
```

```sh
export ORDER_DB_PATH=data/practice.sqlite3
```

Use file-backed databases, not `:memory:`. Relative paths are resolved from the current working directory.

## Run tests and a live demonstration

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/smoke_test.py
```

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/smoke_test.py
```

CI runs the same `python -m pytest -q` command after installing the pinned dependencies.
The 45 TestClient tests run in-process, using temporary databases. The separate smoke command starts
a real Uvicorn server bound only to localhost, sends HTTP requests, checks responses, writes
`samples/live-smoke.json`, stops the server, and removes its temporary database. It does not touch
the learner's normal database. The operating system chooses an available local port.

## Requests and responses

Run these in a second terminal while the server is running. The returned order ID may be greater
than 1 when reusing a database.

PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
$order = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/orders -ContentType 'application/json' -Body '{"product_id":2,"quantity":3}'
$order | ConvertTo-Json
Invoke-RestMethod "http://127.0.0.1:8000/orders/$($order.order_id)"
# curl.exe displays error response bodies on Windows without Invoke-RestMethod throwing.
'{"product_id":2,"quantity":0}' | curl.exe -i -X POST http://127.0.0.1:8000/orders -H 'Content-Type: application/json' --data-binary '@-'
curl.exe -i http://127.0.0.1:8000/orders/999999
```

POSIX shell:

```sh
curl -i http://127.0.0.1:8000/health
order=$(curl -sS -X POST http://127.0.0.1:8000/orders -H 'Content-Type: application/json' -d '{"product_id":2,"quantity":3}')
printf '%s\n' "$order"
id=$(printf '%s' "$order" | .venv/bin/python -c 'import json,sys; print(json.load(sys.stdin)["order_id"])')
curl -i "http://127.0.0.1:8000/orders/$id"
curl -i -X POST http://127.0.0.1:8000/orders -H 'Content-Type: application/json' -d '{"product_id":2,"quantity":0}'
curl -i http://127.0.0.1:8000/orders/999999
```

Successful POST, HTTP 201 (fresh database):

```json
{"order_id":1,"product_id":2,"quantity":3,"unit_price":350,"total_amount":1050}
```

Unknown positive product or order IDs return HTTP 404, with `{"detail":"Product not found"}`
or `{"detail":"Order not found"}`. Request validation errors return HTTP **422**, with a
`detail` array describing the invalid fields. The observed examples are in [the smoke transcript](samples/live-smoke.json).

## Contract and interpretation

- `product_id` is a strict positive JSON integer referring to the catalog.
- `quantity` is a strict JSON integer from 1 through 10 inclusive.
- Strings, booleans, decimal values (including `2.0`), nulls, missing required fields, malformed JSON,
  and unexpected fields are rejected with 422. Clients cannot supply a price or total.
- A valid but unknown product ID returns 404. Neither rejection creates an order.
- The server retrieves the catalog price, calculates `unit_price * quantity`, commits the order,
  and returns the generated ID plus the four order fields.
- Order lookup accepts a positive integer path ID; invalid paths return 422 and unknown positive IDs return 404.
- Orders survive application restarts. There are no update/delete endpoints.

See [requirements](docs/requirements.md), [exact test cases](docs/test-cases.md),
[technical notes](docs/technical.md), and [actual execution evidence](docs/test-evidence.md).

## Limits and development note

This is a local learning service. It has no authentication, payments, inventory, concurrency load
benchmarks, migrations, or deployment configuration. Health reports process responsiveness, not
a database readiness probe. Duplicate POST requests create separate orders; no idempotency key
is implemented. Do not expose this unauthenticated service publicly.
No coverage percentage or production performance is claimed.

The initial implementation, tests, and documentation were prepared with coding assistance and
executed locally. Learner changes and understanding should be demonstrated separately.
