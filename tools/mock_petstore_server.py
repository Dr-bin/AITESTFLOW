"""Local mock Petstore API server with coverage tracking.

Implements endpoints:
- GET /pets
- POST /pets
- GET /pets/{petId}
- DELETE /pets/{petId}
- POST /pets/{petId}/vaccinations

Extra endpoints for coverage:
- GET /__coverage
- POST /__coverage/reset
"""

from __future__ import annotations

import json
import re
import threading
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse


VALID_STATUS = {"available", "pending", "sold"}

# Rows with output=500 are intentionally excluded from coverage denominator.
IGNORED_500_IDS = {"C04", "C08", "C14", "C18", "C21", "C25", "C30", "C35"}
ALL_CONDITION_IDS = {
    "C01",
    "C02",
    "C03",
    "C04",
    "C05",
    "C06",
    "C07",
    "C08",
    "C09",
    "C10",
    "C11",
    "C12",
    "C13",
    "C14",
    "C15",
    "C16",
    "C17",
    "C18",
    "C19",
    "C20",
    "C21",
    "C22",
    "C23",
    "C24",
    "C25",
    "C26",
    "C27",
    "C28",
    "C29",
    "C30",
    "C31",
    "C32",
    "C33",
    "C34",
    "C35",
    "C36",
    "C37",
    "C38",
    "C39",
    "C40",
    "C41",
    "C42",
    "C43",
    "C44",
    "C45",
    "C46",
    "C47",
}


def _json_response(handler: BaseHTTPRequestHandler, code: int, payload: Any) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _empty_response(handler: BaseHTTPRequestHandler, code: int) -> None:
    handler.send_response(code)
    handler.send_header("Content-Length", "0")
    handler.end_headers()


def _read_json(handler: BaseHTTPRequestHandler) -> Optional[Dict[str, Any]]:
    raw_len = handler.headers.get("Content-Length", "0")
    try:
        content_len = int(raw_len)
    except ValueError:
        return None
    if content_len <= 0:
        return {}
    body = handler.rfile.read(content_len)
    try:
        data = json.loads(body.decode("utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _is_iso_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _classify_pet_id_segment(segment: str) -> tuple[str, Optional[int]]:
    """Return (kind, value) where kind in {'ok', 'range', 'type'}."""
    if re.fullmatch(r"-?\d+", segment):
        value = int(segment)
        if value < 1:
            return "range", value
        return "ok", value
    return "type", None


class CoverageTracker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._covered: set[str] = set()

    def mark(self, *condition_ids: str) -> None:
        with self._lock:
            for cid in condition_ids:
                if cid in ALL_CONDITION_IDS:
                    self._covered.add(cid)

    def reset(self) -> None:
        with self._lock:
            self._covered.clear()

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            covered = set(self._covered)
        active_ids = sorted(ALL_CONDITION_IDS - IGNORED_500_IDS)
        covered_active = sorted((covered - IGNORED_500_IDS) & set(active_ids))
        missing_active = sorted(set(active_ids) - set(covered_active))
        total = len(active_ids)
        covered_total = len(covered_active)
        return {
            "note": "Coverage excludes all output=500 conditions by design.",
            "total_conditions_excluding_500": total,
            "covered_conditions_excluding_500": covered_total,
            "coverage_rate": round(covered_total / total, 6) if total else 0.0,
            "covered_condition_ids": covered_active,
            "missing_condition_ids": missing_active,
            "ignored_500_condition_ids": sorted(IGNORED_500_IDS),
            "all_recorded_condition_ids": sorted(covered),
        }


class PetstoreState:
    def __init__(self, coverage: CoverageTracker) -> None:
        self._lock = threading.Lock()
        self.coverage = coverage
        self.pets: Dict[int, Dict[str, Any]] = {
            1: {"id": 1, "name": "SeedOne", "status": "available", "category": "Dog", "price": 50.0},
            5: {"id": 5, "name": "SeedFive", "status": "pending", "category": "Cat", "price": 80.0},
            100: {"id": 100, "name": "SeedHundred", "status": "sold", "category": "Bird", "price": 20.0},
        }
        self._seed_ids = {1, 5, 100}
        self.vaccinations: Dict[int, list[Dict[str, str]]] = {}
        self.next_id = 101

    def list_pets(self, limit: Optional[int], status: Optional[str]) -> list[Dict[str, Any]]:
        with self._lock:
            items = list(self.pets.values())
        if status is not None:
            items = [p for p in items if p.get("status") == status]
        if limit is not None:
            items = items[:limit]
        return items

    def get_pet(self, pet_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            pet = self.pets.get(pet_id)
            return dict(pet) if pet else None

    def create_pet(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            pet_id = self.next_id
            self.next_id += 1
            pet = {
                "id": pet_id,
                "name": payload["name"],
                "status": payload.get("status", "available"),
                "category": payload.get("category", ""),
                "price": payload.get("price", 0),
            }
            self.pets[pet_id] = pet
            return dict(pet)

    def delete_pet(self, pet_id: int) -> bool:
        with self._lock:
            # Keep seeded pets stable to avoid cross-test interference.
            if pet_id in self._seed_ids:
                return True
            if pet_id in self.pets:
                del self.pets[pet_id]
                return True
            return False

    def add_vaccination(self, pet_id: int, vaccine_name: str, date_value: str) -> bool:
        with self._lock:
            if pet_id not in self.pets:
                return False
            self.vaccinations.setdefault(pet_id, []).append(
                {"vaccine_name": vaccine_name, "date": date_value}
            )
            return True


def create_handler(state: PetstoreState):
    class PetstoreHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            parsed = urlparse(self.path)

            if parsed.path == "/__coverage":
                _json_response(self, HTTPStatus.OK, state.coverage.summary())
                return

            if parsed.path == "/pets":
                query = parse_qs(parsed.query)
                limit_raw = query.get("limit", [None])[0]
                status_raw = query.get("status", [None])[0]

                limit: Optional[int] = None
                if limit_raw is not None:
                    limit_text = str(limit_raw)
                    if re.fullmatch(r"-?\d+", limit_text):
                        limit = int(limit_text)
                        if 1 <= limit <= 100:
                            pass
                        else:
                            state.coverage.mark("C02")
                            _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "limit out of range"})
                            return
                    else:
                        state.coverage.mark("C03")
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "limit must be integer"})
                        return

                if status_raw is not None:
                    # Query params are strings; numeric-like values are treated as "type mismatch" bucket.
                    if status_raw in VALID_STATUS:
                        pass
                    elif str(status_raw).isdigit():
                        state.coverage.mark("C07")
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "status type invalid"})
                        return
                    else:
                        state.coverage.mark("C06")
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "status enum invalid"})
                        return

                if limit_raw is not None and limit is not None:
                    state.coverage.mark("C01")
                if status_raw is not None:
                    state.coverage.mark("C05")
                _json_response(self, HTTPStatus.OK, state.list_pets(limit, status_raw))
                return

            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) == 2 and parts[0] == "pets":
                kind, pet_id = _classify_pet_id_segment(parts[1])
                if kind == "type":
                    state.coverage.mark("C29")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "invalid petId type"})
                    return
                if kind == "range":
                    state.coverage.mark("C28")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "petId out of range"})
                    return
                assert pet_id is not None
                pet = state.get_pet(pet_id)
                if pet is None:
                    state.coverage.mark("C27")
                    _json_response(self, HTTPStatus.NOT_FOUND, {"error": "pet not found"})
                    return
                state.coverage.mark("C26")
                _json_response(self, HTTPStatus.OK, pet)
                return

            _json_response(self, HTTPStatus.NOT_FOUND, {"error": "route not found"})

        def do_POST(self) -> None:
            parsed = urlparse(self.path)

            if parsed.path == "/__coverage/reset":
                state.coverage.reset()
                _json_response(self, HTTPStatus.OK, {"message": "coverage reset"})
                return

            if parsed.path == "/pets":
                payload = _read_json(self)
                if payload is None:
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "invalid json"})
                    return

                if "name" not in payload:
                    state.coverage.mark("C13")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "name is required"})
                    return

                name = payload.get("name")
                if not isinstance(name, str):
                    state.coverage.mark("C12")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "name must be string"})
                    return
                if len(name) == 0:
                    state.coverage.mark("C10")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "name cannot be empty"})
                    return
                if len(name) > 50:
                    state.coverage.mark("C11")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "name too long"})
                    return

                status_value = payload.get("status", "available")
                if not isinstance(status_value, str):
                    state.coverage.mark("C17")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "status must be string"})
                    return
                if status_value not in VALID_STATUS:
                    state.coverage.mark("C16")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "status invalid"})
                    return

                category = payload.get("category", "")
                if not isinstance(category, str):
                    state.coverage.mark("C20")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "category must be string"})
                    return

                price = payload.get("price", 0)
                if not isinstance(price, (int, float)) or isinstance(price, bool):
                    state.coverage.mark("C24")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "price must be number"})
                    return
                if price < 0 or price > 10000:
                    state.coverage.mark("C23")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "price out of range"})
                    return

                created = state.create_pet(payload)
                state.coverage.mark("C09", "C15", "C19", "C22")
                _json_response(self, HTTPStatus.CREATED, created)
                return

            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) == 3 and parts[0] == "pets" and parts[2] == "vaccinations":
                kind, pet_id = _classify_pet_id_segment(parts[1])
                if kind == "type":
                    state.coverage.mark("C39")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "invalid petId type"})
                    return
                if kind == "range":
                    state.coverage.mark("C38")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "petId out of range"})
                    return
                assert pet_id is not None

                payload = _read_json(self)
                if payload is None:
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "invalid json"})
                    return

                vaccine_name = payload.get("vaccine_name")
                date_value = payload.get("date")

                if not isinstance(vaccine_name, str):
                    state.coverage.mark("C42")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "vaccine_name must be string"})
                    return
                if vaccine_name == "":
                    state.coverage.mark("C41")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "vaccine_name cannot be empty"})
                    return

                if not isinstance(date_value, str):
                    state.coverage.mark("C46")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "date must be string"})
                    return
                if not _is_iso_date(date_value):
                    state.coverage.mark("C45")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "date format invalid"})
                    return

                if not state.add_vaccination(pet_id, vaccine_name, date_value):
                    state.coverage.mark("C37", "C43", "C47")
                    _json_response(self, HTTPStatus.NOT_FOUND, {"error": "pet not found"})
                    return

                state.coverage.mark("C36", "C40", "C44")
                _json_response(self, HTTPStatus.CREATED, {"message": "Vaccination record added"})
                return

            _json_response(self, HTTPStatus.NOT_FOUND, {"error": "route not found"})

        def do_DELETE(self) -> None:
            parsed = urlparse(self.path)
            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) == 2 and parts[0] == "pets":
                kind, pet_id = _classify_pet_id_segment(parts[1])
                if kind == "type":
                    state.coverage.mark("C34")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "invalid petId type"})
                    return
                if kind == "range":
                    state.coverage.mark("C33")
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "petId out of range"})
                    return
                assert pet_id is not None
                if state.delete_pet(pet_id):
                    state.coverage.mark("C31")
                    _empty_response(self, HTTPStatus.NO_CONTENT)
                    return
                state.coverage.mark("C32")
                _json_response(self, HTTPStatus.NOT_FOUND, {"error": "pet not found"})
                return

            _json_response(self, HTTPStatus.NOT_FOUND, {"error": "route not found"})

    return PetstoreHandler


def start_server(host: str = "127.0.0.1", port: int = 8000) -> tuple[ThreadingHTTPServer, threading.Thread]:
    coverage = CoverageTracker()
    state = PetstoreState(coverage=coverage)
    handler_cls = create_handler(state)
    server = ThreadingHTTPServer((host, port), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


if __name__ == "__main__":
    srv, t = start_server()
    print("Mock Petstore server running on http://127.0.0.1:8000")
    print("Coverage endpoint: http://127.0.0.1:8000/__coverage")
    try:
        t.join()
    except KeyboardInterrupt:
        pass
    finally:
        srv.shutdown()
        srv.server_close()
