import os
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


def _request_timeout_seconds() -> float:
    # Timeout for outgoing HTTP requests to admin-api.
    return _env_float("REQUEST_TIMEOUT_SECONDS", 2.0)


# ----------------------------
# Admin API client helper
# ----------------------------
# This helper function sends GET requests to admin-api.
# We keep it inside main.py for simplicity in this project phase.
# Later, if needed, this logic can be moved into a separate file.


def _admin_get(path: str) -> Dict[str, Any]:
    url = f"{_admin_api_base_url()}{path}"
    try:
        response = requests.get(url, timeout=_request_timeout_seconds())
        return {
            "ok": response.ok,
            "url": url,
            "status_code": response.status_code,
            "data": response.json(),
        }
    except requests.RequestException as exc:
        return {
            "ok": False,
            "url": url,
            "status_code": None,
            "error": str(exc),
        }
    except ValueError as exc:
        # This catches JSON parsing errors.
        return {
            "ok": False,
            "url": url,
            "status_code": response.status_code if "response" in locals() else None,
            "error": f"Invalid JSON response: {exc}",
        }


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
    # This endpoint returns dashboard-friendly metrics.
    # For now, most values are placeholders.
    # We also try to query recent telemetry count from admin-api.
    telemetry = _admin_get("/telemetry/recent?limit=20")

    recent_count = 0
    if telemetry.get("ok") and isinstance(telemetry.get("data"), dict):
        recent_count = telemetry["data"].get("count", 0)

    return {
        "ok": True,
        "service": "dashboard-api",
        "mode": _dashboard_mode(),
        "admin_api_base_url": _admin_api_base_url(),
        "metrics": {
            # These values are placeholders for now.
            # Later they can be replaced by real aggregated values.
            "online_players": 0,
            "active_matches": 0,
            "matchmaking_queue": 0,
            "peak_online_players": 0,
            # This one is currently backed by admin-api telemetry buffer.
            "recent_telemetry_events": recent_count,
        },
        "note": "placeholder dashboard metrics; admin-backed integration is enabled",
    }


@app.get("/summary")
def summary() -> JSONResponse:
    # This endpoint aggregates multiple admin-api results into one response.
    # It is useful for dashboard UI or quick experiment inspection.
    result = {
        "ok": True,
        "service": "dashboard-api",
        "mode": _dashboard_mode(),
        "upstreams": {
            "admin_health": _admin_get("/health"),
            "admin_config": _admin_get("/config"),
            "nakama_api": _admin_get("/nakama/api"),
            "nakama_console": _admin_get("/nakama/console"),
            "recent_telemetry": _admin_get("/telemetry/recent?limit=10"),
        },
    }

    # If any upstream call fails, mark the summary as not fully healthy.
    all_ok = all(item.get("ok", False) for item in result["upstreams"].values())
    result["ok"] = all_ok

    # Return 200 when all upstreams are healthy.
    # Return 502 when one or more upstream checks fail.
    status_code = 200 if all_ok else 502
    return JSONResponse(result, status_code=status_code)