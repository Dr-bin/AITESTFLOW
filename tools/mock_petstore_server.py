"""Local mock Petstore API server for real test execution.

Implements endpoints from input/sample_petstore.yaml:
- GET /pets
- POST /pets
- GET /pets/{petId}
- DELETE /pets/{petId}
- POST /pets/{petId}/vaccinations
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse


VALID_STATUS = {"available", "pending", "sold"}


def _json_response(handler: BaseHTTPRequestHandler, code: int, payload: Any) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _empty_response(handler: BaseHTTPRequestHandler, code: int) -> None:
    handler.send_response(code)
    handler.send_header("Content-Length", "0")
    handler.end_headers()


class PetstoreState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.pets: Dict[int, Dict[str, Any]] = {
            1: {"id": 1, "name": "SeedOne", "status": "available", "category": "Dog", "price": 50.0},
            5: {"id": 5, "name": "SeedFive", "status": "pending", "category": "Cat", "price": 80.0},
            100: {"id": 100, "name": "SeedHundred", "status": "sold", "category": "Bird", "price": 20.0},
        }
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
            if pet is None:
                return None
            return dict(pet)

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


def _parse_int_path_segment(segment: str) -> Optional[int]:
    if not segment or not segment.isdigit():
        return None
    value = int(segment)
    if value < 1:
        return None
    return value


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
        if isinstance(data, dict):
            return data
        return None
    except Exception:
        return None


def _is_iso_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def create_handler(state: PetstoreState):
    class PetstoreHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/pets":
                query = parse_qs(parsed.query)
                limit_raw = query.get("limit", [None])[0]
                status_raw = query.get("status", [None])[0]

                limit: Optional[int] = None
                if limit_raw is not None:
                    if not str(limit_raw).isdigit():
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "limit must be integer"})
                        return
                    limit = int(limit_raw)
                    if limit < 1 or limit > 100:
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "limit out of range"})
                        return

                if status_raw is not None:
                    if not isinstance(status_raw, str) or status_raw == "":
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "invalid status"})
                        return
                    if status_raw not in VALID_STATUS:
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "status enum invalid"})
                        return

                _json_response(self, HTTPStatus.OK, state.list_pets(limit, status_raw))
                return

            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) == 2 and parts[0] == "pets":
                pet_id = _parse_int_path_segment(parts[1])
                if pet_id is None:
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "invalid petId"})
                    return
                pet = state.get_pet(pet_id)
                if pet is None:
                    _json_response(self, HTTPStatus.NOT_FOUND, {"error": "pet not found"})
                    return
                _json_response(self, HTTPStatus.OK, pet)
                return

            _json_response(self, HTTPStatus.NOT_FOUND, {"error": "route not found"})

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/pets":
                payload = _read_json(self)
                if payload is None:
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "invalid json"})
                    return

                name = payload.get("name")
                if not isinstance(name, str):
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "name must be string"})
                    return
                if len(name) < 1 or len(name) > 50:
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "name length invalid"})
                    return

                status_value = payload.get("status", "available")
                if not isinstance(status_value, str) or status_value not in VALID_STATUS:
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "status invalid"})
                    return

                category = payload.get("category", "")
                if not isinstance(category, str):
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "category must be string"})
                    return

                price = payload.get("price", 0)
                if not isinstance(price, (int, float)) or isinstance(price, bool):
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "price must be number"})
                    return
                if price < 0 or price > 10000:
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "price out of range"})
                    return

                created = state.create_pet(payload)
                _json_response(self, HTTPStatus.CREATED, created)
                return

            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) == 3 and parts[0] == "pets" and parts[2] == "vaccinations":
                pet_id = _parse_int_path_segment(parts[1])
                if pet_id is None:
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "invalid petId"})
                    return

                payload = _read_json(self)
                if payload is None:
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "invalid json"})
                    return

                vaccine_name = payload.get("vaccine_name")
                date_value = payload.get("date")
                if not isinstance(vaccine_name, str) or vaccine_name == "":
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "vaccine_name invalid"})
                    return
                if not isinstance(date_value, str) or date_value == "":
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "date invalid"})
                    return
                if not _is_iso_date(date_value):
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "date format invalid"})
                    return

                if not state.add_vaccination(pet_id, vaccine_name, date_value):
                    _json_response(self, HTTPStatus.NOT_FOUND, {"error": "pet not found"})
                    return
                _json_response(self, HTTPStatus.CREATED, {"message": "Vaccination record added"})
                return

            _json_response(self, HTTPStatus.NOT_FOUND, {"error": "route not found"})

        def do_DELETE(self) -> None:
            parsed = urlparse(self.path)
            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) == 2 and parts[0] == "pets":
                pet_id = _parse_int_path_segment(parts[1])
                if pet_id is None:
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "invalid petId"})
                    return
                if state.delete_pet(pet_id):
                    _empty_response(self, HTTPStatus.NO_CONTENT)
                    return
                _json_response(self, HTTPStatus.NOT_FOUND, {"error": "pet not found"})
                return

            _json_response(self, HTTPStatus.NOT_FOUND, {"error": "route not found"})

    return PetstoreHandler


def start_server(host: str = "127.0.0.1", port: int = 8000) -> tuple[ThreadingHTTPServer, threading.Thread]:
    state = PetstoreState()
    handler_cls = create_handler(state)
    server = ThreadingHTTPServer((host, port), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread
