# admin-api (FastAPI)

Independent admin/observability microservice for CMPT756 experiments.

## Endpoints
- `GET /health`
- `GET /config`
- `GET /nakama/api`
- `GET /nakama/console`
- `POST /telemetry/event`

## Environment Variables
- `NAKAMA_HOST` (default: `localhost`)
- `NAKAMA_API_PORT` (default: `7350`)
- `NAKAMA_CONSOLE_PORT` (default: `7351`)
- `TELEMETRY_MODE` (default: `async`, allowed: `off|sync|async`)
- `TELEMETRY_API_BASE_URL`: base URL of standalone telemetry service

## Run Locally (Python)
```bash
cd admin/admin-api
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Run with Docker
```bash
cd admin/admin-api
docker build -t cmpt756-admin-api .
docker run --rm -p 8000:8000 -e NAKAMA_HOST=host.docker.internal cmpt756-admin-api
```

## Run via Compose
Use `admin/docker-compose.yml` and start from `admin`:
```bash
docker compose up -d --build
```
