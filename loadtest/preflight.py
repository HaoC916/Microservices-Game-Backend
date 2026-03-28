#!/usr/bin/env python3
import argparse
import json
import sys
import time
from urllib.parse import urljoin

import requests


def ok(msg):  # simple colored-ish output
    print(f"[OK]  {msg}")


def bad(msg):
    print(f"[BAD] {msg}")


def warn(msg):
    print(f"[WARN] {msg}")


def get_json(url, timeout):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def get_text(url, timeout):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text


def head(url, timeout):
    r = requests.head(url, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    return r.headers


def check_http_json(name, url, timeout):
    try:
        data = get_json(url, timeout)
        ok(f"{name}: GET {url} -> 200")
        return True, data
    except Exception as e:
        bad(f"{name}: GET {url} failed: {e}")
        return False, None


def check_http_head(name, url, timeout):
    try:
        _ = head(url, timeout)
        ok(f"{name}: HEAD {url} -> 200")
        return True
    except Exception as e:
        bad(f"{name}: HEAD {url} failed: {e}")
        return False


def pretty_short(obj, max_len=240):
    s = json.dumps(obj, ensure_ascii=False)
    return s if len(s) <= max_len else s[:max_len] + "..."


def main():
    ap = argparse.ArgumentParser(description="CMPT756 preflight checks for nakama/admin/telemetry/dashboard")
    ap.add_argument("--nakama", default="http://localhost:7350", help="Nakama API base, e.g. http://IP:7350")
    ap.add_argument("--console", default="http://localhost:7351", help="Nakama console base, e.g. http://IP:7351")
    ap.add_argument("--admin", default="http://localhost:8000", help="Admin API base, e.g. http://IP:8000")
    ap.add_argument("--telemetry", default="http://localhost:8200", help="Telemetry API base, e.g. http://IP:8200")
    ap.add_argument("--dashboard", default="http://localhost:8100", help="Dashboard API base, e.g. http://IP:8100")
    ap.add_argument("--timeout", type=float, default=2.5, help="HTTP timeout seconds")
    ap.add_argument("--retries", type=int, default=2, help="retries per check")
    args = ap.parse_args()

    # endpoints
    admin_health = urljoin(args.admin + "/", "health")
    admin_config = urljoin(args.admin + "/", "config")
    admin_nk_api = urljoin(args.admin + "/", "nakama/api")
    admin_nk_console = urljoin(args.admin + "/", "nakama/console")

    tel_health = urljoin(args.telemetry + "/", "health")
    tel_recent = urljoin(args.telemetry + "/", "events/recent?limit=1")
    tel_summary = urljoin(args.telemetry + "/", "stats/summary")

    dash_metrics = urljoin(args.dashboard + "/", "metrics")
    dash_summary = urljoin(args.dashboard + "/", "summary")

    # Nakama: console is easiest to verify as "web"
    nk_console = args.console
    nk_api_root = args.nakama  # returns empty body but should 200 OK

    failures = 0

    def retry(fn, *a):
        last = None
        for i in range(args.retries + 1):
            try:
                return fn(*a)
            except Exception as e:
                last = e
                time.sleep(0.2)
        raise last

    print("=== PRECHECK: service liveness ===")

    # 1) Admin alive
    ok_admin, admin_h = check_http_json("admin-api health", admin_health, args.timeout)
    if not ok_admin:
        failures += 1

    # 2) Telemetry alive
    ok_tel, tel_h = check_http_json("telemetry-api health", tel_health, args.timeout)
    if not ok_tel:
        failures += 1

    # 3) Dashboard alive
    ok_dash, dash_m = check_http_json("dashboard-api metrics", dash_metrics, args.timeout)
    if not ok_dash:
        failures += 1

    # 4) Nakama console alive (HTML)
    if not check_http_head("nakama console", nk_console, args.timeout):
        failures += 1

    # 5) Nakama API gateway alive (HEAD)
    nk_health = urljoin(args.nakama + "/", "healthcheck")
    ok_nk, _ = check_http_json("nakama api healthcheck", nk_health, args.timeout)
    if not ok_nk:
        failures += 1

    print("\n=== PRECHECK: upstream connectivity (what matters) ===")

    # Admin -> Nakama
    ok1, j1 = check_http_json("admin -> nakama/api", admin_nk_api, args.timeout)
    if not ok1 or not j1 or not j1.get("ok", False):
        failures += 1
    else:
        ok(f"admin reaches nakama/api: {pretty_short(j1)}")

    ok2, j2 = check_http_json("admin -> nakama/console", admin_nk_console, args.timeout)
    if not ok2 or not j2 or not j2.get("ok", False):
        failures += 1
    else:
        ok(f"admin reaches nakama/console: {pretty_short(j2)}")

    # Admin config sanity (catch your earlier typo: 'http:10.138.0.7:8200')
    okc, cfg = check_http_json("admin config", admin_config, args.timeout)
    if okc and cfg:
        tbase = str(cfg.get("telemetry_api_base_url", ""))
        if "host.docker.internal" in tbase:
            warn(f"admin telemetry_api_base_url uses host.docker.internal (works on some hosts, breaks on GCE): {tbase}")
        if "http:" in tbase and "http://" not in tbase:
            warn(f"admin telemetry_api_base_url looks malformed (missing //): {tbase}")
        ok(f"admin config: {pretty_short(cfg)}")

    # Telemetry read paths
    ok3, _ = check_http_json("telemetry summary", tel_summary, args.timeout)
    if not ok3:
        failures += 1

    ok4, _ = check_http_json("telemetry recent", tel_recent, args.timeout)
    if not ok4:
        # not fatal if empty? it still should return 200 with count=0
        failures += 1

    # Dashboard summary should show upstream status (best end-to-end check)
    oks, ds = check_http_json("dashboard summary", dash_summary, args.timeout)
    if not oks or not ds:
        failures += 1
    else:
        upstreams = ds.get("upstreams", {})
        # Fail if any upstream has ok:false
        bad_up = []
        for k, v in upstreams.items():
            if isinstance(v, dict) and v.get("ok") is False:
                bad_up.append((k, v.get("error") or v.get("status_code")))
        if bad_up:
            failures += 1
            bad(f"dashboard sees broken upstream(s): {bad_up}")
        else:
            ok("dashboard upstreams all OK")

    print("\n=== RESULT ===")
    if failures == 0:
        ok("ALL CHECKS PASSED ✅ (4 services configured + connected)")
        sys.exit(0)
    else:
        bad(f"{failures} check(s) failed ❌ (see above)")
        sys.exit(2)


if __name__ == "__main__":
    main()