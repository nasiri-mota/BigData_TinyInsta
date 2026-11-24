# Does TinyInsta scale? — Benchmark report, 2026 edition

**Author:** Motahareh Nasiri Jojadeh · Big Data and Cloud project · individual submission
**Deployed application (default version):** https://tinyinsta-512819.ew.r.appspot.com
**Repository:** https://github.com/nasiri-mota/BigData_TinyInsta

**Status:** Part 1 is complete. Part 2 (capacity) is in progress and Part 3 (fix) has not started; their sections will be added after the measurements are done.

## Summary so far

The time needed to build a timeline does not depend on the number of users (U) nor on the number of posts per user (P) in the ranges tested. It depends strongly on the number of followees (F): it is flat up to F = 29, jumps by a factor of about 18 at F = 30, then grows linearly at about 13 ms per followee. The cause was verified directly: Datastore rejects an `IN` filter with more than 30 values, and the application then falls back to one query per author.

## Repository structure

| Path | Origin | Content |
|---|---|---|
| `main.py`, `app.yaml`, `index.yaml`, `requirements.txt`, `deploy_fixed.sh` | instructor, unmodified | application and deployment |
| `bench/` | instructor, unmodified | `seed_exact.py` (data generator), `locustfile.py` (load generator) |
| `SUJET.md`, `public/`, `site/`, `make-site.sh`, `.gitlab-ci.yml` | instructor | assignment |
| `scripts/` | author | measurement orchestration, checks, figures |
| `raw/` | author | raw Locust logs (`raw/part1/`, `raw/pilot/`) |
| `logs/` | author | generation, counting and check logs |
| `figures/` | author | figures (`.png`) and plotted values (`.csv`) |

The instructor's tools print their messages in French; I did not modify them, so some logs in `logs/` and `raw/` contain French text.

## 1. Setup

- **GCP project:** `tinyinsta-512819`. App Engine in region europe-west (URL ending `.ew.r.appspot.com`), runtime `python312`.
- **Versions:** default version with autoscaling, class F1, at most 10 instances (`app.yaml`). `fixedN` versions: manual scaling, class B1, exactly N instances (`deploy_fixed.sh`).
- **Datastore:** Firestore in Datastore mode, location `eur3`. Entity reads cost 0.06 USD per 100,000 above the free 50,000 per day (pricing page, `eur3` selected).
- **Software:** Flask 3.0.0, gunicorn 21.2.0, google-cloud-datastore 2.19.0 (server); Python 3.12, Locust 2.47.0, matplotlib 3.11.2 (client).
- **Load generator location:** Cloud Shell, 2 cores (`nproc`).
- **Dates:** data generated on 23 Nov 2026. Part 1 measured on 23 Nov 2026 from 23:33 UTC (about 40 minutes). Parts 2 and 3: to be completed.

### Datasets

Each dataset has a prefix: U users, exactly P posts and exactly F followees per user. Every dataset was generated, then **counted** with `scripts/count_dataset.py` (logs in `logs/count_*.log`); the counts match exactly.

| Prefix | U | P | F | Posts counted |
|---|---|---|---|---|
| `base` | 1000 | 20 | 20 | 20,000 |
| `u100`, `u10000` | 100 / 10,000 | 20 | 20 | 2,000 / 200,000 |
| `p10`, `p100`, `p1000` | 100 | 10 / 100 / 1000 | 20 | 1,000 / 10,000 / 100,000 |
| `f05` … `f100` (20 sets) | 120 | 20 | 5 … 100 | 2,400 each |

**Caveat:** the P and F series do not use the same U as `base` (they use 100 and 120). Comparisons are therefore made only inside a series, never against `base`.

**Data generation incident.** Early generations with the default gRPC client failed (`DeadlineExceeded`, batches abandoned after 6 attempts). `Post` entities have automatic keys: a batch committed on the server but not acknowledged, then retried, creates duplicates (one dataset ended with 23,500 posts instead of 20,000). Those datasets were deleted (`gcloud firestore bulk-delete`). All datasets listed above were then regenerated with `--rest --threads 3` without errors and counted. The instructor's code was not modified. I do not know why gRPC failed; switching to REST fixed it.
