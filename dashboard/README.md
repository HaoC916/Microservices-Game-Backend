# Dashboard Service (Standalone)
Back to root README: [`../README.md`](../README.md)

This compose runs only `dashboard-api` (FastAPI) so it can be deployed/tested independently.

The dashboard service acts as a lightweight aggregation/query layer for dashboard presentation. In the current project phase, it queries `admin-api` for service status, Nakama reachability, and recent telemetry buffers.

## Run
```bash
cd dashboard
docker compose up -d --build
docker compose ps
```

## Verify
```bash
# curl http://localhost:8100/health
# curl http://localhost:8100/metrics
# curl http://localhost:8100/summary
```
## Environment Variables
- `DASHBOARD_MODE`: dashboard mode (placeholder by default)
- `ADMIN_API_BASE_URL`: upstream admin-api base URL
- `REQUEST_TIMEOUT_SECONDS`: HTTP timeout when querying admin-api

## Current Scope
- Provide a lightweight dashboard backend for experiment monitoring
- Aggregate selected upstream information from admin-api
- Return dashboard-friendly JSON for future UI integration
- Current Endpoints:
  - GET /health
  - GET /metrics
  - GET /summary

## Planned Scope
- Aggregate metrics for experiments:
  - online players
  - active matches
  - matchmaking queue depth
  - peak online users
- Planned future endpoints:
  - trend summaries (p50/p95/p99 by mode/deployment)
  - experiment comparison snapshots
- Planned persistence backend can be added later (not in this placeholder).

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
