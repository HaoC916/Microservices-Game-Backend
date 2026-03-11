# Nakama Baseline (Compose)

Use Docker Compose v2+ commands (`docker compose`, not `docker-compose`).

## Run
```bash
docker compose up -d
docker compose ps
```

## Verify
```bash
docker compose ps
ss -lntp | grep -E '7350|7351|5432' || true
curl -i http://localhost:7351
```
- Console URL: `http://localhost:7351`
- Port `7350` is API/RPC, not a regular web page.

## Logs
```bash
docker compose logs -f nakama
docker compose logs -f postgres
```

## Stop / Reset
```bash
docker compose down
docker compose down -v
```
