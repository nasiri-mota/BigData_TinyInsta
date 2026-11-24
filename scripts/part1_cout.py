"""Part 1: entities read per timeline and cost of 1 million timelines.
Usage: python scripts/part1_cout.py PRICE
  PRICE = USD per 100,000 entity reads (read from the pricing page, location eur3).
Assumptions (read from main.py, not measured):
  - F+1 <= 30: 1 User read + 20 posts = 21 entities
  - F+1 > 30: IN rejected (limit 30), one query per author, limit=20 each: 1 + (F+1)*20
"""
import csv, os, sys

price = float(sys.argv[1])
os.makedirs("figures", exist_ok=True)

def entities(f):
    return 21 if f + 1 <= 30 else 1 + (f + 1) * 20

rows = [["U or P vary (F=20)", 20, entities(20)]]
rows += [[f"F={f}", f, entities(f)] for f in range(5, 101, 5)]
out = [[c, f, n, round(n * 1_000_000 * price / 100_000, 2), price] for c, f, n in rows]
with open("figures/part1_entities_cost.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["case", "F_followees", "entities_read_per_timeline",
                "cost_usd_per_million_timelines", "price_usd_per_100k_reads"])
    w.writerows(out)
for r in out:
    if r[1] in (20, 25, 30, 100):
        print(r)
