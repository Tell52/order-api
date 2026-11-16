# Execution evidence

Executed on 2026-11-17, Windows 11 (10.0.26300), Python 3.13.5, SQLite 3.49.1.
Commands below assume the repository root and use the installed local virtual environment.
`requirements.txt` records the full installed dependency set with exact versions.

| Command | Observed outcome |
| --- | --- |
| `python -m venv .venv` | Created an isolated environment. |
| `.\.venv\Scripts\python.exe -m pip install fastapi uvicorn httpx pytest` | Installed the dependency set subsequently frozen in requirements.txt. |
| `.\.venv\Scripts\python.exe -m pip check` | No broken requirements found. |
| `.\.venv\Scripts\python.exe -m pytest -q` | 45 passed; one dependency deprecation warning. |
| `.\.venv\Scripts\python.exe scripts/smoke_test.py` | Exit 0; real HTTP health 200, create 201, read 200, invalid create 422, unknown order 404. |

The live HTTP sample creates product 2, quantity 3, with unit_price 350 and total_amount 1050 THB.
The full observed response bodies are saved in [samples/live-smoke.json](../samples/live-smoke.json).
The invalid create is followed by lookup of order 2, which returns 404. TestClient tests additionally
inspect actual stored counts for invalid requests and test persistence across separate applications.

## Reproduced issue and correction

The first smoke implementation launched Uvicorn through a subprocess and terminated it at cleanup.
HTTP assertions passed, but Windows then raised `PermissionError: [WinError 32]` when removing
the temporary `server.log` file because it was still in use. The smoke command was therefore not
successful as a whole. The script now runs Uvicorn in a thread, requests graceful shutdown, and joins
that thread before removing the temporary directory. Rerunning the corrected command exited 0.
The HTTP assertions still use a real localhost TCP connection.

## Limits

- TestClient tests are in-process API tests; only the separate smoke command uses a listening HTTP server.
- Starlette 1.10.0 emits a deprecation warning for its HTTPX-based TestClient and recommends HTTPX2.
  The pinned HTTPX combination works for these 45 tests; the warning is retained, not suppressed.
  Migrating the client dependency is future maintenance work.
- No load tests, coverage measurements, authentication checks, or deployment checks were run.
- The manual POSIX commands are provided for equivalent usage but were not executed on this Windows host.
- Local results do not establish GitHub Actions success. Remote CI must be observed for the exact pushed commit.
