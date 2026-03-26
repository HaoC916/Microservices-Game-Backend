# telemetry-api (FastAPI)

Independent telemetry/observability microservice for CMPT756 experiments.

This service is responsible for:

- receiving telemetry events
- storing a recent in-memory event buffer
- exposing recent telemetry data for dashboard preview
- exposing simple summary counters for dashboard integration
- supporting local reset for repeated experiments

Telemetry is now separated from `admin-api`, so admin no longer acts as telemetry storage.  
Instead:

- `admin-api` acts as a telemetry forwarding/control layer
- `telemetry-api` acts as the real telemetry ingestion and summary service

---

## Endpoints
- `GET /health`
- `POST /event`
- `GET /events/recent`
- `GET /stats/summary`
- `POST /reset`

## Environment Variables
- `TELEMETRY_BUFFER_SIZE` (default: `200`)

## Event Model Notes

Telemetry-api stores a normalized top-level event structure for easier preview and summary use.

It also preserves the full original request body under payload.

This means recent telemetry entries may contain:
  - normalized top-level fields for dashboard readability
  - nested original payloads for debugging and experiment analysis

Typical field meanings:
  - source = original event source
  - event_type = original event type
  - mode = admin/runtime forwarding mode
  - ingest_path = direct or via-admin

Note: 
client_mode may appear inside the nested original payload and is client-defined.
It is different from the top-level telemetry mode, which reflects how admin forwarded the event.

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
