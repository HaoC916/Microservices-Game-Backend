#!/usr/bin/env python3
import argparse
import json
import os
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


def summarize_latency(df: pd.DataFrame, col: str) -> dict:
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
    ap.add_argument("--local-async", required=True)
    ap.add_argument("--local-sync", required=True)
    ap.add_argument("--gce-async", required=True)
    ap.add_argument("--gce-sync", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary", required=True)
    args = ap.parse_args()

    ensure_parent_dir(args.out)
    ensure_parent_dir(args.summary)

    series = [
        ("Local-Async", read_jsonl(args.local_async)),
        ("Local-Sync",  read_jsonl(args.local_sync)),
        ("GCE-Async",   read_jsonl(args.gce_async)),
        ("GCE-Sync",    read_jsonl(args.gce_sync)),
    ]

    stats = []
    for name, df in series:
        st = summarize_latency(df, "match_search_ms")
        st["name"] = name
        stats.append(st)

    summary_df = pd.DataFrame(stats)[["name", "count", "p50", "p95", "p99", "mean"]]
    summary_df.to_csv(args.summary, index=False)

    labels = [x["name"] for x in stats]
    p50s = [x["p50"] for x in stats]
    p95s = [x["p95"] for x in stats]
    p99s = [x["p99"] for x in stats]

    x = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(10, 5), dpi=200)
    bars = ax.bar(x, p50s, width=0.65)

    # whisker: p50 -> p95
    for i in range(len(labels)):
        ax.vlines(x[i], p50s[i], p95s[i], linewidth=2)
        ax.hlines(p95s[i], x[i] - 0.12, x[i] + 0.12, linewidth=2)

    # p99 marker (small line)
    for i in range(len(labels)):
        ax.hlines(p99s[i], x[i] - 0.18, x[i] + 0.18, linewidth=3)

    ax.set_title("Match Search Tail Latency (p50 bar, p95 whisker, p99 line)")
    ax.set_ylabel("Latency (ms)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")

    # --- smart-ish label offsets to reduce overlap ---
    # place labels at different vertical offsets based on rank
    p99_sorted_idx = np.argsort(p99s)
    rank = {idx: r for r, idx in enumerate(p99_sorted_idx)}
    for i in range(len(labels)):
        r = rank[i]
        # stagger text: higher rank => bigger offset
        y = p99s[i]
        dy = 2 + r * 2
        ax.text(
            x[i], y + dy,
            f"p99={p99s[i]:.1f}\np95={p95s[i]:.1f}\np50={p50s[i]:.1f}",
            ha="center", va="bottom", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.8),
        )

    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()
    fig.savefig(args.out)
    print("saved:", args.out)
    print("summary:", args.summary)


if __name__ == "__main__":
    main()