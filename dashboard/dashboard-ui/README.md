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
Default Local URL
By default, Vite serves the UI at:
```bash
http://localhost:5173
```

## Backend Dependency

This UI expects the backend dashboard API to be available at:
```bash
http://localhost:8100
```
The API base URL is currently defined in src/App.tsx:
```bash
const API_BASE = "http://localhost:8100";
```
If the backend is deployed elsewhere, update this value.

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
```
- Then open:
```bash
http://localhost:5173
```

### Notes
```text
The page automatically refreshes every 10 seconds
Current gameplay metrics are placeholders
This UI is currently intended for local development and demonstration
```