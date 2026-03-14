# dashboard-api

FastAPI backend service for the CMPT 756 dashboard module.

This service acts as a lightweight aggregation/query layer for dashboard presentation.

In the current project phase, it queries `admin-api` for:
- service health
- config
- Nakama reachability
- recent telemetry buffers

## Endpoints
- `GET /health`
- `GET /metrics`
- `GET /summary`

## Endpoint Behavior

### `GET /health`
Returns the local liveness status of `dashboard-api`.

### `GET /metrics`
Returns dashboard-friendly metrics.
Current gameplay metrics are placeholders, but recent telemetry count is queried from `admin-api`.

### `GET /summary`
Aggregates multiple upstream results from `admin-api`, including:
- `/health`
- `/config`
- `/nakama/api`
- `/nakama/console`
- `/telemetry/recent`

If Nakama is not reachable, this endpoint may return a degraded result.

## Environment Variables
- `DASHBOARD_MODE` (default: `placeholder`)
- `ADMIN_API_BASE_URL` (default for Docker: `http://host.docker.internal:8000`)
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
export DASHBOARD_MODE=placeholder
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
curl http://localhost:8100/summary
```

## Notes
```text
dashboard-api depends on admin-api for current upstream aggregation
If admin-api is unavailable, dashboard data will be incomplete
If Nakama is unavailable, summary output may show degraded upstream status
```