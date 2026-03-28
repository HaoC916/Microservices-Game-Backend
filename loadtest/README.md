# Load Testing Scaffold (k6)
Back to root README: [`../README.md`](../README.md)

This folder contains initial k6 scripts for Nakama baseline checks.

## A) Run with Docker (Recommended)

From repo root:

```bash
docker run --rm -i --network host -v "$PWD:/work" grafana/k6 run /work/loadtest/k6_smoke.js
docker run --rm -i --network host -v "$PWD:/work" grafana/k6 run -e BASE_URL="http://localhost:7351" /work/loadtest/k6_smoke.js
```

Matrix examples:

```bash
docker run --rm -i --network host -v "$PWD:/work" grafana/k6 run -e VUS=10 -e DURATION=60s /work/loadtest/k6_matrix.js
docker run --rm -i --network host -v "$PWD:/work" grafana/k6 run -e VUS=50 -e DURATION=60s /work/loadtest/k6_matrix.js
docker run --rm -i --network host -v "$PWD:/work" grafana/k6 run -e VUS=100 -e DURATION=60s /work/loadtest/k6_matrix.js
```

## B) Native k6 (Optional)

You can install k6 natively and run:

```bash
k6 run loadtest/k6_smoke.js
k6 run -e VUS=50 -e DURATION=60s loadtest/k6_matrix.js
```

Docker is the default/recommended path for this project.

## Target a Remote VM

Set:

```bash
BASE_URL="http://<VM_EXTERNAL_IP>:7351"
```

Then pass it as an env var to k6 (Docker or native).  
If needed, open firewall access for port `7351`.

## Python Bench Harness (`bench.py`)

This repo also includes `loadtest/bench.py` for login + matchmaking + telemetry-coupling experiments.

### Run (local)

```bash
python loadtest/bench.py \
  --nakama http://localhost:7350 \
  --admin http://localhost:8000 \
  --mode sync \
  --vus 10 \
  --iters 20 \
  --sleep-ms 2000 \
  --out logs/local_sync.jsonl \
  --summary logs/summary.csv
```

### Run (GCE)

```bash
python loadtest/bench.py \
  --nakama http://<NAKAMA_VM_EXTERNAL_IP>:7350 \
  --admin http://<ADMIN_VM_EXTERNAL_IP>:8000 \
  --mode sync \
  --vus 10 \
  --iters 20 \
  --sleep-ms 2000 \
  --out logs/gce_sync.jsonl \
  --summary logs/summary.csv
```

### Throughput metrics

- `elapsed_seconds`: wall-clock time for the whole run (all VUs).
- `login_throughput_rps = login_success_count / elapsed_seconds`
- `match_search_throughput_rps = match_search_success_count / elapsed_seconds`
- `telemetry_throughput_rps = telemetry_success_count / elapsed_seconds` (sync mode only)
- `overall_throughput_ops = successful_iterations / elapsed_seconds`

`successful_iterations` means login + match_search both succeeded. Telemetry is counted separately.

### Error breakdown output

- Each JSONL row includes:
  - `stage_failed`: `none|login|match_search|telemetry`
  - `error_type`: stable category
  - `error_detail`: raw message
- Summary CSV includes totals per stage.
- Detailed category counts are written to a separate CSV:
  - default: `<summary>_errors.csv`
  - override: `--errors-out <path>`
