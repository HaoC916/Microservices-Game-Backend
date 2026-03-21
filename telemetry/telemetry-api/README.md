# telemetry-api (FastAPI)

Independent admin/observability microservice for CMPT756 experiments.

## Endpoints
- `GET /health`
- `POST /event`
- `GET /events/recent`
- `GET /stats/summary`


## Environment Variables
- `TELEMETRY_BUFFER_SIZE` (default: `200`)

## Run Locally (Python)
```bash
cd telemetry/telemetry-api
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8200
```

## Run with Docker
```bash
cd telemetry/telemetry-api
docker build -t cmpt756-telemetry-api .
docker run --rm -p 8200:8200 \
  -e TELEMETRY_BUFFER_SIZE=200 \
  cmpt756-telemetry-api
```

## Run via Compose
Use telemetry/docker-compose.yml and start from telemetry:
```bash
docker compose up -d --build
```
