import re
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

DOCS = Path("docs")
FILES = {
    "Local Async": DOCS / "local_logs_async.txt",
    "Local Sync":  DOCS / "local_logs_sync.txt",
    "GCP Async":   DOCS / "gc_logs_async.txt",
    "GCP Sync":    DOCS / "gc_logs_sync.txt",
}
OUT = DOCS / "figures"
OUT.mkdir(parents=True, exist_ok=True)

LAT_RE = re.compile(r"\[LATENCY\].*?\b([a-zA-Z0-9_]+)=([0-9]+)\b")

def parse(path: Path):
    d = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = LAT_RE.search(line)
        if m:
            k, v = m.group(1), int(m.group(2))
            d.setdefault(k, []).append(v)
    return d

def mean_p95(vals):
    a = np.array(vals, dtype=float)
    return float(a.mean()), float(np.percentile(a, 95))

def bar_mean_p95(labels, means, p95s, title, ylabel, outpath):
    x = np.arange(len(labels))
    y = np.array(means)
    top = np.array(p95s)
    yerr = np.vstack([np.zeros_like(y), np.maximum(top - y, 0)])

    plt.figure(figsize=(6.8, 3.6))
    plt.bar(x, y)
    plt.errorbar(x, y, yerr=yerr, fmt="none", capsize=4)
    plt.xticks(x, labels)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, axis="y", alpha=0.3)

    # annotate values
    for i in range(len(labels)):
        plt.text(i, y[i] + 1.0, f"mean={y[i]:.1f}\np95={top[i]:.1f}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close()

def main():
    logs = {k: parse(p) for k, p in FILES.items()}

    # -------- Figure 1: Sync E2E critical path --------
    # E2E = match_search_ms + telemetry_sync_ms (only sync runs)
    e2e_labels = ["Local", "GCP"]
    e2e_means = []
    e2e_p95s = []

    for key in ["Local Sync", "GCP Sync"]:
        ms = logs[key].get("match_search_ms", [])
        ts = logs[key].get("telemetry_sync_ms", [])
        n = min(len(ms), len(ts))
        e2e = [ms[i] + ts[i] for i in range(n)]
        m, p95 = mean_p95(e2e)
        e2e_means.append(m)
        e2e_p95s.append(p95)

    bar_mean_p95(
        e2e_labels, e2e_means, e2e_p95s,
        title="Sync Critical Path (E2E = match_search + telemetry_sync)",
        ylabel="Latency (ms)",
        outpath=OUT / "REPORT_sync_e2e_mean_p95.png",
    )

    # -------- Figure 2 (optional): telemetry overhead only --------
    tele_labels = ["Local", "GCP"]
    tele_means = []
    tele_p95s = []
    for key in ["Local Sync", "GCP Sync"]:
        vals = logs[key].get("telemetry_sync_ms", [])
        m, p95 = mean_p95(vals)
        tele_means.append(m)
        tele_p95s.append(p95)

    bar_mean_p95(
        tele_labels, tele_means, tele_p95s,
        title="Telemetry Sync Overhead (telemetry_sync_ms)",
        ylabel="Latency (ms)",
        outpath=OUT / "REPORT_telemetry_sync_mean_p95.png",
    )

    print("Saved:")
    print(OUT / "REPORT_sync_e2e_mean_p95.png")
    print(OUT / "REPORT_telemetry_sync_mean_p95.png")

if __name__ == "__main__":
    main()