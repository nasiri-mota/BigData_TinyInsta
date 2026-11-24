"""Part 2: is Little's law verified beyond the saturation? (assignment question)
Usage: python scripts/part2_little_saturation.py
Uses figures/fig2b.csv (measured latencies and the prediction C / throughput of each run) and
figures/part2_capacity.csv (the values of C counted in the saturated plateau of each N).
For each N, the runs are split into 'below saturation' (C not in the plateau) and 'saturated' (C in the plateau);
the deviation is |measured latency - C / throughput| / (C / throughput).
Writes figures/part2_little_saturation.csv.
"""
import csv, statistics
from collections import defaultdict

plateau = {int(r["N_instances"]): {int(c) for c in r["C_values_in_plateau"].split()}
           for r in csv.DictReader(open("figures/part2_capacity.csv"))}
dev = defaultdict(lambda: {"mean": [], "median": []})
for r in csv.DictReader(open("figures/fig2b.csv")):
    N, C = int(r["N_instances"]), int(r["C_concurrency"])
    little = float(r["little_prediction_ms_C_over_throughput"])
    region = "saturated" if C in plateau[N] else "below_saturation"
    dev[(N, region)]["mean"].append(abs(float(r["latency_mean_ms"]) - little) / little)
    dev[(N, region)]["median"].append(abs(float(r["latency_median_ms"]) - little) / little)

with open("figures/part2_little_saturation.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["N_instances", "region", "n_runs", "median_abs_dev_mean_latency_pct", "max_abs_dev_mean_latency_pct",
                "median_abs_dev_median_latency_pct", "max_abs_dev_median_latency_pct"])
    print("N  region            runs  mean-latency dev (median/max %)   median-latency dev (median/max %)")
    for (N, region), d in sorted(dev.items()):
        row = [N, region, len(d["mean"]), round(100 * statistics.median(d["mean"]), 1), round(100 * max(d["mean"]), 1),
               round(100 * statistics.median(d["median"]), 1), round(100 * max(d["median"]), 1)]
        w.writerow(row)
        print(f"{N:<2} {region:<17} {row[2]:<5} {row[3]:>6} / {row[4]:<6}                   {row[5]:>6} / {row[6]}")
