"""Part 2: capacity summary from figures/fig2a.csv and figures/fig2b.csv (run plot_part2.py first).
Usage: python scripts/part2_capacity.py
Writes figures/part2_capacity.csv (peak and plateau throughput per N, speed-up and efficiency vs N = 1)
and figures/part2_little.csv (how far measured latency is from Little's law, per N).
Definitions (my choices):
  - throughput of a (N, C) point = mean over the repetitions;
  - peak = highest such point; plateau = mean of the points at or above 90% of the peak (saturated region);
  - speed-up = plateau(N) / plateau(1); efficiency = speed-up / N;
  - Little's law, per run: predicted latency = C / throughput; deviation = |measured - predicted| / predicted.
"""
import csv, statistics
from collections import defaultdict

def read(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))

a = read("figures/fig2a.csv")
b = read("figures/fig2b.csv")

thr = defaultdict(list)   # (N, C) -> [throughput per rep]
fails, reqs = defaultdict(int), defaultdict(int)
for r in a:
    N, C = int(r["N_instances"]), int(r["C_concurrency"])
    thr[(N, C)].append(float(r["throughput_rps"]))
    fails[N] += int(r["n_failed"]); reqs[N] += int(r["n_requests"])

Ns = sorted({k[0] for k in thr})
rows, plateau = [], {}
for N in Ns:
    pts = {C: statistics.mean(v) for (n, C), v in thr.items() if n == N}
    peak = max(pts.values())
    sat = {C: x for C, x in pts.items() if x >= 0.9 * peak}
    plateau[N] = statistics.mean(sat.values())
    rows.append([N, round(peak, 1), round(plateau[N], 1), " ".join(str(c) for c in sorted(sat)),
                 reqs[N], fails[N], round(100.0 * fails[N] / reqs[N], 3)])
base = plateau.get(1)
out = []
for r in rows:
    N = r[0]
    sp = plateau[N] / base if base else float("nan")
    out.append(r[:4] + [round(sp, 2), round(sp / N, 2)] + r[4:])
with open("figures/part2_capacity.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["N_instances", "peak_throughput_rps", "plateau_throughput_rps", "C_values_in_plateau",
                "speedup_vs_N1", "efficiency_speedup_over_N", "n_requests", "n_failed", "failed_pct"])
    w.writerows(out)

dev_med, dev_mean = defaultdict(list), defaultdict(list)
for r in b:
    N = int(r["N_instances"]); little = float(r["little_prediction_ms_C_over_throughput"])
    dev_med[N].append(abs(float(r["latency_median_ms"]) - little) / little)
    dev_mean[N].append(abs(float(r["latency_mean_ms"]) - little) / little)
with open("figures/part2_little.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["N_instances", "median_abs_dev_median_latency_pct", "max_abs_dev_median_latency_pct",
                "median_abs_dev_mean_latency_pct", "max_abs_dev_mean_latency_pct"])
    for N in sorted(dev_med):
        w.writerow([N, round(100 * statistics.median(dev_med[N]), 1), round(100 * max(dev_med[N]), 1),
                    round(100 * statistics.median(dev_mean[N]), 1), round(100 * max(dev_mean[N]), 1)])

print("N  peak  plateau  C_in_plateau        speedup  efficiency  failed")
for r in out:
    print(f"{r[0]:<3}{r[1]:<6}{r[2]:<9}{r[3]:<20}{r[4]:<9}{r[5]:<12}{r[7]} / {r[6]} ({r[8]}%)")
print()
print("Little's law, absolute deviation of latency vs C/throughput (median over runs / max):")
for N in sorted(dev_med):
    print(f"N={N}: median latency {100*statistics.median(dev_med[N]):.1f}% / {100*max(dev_med[N]):.1f}%   "
          f"mean latency {100*statistics.median(dev_mean[N]):.1f}% / {100*max(dev_mean[N]):.1f}%")
