import csv, glob, os, statistics, sys
folder = sys.argv[1]
rows = []
for path in sorted(glob.glob(f"{folder}/*.csv")):
    with open(path) as f:
        r = list(csv.DictReader(f))
    ok = [x for x in r if x["STATUS"] == "200"]
    inst = {x["INSTANCE"] for x in ok if x["INSTANCE"]}
    srv = [float(x["SERVER_MS"]) for x in ok if x["SERVER_MS"]]
    lat = [float(x["LATENCY_MS"]) for x in ok]
    codes = {}
    for x in r:
        codes[x["STATUS"]] = codes.get(x["STATUS"], 0) + 1
    rows.append([os.path.basename(path), len(r), len(ok), len(r) - len(ok),
                 len(inst), round(statistics.median(srv), 1) if srv else "",
                 round(statistics.median(lat), 1) if lat else "", codes])
print("file, requests, ok, failures, instances, server_median_ms, client_median_ms, status_codes")
for x in rows:
    print(*x, sep=", ")
