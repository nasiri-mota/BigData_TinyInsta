import sys
from google.cloud import datastore
from google.cloud.datastore.query import PropertyFilter

project, prefix = sys.argv[1], sys.argv[2]
c = datastore.Client(project=project)
lo, hi = f"{prefix}_u", f"{prefix}_u\uffff"

def count(q):
    agg = c.aggregation_query(q)
    agg.count(alias="n")
    return list(agg.fetch())[0][0].value

q = c.query(kind="Post")
q.add_filter(filter=PropertyFilter("author", ">=", lo))
q.add_filter(filter=PropertyFilter("author", "<", hi))
posts = count(q)

q = c.query(kind="User")
q.add_filter(filter=PropertyFilter("__key__", ">=", c.key("User", lo)))
q.add_filter(filter=PropertyFilter("__key__", "<", c.key("User", hi)))
users = count(q)

print(f"[{prefix}] users={users} posts={posts}")
