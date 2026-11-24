from google.cloud import datastore
from google.cloud.datastore.query import PropertyFilter

c = datastore.Client(project="tinyinsta-512819", _use_grpc=False)
for prefix in ("f25", "f30"):
    u = c.get(c.key("User", f"{prefix}_u00000"))
    authors = list({*u["follows"], f"{prefix}_u00000"})
    q = c.query(kind="Post")
    q.add_filter(filter=PropertyFilter("author", "IN", authors))
    q.order = ["-created"]
    try:
        r = list(q.fetch(limit=20))
        print(prefix, "valeurs IN =", len(authors), "-> OK,", len(r), "posts")
    except Exception as e:
        print(prefix, "valeurs IN =", len(authors), "-> ERREUR", type(e).__name__, str(e)[:160])
