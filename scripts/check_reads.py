"""Part 3 check: how many queries and how many entities does each version of get_timeline really use?
Usage: python scripts/check_reads.py
For one user of each dataset f25, f30, f60 and f100, the original code (main.py) and the new code
(part3/main.py) are run against Datastore with counters around client.get and query.fetch.
Counted: queries attempted, queries that raised an error, entities returned by Datastore to the client
(the User entity read by key plus the posts). Nothing is written to Datastore.
Writes logs/part3_reads.csv. The entities returned are what the pricing counts as entity reads
(index entries are not billed for these queries, according to the pricing page).
"""
import csv, importlib.util, os, sys, types

PROJECT = "tinyinsta-512819"
DATASETS = ["f25", "f30", "f60", "f100"]

class Counter:
    def __init__(self):
        self.queries = 0; self.failed = 0; self.entities = 0

def instrument(client, c):
    orig_query, orig_get = client.query, client.get

    def query(*a, **k):
        q = orig_query(*a, **k)
        real_fetch = q.fetch
        def fetch(*fa, **fk):
            c.queries += 1
            def gen():
                try:
                    for e in real_fetch(*fa, **fk):
                        c.entities += 1
                        yield e
                except Exception:
                    c.failed += 1
                    raise
            return gen()
        q.fetch = fetch
        return q

    def get(*a, **k):
        r = orig_get(*a, **k)
        if r is not None:
            c.entities += 1
        return r

    client.query, client.get = query, get

def measure(mod, user, c):
    c.queries = c.failed = c.entities = 0
    result = mod.get_timeline(user)
    return len(result)

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT
    try:
        import flask  # noqa: F401
    except ImportError:
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
    c = Counter()
    instrument(client, c)
    old.client = client
    new.client = client

    rows = []
    for prefix in DATASETS:
        user = f"{prefix}_u00000"
        for label, mod in (("original", old), ("new", new)):
            n_posts = measure(mod, user, c)
            rows.append([prefix, label, n_posts, c.queries, c.failed, c.entities])
            print(f"{prefix} {label:<8} posts returned={n_posts:<3} queries attempted={c.queries:<4} "
                  f"failed={c.failed} entities read={c.entities}")
    os.makedirs("logs", exist_ok=True)
    with open("logs/part3_reads.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["dataset", "version", "posts_returned", "queries_attempted", "queries_failed",
                    "entities_read_by_client"])
        w.writerows(rows)

if __name__ == "__main__":
    main()
