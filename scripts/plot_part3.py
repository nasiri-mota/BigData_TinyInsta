"""Part 3: before/after figure for the fix of get_timeline (groups of at most 30 authors).
Usage: python scripts/plot_part3.py
Reads raw/part3/<version>_f<F>_r<rep>.csv (versions fixed1 = original code, p3a = new code, measured in the
same session) and, for reference only, raw/part1/f<F>_r<rep>.csv (original code, measured the night before).
Writes figures/fig3.csv/.png and figures/part3_summary.csv.
"""
import csv, glob, os, re, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "figures"
os.makedirs(OUT, exist_ok=True)

def stats(path):
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    ok = [r for r in rows if r["STATUS"] == "200"]
    srv = [float(r["SERVER_MS"]) for r in ok if r["SERVER_MS"]]
    lat = [float(r["LATENCY_MS"]) for r in ok]
    return dict(n_requests=len(rows), n_ok=len(ok), n_failed=len(rows) - len(ok),
                instances=len({r["INSTANCE"] for r in ok if r["INSTANCE"]}),
                server_median_ms=statistics.median(srv) if srv else float("nan"),
                client_median_ms=statistics.median(lat) if lat else float("nan"))

data = {}  # (version, F, rep) -> stats
for path in sorted(glob.glob("raw/part3/*_f*_r*.csv")):
    m = re.match(r"(.+)_f(\d+)_r(\d+)\.csv$", os.path.basename(path))
    if m:
        data[(m.group(1), int(m.group(2)), int(m.group(3)))] = stats(path)
part1 = {}
for path in sorted(glob.glob("raw/part1/f*_r*.csv")):
    m = re.match(r"f(\d+)_r(\d+)\.csv$", os.path.basename(path))
    if m:
        part1[(int(m.group(1)), int(m.group(2)))] = stats(path)

def mean_over(d, key, version, F):
    v = [s[key] for (ver, f, _), s in d.items() if ver == version and f == F and s[key] == s[key]]
    return statistics.mean(v) if v else float("nan")

def mean_part1(F):
    v = [s["server_median_ms"] for (f, _), s in part1.items() if f == F]
    return statistics.mean(v) if v else float("nan")

versions = sorted({k[0] for k in data})
Fs = sorted({k[1] for k in data})
Fp = sorted({k[0] for k in part1})

with open(f"{OUT}/fig3.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["version", "F_followees", "rep", "n_requests", "n_failed", "instances_serving",
                "server_median_ms", "client_median_ms"])
    for (ver, F, rep), s in sorted(data.items()):
        w.writerow([ver, F, rep, s["n_requests"], s["n_failed"], s["instances"],
                    round(s["server_median_ms"], 1), round(s["client_median_ms"], 1)])

rows = []
for F in Fs:
    before = mean_over(data, "server_median_ms", "fixed1", F)
    after = mean_over(data, "server_median_ms", "p3a", F)
    p1 = mean_part1(F)
    before2 = mean_over(data, "server_median_ms", "fixed1after", F)
    rows.append([F, round(before, 1), round(before2, 1), round(after, 1),
                 round(before / after, 1) if before == before and after == after and after > 0 else "",
                 round(before2 / after, 1) if before2 == before2 and after == after and after > 0 else "",
                 round(p1, 1)])
with open(f"{OUT}/part3_summary.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["F_followees", "fixed1_before_p3a_server_ms", "fixed1_after_p3a_server_ms", "p3a_server_ms",
                "speedup_vs_fixed1_before", "speedup_vs_fixed1_after", "part1_original_previous_night_server_ms"])
    w.writerows(rows)

fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
a = ax[0]
if Fp:
    a.plot(Fp, [mean_part1(F) for F in Fp], "--", color="gray", label="original code, Part 1 (previous night)")
fx = [F for F in Fs if mean_over(data, "server_median_ms", "fixed1", F) == mean_over(data, "server_median_ms", "fixed1", F)]
a.plot(fx, [mean_over(data, "server_median_ms", "fixed1", F) for F in fx], "s", color="C3", label="original code (fixed1), before p3a, same session")
fa = [F for F in Fs if mean_over(data, "server_median_ms", "fixed1after", F) == mean_over(data, "server_median_ms", "fixed1after", F)]
a.plot(fa, [mean_over(data, "server_median_ms", "fixed1after", F) for F in fa], "^", color="C1", label="original code (fixed1), after p3a")
a.plot(Fs, [mean_over(data, "server_median_ms", "p3a", F) for F in Fs], "o-", color="C0", label="new code (p3a)")
a.set_ylim(bottom=0); a.set_xlabel("F (followees per user)"); a.set_ylabel("median server time (ms)")
a.set_title("Before / after — U = 120, P = 20, one request at a time"); a.legend(fontsize=8); a.grid(alpha=0.3)
b = ax[1]
b.plot(Fs, [mean_over(data, "server_median_ms", "p3a", F) for F in Fs], "o-", color="C0", label="new code (p3a), mean of 2 runs")
for rep, mk in ((1, "."), (2, "x")):
    pts = [(F, data[("p3a", F, rep)]["server_median_ms"]) for F in Fs if ("p3a", F, rep) in data]
    b.plot([p[0] for p in pts], [p[1] for p in pts], mk, color="gray", alpha=0.7, label=f"run {rep}")
for x in (30, 60, 90):
    b.axvline(x, color="k", linestyle=":", alpha=0.4)
b.set_ylim(bottom=0); b.set_xlabel("F (followees per user)"); b.set_ylabel("median server time (ms)")
b.set_title("New code only — U = 120, P = 20\n(dotted lines: F = 30, 60, 90)"); b.legend(fontsize=8); b.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(f"{OUT}/fig3.png", dpi=150); plt.close(fig)

print("F    fixed1_before  fixed1_after  p3a(ms)  speedup_b  speedup_a  part1(ms)")
for r in rows:
    print(f"{r[0]:<5}{str(r[1]):<15}{str(r[2]):<14}{str(r[3]):<9}{str(r[4]):<11}{str(r[5]):<11}{r[6]}")
bad = [(k, s["instances"], s["n_failed"]) for k, s in sorted(data.items()) if s["instances"] != 1 or s["n_failed"] > 0]
print("runs with instances != 1 or failures:", bad if bad else "none")
