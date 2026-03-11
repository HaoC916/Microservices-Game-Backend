# Load Testing Scaffold (k6)

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
