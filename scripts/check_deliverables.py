"""Checks the deliverables listed in the assignment (section 8 and the experimental charter).
Usage: python scripts/check_deliverables.py
Prints OK / MISSING for each item. Nothing is modified. It checks that things exist and are consistent;
it cannot judge the quality of the explanations.
"""
import csv, glob, os, re, sys

ok_all = True
def report(ok, label, detail=""):
    global ok_all
    ok_all &= bool(ok)
    print(("OK       " if ok else "MISSING  ") + label + (f"  [{detail}]" if detail else ""))

def read(path):
    return open(path, encoding="utf-8").read() if os.path.exists(path) else ""

readme = read("README.md")
print("== Files")
report(bool(readme), "README.md")
figs = ["fig1a", "fig1b", "fig2a", "fig2b", "fig3"]
for f in figs:
    report(os.path.exists(f"figures/{f}.png"), f"figures/{f}.png")
    report(os.path.exists(f"figures/{f}.csv"), f"figures/{f}.csv")
for part, n in (("part1", 52), ("part2", 42), ("part3", 52)):
    k = len(glob.glob(f"raw/{part}/*.csv"))
    report(k >= n, f"raw/{part}/ raw logs", f"{k} files, expected {n}")
report(os.path.exists("Makefile") or os.path.exists("scripts/make_all.sh"),
       "one command that regenerates all the figures (Makefile or scripts/make_all.sh)")
report(os.path.exists("part3/main.py"), "part3/main.py (modified code kept apart from the instructor's main.py)")

print("\n== README sections imposed by the assignment")
for pat, label in ((r"^## 1\. ", "1. Setup"), (r"^## 2\. ", "2. Results"), (r"^## 3\. ", "3. Verdicts"),
                   (r"^## 4\. ", "4. Validity"), (r"^## 5\. ", "5. Cost")):
    report(re.search(pat, readme, re.M), label)
for key in ("Part 1", "Part 2", "Part 3"):
    report(re.search(rf"^### 2\.\d {key}", readme, re.M), f"Results: {key}")
report("Initial expectations" in readme, "hypothesis, Part 1")
report(re.search(r"Hypotheses \(written on .*before any Part 2", readme), "hypothesis, Part 2")
report(re.search(r"Hypotheses \(written on .*before any Part 3", readme), "hypothesis, Part 3")
for f in figs:
    report(f"figures/{f}.png" in readme, f"{f}.png displayed in the README")
for row in ("| Users (U)", "| Posts per user (P)", "| Followees (F)", "| Instances (N)"):
    report(row in readme, f"verdict table row {row[2:]}")
for i in range(1, 7):
    report(re.search(rf"^{i}\. \*", readme, re.M), f"validity question {i} answered")
report("Tools and AI assistance" in readme, "AI assistance declared")

print("\n== Placeholders left in the README")
left = [l.strip()[:100] for l in readme.splitlines()
        if re.search(r"to be completed|still to be|will be filled|not started|TODO|\[AUTHOR|\[CORES", l, re.I)]
report(not left, "no unfinished placeholder", "; ".join(left[:5]))

print("\n== Content of the CSV files")
def table(path):
    if not os.path.exists(path):
        return []
    return list(csv.DictReader(open(path)))
for f in figs:
    p = f"figures/{f}.csv"
    if os.path.exists(p):
        head = open(p).readline().strip()
        has_unit = re.search(r"_ms|_rps|_pct|_users|_per_", head) is not None
        report(has_unit, f"{f}.csv header has units", head[:90])
for name, col, expect in (("figures/fig1a.csv", "n_instances", lambda r: r == "1"),
                          ("figures/fig1b.csv", "n_instances", lambda r: r == "1"),
                          ("figures/fig3.csv", "instances_serving", lambda r: r == "1")):
    rows = table(name)
    if rows:
        bad = [r for r in rows if not expect(r[col])]
        report(not bad, f"{name}: every run served by exactly 1 instance", f"{len(rows)} runs, {len(bad)} different")
rows = table("figures/fig2a.csv")
if rows:
    bad = [r for r in rows if r["instances_serving"] != r["N_instances"]]
    report(not bad, "figures/fig2a.csv: instances serving = N in every run", f"{len(rows)} runs, {len(bad)} different")

print("\n== Not checked here")
print("  - default version still answers:  curl -s \"https://tinyinsta-512819.ew.r.appspot.com/api/timeline?user=base_u00001\" | head -c 150")
print("  - all fixedN / p3a versions stopped and useless versions deleted; datasets purged (end of the project)")
print("  - the two URLs submitted on Madoc")
print("\nALL OK" if ok_all else "\nSOME ITEMS ARE MISSING")
