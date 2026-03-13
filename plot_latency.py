import re
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# ---------- Config ----------
DOCS_DIR = Path("docs")
LOG_FILES = {
    "Local-Async": DOCS_DIR / "local_logs_async.txt",
    "Local-Sync":  DOCS_DIR / "local_logs_sync.txt",
    "GCP-Async":   DOCS_DIR / "gc_logs_async.txt",
    "GCP-Sync":    DOCS_DIR / "gc_logs_sync.txt",
}
OUT_DIR = DOCS_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LAT_RE = re.compile(r"\[LATENCY\].*?\b([a-zA-Z0-9_]+)=([0-9]+)\b")

def parse_latency_file(path: Path) -> dict[str, list[int]]:
    metrics: dict[str, list[int]] = {}
    text = path.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        m = LAT_RE.search(line)
        if not m:
            continue
        name, val = m.group(1), int(m.group(2))
        metrics.setdefault(name, []).append(val)
    return metrics

def pct(a: np.ndarray, p: float) -> float:
    return float(np.percentile(a, p)) if a.size else float("nan")

def summary(vals: list[int]) -> dict:
    a = np.array(vals, dtype=float)
    return {
        "n": int(a.size),
        "mean": float(a.mean()),
        "p50": pct(a, 50),
        "p95": pct(a, 95),
        "p99": pct(a, 99),
        "min": float(a.min()),
        "max": float(a.max()),
    }

def save_fig(path: Path):
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()

# ---------- Plot styles (bigger, 2-column friendly) ----------
plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
})

def hboxplot(title: str, xlabel: str, groups: list[tuple[str, list[int]]], outpath: Path):
    labels = [g[0] for g in groups]
    data = [g[1] for g in groups]

    plt.figure(figsize=(7.2, 3.6))  # good for 2-column paper when scaled
    plt.boxplot(
        data,
        vert=False,
        labels=labels,
        showfliers=False,  # reduce clutter for small N
    )
    plt.grid(True, axis="x", alpha=0.3)
    plt.title(title)
    plt.xlabel(xlabel)
    save_fig(outpath)

def ecdf(title: str, xlabel: str, groups: list[tuple[str, list[int]]], outpath: Path, xlim=None):
    plt.figure(figsize=(7.2, 3.6))
    for label, vals in groups:
        a = np.sort(np.array(vals, dtype=float))
        if a.size == 0:
            continue
        y = np.arange(1, len(a) + 1) / len(a)
        plt.step(a, y, where="post", label=label)
    plt.grid(True, alpha=0.3)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("ECDF")
    if xlim:
        plt.xlim(*xlim)
    # legend outside (clean)
    plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), borderaxespad=0.0)
    save_fig(outpath)

def bar_mean_p95(title: str, ylabel: str, groups: list[tuple[str, list[int]]], outpath: Path):
    labels = [g[0] for g in groups]
    means = []
    p95s = []
    for _, vals in groups:
        a = np.array(vals, dtype=float)
        means.append(a.mean() if a.size else np.nan)
        p95s.append(np.percentile(a, 95) if a.size else np.nan)

    x = np.arange(len(labels))
    plt.figure(figsize=(7.2, 3.6))
    # bars = mean; error bar top = p95 (we show mean->p95 as asymmetric error)
    y = np.array(means)
    top = np.array(p95s)
    yerr = np.vstack([np.zeros_like(y), np.maximum(top - y, 0)])

    plt.bar(x, y)
    plt.errorbar(x, y, yerr=yerr, fmt="none", capsize=4)
    plt.xticks(x, labels, rotation=0)
    plt.grid(True, axis="y", alpha=0.3)
    plt.title(title)
    plt.ylabel(ylabel)
    save_fig(outpath)

def main():
    parsed = {name: parse_latency_file(path) for name, path in LOG_FILES.items()}

    # --- Match search across all 4 ---
    match_groups = [(k, parsed[k].get("match_search_ms", [])) for k in LOG_FILES.keys()]
    hboxplot(
        "Match Search Latency (match_search_ms)",
        "Latency (ms)",
        match_groups,
        OUT_DIR / "pretty_match_search_hbox.png",
    )
    bar_mean_p95(
        "Match Search: Mean with p95 (higher = worse)",
        "Latency (ms)",
        match_groups,
        OUT_DIR / "pretty_match_search_mean_p95.png",
    )
    # ECDF with tight xlim to make differences visible
    all_match = [v for _, vals in match_groups for v in vals]
    if all_match:
        lo, hi = min(all_match), max(all_match)
        pad = max(2, int((hi - lo) * 0.1))
        ecdf(
            "Match Search ECDF (match_search_ms)",
            "Latency (ms)",
            match_groups,
            OUT_DIR / "pretty_match_search_ecdf.png",
            xlim=(lo - pad, hi + pad),
        )

    # --- Telemetry sync only (Local Sync vs GCP Sync) ---
    tele_groups = [(k, parsed[k].get("telemetry_sync_ms", [])) for k in ["Local-Sync", "GCP-Sync"]]
    hboxplot(
        "Telemetry Sync Overhead (telemetry_sync_ms)",
        "Latency (ms)",
        tele_groups,
        OUT_DIR / "pretty_telemetry_sync_hbox.png",
    )
    bar_mean_p95(
        "Telemetry Sync: Mean with p95 (higher = worse)",
        "Latency (ms)",
        tele_groups,
        OUT_DIR / "pretty_telemetry_sync_mean_p95.png",
    )
    all_tele = [v for _, vals in tele_groups for v in vals]
    if all_tele:
        lo, hi = min(all_tele), max(all_tele)
        pad = max(2, int((hi - lo) * 0.1))
        ecdf(
            "Telemetry Sync ECDF (telemetry_sync_ms)",
            "Latency (ms)",
            tele_groups,
            OUT_DIR / "pretty_telemetry_sync_ecdf.png",
            xlim=(lo - pad, hi + pad),
        )

    # --- E2E in sync mode only ---
    e2e_groups = []
    for k in ["Local-Sync", "GCP-Sync"]:
        ms = parsed[k].get("match_search_ms", [])
        ts = parsed[k].get("telemetry_sync_ms", [])
        n = min(len(ms), len(ts))
        e2e = [ms[i] + ts[i] for i in range(n)]
        e2e_groups.append((k.replace("-Sync", "-Sync-E2E"), e2e))

    hboxplot(
        "Critical Path in Sync Mode (match_search + telemetry_sync)",
        "Latency (ms)",
        e2e_groups,
        OUT_DIR / "pretty_sync_e2e_hbox.png",
    )
    bar_mean_p95(
        "Sync Critical Path: Mean with p95 (higher = worse)",
        "Latency (ms)",
        e2e_groups,
        OUT_DIR / "pretty_sync_e2e_mean_p95.png",
    )
    all_e2e = [v for _, vals in e2e_groups for v in vals]
    if all_e2e:
        lo, hi = min(all_e2e), max(all_e2e)
        pad = max(2, int((hi - lo) * 0.1))
        ecdf(
            "Sync Critical Path ECDF (E2E)",
            "Latency (ms)",
            e2e_groups,
            OUT_DIR / "pretty_sync_e2e_ecdf.png",
            xlim=(lo - pad, hi + pad),
        )

    # --- Print small textual summary for sanity ---
    print("=== Summary ===")
    for g in LOG_FILES.keys():
        ms = parsed[g].get("match_search_ms", [])
        if ms:
            s = summary(ms)
            print(f"{g:11s} match_search_ms n={s['n']} mean={s['mean']:.2f} p95={s['p95']:.2f} max={s['max']:.0f}")
    for g in ["Local-Sync", "GCP-Sync"]:
        ts = parsed[g].get("telemetry_sync_ms", [])
        if ts:
            s = summary(ts)
            print(f"{g:11s} telemetry_sync_ms n={s['n']} mean={s['mean']:.2f} p95={s['p95']:.2f} max={s['max']:.0f}")

    print(f"\nSaved nicer figures to: {OUT_DIR.resolve()}")

if __name__ == "__main__":
    main()