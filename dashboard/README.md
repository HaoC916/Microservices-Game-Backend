# Dashboard Service
Back to root README: [`../README.md`](../README.md)

This directory contains the dashboard module for the CMPT 756 project.

It currently includes:

- `dashboard-api`: a FastAPI backend service for dashboard aggregation/query
- `dashboard-ui`: a React + TypeScript + Vite frontend for dashboard visualization

The dashboard service is designed as a lightweight presentation layer.

## Directory Structure
```text
dashboard/
├── dashboard-api/   # FastAPI backend
├── dashboard-ui/    # React frontend
├── docker-compose.yml
├── .env.example
└── README.md
```

## Current Scope
```text
- Provide a lightweight dashboard backend for experiment monitoring
- Aggregate selected upstream information from 
  - admin-api
  - telemetry-api
  - nakama-api
- Return dashboard-friendly JSON for UI display
- Support runtime telemetry mode switching through dashboard
- Support telemetry reset through dashboard
- Provide an Experiment Metrics summary endpoint for future experiment data ingestion
- Current Endpoints:
  - GET /health
  - GET /metrics
  - GET /summary
  - GET /experiments/summary
  - POST /experiments/summary
  - POST /experiments/reset
  - GET /telemetry/mode
  - POST /telemetry/mode
  - POST /telemetry/reset
```

## Planned Scope
```text
- Replace placeholder experiment metrics with real experiment summaries
- Read experiment results from:
  - parsed log files
  - exported summary files
  - or a future database-backed source
- Add richer experiment summaries such as:
  - mean / median / p95 / p99
  - deployment comparison snapshots
  - local vs GCP views
- Optionally add persistence or a dedicated stats service later
- Optionally revisit Nakama Console support if needed in a later dashboard phase
```

## Environment Variables
```bash
For dashboard-api:
- `DASHBOARD_MODE`: dashboard mode (placeholder by default)
- `ADMIN_API_BASE_URL`: upstream admin-api base URL
- `TELEMETRY_API_BASE_URL`: upstream telemetry-api base URL
- `NAKAMA_API_BASE_URL`: upstream Nakama API base URL
- `REQUEST_TIMEOUT_SECONDS`: HTTP timeout when querying admin-api
```

## Verify
```bash
curl http://localhost:8100/health
curl http://localhost:8100/metrics
curl http://localhost:8100/experiments/summary
curl http://localhost:8100/summary
```

## Recommended Local Startup Order
### Terminal 1: Start admin-api
```bash
cd admin/admin-api
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Terminal 2: Start telemetry-api
```bash
cd telemetry/telemetry-api
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8200
```

### Terminal 3: Start dashboard-api
```bash
cd dashboard/dashboard-api
source .venv/bin/activate
export ADMIN_API_BASE_URL=http://localhost:8000
export TELEMETRY_API_BASE_URL=http://localhost:8200
export NAKAMA_API_BASE_URL=http://localhost:7350
export DASHBOARD_MODE=prototype
export REQUEST_TIMEOUT_SECONDS=2
uvicorn app.main:app --host 0.0.0.0 --port 8100
```

### Terminal 4: Start dashboard-ui
```bash
cd dashboard/dashboard-ui
npm install
npm run dev
```
- Then open:
```bash
http://localhost:5173
```

## Local Validation Example

1. Change telemetry mode from dashboard backend
```bash
curl -X POST http://localhost:8100/telemetry/mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"sync"}'
```

2. Add a telemetry event through admin-api
```bash
curl -X POST http://localhost:8000/telemetry/event \
  -H "Content-Type: application/json" \
  -d '{"event_type":"player_login","player_id":"p2","source":"ui-test"}'
```
Expected result:
```text
- Telemetry Service event count increases
- Events Preview shows the new telemetry event
- Admin Service card reflects the current telemetry mode
```

3. Reset telemetry state through dashboard backend
```bash
curl -X POST http://localhost:8100/telemetry/reset
```
Expected result:
```text
- Telemetry count returns to zero
- Events Preview becomes empty
```

## Local Development Notes
```text
dashboard-ui reads data only from dashboard-api
dashboard-api aggregates/proxies data from admin-api, telemetry-api, and nakama-api
admin-api is currently the telemetry control / forwarding layer
telemetry-api is the telemetry ingestion / recent buffer / summary layer
dashboard currently checks Nakama API reachability only
Nakama Console is not currently part of dashboard monitoring
If Nakama is not running locally, the UI will still render, but Nakama-related sections may show unavailable or degraded status
Gameplay Metrics are still placeholders
Experiment Metrics are currently connected to dashboard-api but may still contain placeholder values until real experiment summaries are provided
```

## Experiment Metrics Note

The Experiment Metrics panel is already part of the UI.

Current phase:

values are served by dashboard-api /experiments/summary
data may be manually updated via POST /experiments/summary
data may be reset via POST /experiments/reset

Future phase:

dashboard-api may replace in-memory experiment values with:
parsed experiment logs
exported summary files
or a database-backed source

Expected long-term path:
```text
run experiments -> generate logs or summary -> dashboard-api reads summary -> dashboard-ui displays experiment metrics
```

## Deploy on GCP VM (Dashboard VM)
See root deployment guide: [`../README.md#gcp-vm-deployment-guide`](../README.md#gcp-vm-deployment-guide)

1. SSH into Dashboard VM.
2. Install Docker + Compose v2.
3. Copy/extract repo onto VM.
4. Configure upstream admin endpoint:
```bash
cd ~/cmpt756-final-project/dashboard
cp .env.example .env
# edit .env and set:
# ADMIN_API_BASE_URL=http://<admin_vm_external_ip>:8000
```
5. Start service:
```bash
docker compose up -d --build
docker compose ps
```
6. Validate:
```bash
# curl http://localhost:8100/health
# curl http://localhost:8100/metrics
# curl http://localhost:8100/experiments/summary
# curl http://localhost:8100/summary
```

7. Validate externally (if firewall allows):
```bash
# curl http://<dashboard_vm_external_ip>:8100/health
# curl http://<dashboard_vm_external_ip>:8100/metrics
# curl http://<dashboard_vm_external_ip>:8100/experiments/summary
# curl http://<dashboard_vm_external_ip>:8100/summary
```

Required firewall ports (target tag `dashboardapi`):
- `8100/tcp`: dashboard-api HTTP

### Cloud Deployment Note
```text
For local development, environment variables are exported in the shell before starting uvicorn.
For VM/container deployment, the same values should be provided through:
  .env
  docker-compose.yml
  VM/service configuration
```