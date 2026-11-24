"""Part 2: capacity analysis from raw/part2/n<N>_c<C>_r<rep>.csv (+ logs/part2_cpu_*.log).
Usage: python scripts/plot_part2.py
Produces figures/fig2a.csv/.png (throughput vs C), figures/fig2b.csv/.png (latency vs C, with the
Little's-law prediction) and figures/part2_checks.csv (instances, failures, client CPU per run).
Throughput = HTTP 200 responses per second in the steady window [T0+5 s, T0+70 s) of each run.
"""
import csv, glob, os, re, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAW, LOGS, OUT = "raw/part2", "logs", "figures"
WIN_START, WIN_END = 5.0, 70.0
os.makedirs(OUT, exist_ok=True)

def cpu_busy(path):
    """Mean and max CPU busy % of the client from a vmstat log (first sample, average since boot, dropped)."""
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
    if not idle:
        return float("nan"), float("nan")
    return 100 - statistics.mean(idle), 100 - min(idle)

def analyse(path):
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    ok_all = [r for r in rows if r["STATUS"] == "200"]
    t0 = min(float(r["T_START"]) for r in rows) if rows else 0.0
    win = [r for r in ok_all if WIN_START <= float(r["T_START"]) - t0 < WIN_END]
    lat = [float(r["LATENCY_MS"]) for r in win]
    srv = [float(r["SERVER_MS"]) for r in win if r["SERVER_MS"]]
    users = [int(r["USERS"]) for r in rows if r["USERS"] not in ("", None)]
    return dict(
        n_requests=len(rows), n_ok=len(ok_all), n_failed=len(rows) - len(ok_all),
        instances=len({r["INSTANCE"] for r in ok_all if r["INSTANCE"]}),
        throughput_rps=len(win) / (WIN_END - WIN_START),
        latency_median_ms=statistics.median(lat) if lat else float("nan"),
        latency_mean_ms=statistics.mean(lat) if lat else float("nan"),
        latency_p95_ms=sorted(lat)[int(0.95 * (len(lat) - 1))] if lat else float("nan"),
        server_median_ms=statistics.median(srv) if srv else float("nan"),
        users_max=max(users) if users else 0)

data = {}  # (N, C, rep) -> dict
for path in sorted(glob.glob(f"{RAW}/n*_c*_r*.csv")):
    m = re.match(r"n(\d+)_c(\d+)_r(\d+)\.csv$", os.path.basename(path))
    if not m:
        continue
    N, C, rep = map(int, m.groups())
    d = analyse(path)
    d["cpu_busy_mean_pct"], d["cpu_busy_max_pct"] = cpu_busy(f"{LOGS}/part2_cpu_n{N}_c{C}_r{rep}.log")
    data[(N, C, rep)] = d

Ns = sorted({k[0] for k in data})
Cs = sorted({k[1] for k in data})

def mean_rep(N, C, key):
    v = [d[key] for (n, c, _), d in data.items() if n == N and c == C and d[key] == d[key]]
    return statistics.mean(v) if v else float("nan")

def w(path, header, lines):
    with open(path, "w", newline="") as fh:
        cw = csv.writer(fh, lineterminator="\n"); cw.writerow(header); cw.writerows(lines)

# ---- Fig 2a: throughput vs C
w(f"{OUT}/fig2a.csv", ["N_instances", "C_concurrency", "rep", "throughput_rps", "n_requests", "n_failed", "instances_serving"],
  [[N, C, rep, round(d["throughput_rps"], 2), d["n_requests"], d["n_failed"], d["instances"]]
   for (N, C, rep), d in sorted(data.items())])
fig, a = plt.subplots(figsize=(6.5, 4.4))
for N in Ns:
    xs = [C for C in Cs if (N, C, 1) in data or (N, C, 2) in data]
    a.plot(xs, [mean_rep(N, C, "throughput_rps") for C in xs], "o-", label=f"N = {N} (mean of runs)")
    for rep in (1, 2):
        pts = [(C, data[(N, C, rep)]["throughput_rps"]) for C in xs if (N, C, rep) in data]
        a.plot([p[0] for p in pts], [p[1] for p in pts], ".", color="gray", alpha=0.5)
a.set_xscale("log", base=2); a.set_ylim(bottom=0)
a.set_xlabel("C (simultaneous Locust users)"); a.set_ylabel("throughput (HTTP 200 per second)")
a.set_title("Throughput vs concurrency — fixedN, dataset base (U=1000, P=20, F=20)")
a.legend(); a.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(f"{OUT}/fig2a.png", dpi=150); plt.close(fig)

# ---- Fig 2b: latency vs C with Little's law prediction (latency ~ C / throughput)
lines = []
for (N, C, rep), d in sorted(data.items()):
    little = 1000.0 * C / d["throughput_rps"] if d["throughput_rps"] > 0 else float("nan")
    lines.append([N, C, rep, round(d["latency_median_ms"], 1), round(d["latency_mean_ms"], 1),
                  round(d["latency_p95_ms"], 1), round(little, 1)])
w(f"{OUT}/fig2b.csv", ["N_instances", "C_concurrency", "rep", "latency_median_ms", "latency_mean_ms",
                       "latency_p95_ms", "little_prediction_ms_C_over_throughput"], lines)
fig, a = plt.subplots(figsize=(6.5, 4.4))
for i, N in enumerate(Ns):
    xs = [C for C in Cs if (N, C, 1) in data or (N, C, 2) in data]
    col = f"C{i}"
    a.plot(xs, [mean_rep(N, C, "latency_median_ms") for C in xs], "o-", color=col, label=f"N = {N}: measured median")
    a.plot(xs, [mean_rep(N, C, "latency_mean_ms") for C in xs], "s:", color=col, label=f"N = {N}: measured mean")
    a.plot(xs, [1000.0 * C / mean_rep(N, C, "throughput_rps") for C in xs], "--", color=col, label=f"N = {N}: Little, C / throughput")
a.set_xscale("log", base=2); a.set_yscale("log")
a.set_xlabel("C (simultaneous Locust users)"); a.set_ylabel("latency (ms, log scale)")
a.set_title("Latency vs concurrency — fixedN\ndataset base (U=1000, P=20, F=20)")
a.legend(fontsize=8); a.grid(alpha=0.3, which="both")
fig.tight_layout(); fig.savefig(f"{OUT}/fig2b.png", dpi=150); plt.close(fig)

# ---- validity checks
w(f"{OUT}/part2_checks.csv",
  ["N_instances", "C_concurrency", "rep", "instances_serving", "n_requests", "n_failed", "users_max",
   "client_cpu_busy_mean_pct", "client_cpu_busy_max_pct"],
  [[N, C, rep, d["instances"], d["n_requests"], d["n_failed"], d["users_max"],
    round(d["cpu_busy_mean_pct"], 1), round(d["cpu_busy_max_pct"], 1)] for (N, C, rep), d in sorted(data.items())])

print("N  C  rep  thr(rps)  lat_med(ms)  Little(ms)  inst  fail  cpu_mean%  cpu_max%")
for (N, C, rep), d in sorted(data.items()):
    little = 1000.0 * C / d["throughput_rps"] if d["throughput_rps"] > 0 else float("nan")
    flag = "" if d["instances"] == N else "  <-- instances != N"
    print(f"{N:<2} {C:<3}{rep:<5}{d['throughput_rps']:<10.1f}{d['latency_median_ms']:<13.1f}{little:<12.1f}"
          f"{d['instances']:<6}{d['n_failed']:<6}{d['cpu_busy_mean_pct']:<11.1f}{d['cpu_busy_max_pct']:.1f}{flag}")
