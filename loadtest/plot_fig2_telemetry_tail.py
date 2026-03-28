#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def ensure_parent_dir(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_jsonl(path: str) -> pd.DataFrame:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return pd.DataFrame(rows)


def pct(x: np.ndarray, p: float) -> float:
    return float(np.percentile(x, p)) if len(x) else float("nan")


def summarize(df: pd.DataFrame, col: str) -> dict:
    s = df[col].dropna()
    s = s[s >= 0]
    arr = s.to_numpy(dtype=float)
    return {
        "count": int(len(arr)),
        "p50": pct(arr, 50),
        "p95": pct(arr, 95),
        "p99": pct(arr, 99),
        "mean": float(np.mean(arr)) if len(arr) else float("nan"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local-sync", required=True)
    ap.add_argument("--gce-sync", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--logy", action="store_true", help="use log y-axis (recommended)")
    args = ap.parse_args()

    ensure_parent_dir(args.out)
    ensure_parent_dir(args.summary)

    local_df = read_jsonl(args.local_sync)
    gce_df = read_jsonl(args.gce_sync)

    local = summarize(local_df, "telemetry_sync_ms")
    gce = summarize(gce_df, "telemetry_sync_ms")

    summary_df = pd.DataFrame([
        {"env": "Local sync", **local},
        {"env": "GCE sync", **gce},
    ])[["env", "count", "p50", "p95", "p99", "mean"]]
    summary_df.to_csv(args.summary, index=False)

    labels = ["Local sync", "GCE sync"]
    p50s = [local["p50"], gce["p50"]]
    p95s = [local["p95"], gce["p95"]]
    p99s = [local["p99"], gce["p99"]]
    x = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
    ax.bar(x, p50s, width=0.55)

    # whisker p50->p95 and p99 line
    for i in range(2):
        ax.vlines(x[i], p50s[i], p95s[i], linewidth=2)
        ax.hlines(p95s[i], x[i] - 0.12, x[i] + 0.12, linewidth=2)
        ax.hlines(p99s[i], x[i] - 0.20, x[i] + 0.20, linewidth=3)

    ax.set_title("Telemetry sync tail latency (Local vs GCE)\nBars=p50, whisker to p95, line=p99")
    ax.set_ylabel("Latency (ms)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)

    if args.logy:
        ax.set_yscale("log")  # this fixes “everything squished at bottom”
        ax.set_ylabel("Latency (ms, log scale)")

    # label boxes with offsets
    for i in range(2):
        y = p99s[i]
        ax.text(
            x[i], y * (1.10 if args.logy else 1.02),
            f"p50={p50s[i]:.1f}\np95={p95s[i]:.1f}\np99={p99s[i]:.1f}",
            ha="center", va="bottom", fontsize=10,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85),
        )

    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(args.out)
    print("saved:", args.out)
    print("summary:", args.summary)


if __name__ == "__main__":
    main()