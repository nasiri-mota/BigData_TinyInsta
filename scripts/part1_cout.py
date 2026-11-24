"""Part 1 : entites lues par timeline et cout de 1 million de timelines.
Usage : python scripts/part1_cout.py PRIX
  PRIX = prix en USD pour 100 000 lectures d'entites (lu sur la page Tarifs, emplacement eur3).
Hypotheses (lues dans main.py, non mesurees) :
  - F+1 <= 30 : 1 lecture User + 20 posts = 21 entites
  - F+1 > 30  : IN refuse (limite 30), une requete par auteur, limit=20 chacune : 1 + (F+1)*20
"""
import csv, os, sys

price = float(sys.argv[1])
os.makedirs("figures", exist_ok=True)

def entities(f):
    return 21 if f + 1 <= 30 else 1 + (f + 1) * 20

rows = [["U ou P varient (F=20)", 20, entities(20)]]
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
