#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import base64
import csv
import json
import os
import random
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode, urlparse

import requests
import websocket


# -----------------------------
# Helpers: stats
# -----------------------------
def percentile(sorted_vals: List[float], p: float) -> float:
    """p in [0,100]. Uses linear interpolation."""
    if not sorted_vals:
        return float("nan")
    if p <= 0:
        return sorted_vals[0]
    if p >= 100:
        return sorted_vals[-1]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def summarize_ms(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"count": 0, "mean": float("nan"), "median": float("nan"), "p95": float("nan"), "p99": float("nan")}
    vals = sorted(values)
    mean = sum(vals) / len(vals)
    median = percentile(vals, 50)
    return {
        "count": len(vals),
        "mean": mean,
        "median": median,
        "p95": percentile(vals, 95),
        "p99": percentile(vals, 99),
    }


def rand_id(prefix: str = "dev") -> str:
    tail = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16))
    return f"{prefix}_{tail}"


# -----------------------------
# Nakama API client (HTTP 7350)
# -----------------------------
@dataclass
class NakamaConfig:
    base_url: str          # e.g. http://localhost:7350
    server_key: str        # defaultkey
    ws_path: str = "/ws"   # realtime websocket base path


class NakamaHTTP:
    def __init__(self, cfg: NakamaConfig, timeout_s: float = 3.0):
        self.cfg = cfg
        self.timeout_s = timeout_s
        # Nakama uses Basic auth with server key as username and empty password: base64("server_key:")
        b64 = base64.b64encode(f"{cfg.server_key}:".encode("utf-8")).decode("utf-8")
        self._basic_auth_header = {"Authorization": f"Basic {b64}"}
        self._session = requests.Session()
        ws_path = cfg.ws_path.strip()
        if not ws_path.startswith("/"):
            ws_path = f"/{ws_path}"
        self._ws_path = ws_path

    def authenticate_device(self, device_id: str, create: bool = True) -> Tuple[str, float]:
        """
        POST /v2/account/authenticate/device
        Returns (jwt_token, latency_ms)
        """
        url = f"{self.cfg.base_url}/v2/account/authenticate/device"
        payload = {"id": device_id, "create": create}
        t0 = time.perf_counter()
        r = self._session.post(url, json=payload, headers=self._basic_auth_header, timeout=self.timeout_s)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        r.raise_for_status()
        data = r.json()
        token = data.get("token")
        if not token:
            raise RuntimeError(f"Missing token in response: {data}")
        return token, dt_ms

    def _ws_base_url(self) -> str:
        parsed = urlparse(self.cfg.base_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 7350
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return f"{scheme}://{host}:{port}{self._ws_path}"

    def _ws_candidates(self, token: str) -> List[str]:
        base = self._ws_base_url()
        return [
            f"{base}?{urlencode({'token': token})}",
            f"{base}?{urlencode({'token': token, 'format': 'json'})}",
            f"{base}?{urlencode({'token': token, 'lang': 'en', 'status': 'false'})}",
        ]

    def connect_ws(self, token: str) -> Tuple[websocket.WebSocket, str]:
        attempted: List[str] = []
        last_error: Optional[str] = None
        for ws_url in self._ws_candidates(token):
            attempted.append(ws_url)
            ws = websocket.WebSocket()
            try:
                ws.connect(ws_url, timeout=self.timeout_s)
                return ws, ws_url
            except Exception as exc:
                last_error = str(exc)
                try:
                    ws.close()
                except Exception:
                    pass

        raise RuntimeError(
            f"Unable to connect realtime WS. tried={attempted} last_error={last_error}"
        )

    @staticmethod
    def _find_key(obj: Any, wanted: str) -> Any:
        if isinstance(obj, dict):
            if wanted in obj:
                return obj[wanted]
            for value in obj.values():
                found = NakamaHTTP._find_key(value, wanted)
                if found is not None:
                    return found
        elif isinstance(obj, list):
            for item in obj:
                found = NakamaHTTP._find_key(item, wanted)
                if found is not None:
                    return found
        return None

    def matchmaker_add_ws(self, token: str, min_count: int = 2, max_count: int = 2, query: str = "*") -> Tuple[str, float, str]:
        """
        Nakama realtime WS call:
          {"cid":"1","matchmaker_add":{...}}
        Returns (ticket, latency_ms, ws_endpoint_used).
        """
        ws, ws_url = self.connect_ws(token)
        payload = {
            "cid": "1",
            "matchmaker_add": {
                "query": query,
                "min_count": min_count,
                "max_count": max_count,
                "string_properties": {},
                "numeric_properties": {},
            },
        }
        t0 = time.perf_counter()
        try:
            ws.send(json.dumps(payload, separators=(",", ":")))
            deadline = time.perf_counter() + self.timeout_s

            while True:
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    raise TimeoutError(f"Timed out waiting for matchmaker_ticket (ws={ws_url})")
                ws.settimeout(remaining)
                raw = ws.recv()
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8", errors="replace")

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                mm_ticket = self._find_key(data, "matchmaker_ticket")
                if mm_ticket is None:
                    continue

                if isinstance(mm_ticket, dict):
                    ticket = mm_ticket.get("ticket")
                else:
                    ticket = mm_ticket
                if not ticket:
                    continue

                dt_ms = (time.perf_counter() - t0) * 1000.0
                return str(ticket), dt_ms, ws_url
        finally:
            try:
                ws.close()
            except Exception:
                pass


# -----------------------------
# Admin telemetry (HTTP 8000)
# -----------------------------
def post_telemetry_sync(admin_base: str, payload: dict, timeout_s: float = 2.0) -> float:
    """
    POST admin-api /telemetry/event and wait for response.
    Returns latency_ms.
    """
    url = f"{admin_base}/telemetry/event"
    t0 = time.perf_counter()
    r = requests.post(url, json=payload, timeout=timeout_s)
    dt_ms = (time.perf_counter() - t0) * 1000.0
    r.raise_for_status()
    return dt_ms


def post_telemetry_async_fire_and_forget(admin_base: str, payload: dict, timeout_s: float = 2.0) -> None:
    """
    Fire-and-forget telemetry send. We do not measure this latency as part of critical path.
    """
    url = f"{admin_base}/telemetry/event"
    try:
        requests.post(url, json=payload, timeout=timeout_s)
    except Exception:
        # best-effort: ignore errors in async mode
        return


# -----------------------------
# Worker (one virtual user)
# -----------------------------
@dataclass
class RunConfig:
    nakama_base: str
    admin_base: str
    server_key: str
    telemetry_mode: str        # off|async|sync
    vus: int
    iters: int
    sleep_ms: int
    out_jsonl: str
    summary_csv: str
    timeout_nakama_s: float
    timeout_admin_s: float
    ws_path: str


def vu_worker(vu_id: int, cfg: RunConfig) -> List[dict]:
    """
    Each VU uses a stable device id (so we don't create infinite accounts).
    For each iteration:
      - authenticate_device (login)
      - matchmaker_add
      - telemetry: sync/off/async
    """
    results = []
    nk = NakamaHTTP(NakamaConfig(cfg.nakama_base, cfg.server_key, cfg.ws_path), timeout_s=cfg.timeout_nakama_s)
    device_id = f"cmpt756_vu{vu_id}_{rand_id('device')}"
    token: Optional[str] = None

    for i in range(cfg.iters):
        row = {
            "ts_epoch_ms": int(time.time() * 1000),
            "vu": vu_id,
            "iter": i,
            "login_ms": None,
            "match_search_ms": None,
            "telemetry_sync_ms": None,
            "ws_endpoint": None,
            "ok": True,
            "error": None,
        }

        try:
            token, login_ms = nk.authenticate_device(device_id=device_id, create=True)
            row["login_ms"] = login_ms

            _, match_ms, ws_endpoint = nk.matchmaker_add_ws(token=token, min_count=2, max_count=2, query="*")
            row["match_search_ms"] = match_ms
            row["ws_endpoint"] = ws_endpoint

            # Telemetry event payload (align with your current schema)
            tele_payload = {
                "event": "bench_sample",
                "client_tag": "bench",
                "client_mode": cfg.telemetry_mode,
                "login_ms": login_ms,
                "match_search_ms": match_ms,
                "ts_ms": int(time.time() * 1000),
            }

            if cfg.telemetry_mode == "sync":
                tms = post_telemetry_sync(cfg.admin_base, tele_payload, timeout_s=cfg.timeout_admin_s)
                row["telemetry_sync_ms"] = tms
            elif cfg.telemetry_mode == "async":
                # fire-and-forget in a background thread (still best-effort)
                # Not measured as critical-path
                post_telemetry_async_fire_and_forget(cfg.admin_base, tele_payload, timeout_s=cfg.timeout_admin_s)
            else:
                # off
                pass

        except Exception as e:
            row["ok"] = False
            ws_ep = row.get("ws_endpoint")
            if ws_ep:
                row["error"] = f"{e} (ws_endpoint={ws_ep})"
            else:
                row["error"] = str(e)

        results.append(row)

        if cfg.sleep_ms > 0:
            time.sleep(cfg.sleep_ms / 1000.0)

    return results


# -----------------------------
# Main
# -----------------------------
def main():
    ap = argparse.ArgumentParser(description="CMPT756 Nakama benchmark harness (login + matchmaker + telemetry coupling).")
    ap.add_argument("--nakama", required=True, help="Nakama base URL, e.g. http://localhost:7350")
    ap.add_argument("--admin", required=True, help="Admin API base URL, e.g. http://localhost:8000")
    ap.add_argument("--server-key", default="defaultkey", help="Nakama server key (default: defaultkey)")
    ap.add_argument("--mode", choices=["off", "async", "sync"], default="async", help="Telemetry mode (client-side)")
    ap.add_argument("--vus", type=int, default=1, help="Virtual users (threads).")
    ap.add_argument("--iters", type=int, default=20, help="Iterations per VU.")
    ap.add_argument("--sleep-ms", type=int, default=2000, help="Cooldown between iterations per VU (ms).")
    ap.add_argument("--out", default="logs/run.jsonl", help="Output JSONL path.")
    ap.add_argument("--summary", default="summary.csv", help="Output summary CSV path.")
    ap.add_argument("--nakama-timeout", type=float, default=3.0, help="Nakama HTTP timeout seconds.")
    ap.add_argument("--admin-timeout", type=float, default=2.0, help="Admin HTTP timeout seconds.")
    ap.add_argument("--ws-path", default="/ws", help='Nakama realtime websocket path (default: "/ws").')
    args = ap.parse_args()

    cfg = RunConfig(
        nakama_base=args.nakama.rstrip("/"),
        admin_base=args.admin.rstrip("/"),
        server_key=args.server_key,
        telemetry_mode=args.mode,
        vus=args.vus,
        iters=args.iters,
        sleep_ms=args.sleep_ms,
        out_jsonl=args.out,
        summary_csv=args.summary,
        timeout_nakama_s=args.nakama_timeout,
        timeout_admin_s=args.admin_timeout,
        ws_path=args.ws_path,
    )

    os.makedirs(os.path.dirname(cfg.out_jsonl) or ".", exist_ok=True)

    all_rows: List[dict] = []
    with ThreadPoolExecutor(max_workers=cfg.vus) as ex:
        futs = [ex.submit(vu_worker, vu_id, cfg) for vu_id in range(1, cfg.vus + 1)]
        for f in as_completed(futs):
            all_rows.extend(f.result())

    # Write JSONL
    with open(cfg.out_jsonl, "w", encoding="utf-8") as w:
        for r in all_rows:
            w.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Extract stats
    login_vals = [r["login_ms"] for r in all_rows if r["ok"] and isinstance(r["login_ms"], (int, float))]
    match_vals = [r["match_search_ms"] for r in all_rows if r["ok"] and isinstance(r["match_search_ms"], (int, float))]
    tele_vals = [r["telemetry_sync_ms"] for r in all_rows if r["ok"] and isinstance(r["telemetry_sync_ms"], (int, float))]

    login_s = summarize_ms(login_vals)
    match_s = summarize_ms(match_vals)
    tele_s = summarize_ms(tele_vals) if cfg.telemetry_mode == "sync" else {"count": 0, "mean": float("nan"), "median": float("nan"), "p95": float("nan"), "p99": float("nan")}

    # Write summary CSV (single row)
    header = [
        "nakama", "admin", "mode", "vus", "iters_per_vu", "total_samples",
        "login_mean_ms", "login_p95_ms", "login_p99_ms",
        "match_search_mean_ms", "match_search_p95_ms", "match_search_p99_ms",
        "telemetry_sync_mean_ms", "telemetry_sync_p95_ms", "telemetry_sync_p99_ms",
        "error_count"
    ]
    error_count = sum(1 for r in all_rows if not r["ok"])
    row = [
        cfg.nakama_base, cfg.admin_base, cfg.telemetry_mode, cfg.vus, cfg.iters, len(all_rows),
        login_s["mean"], login_s["p95"], login_s["p99"],
        match_s["mean"], match_s["p95"], match_s["p99"],
        tele_s["mean"], tele_s["p95"], tele_s["p99"],
        error_count
    ]

    write_header = not os.path.exists(cfg.summary_csv)
    with open(cfg.summary_csv, "a", newline="", encoding="utf-8") as f:
        cw = csv.writer(f)
        if write_header:
            cw.writerow(header)
        cw.writerow(row)

    print("=== DONE ===")
    print(f"raw_jsonl: {cfg.out_jsonl}")
    print(f"summary_csv: {cfg.summary_csv}")
    print(f"mode={cfg.telemetry_mode} vus={cfg.vus} iters={cfg.iters} errors={error_count}")
    print("login:", login_s)
    print("match_search:", match_s)
    if cfg.telemetry_mode == "sync":
        print("telemetry_sync:", tele_s)


if __name__ == "__main__":
    main()
