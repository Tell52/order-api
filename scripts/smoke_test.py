"""Run real localhost HTTP requests against a temporary Uvicorn server/database."""

import json
from pathlib import Path
import socket
import tempfile
import time
from threading import Thread

import httpx
import uvicorn

# Running as a file places scripts/ on sys.path; add the repository root.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from order_api.app import create_app


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="order-api-smoke-") as temporary:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
            server = uvicorn.Server(uvicorn.Config(
                create_app(Path(temporary) / "orders.sqlite3"), log_level="error"))
            thread = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
            thread.start()
            try:
                with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=2, trust_env=False) as client:
                    for attempt in range(100):
                        if not thread.is_alive():
                            raise RuntimeError("Server exited before becoming ready")
                        try:
                            health = client.get("/health")
                            if health.status_code == 200:
                                break
                        except httpx.ConnectError:
                            pass
                        time.sleep(0.1)
                    else:
                        raise RuntimeError("Server did not become ready within 10 seconds")
                    created = client.post("/orders", json={"product_id": 2, "quantity": 3})
                    expected = {"order_id": 1, "product_id": 2, "quantity": 3,
                                "unit_price": 350, "total_amount": 1050}
                    assert health.json() == {"status": "ok"}
                    assert created.status_code == 201 and created.json() == expected
                    read = client.get("/orders/1")
                    assert read.status_code == 200 and read.json() == expected
                    invalid = client.post("/orders", json={"product_id": 2, "quantity": 0})
                    assert invalid.status_code == 422
                    unknown = client.get("/orders/2")
                    assert unknown.status_code == 404
                    responses = [health, created, read, invalid, unknown]
                    transcript = [{"method": response.request.method,
                                   "path": response.request.url.path,
                                   "status": response.status_code,
                                   "response": response.json()} for response in responses]
                    output = root / "samples" / "live-smoke.json"
                    output.parent.mkdir(exist_ok=True)
                    output.write_text(json.dumps(transcript, indent=2) + "\n", encoding="utf-8")
                    print("Live HTTP smoke passed: GET health 200; POST order 201; GET order 200; invalid POST 422; unknown GET 404.")
                    print("Created total_amount=1050 THB. Transcript: samples/live-smoke.json")
            finally:
                server.should_exit = True
                thread.join(timeout=5)
                if thread.is_alive():
                    raise RuntimeError("Server did not stop within 5 seconds")


if __name__ == "__main__":
    main()
