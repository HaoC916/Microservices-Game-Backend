# Admin Service (Standalone)
Back to root README: [`../README.md`](../README.md)

This compose runs only `admin-api` (FastAPI) so it can be deployed/tested independently from Nakama.

## Run
```bash
cd admin
docker compose up -d --build
docker compose ps
```

## Verify
```bash
curl http://localhost:8000/health
curl http://localhost:8000/config
```

## Environment Variables
- `NAKAMA_HOST`: Nakama host/IP to check (split-VM target)
- `NAKAMA_API_PORT`: Nakama API port (`7350` by default)
- `NAKAMA_CONSOLE_PORT`: Nakama Console port (`7351` by default)
- `TELEMETRY_MODE`: admin ingestion mode (`off|sync|async`)
- `TELEMETRY_BUFFER_SIZE`: in-memory recent event buffer size

## Telemetry Payload Note
When fishgame posts telemetry, payload includes:
- `client_mode` (fishgame experiment mode)
- `client_tag` (`fishgame`)

This is separate from admin-api’s own `TELEMETRY_MODE`.

## Deploy on GCP VM (Admin VM)
See root deployment guide: [`../README.md#gcp-vm-deployment-guide`](../README.md#gcp-vm-deployment-guide)

1. SSH into Admin VM.
2. Install Docker + Compose v2.
3. Copy/extract repo onto VM.
4. Configure upstream Nakama endpoint:
```bash
cd ~/cmpt756-final-project/admin
cp .env.example .env
# edit .env and set:
# NAKAMA_HOST=<nakama_external_ip_or_dns>
```
5. Start service:
```bash
docker compose up -d --build
docker compose ps
```
6. Validate locally on Admin VM:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/nakama/api
```
7. Validate externally (if firewall allows):
```bash
curl http://<admin_vm_external_ip>:8000/health
curl http://<admin_vm_external_ip>:8000/config
```

Required firewall ports (target tag `adminapi`):
- `8000/tcp`: admin-api HTTP
