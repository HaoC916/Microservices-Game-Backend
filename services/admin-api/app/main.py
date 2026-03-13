import os
import time
from collections import deque
from typing import Any, Deque, Dict, List

import requests
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="admin-api", version="0.1.0")

REQUEST_TIMEOUT_SECONDS = 2.0
BUFFER_SIZE = int(os.getenv("TELEMETRY_BUFFER_SIZE", "200"))
RECENT_EVENTS: Deque[Dict[str, Any]] = deque(maxlen=BUFFER_SIZE)


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    return value if value else default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def _telemetry_mode() -> str:
    mode = _env_str("TELEMETRY_MODE", "async").lower()
    if mode not in ("off", "sync", "async"):
        return "async"
    return mode


def _nakama_host() -> str:
    return _env_str("NAKAMA_HOST", "localhost")


def _nakama_api_port() -> int:
    return _env_int("NAKAMA_API_PORT", 7350)


def _nakama_console_port() -> int:
    return _env_int("NAKAMA_CONSOLE_PORT", 7351)


def _nakama_api_url() -> str:
    return f"http://{_nakama_host()}:{_nakama_api_port()}"


def _nakama_console_url() -> str:
    return f"http://{_nakama_host()}:{_nakama_console_port()}"


def _upstream_check(url: str) -> Dict[str, Any]:
    start = time.monotonic()
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        latency_ms = int((time.monotonic() - start) * 1000)
        return {
            "ok": True,
            "url": url,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        }
    except requests.RequestException as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        return {
            "ok": False,
            "url": url,
            "status_code": None,
            "latency_ms": latency_ms,
            "error": str(exc),
        }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
def config() -> Dict[str, Any]:
    return {
        "nakama_host": _nakama_host(),
        "nakama_api_port": _nakama_api_port(),
        "nakama_console_port": _nakama_console_port(),
        "nakama_api_url": _nakama_api_url(),
        "nakama_console_url": _nakama_console_url(),
        "telemetry_mode": _telemetry_mode(),
    }


@app.get("/nakama/api")
def nakama_api() -> JSONResponse:
    result = _upstream_check(_nakama_api_url())
    status = 200 if result["ok"] else 502
    return JSONResponse(result, status_code=status)


@app.get("/nakama/console")
def nakama_console() -> JSONResponse:
    result = _upstream_check(_nakama_console_url())
    status = 200 if result["ok"] else 502
    return JSONResponse(result, status_code=status)


@app.post("/telemetry/event")
def telemetry_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    mode = _telemetry_mode()
    event = {
        "received_ts_ms": int(time.time() * 1000),
        "mode": mode,
        # Keep full client payload as-is for coupling experiments.
        "payload": payload,
    }
    print("[TELEMETRY]", event)

    if mode == "off":
        return {"accepted": False, "reason": "telemetry_off"}

    RECENT_EVENTS.append(event)
    return {"accepted": True, "stored": True, "count": len(RECENT_EVENTS)}


@app.get("/telemetry/recent")
def telemetry_recent(limit: int = 20) -> Dict[str, Any]:
    safe_limit = max(1, min(limit, BUFFER_SIZE))
    events: List[Dict[str, Any]] = list(RECENT_EVENTS)[-safe_limit:]
    return {"count": len(events), "events": events}
