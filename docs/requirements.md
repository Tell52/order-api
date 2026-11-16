# Requirements

All prices and records in this exercise are synthetic.

| ID | Requirement |
| --- | --- |
| R01 | GET `/health` returns 200 and exactly `{"status":"ok"}`. |
| R02 | POST `/orders` accepts only `product_id` and `quantity`, both required. Product ID is a strict positive JSON integer; quantity is a strict JSON integer between 1 and 10 inclusive. No string, boolean, float, or null coercion. |
| R03 | Request schema violations and malformed/empty JSON return 422 with a `detail` array. Extra fields, including price/total attempts, are forbidden. |
| R04 | A well-formed unknown product ID returns 404 and `{"detail":"Product not found"}`. |
| R05 | A valid POST uses the fixed catalog price and integer multiplication, commits one order, and returns 201 with generated `order_id`, `product_id`, `quantity`, `unit_price`, and `total_amount`. |
| R06 | GET `/orders/{order_id}` returns the exact stored order with 200. Unknown positive IDs return 404 and `{"detail":"Order not found"}`. Invalid nonpositive/noninteger paths return 422. |
| R07 | Rejected POST requests do not create or change orders. |
| R08 | A configured file database keeps orders after closing and reopening the application. Subsequent orders receive new IDs. `ORDER_DB_PATH` configures the file; tests may pass a path to `create_app`. |

The fixed catalog is documented in the README. An identical repeated valid POST is a new order.
Validation occurs before any INSERT. The response is sent only after the transaction commits.
