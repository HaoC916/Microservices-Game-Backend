# Nakama Stack (Single-Machine Dev)
Back to root README: [`../README.md`](../README.md)

This folder runs the local development stack in one compose:
- `postgres`
- `nakama`
- `admin-api`

## Run
```bash
cd nakama
docker compose up -d --build
docker compose ps
```

## Verify
```bash
curl http://localhost:8000/health
curl http://localhost:7351
```

## Published Ports
- `5432`: Postgres
- `7349`: Nakama gRPC
- `7350`: Nakama API
- `7351`: Nakama Console
- `8000`: admin-api

## Notes
- Local runtime data mount: `./data:/nakama/data`
- Console credentials are defined in `nakama/docker-compose.yml`.

## Deploy on GCP VM (Nakama VM)
See root deployment guide: [`../README.md#gcp-vm-deployment-guide`](../README.md#gcp-vm-deployment-guide)

1. SSH into Nakama VM (Ubuntu 22.04 minimal).
2. Install Docker + Compose v2 (from root README guide).
3. Copy/extract repo onto VM.
4. Start only Nakama + Postgres for split mode:
```bash
cd ~/cmpt756-final-project/nakama
docker compose up -d --build postgres nakama
docker compose ps
```
5. Verify:
```bash
curl http://localhost:7351
```

Required firewall ports (target tag `nakama`):
- `7350/tcp`: Nakama API
- `7351/tcp`: Nakama Console
- `7349/tcp`: optional (gRPC / advanced clients)
