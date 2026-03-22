import os
import time
#from collections import deque
#from typing import Any, Deque, Dict, List
from typing import Any, Dict

import requests
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="admin-api", version="0.1.0")

REQUEST_TIMEOUT_SECONDS = 2.0
RUNTIME_TELEMETRY_MODE = None  
#BUFFER_SIZE = int(os.getenv("TELEMETRY_BUFFER_SIZE", "200"))
#RECENT_EVENTS: Deque[Dict[str, Any]] = deque(maxlen=BUFFER_SIZE)


class TelemetryModeRequest(BaseModel):
    mode: str


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    return value if value else default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default

# --------------------------------------------------
# Telemetry settings
# --------------------------------------------------
# TELEMETRY_MODE controls experiment behavior:
# - off   : ignore telemetry
# - sync  : forward to telemetry-api and wait for response
# - async : simplified version, return immediately
def _telemetry_mode() -> str:
    mode = RUNTIME_TELEMETRY_MODE or _env_str("TELEMETRY_MODE", "async").lower()
    if mode not in ("off", "sync", "async"):
        return "async"
    return mode

# This tells admin-api where the standalone telemetry service is running.
# Example:
#   local: http://localhost:8200
#   docker: http://telemetry-api:8200
#   GCE VM: http://<telemetry_vm_ip>:8200
def _telemetry_api_base_url() -> str:
    return _env_str("TELEMETRY_API_BASE_URL", "http://localhost:8200").rstrip("/")
    #return _env_str("TELEMETRY_API_BASE_URL", "http://host.docker.internal:8200").rstrip("/")


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


# --------------------------------------------------
# Helper: forward telemetry event to telemetry-api
# --------------------------------------------------
# This function sends one event to the standalone telemetry service.
def _forward_telemetry_event(event: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{_telemetry_api_base_url()}/event"
    start = time.monotonic()

    try:
        response = requests.post(url, json=event, timeout=REQUEST_TIMEOUT_SECONDS)
        latency_ms = int((time.monotonic() - start) * 1000)

        return {
            "ok": response.ok,
            "url": url,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "data": response.json(),
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
        "telemetry_api_base_url": _telemetry_api_base_url(),
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


@app.get("/telemetry/mode")
def telemetry_mode() -> Dict[str, str]:
    if RUNTIME_TELEMETRY_MODE is not None:
        return {"mode": RUNTIME_TELEMETRY_MODE, "source": "runtime"}
    return {"mode": _env_str("TELEMETRY_MODE", "async").lower(), "source": "env"}

@app.post("/telemetry/mode")
def set_telemetry_mode(request: TelemetryModeRequest) -> Dict[str, str]:
    global RUNTIME_TELEMETRY_MODE
    mode = request.mode.lower()
    if mode not in ("off", "sync", "async"):
        return {"error": "invalid_mode", "message": "Mode must be one of: off, sync, async"}

    RUNTIME_TELEMETRY_MODE = mode
    return {"mode": RUNTIME_TELEMETRY_MODE, "source": "runtime"}

@app.post("/telemetry/event")
#def telemetry_event(payload: Dict[str, Any]) -> Dict[str, Any]:
def telemetry_event(payload: Dict[str, Any], background_tasks: BackgroundTasks) -> Dict[str, Any]:
    mode = _telemetry_mode()
    event = {
        "received_ts_ms": int(time.time() * 1000),
        "mode": mode,
        # Keep full client payload as-is for coupling experiments.
        "payload": payload,
    }
    print("[ADMIN TELEMETRY GATEWAY]", event)

    # Mode 1: telemetry off
    if mode == "off":
        return {"accepted": False, "reason": "telemetry_off"}
    
    # Mode 2: sync
    # Admin forwards to telemetry-api and waits for its response.
    # This keeps telemetry on the critical path.
    if mode == "sync":
        forward_result = _forward_telemetry_event(event)

        return {
            "accepted": forward_result.get("ok", False),
            "mode": mode,
            "forwarded": True,
            "telemetry_result": forward_result,
        }
    
    # Mode 3: async
    # return immediately without waiting for telemetry-api.
    # Later this can be improved with BackgroundTasks.
    background_tasks.add_task(_forward_telemetry_event, event)
    return {
        "accepted": True,
        "mode": mode,
        "forwarded": True,
        "delivery": "background",
    }

    #RECENT_EVENTS.append(event)
    #return {"accepted": True, "stored": True, "count": len(RECENT_EVENTS)}

"""
@app.get("/telemetry/recent")
def telemetry_recent(limit: int = 20) -> Dict[str, Any]:
    safe_limit = max(1, min(limit, BUFFER_SIZE))
    events: List[Dict[str, Any]] = list(RECENT_EVENTS)[-safe_limit:]
    return {"count": len(events), "events": events}
"""