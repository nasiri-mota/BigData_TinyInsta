"""Part 2: server time (Server-Timing, measured around get_timeline) against concurrency.
Usage: python scripts/part2_server_time.py
Reads raw/part2/n<N>_c<C>_r<rep>.csv (HTTP 200 answers in the window 5 s to 70 s of each run, as in plot_part2.py)
and writes figures/part2_server_time.csv. If the server time stays about constant while the client latency grows
with C, the waiting happens outside get_timeline (queue before the function); if it grows, the time inside the
function itself is affected by the load (Datastore, CPU of the instance).
"""
import csv, glob, os, re, statistics
from collections import defaultdict

WIN_START, WIN_END = 5.0, 70.0
rows = []
for path in sorted(glob.glob("raw/part2/n*_c*_r*.csv")):
    m = re.match(r"n(\d+)_c(\d+)_r(\d+)\.csv$", os.path.basename(path))
    if not m:
        continue
    N, C, rep = map(int, m.groups())
    data = list(csv.DictReader(open(path)))
    if not data:
        continue
    t0 = min(float(r["T_START"]) for r in data)
    ok = [r for r in data if r["STATUS"] == "200" and WIN_START <= float(r["T_START"]) - t0 < WIN_END and r["SERVER_MS"]]
    srv = [float(r["SERVER_MS"]) for r in ok]
    lat = [float(r["LATENCY_MS"]) for r in ok]
    if not srv:
        continue
    srv_sorted = sorted(srv)
    rows.append([N, C, rep, len(srv), round(statistics.median(srv), 1),
                 round(srv_sorted[int(0.95 * (len(srv) - 1))], 1),
                 round(statistics.median(lat), 1), round(statistics.median(lat) - statistics.median(srv), 1)])

os.makedirs("figures", exist_ok=True)
with open("figures/part2_server_time.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["N_instances", "C_concurrency", "rep", "n_answers", "server_median_ms", "server_p95_ms",
                "client_median_ms", "client_minus_server_median_ms"])
    w.writerows(rows)

agg = defaultdict(list)
for N, C, rep, n, sm, sp, cm, gap in rows:
    agg[(N, C)].append((sm, cm, gap))
print("N  C   server_median(ms)  client_median(ms)  client-server(ms)   (mean of the repetitions)")
for (N, C), v in sorted(agg.items()):
    print(f"{N:<2} {C:<3} {statistics.mean(x[0] for x in v):<18.1f} {statistics.mean(x[1] for x in v):<18.1f} "
          f"{statistics.mean(x[2] for x in v):.1f}")
