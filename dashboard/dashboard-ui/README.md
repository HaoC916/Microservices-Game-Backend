# dashboard-ui

Frontend UI for the CMPT 756 dashboard service.

This React + TypeScript + Vite application displays monitoring information from the local `dashboard-api`.

## Tech Stack
- React
- TypeScript
- Vite
- Tailwind CSS
- lucide-react icons

## Requirements
- Node.js
- npm

## Install
```bash
cd dashboard/dashboard-ui
npm install
```

## RUN
```bash
npm run dev
```

## Default Local URL
```bash
Default Local URL
By default, Vite serves the UI at:
http://localhost:5173
```

## Backend Dependency
```bash
This UI expects the backend dashboard API to be available at:
http://localhost:8100
The API base URL is currently defined in src/App.tsx:
const API_BASE = "http://localhost:8100";
If the backend is deployed elsewhere, update this value.
```

## Recommended Local Startup Order
### Terminal 1: Start admin-api
```bash
cd admin/admin-api
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
### Terminal 2: Start dashboard-api
```bash
cd dashboard/dashboard-api
source .venv/bin/activate
export ADMIN_API_BASE_URL=http://localhost:8000
export DASHBOARD_MODE=placeholder
export REQUEST_TIMEOUT_SECONDS=2
uvicorn app.main:app --host 0.0.0.0 --port 8100
```

### Terminal 3: Start dashboard-ui
```bash
cd dashboard/dashboard-ui
npm install
npm run dev
Then open:
http://localhost:5173
```

### Local Validation Example
```bash
You can manually add a telemetry event and observe the UI update:
curl -X POST http://localhost:8000/telemetry/event \
  -H "Content-Type: application/json" \
  -d '{"event_type":"player_login","player_id":"p2","source":"ui-test"}'
Expected result:
- Recent Telemetry count increases
- Telemetry Preview shows the new event
```

