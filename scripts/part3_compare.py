"""Part 3: compare the original get_timeline (main.py) and the new one (part3/main.py) on real data.
Usage: python scripts/part3_compare.py [USERS_PER_DATASET]
For each dataset and each of the first K users, both functions are run against Datastore and the
returned lists of posts are compared. Nothing is written to Datastore. Timings printed here are only
indicative (single runs from Cloud Shell); the real measurements use Locust.
Outcomes: identical; tie_only (same creation dates in the same order, but posts created at the same
second appear in another order); different (the lists do not have the same dates: a real discrepancy).
"""
import csv, importlib.util, os, statistics, sys, time, types

PROJECT = "tinyinsta-512819"
DATASETS = ["f25", "f30", "f60", "f100"]

def key(p):
    return (p.get("author"), p.get("content"), p.get("created"))

def compare(old, new):
    if [key(p) for p in old] == [key(p) for p in new]:
        return "identical"
    if [p.get("created") for p in old] == [p.get("created") for p in new]:
        return "tie_only"
    return "different"

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT
    try:
        import flask  # noqa: F401
    except ImportError:  # the check does not need Flask: use a stub so that main.py can be imported
        stub = types.ModuleType("flask")
        class FakeFlask:
            def __init__(self, *a, **kw): self.secret_key = None
            def route(self, *a, **kw): return lambda f: f
        stub.Flask = FakeFlask
        for n in ("request", "redirect", "url_for", "render_template_string", "session", "jsonify"):
            setattr(stub, n, None)
        sys.modules["flask"] = stub
    from google.cloud import datastore
    old = load("old_main", "main.py")
    new = load("new_main", "part3/main.py")
    client = datastore.Client(project=PROJECT, _use_grpc=False)
    old.client = client
    new.client = client

    rows = []
    for prefix in DATASETS:
        res, t_old, t_new = [], [], []
        for i in range(k):
            user = f"{prefix}_u{i:05d}"
            t = time.perf_counter(); a = old.get_timeline(user); t_old.append(1000 * (time.perf_counter() - t))
            t = time.perf_counter(); b = new.get_timeline(user); t_new.append(1000 * (time.perf_counter() - t))
            res.append(compare(a, b))
        row = [prefix, k, res.count("identical"), res.count("tie_only"), res.count("different"),
               round(statistics.mean(t_old)), round(statistics.mean(t_new))]
        rows.append(row)
        print(f"{prefix}: users={k} identical={row[2]} tie_only={row[3]} different={row[4]} "
              f"old~{row[5]} ms new~{row[6]} ms (single runs, indicative)")
    os.makedirs("logs", exist_ok=True)
    with open("logs/part3_compare.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["dataset", "users_compared", "identical", "tie_only", "different",
                    "old_mean_ms_indicative", "new_mean_ms_indicative"])
        w.writerows(rows)

if __name__ == "__main__":
    main()
