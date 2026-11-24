#!/usr/bin/env bash
# Part 3: same protocol as Part 1 (one request at a time, -u 1, 45 s per run, 2 repetitions, random order,
# discarded warm-up) for a given version and a list of F values.
# Usage: ./scripts/part3.sh VERSION URL "F1 F2 ..." [REPETITIONS]
# Example: ./scripts/part3.sh p3a "$URL" "5 10 15 20 25 30 35 40 45 50 55 60 65 70 75 80 85 90 95 100" 2
set -u
VER="${1:?version}"; URL="${2:?URL}"; FS="${3:?list of F}"; REPS="${4:-2}"
DUR=45s
mkdir -p raw/part3 raw/pilot logs
# discarded warm-up
TINY_PREFIX=base TINY_USERS=1000 TINY_LOG=raw/pilot/warmup_part3_${VER}.csv \
  python -m locust -f bench/locustfile.py --headless -u 1 -r 1 -t 20s --only-summary --host "$URL" >/dev/null 2>&1
for rep in $(seq 1 $REPS); do
  for f in $(echo $FS | tr ' ' '\n' | shuf); do
    p=$(printf 'f%02d' $f)
    echo "$(date -u +%T) $VER rep$rep $p"
    TINY_PREFIX=$p TINY_USERS=120 TINY_LOG=raw/part3/${VER}_${p}_r${rep}.csv \
      python -m locust -f bench/locustfile.py --headless -u 1 -r 1 -t $DUR --only-summary --host "$URL" \
      >logs/part3_${VER}_${p}_r${rep}.log 2>&1
  done
done
echo "DONE -> stop the version: gcloud app versions stop $VER"
