"""Extra experiment (threads): one instance with one request at a time (fixed1) against 4 threads (p3b).
Usage: python scripts/plot_extra.py
Reads raw/extra/<tag>_c<C>_r<rep>.csv, tags fixed1before (original, before p3b), p3b (new start command),
fixed1after (original again, after p3b, only a few C values), and logs/extra_cpu_<tag>_c<C>_r<rep>.log.
Throughput = HTTP 200 answers per second in the window 5 s to 70 s of each run (as in plot_part2.py).
Writes figures/fig_extra.csv/.png and figures/extra_summary.csv.
"""
import csv, glob, os, re, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WIN_START, WIN_END = 5.0, 70.0
TAGS = ["fixed1before", "p3b", "fixed1after"]

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
for path in sorted(glob.glob("raw/extra/*_c*_r*.csv")):
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
    cm, cx = cpu_busy(f"logs/extra_cpu_{tag}_c{C}_r{rep}.log")
    data[(tag, C, rep)] = dict(
        n_requests=len(rows), n_failed=len(rows) - len(ok_all),
        instances=len({r["INSTANCE"] for r in ok_all if r["INSTANCE"]}),
        thr=len(win) / (WIN_END - WIN_START),
        lat_med=statistics.median(lat) if lat else float("nan"),
        lat_mean=statistics.mean(lat) if lat else float("nan"),
        srv_med=statistics.median(srv) if srv else float("nan"), cpu_mean=cm, cpu_max=cx)

def mean_of(tag, C, key):
    v = [d[key] for (t, c, _), d in data.items() if t == tag and c == C and d[key] == d[key]]
    return statistics.mean(v) if v else float("nan")

Cs = sorted({k[1] for k in data})
os.makedirs("figures", exist_ok=True)
with open("figures/fig_extra.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["version", "C_concurrency", "rep", "n_requests", "n_failed", "instances_serving", "throughput_rps",
                "latency_median_ms", "latency_mean_ms", "server_median_ms", "client_cpu_busy_mean_pct", "client_cpu_busy_max_pct"])
    for (tag, C, rep), d in sorted(data.items()):
        w.writerow([tag, C, rep, d["n_requests"], d["n_failed"], d["instances"], round(d["thr"], 2),
                    round(d["lat_med"], 1), round(d["lat_mean"], 1), round(d["srv_med"], 1),
                    round(d["cpu_mean"], 1), round(d["cpu_max"], 1)])

style = {"fixed1before": ("o-", "C3", "original start command (fixed1), before p3b"),
         "p3b": ("s-", "C0", "--threads 4 (p3b)"),
         "fixed1after": ("^", "C1", "original start command (fixed1), after p3b")}
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
for tag in TAGS:
    xs = [C for C in Cs if any((tag, C, r) in data for r in (1, 2))]
    if not xs:
        continue
    mk, col, lab = style[tag]
    ax[0].plot(xs, [mean_of(tag, C, "thr") for C in xs], mk, color=col, label=lab)
    ax[1].plot(xs, [mean_of(tag, C, "lat_med") for C in xs], mk, color=col, label=lab)
ax[0].set_ylim(bottom=0); ax[0].set_ylabel("throughput (HTTP 200 per second)")
ax[1].set_yscale("log"); ax[1].set_ylabel("median latency (ms, log scale)")
for a in ax:
    a.set_xscale("log", base=2); a.set_xlabel("C (simultaneous Locust users)"); a.grid(alpha=0.3, which="both"); a.legend(fontsize=8)
fig.suptitle("One instance (class B1), dataset base (U=1000, P=20, F=20): start command with 1 and with 4 threads", fontsize=10)
fig.tight_layout(); fig.savefig("figures/fig_extra.png", dpi=150); plt.close(fig)

def saturated(tag):
    pts = {C: mean_of(tag, C, "thr") for C in Cs if any((tag, C, r) in data for r in (1, 2))}
    if not pts:
        return float("nan"), []
    peak = max(pts.values()); sat = {C: x for C, x in pts.items() if x >= 0.9 * peak}
    return statistics.mean(sat.values()), sorted(sat)

rows = []
for tag in TAGS:
    sat, cs = saturated(tag)
    rows.append([tag, round(sat, 1), " ".join(map(str, cs)), round(mean_of(tag, 64, "lat_med"), 1),
                 round(mean_of(tag, 64, "srv_med"), 1), round(mean_of(tag, 8, "thr"), 1),
                 round(max([d["cpu_mean"] for (t, _, _), d in data.items() if t == tag] or [float("nan")]), 1)])
base = rows[0][1]
with open("figures/extra_summary.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["version", "saturated_throughput_rps", "C_values_in_plateau", "latency_median_C64_ms",
                "server_median_C64_ms", "throughput_C8_rps", "max_client_cpu_busy_mean_pct", "ratio_to_fixed1before"])
    for r in rows:
        w.writerow(r + [round(r[1] / base, 2) if base == base and r[1] == r[1] else ""])
print("version        sat_thr  plateau_C          lat_med_C64  srv_med_C64  thr_C8  max_cpu_mean%  ratio")
for r in rows:
    print(f"{r[0]:<14} {str(r[1]):<8} {r[2]:<18} {str(r[3]):<12} {str(r[4]):<12} {str(r[5]):<7} {str(r[6]):<14} "
          f"{round(r[1]/base, 2) if base == base and r[1] == r[1] else ''}")
bad = [(k, d["instances"], d["n_failed"]) for k, d in sorted(data.items()) if d["instances"] != 1 or d["n_failed"] > 0]
print("runs with instances != 1:", [b for b in bad if b[1] != 1] or "none", "| runs with failures:", len([b for b in bad if b[2] > 0]), "of", len(data))
