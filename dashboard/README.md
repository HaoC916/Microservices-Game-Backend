# Dashboard Service (Placeholder)
Back to root README: [`../README.md`](../README.md)

This is a stub service for future dashboard/reporting APIs.

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
```

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
4. (Optional placeholder config) set upstream env values in `.env` for future integration:
```bash
cd ~/cmpt756-final-project/dashboard
cp .env.example .env
# optional placeholders for future wiring:
# ADMIN_API_BASE_URL=http://<admin_vm_external_ip>:8000
# NAKAMA_API_BASE_URL=http://<nakama_vm_external_ip>:7350
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
```

Required firewall ports (target tag `dashboardapi`):
- `8100/tcp`: dashboard-api HTTP
