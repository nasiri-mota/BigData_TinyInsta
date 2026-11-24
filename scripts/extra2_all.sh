#!/usr/bin/env bash
# Extra experiment, attempt 2, everything in one command. It starts fixed1 and p3b, checks their start logs,
# runs the alternating measurements (about 40 minutes), stops BOTH versions, and analyses the results.
# Run it with nohup so that a disconnection of Cloud Shell does not interrupt it:
#   nohup bash scripts/extra2_all.sh > logs/extra2_all.log 2>&1 &
# The versions are billed while they run; the script stops them at the end, whatever happens before.
set -u
cd "$(dirname "$0")/.."
P=tinyinsta-512819
log() { echo "$(date -u +%FT%TZ) $*" | tee -a logs/instance_hours.log; }
log "start fixed1 and p3b (extra experiment, attempt 2)"
gcloud app versions start fixed1 p3b --service default --project=$P --quiet
UA=$(gcloud app versions describe fixed1 --service default --project=$P --format='value(versionUrl)')
UB=$(gcloud app versions describe p3b --service default --project=$P --format='value(versionUrl)')
echo "$UA"; echo "$UB"
sleep 60
for u in "$UA" "$UB"; do curl -s "$u/api/timeline?user=base_u00001" | head -c 60; echo; done
for v in fixed1 p3b; do
  gcloud app logs read --service=default --version=$v --project=$P --limit=100 2>/dev/null \
    | grep -iE "gunicorn|Using worker|Booting worker" > logs/extra2_${v}_startup.txt
  echo "--- $v startup:"; cat logs/extra2_${v}_startup.txt
done
log "start extra experiment attempt 2 measurements"
./scripts/part2_extra_interleaved.sh "$UA" "$UB" 2
gcloud app versions stop fixed1 p3b --service default --project=$P --quiet
log "stop fixed1 and p3b (extra experiment, attempt 2 done)"
gcloud app versions list --project=$P | grep -E "VERSION.ID|SERVING_STATUS"
python scripts/plot_extra2.py | tee logs/extra2_summary.txt
echo "ALL DONE"
