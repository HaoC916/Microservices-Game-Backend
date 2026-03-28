# dashboard-api

FastAPI backend service for the CMPT 756 dashboard module.

This service acts as a lightweight aggregation and query layer for dashboard presentation.

In the current project phase, it aggregates and proxies data across multiple upstream services:

- `admin-api` for health, config, and telemetry mode control
- `telemetry-api` for telemetry health, recent events, and summary counters
- `nakama-api` for Nakama service reachability

It also exposes a temporary in-memory experiment summary interface for dashboard testing and future experiment data integration.

## Endpoints

- `GET /health`
- `GET /metrics`
- `GET /experiments/summary`
- `POST /experiments/summary`
- `POST /experiments/reset`
- `GET /telemetry/mode`
- `POST /telemetry/mode`
- `POST /telemetry/reset`
- `GET /summary`

---

### `POST /experiments/reset`
Clears the in-memory experiment summary state without restarting `dashboard-api`.

### `GET /telemetry/mode`
Proxies telemetry mode read requests to `admin-api`.

### `POST /telemetry/mode`
Proxies telemetry mode update requests to `admin-api`.

Allowed values:
- `off`
- `sync`
- `async`

### `POST /telemetry/reset`
Proxies telemetry reset requests to `telemetry-api`.

This allows `dashboard-ui` to clear telemetry state without calling `telemetry-api` directly.

### `GET /summary`
Aggregates multiple upstream results into one dashboard response.

Current upstream aggregation includes:
- `admin-api /health`
- `admin-api /config`
- `telemetry-api /health`
- `telemetry-api /events/recent?limit=10`
- `telemetry-api /stats/summary`
- Nakama API reachability

If one or more upstream checks fail, the summary response may return a degraded result.

---

## Current Architecture Role

`dashboard-api` is a presentation-side aggregation service.  
It does **not** own gameplay logic, telemetry ingestion, or admin control logic.

Current separation of responsibilities:

- `admin-api` = control / config / telemetry forwarding layer
- `telemetry-api` = telemetry ingestion / recent buffer / summary layer
- `nakama` = game backend
- `dashboard-api` = aggregation / presentation layer

---

## Experiment Metrics Note

The current `Experiment Metrics` support is intentionally lightweight.

Current phase:
- in-memory values can be written via `POST /experiments/summary`
- reset via `POST /experiments/reset`

Future phase:
- experiment values may be read from:
  - parsed experiment log files
  - exported summary files
  - a database-backed store

This design keeps the frontend API stable while allowing the backend data source to evolve later.

---

## Environment Variables
- `DASHBOARD_MODE` (default: `prototype`)
- `ADMIN_API_BASE_URL` (default: `http://host.docker.internal:8000`)
- `TELEMETRY_API_BASE_URL` (default: `http://host.docker.internal:8200`)
- `NAKAMA_API_BASE_URL` (default: `http://host.docker.internal:7350`)
- `REQUEST_TIMEOUT_SECONDS` (default: `2`)

## CORS
This service enables CORS for local frontend development on:
- `http://localhost:5173`
- `http://127.0.0.1:5173`

This allows `dashboard-ui` to fetch data from the browser during local development.

## Run Locally (Python)
```bash
cd dashboard/dashboard-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export ADMIN_API_BASE_URL=http://localhost:8000
export TELEMETRY_API_BASE_URL=http://localhost:8200
export NAKAMA_API_BASE_URL=http://localhost:7350
export DASHBOARD_MODE=prototype
export REQUEST_TIMEOUT_SECONDS=2

uvicorn app.main:app --host 0.0.0.0 --port 8100
```

## Run with Docker
```bash
cd dashboard
docker compose up -d --build
docker compose ps
```

## Verify
```bash
curl http://localhost:8100/health
curl http://localhost:8100/metrics
curl http://localhost:8100/experiments/summary
curl http://localhost:8100/summary
```

## Example: update experiment summary
```bash
curl -X POST http://localhost:8100/experiments/summary \
  -H "Content-Type: application/json" \
  -d '{
    "telemetry_mode": "sync",
    "sample_count": 20,
    "login_mean_ms": 120,
    "login_p95_ms": 180,
    "match_search_mean_ms": 350,
    "match_search_p95_ms": 420,
    "telemetry_sync_mean_ms": 18
  }'
```

## Example: reset experiment summary
```bash
curl -X POST http://localhost:8100/experiments/reset
```

## Example: change telemetry mode
```bash
curl -X POST http://localhost:8100/telemetry/mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"sync"}'
```

## Example: reset telemetry state
```bash
curl -X POST http://localhost:8100/telemetry/reset
```

## Notes
dashboard-api depends on multiple upstream for aggregation

If admin-api, telemetry-api, or nakama-api are unavailable, dashboard data may be incomplete

gameplay metrics are still placeholders; current real visibility mainly comes from service probes, telemetry preview, experiment summary values.