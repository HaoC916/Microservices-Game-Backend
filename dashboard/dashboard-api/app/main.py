import os
import time
from typing import Any, Dict

import requests
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="dashboard-api", version="0.1.0")


# --------------------------------------------------
# CORS configuration
# --------------------------------------------------
# The frontend UI runs on a different local port (for example 5173),
# so the browser treats requests to dashboard-api as cross-origin.
# Without CORS, fetch() from the browser will fail even if curl works.
#
# For local development, we allow the Vite dev server origin.
# If deploy the frontend elsewhere, add that origin here.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# Environment helpers
# ----------------------------
# These helper functions read values from environment variables.
# If the variable is missing or invalid, they fall back to a default value.
# This makes the service easier to run locally and on VMs.

def _env_str(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    return value if value else default

def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        return float(raw)
    except ValueError:
        return default

def _dashboard_mode() -> str:
    # Current dashboard mode.
    # For now, "placeholder" is enough for the project stage.
    return _env_str("DASHBOARD_MODE", "placeholder")

def _admin_api_base_url() -> str:
    # Base URL of the admin-api service.
    # Example:
    #   local Docker Desktop: http://host.docker.internal:8000
    #   GCP VM deployment:    http://<admin_vm_external_ip>:8000
    return _env_str("ADMIN_API_BASE_URL", "http://host.docker.internal:8000").rstrip("/")

def _telemetry_api_base_url() -> str:
    # Base URL of the telemetry-api service.
    # Example:
    #   local Docker Desktop: http://host.docker.internal:8200
    #   GCP VM deployment:    http://<telemetry_vm_external_ip>:8200
    return _env_str("TELEMETRY_API_BASE_URL", "http://host.docker.internal:8200").rstrip("/")


def _nakama_api_base_url() -> str:
    # Base URL of the Nakama API service.
    # Example:
    #   local Docker Desktop: http://host.docker.internal:7350
    #   GCP VM deployment:    http://<nakama_vm_external_ip>:7350
    return _env_str("NAKAMA_API_BASE_URL", "http://host.docker.internal:7350").rstrip("/")

"""
def _nakama_console_base_url() -> str:
    # Base URL of the Nakama Console service.
    # Example:
    #   local Docker Desktop: http://host.docker.internal:7351
    #   GCP VM deployment:    http://<nakama_vm_external_ip>:7351
    return _env_str("NAKAMA_CONSOLE_BASE_URL", "http://host.docker.internal:7351").rstrip("/")
"""

def _request_timeout_seconds() -> float:
    # Timeout for outgoing HTTP requests to admin-api.
    return _env_float("REQUEST_TIMEOUT_SECONDS", 2.0)

# ----------------------------
# Generic HTTP client helper
# ----------------------------
# This helper sends GET requests to any service base URL
# and returns a normalized JSON structure.

def _service_get(base_url: str, path: str = "") -> Dict[str, Any]:
    url = f"{base_url}{path}"
    start = time.monotonic()

    try:
        response = requests.get(url, timeout=_request_timeout_seconds())
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
    except ValueError as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        return {
            "ok": False,
            "url": url,
            "status_code": response.status_code if "response" in locals() else None,
            "latency_ms": latency_ms,
            "error": f"Invalid JSON response: {exc}",
        }
    
def _admin_get(path: str) -> Dict[str, Any]:
    return _service_get(_admin_api_base_url(), path)

def _telemetry_get(path: str) -> Dict[str, Any]:
    return _service_get(_telemetry_api_base_url(), path)

def _nakama_api_get(path: str = "") -> Dict[str, Any]:
    return _service_get(_nakama_api_base_url(), path)

"""
def _nakama_console_get(path: str = "") -> Dict[str, Any]:
    return _service_get(_nakama_console_base_url(), path)
"""

# ----------------------------
# Dashboard endpoints
# ----------------------------

@app.get("/health")
def health() -> Dict[str, Any]:
    # Basic liveness endpoint for dashboard-api itself.
    # This does not check upstream services.
    return {
        "ok": True,
        "service": "dashboard-api",
        "mode": _dashboard_mode(),
    }

@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    # Read telemetry summary directly from telemetry-api.
    telemetry_summary = _telemetry_get("/stats/summary")

    recent_count = 0
    total_events = 0

    if telemetry_summary.get("ok") and isinstance(telemetry_summary.get("data"), dict):
        summary_data = telemetry_summary["data"]
        recent_count = summary_data.get("recent_buffer_count", 0)
        total_events = summary_data.get("total_events", 0)

    return {
        "ok": True,
        "service": "dashboard-api",
        "mode": _dashboard_mode(),
        "admin_api_base_url": _admin_api_base_url(),
        "telemetry_api_base_url": _telemetry_api_base_url(),
        "nakama_api_base_url": _nakama_api_base_url(),
        #"nakama_console_base_url": _nakama_console_base_url(),
        "metrics": {
            "online_players": 0,
            "active_matches": 0,
            "matchmaking_queue": 0,
            "peak_online_players": 0,
            "recent_telemetry_events": recent_count,
            "total_telemetry_events": total_events,
        },
        # "note": "placeholder gameplay metrics; telemetry data is now read from telemetry-api",
    }


@app.get("/summary")
def summary() -> JSONResponse:
    admin_health = _admin_get("/health")
    admin_config = _admin_get("/config")
    telemetry_health = _telemetry_get("/health")
    telemetry_recent = _telemetry_get("/events/recent?limit=10")
    telemetry_summary = _telemetry_get("/stats/summary")
    nakama_api = _nakama_api_get()

    telemetry_mode = "unknown"
    if admin_config.get("ok") and isinstance(admin_config.get("data"), dict):
        telemetry_mode = admin_config["data"].get("telemetry_mode", "unknown")

    # Aggregate selected data from multiple services.
    result = {
        "ok": True,
        "service": "dashboard-api",
        "mode": _dashboard_mode(),
        "telemetry_mode": telemetry_mode,
        "upstreams": {
            # admin service
            "admin_health": admin_health,
            "admin_config": admin_config,

            # telemetry service
            "telemetry_health": telemetry_health,
            "telemetry_recent": telemetry_recent,
            "telemetry_summary": telemetry_summary,

            # Nakama service
            "nakama_api": nakama_api,
            #"nakama_console": _nakama_console_get(),
        },
    }

    # If any upstream call fails, mark the summary as not fully healthy.
    all_ok = all(item.get("ok", False) for item in result["upstreams"].values())
    result["ok"] = all_ok

    # Return 200 when all upstreams are healthy.
    # Return 502 when one or more upstream checks fail.
    status_code = 200 if all_ok else 502
    return JSONResponse(result, status_code=status_code)