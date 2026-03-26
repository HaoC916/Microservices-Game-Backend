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

By default, Vite serves the UI at:
```bash
http://localhost:5173
```

## Backend Dependency

This UI expects dashboard-api to be available at:
```bash
http://localhost:8100
```
The API base URL is currently defined in src/App.tsx:
```bash
const API_BASE = "http://localhost:8100";
```
If the backend is deployed elsewhere, update this value.

### Current Architecture Role

dashboard-ui is a presentation layer only.

It does not talk directly to admin-api, telemetry-api, or Nakama.
Instead, it communicates with dashboard-api, which aggregates and proxies backend data.

Current flow:

dashboard-ui -> dashboard-api -> admin-api / telemetry-api / nakama-api

### Future Direction

The current UI is designed so that experiment metrics can later be populated from:

parsed experiment log summaries
exported summary files
or a database-backed backend source

### Notes

```text
The page automatically refreshes every 3 seconds
Gameplay Metrics are still placeholder values
Experiment Metrics are connected to dashboard-api /experiments/summary
Events Preview shows recent telemetry events, not all local client logs
Newer telemetry events are shown first
The preview panel has a fixed height and vertical scrolling
This UI is currently intended for local development, testing, and demonstration
```