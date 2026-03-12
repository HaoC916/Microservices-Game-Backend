# CMPT756 Final Project

## Project Summary
Course project for CMPT 756 (Distributed & Cloud Systems).

Project title: Cloud Deployment Choices Impacting Performance of a Web Application Using Microservices Architecture.

Workload choice: Nakama (open-source game backend) as a microservices-based, web-facing service platform.

Current scope in this repository: local baseline using Docker Compose, initial k6 load-testing scaffold, and experiment logging templates. We do not vendor Nakama source code.

## Team
- Chenzheng Li, `cla429@sfu.ca`
- Luna Sang, `dsa133@sfu.ca`
- Ryan Chen, `hca116@sfu.ca`
- Tracy Cui, `lca213@sfu.ca`
- Wenxiang He, `wha61@sfu.ca`

## Repository Layout
- `infra/nakama/docker-compose.yml`: Local Nakama + Postgres baseline stack.
- `infra/nakama/README.md`: Folder-scoped run/verify commands.
- `infra/nakama/data/`: Local mounted data/config path for Nakama container.
- `loadtest/k6_smoke.js`: Fixed smoke test (10 VUs, 60s).
- `loadtest/k6_matrix.js`: Parametric test via `VUS` and `DURATION`.
- `loadtest/README.md`: k6 usage guide (Docker-first).
- `docs/experiment-log.md`: Template for recording benchmark runs.
- `infra/deprecated/teeworlds/`: Archived old scaffold, not active.
- `THIRD_PARTY_NOTICES.md`: Third-party attribution and dependency notes.

## Quick Start (Local Baseline)
Prereqs: Docker Engine + Docker Compose v2 (`docker compose`).

Start stack:
```bash
cd infra/nakama
docker compose up -d
docker compose ps
```

Verify:
```bash
docker compose ps
ss -lntp | grep -E '5432|7350|7351' || true
curl -i http://localhost:7351
```
- Console URL: `http://localhost:7351`
- Port `7350` is API/RPC, not a normal webpage.
- Console credentials are configured in compose/config files (not documented here).

Stop stack:
```bash
cd infra/nakama
docker compose down
```

Reset stack (including DB volume):
```bash
cd infra/nakama
docker compose down -v
```

## Fish Game (Godot) Experiment Client
Fish Game (`fishgame-godot`) is used as a client workload generator for Nakama (the backend under test).

Prereqs:
- Godot `3.5.3`
- Reachable Nakama endpoint

Configure endpoint:
- Edit `fishgame-godot/autoload/Online.gd`:
  - `nakama_host` (target host/IP)
  - `nakama_port` (default `7350`)
  - `nakama_server_key` (default `defaultkey`)

Hotkeys (MatchScreen):
- `F8`: print resolved log file path to Godot Output
- `F9`: toggle autotest matchmaking (`20` iterations, `2s` cooldown)
- `F10`: toggle optional help overlay (hidden by default)

Metrics:
- `login_ms`: login request latency
- `create_account_ms`: account creation request latency
- `match_search_ms`: matchmaking request -> ticket/response latency
- `match_found_ms`: matchmaking start -> match found event (requires 2 clients)
- `create_match_ms`: private match create -> join callback latency
- `join_match_ms`: join match request -> join callback latency

Logs:
- Godot Output panel
- `user://cmpt756_latency_log.txt` (client-local log file)

Teammate quick test checklist:
1. Start Nakama backend.
2. Run Fish Game client and log in.
3. Press `F9` on MatchScreen and wait for repeated samples.
4. Press `F8`, locate `cmpt756_latency_log.txt`, and share the file.

## Run Load Tests (k6 via Docker)
Run from repo root:

Smoke:
```bash
docker run --rm -i --network host -v "$PWD:/work" grafana/k6 run /work/loadtest/k6_smoke.js
docker run --rm -i --network host -v "$PWD:/work" grafana/k6 run -e BASE_URL="http://localhost:7351" /work/loadtest/k6_smoke.js
```

Matrix:
```bash
docker run --rm -i --network host -v "$PWD:/work" grafana/k6 run -e VUS=10 -e DURATION=60s /work/loadtest/k6_matrix.js
docker run --rm -i --network host -v "$PWD:/work" grafana/k6 run -e VUS=50 -e DURATION=60s /work/loadtest/k6_matrix.js
docker run --rm -i --network host -v "$PWD:/work" grafana/k6 run -e VUS=100 -e DURATION=60s /work/loadtest/k6_matrix.js
```

## Record Results (`docs/experiment-log.md`)
- After each run, copy p50/p95/p99, request rate, and error rate from k6 summary output.
- Record environment details (local/VM/K8s), target URL, and notes (CPU/memory anomalies).
- Keep one row per test configuration for clean comparisons.

## Troubleshooting
- Ports in use (`5432`, `7350`, `7351`): run `ss -lntp` and adjust port mappings in `infra/nakama/docker-compose.yml`.
- Service not healthy: run `cd infra/nakama && docker compose ps`.
- Logs for diagnosis: run `cd infra/nakama && docker compose logs -f postgres` and `cd infra/nakama && docker compose logs -f nakama`.
- Clean restart if state is broken: run `cd infra/nakama && docker compose down -v` then `docker compose up -d`.

## Licensing
See `THIRD_PARTY_NOTICES.md` for Nakama/PostgreSQL third-party notices.
