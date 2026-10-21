"""End-to-end backend endpoint verification using the SQLite sample database."""

import json
import sys
import time
from typing import Any

import requests

BASE_URL = "http://localhost:8000"
SAMPLE_URI = "sqlite:///c:/Users/MohanaPrasanthSivaku/Desktop/lakeforge/sample_data.db"

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    tag = PASS if ok else FAIL
    print(f"{tag} {name}")
    if detail:
        print(f"       {detail}")
    results.append((name, ok, detail))


def pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2, default=str)[:400]
    except Exception:
        return str(obj)[:400]


def wait_for_backend(retries: int = 20) -> bool:
    for _ in range(retries):
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=2)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)
    return False


def test_health() -> None:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    ok = r.status_code == 200 and r.json().get("status") == "healthy"
    record("GET /health", ok, f"status={r.status_code} body={r.json()}")


def test_list_sources_empty() -> None:
    r = requests.get(f"{BASE_URL}/api/sources", timeout=5)
    ok = r.status_code == 200 and isinstance(r.json(), list)
    record("GET /api/sources (initial)", ok, f"status={r.status_code} count={len(r.json()) if ok else 'n/a'}")


def test_create_source() -> str | None:
    payload = {
        "name": "SQLite Sample DB",
        "uri": SAMPLE_URI,
        "description": "E2E test sample database",
        "tags": ["test", "sqlite"],
    }
    r = requests.post(f"{BASE_URL}/api/sources", json=payload, timeout=10)
    ok = r.status_code == 201 and r.json().get("id")
    detail = f"status={r.status_code} body={pretty(r.json())}"
    record("POST /api/sources", ok, detail)
    return r.json().get("id") if ok else None


def test_get_source(source_id: str) -> None:
    r = requests.get(f"{BASE_URL}/api/sources/{source_id}", timeout=5)
    ok = r.status_code == 200 and r.json().get("id") == source_id
    record(f"GET /api/sources/{source_id}", ok, f"status={r.status_code}")


def test_list_sources_populated(expected_id: str) -> None:
    r = requests.get(f"{BASE_URL}/api/sources", timeout=5)
    ids = [s.get("id") for s in r.json()] if r.status_code == 200 else []
    ok = expected_id in ids
    record("GET /api/sources (after create)", ok, f"ids={ids}")


def test_test_connection(source_id: str) -> None:
    r = requests.post(f"{BASE_URL}/api/sources/{source_id}/test", timeout=15)
    body = r.json() if r.status_code == 200 else {}
    ok = r.status_code == 200 and body.get("status") in {"success", "ok", "connected"}
    record(f"POST /api/sources/{source_id}/test", ok, f"status={r.status_code} body={pretty(body)}")


def test_start_inspection(source_id: str) -> str | None:
    payload = {"source_id": source_id, "include_profile": True, "sample_size": 100}
    r = requests.post(f"{BASE_URL}/api/inspect/start", json=payload, timeout=30)
    ok = r.status_code == 200 and r.json().get("session_id")
    detail = f"status={r.status_code} body={pretty(r.json())}"
    record("POST /api/inspect/start", ok, detail)
    return r.json().get("session_id") if ok else None


def test_inspection_status(session_id: str) -> None:
    r = requests.get(f"{BASE_URL}/api/inspect/{session_id}/status", timeout=5)
    ok = r.status_code == 200 and r.json().get("status") in {"completed", "in_progress", "error"}
    record(f"GET /api/inspect/{session_id}/status", ok, f"body={pretty(r.json())}")


def test_inspection_schema(session_id: str) -> None:
    r = requests.get(f"{BASE_URL}/api/inspect/{session_id}/schema", timeout=10)
    ok = r.status_code == 200 and "schema" in r.json()
    detail = f"status={r.status_code} preview={pretty(r.json())}"
    record(f"GET /api/inspect/{session_id}/schema", ok, detail)


def test_inspection_profile(session_id: str) -> None:
    r = requests.get(f"{BASE_URL}/api/inspect/{session_id}/profile", timeout=10)
    ok = r.status_code == 200 and "profile" in r.json()
    detail = f"status={r.status_code} preview={pretty(r.json())}"
    record(f"GET /api/inspect/{session_id}/profile", ok, detail)


def test_inspection_samples(session_id: str) -> None:
    r = requests.get(f"{BASE_URL}/api/inspect/{session_id}/samples?limit=10", timeout=10)
    ok = r.status_code == 200 and "samples" in r.json()
    record(f"GET /api/inspect/{session_id}/samples", ok, f"status={r.status_code}")


def test_dbeaver_list() -> None:
    r = requests.get(f"{BASE_URL}/api/dbeaver/connections", timeout=10)
    ok = r.status_code == 200
    body = r.json() if ok else None
    detail = f"status={r.status_code} count={len(body) if isinstance(body, list) else 'n/a'}"
    record("GET /api/dbeaver/connections", ok, detail)


def test_delete_source(source_id: str) -> None:
    r = requests.delete(f"{BASE_URL}/api/sources/{source_id}", timeout=5)
    ok = r.status_code in {200, 204}
    record(f"DELETE /api/sources/{source_id}", ok, f"status={r.status_code}")


def main() -> int:
    print(f"{INFO} Waiting for backend at {BASE_URL} ...")
    if not wait_for_backend():
        print(f"{FAIL} Backend not reachable")
        return 1

    print(f"\n{INFO} === Health & Sources ===")
    test_health()
    test_list_sources_empty()
    source_id = test_create_source()
    if not source_id:
        print(f"{FAIL} Cannot continue without a source")
        return 1
    test_get_source(source_id)
    test_list_sources_populated(source_id)
    test_test_connection(source_id)

    print(f"\n{INFO} === Inspection ===")
    session_id = test_start_inspection(source_id)
    if session_id:
        test_inspection_status(session_id)
        test_inspection_schema(session_id)
        test_inspection_profile(session_id)
        test_inspection_samples(session_id)
    else:
        print(f"{FAIL} Skipping inspection detail tests (no session)")

    print(f"\n{INFO} === DBeaver ===")
    test_dbeaver_list()

    print(f"\n{INFO} === Cleanup ===")
    test_delete_source(source_id)

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"Results: {passed}/{total} passed")
    print("=" * 60)
    for name, ok, _ in results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
