"""Extra experiment, attempt 2 (alternating measurements of fixed1 and p3b): analysis.
Usage: python scripts/plot_extra2.py
Reads raw/extra2/<version>_c<C>_r<rep>.csv and logs/extra2_cpu_<version>_c<C>_r<rep>.log.
Throughput = HTTP 200 answers per second in the window 5 s to 70 s of each run (as in plot_part2.py).
A run is called disturbed if more than one instance answered or if more than 100 requests failed.
Writes figures/fig_extra2.csv/.png (one line per run), figures/extra2_pairs.csv (p3b against fixed1 for each
C and repetition, measured one after the other) and figures/extra2_summary.csv.
"""
import csv, glob, os, re, statistics
from collections import Counter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WIN_START, WIN_END = 5.0, 70.0
TAGS = ["fixed1", "p3b"]

def cpu_busy(path):
    if not os.path.exists(path):
        return float("nan"), float("nan")
    idle, col = [], None
    for line in open(path):
        parts = line.split()
        if "id" in parts and "us" in parts:
            col = parts.index("id"); continue
        if col is not None and parts and all(p.lstrip("-").isdigit() for p in parts) and len(parts) > col:
            idle.append(int(parts[col]))
    idle = idle[1:]
    return (100 - statistics.mean(idle), 100 - min(idle)) if idle else (float("nan"), float("nan"))

data = {}
for path in sorted(glob.glob("raw/extra2/*_c*_r*.csv")):
    m = re.match(r"(.+)_c(\d+)_r(\d+)\.csv$", os.path.basename(path))
    if not m or m.group(1) not in TAGS:
        continue
    tag, C, rep = m.group(1), int(m.group(2)), int(m.group(3))
    rows = list(csv.DictReader(open(path)))
    if not rows:
        continue
    t0 = min(float(r["T_START"]) for r in rows)
    ok_all = [r for r in rows if r["STATUS"] == "200"]
    win = [r for r in ok_all if WIN_START <= float(r["T_START"]) - t0 < WIN_END]
    lat = [float(r["LATENCY_MS"]) for r in win]
    srv = [float(r["SERVER_MS"]) for r in win if r["SERVER_MS"]]
    cm, cx = cpu_busy(f"logs/extra2_cpu_{tag}_c{C}_r{rep}.log")
    n_failed = len(rows) - len(ok_all)
    inst = len({r["INSTANCE"] for r in ok_all if r["INSTANCE"]})
    codes = Counter(r["STATUS"] for r in rows if r["STATUS"] != "200")
    data[(tag, C, rep)] = dict(
        n_requests=len(rows), n_failed=n_failed, instances=inst, thr=len(win) / (WIN_END - WIN_START),
        lat_med=statistics.median(lat) if lat else float("nan"),
        srv_med=statistics.median(srv) if srv else float("nan"), cpu_mean=cm, cpu_max=cx,
        disturbed=(inst != 1 or n_failed > 100), codes=dict(codes))

def mean_of(tag, C, key, clean=False):
    v = [d[key] for (t, c, _), d in data.items() if t == tag and c == C and d[key] == d[key] and not (clean and d["disturbed"])]
    return statistics.mean(v) if v else float("nan")

Cs = sorted({k[1] for k in data})
os.makedirs("figures", exist_ok=True)
with open("figures/fig_extra2.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["version", "C_concurrency", "rep", "n_requests", "n_failed", "instances_serving", "disturbed",
                "throughput_rps", "latency_median_ms", "server_median_ms", "client_cpu_busy_mean_pct", "client_cpu_busy_max_pct",
                "non_200_codes"])
    for (tag, C, rep), d in sorted(data.items()):
        w.writerow([tag, C, rep, d["n_requests"], d["n_failed"], d["instances"], int(d["disturbed"]), round(d["thr"], 2),
                    round(d["lat_med"], 1), round(d["srv_med"], 1), round(d["cpu_mean"], 1), round(d["cpu_max"], 1),
                    " ".join(f"{k}:{v}" for k, v in d["codes"].items())])

pairs = []
for C in Cs:
    for rep in (1, 2):
        a, b = data.get(("fixed1", C, rep)), data.get(("p3b", C, rep))
        if a and b:
            pairs.append([C, rep, round(a["thr"], 2), round(b["thr"], 2), round(b["thr"] / a["thr"], 3),
                          round(a["lat_med"], 1), round(b["lat_med"], 1), round(b["srv_med"] - a["srv_med"], 1),
                          int(a["disturbed"] or b["disturbed"])])
with open("figures/extra2_pairs.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["C_concurrency", "rep", "fixed1_throughput_rps", "p3b_throughput_rps", "ratio_p3b_over_fixed1",
                "fixed1_latency_median_ms", "p3b_latency_median_ms", "p3b_minus_fixed1_server_median_ms", "pair_has_disturbed_run"])
    w.writerows(pairs)

def saturated(tag, clean):
    pts = {C: mean_of(tag, C, "thr", clean) for C in Cs}
    pts = {C: x for C, x in pts.items() if x == x}
    if not pts:
        return float("nan"), []
    peak = max(pts.values()); sat = {C: x for C, x in pts.items() if x >= 0.9 * peak}
    return statistics.mean(sat.values()), sorted(sat)

fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
style = {"fixed1": ("o-", "C3", "original start command (fixed1)"), "p3b": ("s-", "C0", "--threads 4 (p3b)")}
for tag in TAGS:
    mk, col, lab = style[tag]
    xs = [C for C in Cs if any((tag, C, r) in data for r in (1, 2))]
    ax[0].plot(xs, [mean_of(tag, C, "thr") for C in xs], mk, color=col, label=lab)
    ax[1].plot(xs, [mean_of(tag, C, "lat_med") for C in xs], mk, color=col, label=lab)
    for rep in (1, 2):
        pts = [(C, data[(tag, C, rep)]) for C in xs if (tag, C, rep) in data]
        ax[0].plot([p[0] for p in pts], [p[1]["thr"] for p in pts], ".", color="gray", alpha=0.5)
        dis = [p for p in pts if p[1]["disturbed"]]
        ax[0].plot([p[0] for p in dis], [p[1]["thr"] for p in dis], "x", color="k")
ax[0].set_ylim(bottom=0); ax[0].set_ylabel("throughput (HTTP 200 per second); x = disturbed run")
ax[1].set_yscale("log"); ax[1].set_ylabel("median latency (ms, log scale)")
for a in ax:
    a.set_xscale("log", base=2); a.set_xlabel("C (simultaneous Locust users)"); a.grid(alpha=0.3, which="both"); a.legend(fontsize=8)
fig.suptitle("One instance (class B1), dataset base (U=1000, P=20, F=20), alternating measurements: 1 worker vs 4 threads", fontsize=10)
fig.tight_layout(); fig.savefig("figures/fig_extra2.png", dpi=150); plt.close(fig)

rows = []
for tag in TAGS:
    sa, ca = saturated(tag, False); sc, cc = saturated(tag, True)
    runs = [d for (t, _, _), d in data.items() if t == tag]
    rows.append([tag, len(runs), sum(d["disturbed"] for d in runs), round(sa, 1), round(sc, 1),
                 round(mean_of(tag, 64, "lat_med"), 1), round(statistics.median(d["srv_med"] for d in runs), 1),
                 round(max(d["cpu_mean"] for d in runs), 1)])
ratios = [r[4] for r in pairs]
clean_ratios = [r[4] for r in pairs if not r[8]]
with open("figures/extra2_summary.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["version", "n_runs", "n_disturbed_runs", "saturated_throughput_rps_all_runs",
                "saturated_throughput_rps_without_disturbed", "latency_median_C64_ms", "server_median_all_runs_ms",
                "max_client_cpu_busy_mean_pct"])
    w.writerows(rows)
print("version  runs  disturbed  sat_thr(all)  sat_thr(clean)  lat_med_C64  srv_med  max_cpu_mean%")
for r in rows:
    print(f"{r[0]:<8} {r[1]:<5} {r[2]:<10} {str(r[3]):<13} {str(r[4]):<15} {str(r[5]):<12} {str(r[6]):<8} {r[7]}")
if ratios:
    print(f"paired ratio p3b / fixed1 (throughput): mean {statistics.mean(ratios):.2f}, min {min(ratios):.2f}, max {max(ratios):.2f}, "
          f"p3b higher in {sum(r > 1 for r in ratios)} of {len(ratios)} pairs; "
          f"without disturbed pairs: mean {statistics.mean(clean_ratios):.2f} ({len(clean_ratios)} pairs)" if clean_ratios else "")
bad = {k: d for k, d in data.items() if d["disturbed"]}
print("disturbed runs:", {f"{k[0]} C={k[1]} r{k[2]}": (d["instances"], d["n_failed"], d["codes"]) for k, d in sorted(bad.items())} or "none")
