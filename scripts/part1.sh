#!/usr/bin/env bash
# Part 1: version fixed1, one request at a time (-u 1).
# Usage: ./scripts/part1.sh URL [REPETITIONS]
set -u
URL="$1"; REPS="${2:-2}"; DUR=45s
SETS="u100:100 base:1000 u10000:10000 p10:100 p100:100 p1000:100"
for f in $(seq 5 5 100); do SETS="$SETS $(printf 'f%02d' $f):120"; done
mkdir -p raw/part1 raw/pilot logs
# discarded warm-up (first requests on a fresh instance)
TINY_PREFIX=base TINY_USERS=1000 TINY_LOG=raw/pilot/warmup.csv \
  python -m locust -f bench/locustfile.py --headless -u 1 -r 1 -t 20s --only-summary --host "$URL" >/dev/null 2>&1
for rep in $(seq 1 $REPS); do
  for s in $(echo $SETS | tr ' ' '\n' | shuf); do
    p=${s%%:*}; n=${s##*:}
    echo "$(date -u +%T) rep$rep $p"
    TINY_PREFIX=$p TINY_USERS=$n TINY_LOG=raw/part1/${p}_r${rep}.csv \
      python -m locust -f bench/locustfile.py --headless -u 1 -r 1 -t $DUR --only-summary --host "$URL" >logs/part1_${p}_r${rep}.log 2>&1
  done
done
echo FINI
