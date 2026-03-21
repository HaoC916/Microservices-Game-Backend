import os
import time
from collections import deque
from typing import Any, Deque, Dict, List

from fastapi import FastAPI

# --------------------------------------------------
# Create FastAPI app
# --------------------------------------------------
# This creates the standalone telemetry service.
# It is responsible for:
# 1. receiving telemetry events
# 2. storing a recent in-memory buffer
# 3. returning simple summary statistics
app = FastAPI(title="telemetry-api", version="0.1.0")


# --------------------------------------------------
# Environment helpers
# --------------------------------------------------
# These helper functions read environment variables safely.
# If the value is missing or invalid, they return a default value.

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
# Telemetry configuration
# --------------------------------------------------
# TELEMETRY_BUFFER_SIZE controls how many recent events
# are kept in memory for preview and dashboard display.
BUFFER_SIZE = _env_int("TELEMETRY_BUFFER_SIZE", 200)

# RECENT_EVENTS stores the latest telemetry events only.
# deque(maxlen=BUFFER_SIZE) automatically drops old events
# when the buffer is full.
RECENT_EVENTS: Deque[Dict[str, Any]] = deque(maxlen=BUFFER_SIZE)

# TOTAL_EVENTS counts how many telemetry events have ever been accepted
# since the service started.
TOTAL_EVENTS = 0


# --------------------------------------------------
# Helper: normalize an incoming telemetry event
# --------------------------------------------------
# This function converts the raw payload into a cleaner event object.
# We keep a fixed top-level structure so dashboard preview is easier to read.
def _build_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    original_payload = payload.get("payload", payload)
    event = {
        # server-side receive timestamp
        "received_ts_ms": int(time.time() * 1000),
        # optional metadata from client payload
        "source": original_payload.get("source", "unknown"),
        "event_type": original_payload.get("event_type", "unknown"),
        "mode": payload.get("mode", original_payload.get("mode", "unknown")),
        # ingestion path metadata
        "ingest_path": "via-admin" if "payload" in payload else "direct",
        # keep the full original payload for experiments
        "payload": payload,
    }
    return event


# --------------------------------------------------
# GET /health
# --------------------------------------------------
# Simple liveness endpoint.
# Dashboard will use this to decide whether telemetry service is reachable.
@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "service": "telemetry-api",
    }


# --------------------------------------------------
# POST /event
# --------------------------------------------------
# Accept one telemetry event from a client or from admin-api.
#
# Example input:
# {
#   "source": "fish-game-client",
#   "event_type": "matchmaking",
#   "mode": "sync",
#   "login_ms": 123,
#   "match_search_ms": 456
# }
@app.post("/event")
def create_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    global TOTAL_EVENTS

    event = _build_event(payload)

    # Print for local debugging.
    # This is useful in early project stages.
    print("[TELEMETRY]", event)

    # Store into recent buffer
    RECENT_EVENTS.append(event)

    # Increase total accepted event counter
    TOTAL_EVENTS += 1

    return {
        "accepted": True,
        "stored": True,
        "recent_buffer_count": len(RECENT_EVENTS),
        "total_events": TOTAL_EVENTS,
    }


# --------------------------------------------------
# GET /events/recent
# --------------------------------------------------
# Return the most recent N telemetry events.
# Dashboard preview panel will use this endpoint.
@app.get("/events/recent")
def get_recent_events(limit: int = 10) -> Dict[str, Any]:
    safe_limit = max(1, min(limit, BUFFER_SIZE))
    events: List[Dict[str, Any]] = list(RECENT_EVENTS)[-safe_limit:]

    return {
        "count": len(events),
        "events": events,
    }


# --------------------------------------------------
# GET /stats/summary
# --------------------------------------------------
# Return simple telemetry summary values.
# Dashboard /metrics already expects:
# - recent_buffer_count
# - total_events
@app.get("/stats/summary")
def get_stats_summary() -> Dict[str, Any]:
    return {
        "ok": True,
        "service": "telemetry-api",
        "recent_buffer_count": len(RECENT_EVENTS),
        "total_events": TOTAL_EVENTS,
        "buffer_size": BUFFER_SIZE,
    }