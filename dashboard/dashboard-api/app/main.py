from fastapi import FastAPI

app = FastAPI(title="dashboard-api", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return {
        "online_players": 0,
        "active_matches": 0,
        "matchmaking_queue": 0,
        "peak_online_players": 0,
    }
