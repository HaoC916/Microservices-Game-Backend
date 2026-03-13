# Architecture Overview

## Service Diagram
```text
Fish Game Client (Godot)
        |
        | gameplay/auth/match APIs
        v
Nakama ---------------------> Postgres
  ^                            (Nakama-owned DB)
  |
  | synchronous HTTP checks
  |
admin-api (FastAPI)
  |
  | telemetry/event (currently in-memory)
  v
future: Pub/Sub -> Function (serverless)
```

## Coupling Notes
- Avoid shared DB:
  - `admin-api` never reads/writes Nakama/Postgres storage directly.
  - Service interaction is through HTTP APIs only.
- Synchronous calls add coupling:
  - `admin-api` health/check endpoints depend on Nakama availability and latency.
  - This is useful for measuring call-path coupling in experiments.
- Asynchronous telemetry reduces coupling:
  - Current in-memory telemetry endpoint is a placeholder.
  - Future event-driven telemetry (Pub/Sub + Function) decouples ingestion from core request path.
