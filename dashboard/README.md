# Dashboard Service
Back to root README: [`../README.md`](../README.md)

This directory contains the dashboard module for the CMPT 756 project.

It currently includes:

- `dashboard-api`: a FastAPI backend service for dashboard aggregation/query
- `dashboard-ui`: a React + TypeScript + Vite frontend for dashboard visualization

The dashboard service is designed as a lightweight presentation layer. In the current project phase, `dashboard-api` queries `admin-api` for service status, Nakama reachability, and recent telemetry buffers.

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
- Aggregate selected upstream information from admin-api
- Return dashboard-friendly JSON for future UI integration
- Current Endpoints:
  - GET /health
  - GET /metrics
  - GET /summary
```

## Planned Scope
```text
- Aggregate metrics for experiments:
  - online players
  - active matches
  - matchmaking queue depth
  - peak online users
- Add experiment-focused summaries:
  - p50 / p95 / p99 comparison by deployment mode
  - experiment comparison snapshots
- Optionally add persistence or a dedicated stats service later
```

## Environment Variables
```bash
For dashboard-api:
- `DASHBOARD_MODE`: dashboard mode (placeholder by default)
- `ADMIN_API_BASE_URL`: upstream admin-api base URL
- `REQUEST_TIMEOUT_SECONDS`: HTTP timeout when querying admin-api
```

## Verify
```bash
curl http://localhost:8100/health
curl http://localhost:8100/metrics
curl http://localhost:8100/summary
```

## Recommended Local Startup Order
### Terminal 1: Start admin-api
```bash
cd admin/admin-api
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
### Terminal 2: Start dashboard-api
```bash
cd dashboard/dashboard-api
source .venv/bin/activate
export ADMIN_API_BASE_URL=http://localhost:8000
export DASHBOARD_MODE=placeholder
export REQUEST_TIMEOUT_SECONDS=2
uvicorn app.main:app --host 0.0.0.0 --port 8100
```

### Terminal 3: Start dashboard-ui
```bash
cd dashboard/dashboard-ui
npm install
npm run dev
```
- Then open:
```bash
http://localhost:5173
```

### Local Validation Example
You can manually add a telemetry event and observe the UI update:
```bash
curl -X POST http://localhost:8000/telemetry/event \
  -H "Content-Type: application/json" \
  -d '{"event_type":"player_login","player_id":"p2","source":"ui-test"}'
```
```text
Expected result:
- Recent Telemetry count increases
- Telemetry Preview shows the new event
```

### Local Development Notes
```text
dashboard-ui reads data from dashboard-api
dashboard-api queries admin-api
admin-api checks Nakama status and serves recent telemetry buffers
If Nakama is not running locally, the UI will still render, but Nakama-related panels may show degraded or unavailable status
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
# curl http://localhost:8100/summary
```

7. Validate externally (if firewall allows):
```bash
# curl http://<dashboard_vm_external_ip>:8100/health
# curl http://<dashboard_vm_external_ip>:8100/metrics
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