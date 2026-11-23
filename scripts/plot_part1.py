"""Part 1 : figures 1a et 1b a partir de raw/part1/*.csv (fixed1, -u 1).
Usage : python scripts/plot_part1.py
Produit figures/fig1a.csv/.png et figures/fig1b.csv/.png
"""
import csv, glob, os, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAW, OUT = "raw/part1", "figures"
os.makedirs(OUT, exist_ok=True)

# prefixe -> (U, P, F)
PARAMS = {"u100": (100, 20, 20), "base": (1000, 20, 20), "u10000": (10000, 20, 20),
          "p10": (100, 10, 20), "p100": (100, 100, 20), "p1000": (100, 1000, 20)}
for f in range(5, 101, 5):
    PARAMS[f"f{f:02d}"] = (120, 20, f)

def stats(path):
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    ok = [r for r in rows if r["STATUS"] == "200"]
    srv = [float(r["SERVER_MS"]) for r in ok if r["SERVER_MS"]]
    lat = [float(r["LATENCY_MS"]) for r in ok]
    inst = {r["INSTANCE"] for r in ok if r["INSTANCE"]}
    return dict(n_requests=len(rows), n_ok=len(ok), n_instances=len(inst),
                server_median_ms=statistics.median(srv) if srv else float("nan"),
                client_median_ms=statistics.median(lat) if lat else float("nan"))

data = {}  # prefixe -> {rep: stats}
for path in sorted(glob.glob(f"{RAW}/*_r*.csv")):
    name = os.path.basename(path)[:-4]
    prefix, rep = name.rsplit("_r", 1)
    if prefix in PARAMS:
        data.setdefault(prefix, {})[int(rep)] = stats(path)

def write_csv(path, header, lines):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n"); w.writerow(header); w.writerows(lines)

def mean_over_reps(prefix, key):
    v = [s[key] for s in data.get(prefix, {}).values()]
    return statistics.mean(v) if v else float("nan")

# ---------- Fig 1a : facteurs U et P ----------
hdr = ["factor", "dataset", "U_users", "P_posts_per_user", "F_followees", "rep",
       "n_requests", "n_instances", "server_median_ms", "client_median_ms"]
lines = []
for factor, sets in (("U", ["u100", "base", "u10000"]), ("P", ["p10", "p100", "p1000"])):
    for p in sets:
        for rep, s in sorted(data.get(p, {}).items()):
            U, P, F = PARAMS[p]
            lines.append([factor, p, U, P, F, rep, s["n_requests"], s["n_instances"],
                          round(s["server_median_ms"], 2), round(s["client_median_ms"], 2)])
write_csv(f"{OUT}/fig1a.csv", hdr, lines)

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
for a, factor, sets, idx, fixed in ((ax[0], "U", ["u100", "base", "u10000"], 0, "P=20, F=20"),
                                    (ax[1], "P", ["p10", "p100", "p1000"], 1, "U=100, F=20")):
    xs = [PARAMS[p][idx] for p in sets]
    for rep in (1, 2):
        ys = [data.get(p, {}).get(rep, {}).get("server_median_ms", float("nan")) for p in sets]
        a.plot(xs, ys, "o", alpha=0.6, label=f"run {rep}")
    a.plot(xs, [mean_over_reps(p, "server_median_ms") for p in sets], "-", color="gray", label="moyenne")
    a.set_xscale("log"); a.set_yscale("log")
    a.set_xlabel(f"{factor} ({'utilisateurs' if factor == 'U' else 'posts par utilisateur'})")
    a.set_ylabel("temps serveur médian (ms)")
    a.set_title(f"Facteur {factor} — fixes : {fixed}\nfixed1, 1 requête à la fois")
    a.legend()
fig.tight_layout(); fig.savefig(f"{OUT}/fig1a.png", dpi=150); plt.close(fig)

# ---------- Fig 1b : facteur F ----------
fsets = [f"f{f:02d}" for f in range(5, 101, 5)]
lines = []
for p in fsets:
    for rep, s in sorted(data.get(p, {}).items()):
        U, P, F = PARAMS[p]
        lines.append([F, U, P, rep, s["n_requests"], s["n_instances"],
                      round(s["server_median_ms"], 2), round(s["client_median_ms"], 2),
                      round(s["client_median_ms"] - s["server_median_ms"], 2)])
write_csv(f"{OUT}/fig1b.csv",
          ["F_followees", "U_users", "P_posts_per_user", "rep", "n_requests", "n_instances",
           "server_median_ms", "client_median_ms", "network_gap_median_ms"], lines)

fig, a = plt.subplots(figsize=(6.5, 4.2))
xs = [PARAMS[p][2] for p in fsets]
a.plot(xs, [mean_over_reps(p, "server_median_ms") for p in fsets], "o-", label="serveur (Server-Timing)")
a.plot(xs, [mean_over_reps(p, "client_median_ms") for p in fsets], "s--", label="client (Locust)")
a.set_xlabel("F (comptes suivis par utilisateur)"); a.set_ylabel("médiane (ms), moyenne des runs")
a.set_title("Facteur F — fixes : U=120, P=20\nfixed1, 1 requête à la fois")
a.legend(); a.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(f"{OUT}/fig1b.png", dpi=150); plt.close(fig)
print("OK :", sorted(data), "->", OUT)
