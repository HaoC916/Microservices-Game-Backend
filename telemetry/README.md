# Telemetry Service (Standalone)
Back to root README: [`../README.md`](../README.md)

This compose runs only `telemetry-api` (FastAPI) so it can be deployed and tested independently as a standalone telemetry microservice.

The telemetry service is responsible for:

- receiving telemetry events
- storing a recent in-memory event buffer
- exposing recent telemetry data
- exposing simple summary statistics for dashboard integration

It is separated from `admin-api` so telemetry can be evaluated as its own microservice in local and cloud deployment experiments.

## Endpoints
- `GET /health`
- `POST /event`
- `GET /events/recent`
- `GET /stats/summary`

## Run
```bash
cd telemetry
docker compose up -d --build
docker compose ps
```

## Verify
```bash
curl http://localhost:8200/health
curl http://localhost:8200/stats/summary
```

Post an example event:
```bash
curl -X POST http://localhost:8200/event \
  -H "Content-Type: application/json" \
  -d '{
    "source": "fish-game-client",
    "event_type": "matchmaking",
    "mode": "sync",
    "login_ms": 120,
    "match_search_ms": 350
  }'
```

Then verify recent events:
```bash
curl http://localhost:8200/events/recent?limit=10
```

## Environment Variables
- `TELEMETRY_BUFFER_SIZE`: in-memory recent event buffer size

## Event Notes
The telemetry service accepts event payloads either:
- directly from a client
- indirectly from admin-api when admin forwards telemetry in sync mode
In the forwarding case, the original client payload may be wrapped inside a top-level payload field.

## Role in the Project
Telemetry can be used in two ways during experiments:
- direct ingestion: client posts directly to telemetry-api
- forwarded ingestion: client posts to admin-api, and admin forwards telemetry to telemetry-api in sync mode
This separation allows the project to study how service coupling and deployment choices affect latency.

## Deploy on GCP VM (Admin VM)
See root deployment guide: [`../README.md#gcp-vm-deployment-guide`](../README.md#gcp-vm-deployment-guide)

1. SSH into Telemetry VM.
2. Install Docker + Compose v2.
3. Copy/extract repo onto VM.
4. Configure upstream Nakama endpoint:
```bash
cd ~/cmpt756-final-project/telemetry
cp .env.example .env
# edit .env and set:
# TELEMETRY_BUFFER_SIZE=200
```
5. Start service:
```bash
docker compose up -d --build
docker compose ps
```
6. Validate locally on Admin VM:
```bash
curl http://localhost:8200/health
curl http://localhost:8200/stats/summary
```
7. Validate externally (if firewall allows):
```bash
curl http://<telemetry_vm_external_ip>:8200/health
curl http://<telemetry_vm_external_ip>:8200/stats/summary
```

Required firewall ports (target tag `telemetryapi`):
- `8200/tcp`: telemetry-api HTTP