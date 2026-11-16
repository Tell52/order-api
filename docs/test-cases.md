# Test cases

Each pytest parameter below is an independently collected test with a fresh temporary database.
The input column contains literal JSON or an exact HTTP path. Invalid-request cases first create
`{"product_id":2,"quantity":1}` and verify its unchanged total of 350 THB after the rejection.

| Requirement | Exact input/action | Expected status | Response or database effect | Reason | Automated test |
| --- | --- | ---: | --- | --- | --- |
| R01 | `GET /health` | 200 | Exact response {"status":"ok"}; no write | Service responds | `test_health` |
| R02, R05, R06 | `{"product_id":1,"quantity":1}; GET /orders/1` | 201, 200 | Exact fields: order_id=1, product_id=1, quantity=1, unit_price=50, total_amount=50; count=1; GET equals POST | Inclusive quantity boundary | `test_create_and_read[1-1-50]` |
| R02, R05, R06 | `{"product_id":1,"quantity":10}; GET /orders/1` | 201, 200 | Exact fields: order_id=1, product_id=1, quantity=10, unit_price=50, total_amount=500; count=1; GET equals POST | Inclusive quantity boundary | `test_create_and_read[1-10-50]` |
| R02, R05, R06 | `{"product_id":2,"quantity":3}; GET /orders/1` | 201, 200 | Exact fields: order_id=1, product_id=2, quantity=3, unit_price=350, total_amount=1050; count=1; GET equals POST | Every catalog price and arithmetic | `test_create_and_read[2-3-350]` |
| R02, R05, R06 | `{"product_id":3,"quantity":2}; GET /orders/1` | 201, 200 | Exact fields: order_id=1, product_id=3, quantity=2, unit_price=120, total_amount=240; count=1; GET equals POST | Every catalog price and arithmetic | `test_create_and_read[3-2-120]` |
| R02, R03, R07 | `{"product_id":1,"quantity":0}` | 422 | detail is an array; count stays 1; existing order total remains 350 | quantity zero | `test_invalid_request_leaves_orders_unchanged[quantity-zero]` |
| R02, R03, R07 | `{"product_id":1,"quantity":11}` | 422 | detail is an array; count stays 1; existing order total remains 350 | quantity eleven | `test_invalid_request_leaves_orders_unchanged[quantity-eleven]` |
| R02, R03, R07 | `{"product_id":1,"quantity":-1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | quantity negative | `test_invalid_request_leaves_orders_unchanged[quantity-negative]` |
| R02, R03, R07 | `{"product_id":1,"quantity":"2"}` | 422 | detail is an array; count stays 1; existing order total remains 350 | quantity string | `test_invalid_request_leaves_orders_unchanged[quantity-string]` |
| R02, R03, R07 | `{"product_id":1,"quantity":true}` | 422 | detail is an array; count stays 1; existing order total remains 350 | quantity true | `test_invalid_request_leaves_orders_unchanged[quantity-true]` |
| R02, R03, R07 | `{"product_id":1,"quantity":false}` | 422 | detail is an array; count stays 1; existing order total remains 350 | quantity false | `test_invalid_request_leaves_orders_unchanged[quantity-false]` |
| R02, R03, R07 | `{"product_id":1,"quantity":1.5}` | 422 | detail is an array; count stays 1; existing order total remains 350 | quantity fraction | `test_invalid_request_leaves_orders_unchanged[quantity-fraction]` |
| R02, R03, R07 | `{"product_id":1,"quantity":2.0}` | 422 | detail is an array; count stays 1; existing order total remains 350 | quantity integral float | `test_invalid_request_leaves_orders_unchanged[quantity-integral-float]` |
| R02, R03, R07 | `{"product_id":1,"quantity":null}` | 422 | detail is an array; count stays 1; existing order total remains 350 | quantity null | `test_invalid_request_leaves_orders_unchanged[quantity-null]` |
| R02, R03, R07 | `{"product_id":0,"quantity":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | product zero | `test_invalid_request_leaves_orders_unchanged[product-zero]` |
| R02, R03, R07 | `{"product_id":-1,"quantity":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | product negative | `test_invalid_request_leaves_orders_unchanged[product-negative]` |
| R02, R03, R07 | `{"product_id":"1","quantity":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | product string | `test_invalid_request_leaves_orders_unchanged[product-string]` |
| R02, R03, R07 | `{"product_id":true,"quantity":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | product true | `test_invalid_request_leaves_orders_unchanged[product-true]` |
| R02, R03, R07 | `{"product_id":false,"quantity":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | product false | `test_invalid_request_leaves_orders_unchanged[product-false]` |
| R02, R03, R07 | `{"product_id":1.5,"quantity":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | product fraction | `test_invalid_request_leaves_orders_unchanged[product-fraction]` |
| R02, R03, R07 | `{"product_id":1.0,"quantity":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | product integral float | `test_invalid_request_leaves_orders_unchanged[product-integral-float]` |
| R02, R03, R07 | `{"product_id":null,"quantity":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | product null | `test_invalid_request_leaves_orders_unchanged[product-null]` |
| R02, R03, R07 | `{"product_id":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | missing quantity | `test_invalid_request_leaves_orders_unchanged[missing-quantity]` |
| R02, R03, R07 | `{"quantity":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | missing product | `test_invalid_request_leaves_orders_unchanged[missing-product]` |
| R02, R03, R07 | `{}` | 422 | detail is an array; count stays 1; existing order total remains 350 | missing both | `test_invalid_request_leaves_orders_unchanged[missing-both]` |
| R02, R03, R07 | `{"product_id":1,"quantity":1,"price":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | price tampering | `test_invalid_request_leaves_orders_unchanged[price-tampering]` |
| R02, R03, R07 | `{"product_id":1,"quantity":1,"unit_price":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | unit price tampering | `test_invalid_request_leaves_orders_unchanged[unit-price-tampering]` |
| R02, R03, R07 | `{"product_id":1,"quantity":1,"total_amount":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | total tampering | `test_invalid_request_leaves_orders_unchanged[total-tampering]` |
| R02, R03, R07 | `{"product_id":1,"quantity":1,"total":1}` | 422 | detail is an array; count stays 1; existing order total remains 350 | total alias tampering | `test_invalid_request_leaves_orders_unchanged[total-alias-tampering]` |
| R02, R03, R07 | `{"product_id":1,"quantity":1,"note":"hello"}` | 422 | detail is an array; count stays 1; existing order total remains 350 | other extra field | `test_invalid_request_leaves_orders_unchanged[other-extra-field]` |
| R02, R03, R07 | `[1,2]` | 422 | detail is an array; count stays 1; existing order total remains 350 | array body | `test_invalid_request_leaves_orders_unchanged[array-body]` |
| R02, R03, R07 | `"hello"` | 422 | detail is an array; count stays 1; existing order total remains 350 | string body | `test_invalid_request_leaves_orders_unchanged[string-body]` |
| R03, R07 | `{"product_id":1,` | 422 | detail is an array; count stays 0 | Truncated JSON | `test_malformed_or_empty_body` |
| R03, R07 | `<empty body>` | 422 | detail is an array; count stays 0 | Absent JSON body | `test_malformed_or_empty_body` |
| R03, R07 | `null` | 422 | detail is an array; count stays 0 | JSON null instead of object | `test_malformed_or_empty_body` |
| R04, R07 | `{"product_id":999,"quantity":1}` | 404 | Exact detail: Product not found; count stays 0 | Unknown valid product ID | `test_unknown_product` |
| R04, R07 | `{"product_id":1208925819614629174706176,"quantity":1}` | 404 | Exact detail: Product not found; count stays 0 | Unknown valid product ID | `test_unknown_product` |
| R06 | `GET /orders/999` | 404 | Exact detail: Order not found; count stays 0 | Unknown positive ID, including value above SQLite integer capacity | `test_unknown_order` |
| R06 | `GET /orders/1208925819614629174706176` | 404 | Exact detail: Order not found; count stays 0 | Unknown positive ID, including value above SQLite integer capacity | `test_unknown_order` |
| R06 | `GET /orders/0` | 422 | No order is created; count stays 0 | Invalid path ID | `test_invalid_order_path` |
| R06 | `GET /orders/-1` | 422 | No order is created; count stays 0 | Invalid path ID | `test_invalid_order_path` |
| R06 | `GET /orders/hello` | 422 | No order is created; count stays 0 | Invalid path ID | `test_invalid_order_path` |
| R06 | `GET /orders/1.5` | 422 | No order is created; count stays 0 | Invalid path ID | `test_invalid_order_path` |
| R08 | `POST {"product_id":3,"quantity":10}; close; reopen same file; GET /orders/1; POST {"product_id":1,"quantity":1}` | 201, 200, 201 | First record remains equal (total=1200); second ID=2; count=2 | Persistence and new-ID continuity | `test_persistence_after_reopen` |
| R08 | `ORDER_DB_PATH=<temporary>/nested/configured.sqlite3; POST {"product_id":1,"quantity":1}` | 201 | Configured database file exists | Environment configuration and parent directory creation | `test_environment_database_path` |

For POST rows, send `Content-Type: application/json` to `/orders`.
Positive unknown IDs have valid syntax, so they return 404 rather than a schema-validation error.
Manual PowerShell and POSIX examples are in the README. Live HTTP smoke evidence is documented separately.
