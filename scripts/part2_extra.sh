#!/usr/bin/env bash
# Extra experiment: same protocol as scripts/part2.sh for one instance, but the results are kept under a tag
# (raw/extra/<TAG>_c<C>_r<rep>.csv) so that the Part 2 data are never overwritten.
# Usage: ./scripts/part2_extra.sh TAG URL [REPETITIONS] ["C values"]
# Example: ./scripts/part2_extra.sh p3b "$URL" 2 "1 2 4 8 16 32 64"
set -u
TAG="${1:?usage: ./scripts/part2_extra.sh TAG URL [REPETITIONS] [\"C values\"]}"; URL="${2:?missing URL}"
REPS="${3:-2}"; CS="${4:-1 2 4 8 16 32 64}"
DUR=75s
mkdir -p raw/extra raw/pilot logs
# discarded warm-up
TINY_PREFIX=base TINY_USERS=1000 TINY_LOG=raw/pilot/warmup_extra_${TAG}.csv \
  python -m locust -f bench/locustfile.py --headless -u 4 -r 4 -t 20s --only-summary --host "$URL" >/dev/null 2>&1
for rep in $(seq 1 $REPS); do
  for c in $(echo $CS | tr ' ' '\n' | shuf); do
    echo "$(date -u +%T) $TAG rep$rep C=$c"
    vmstat 5 > logs/extra_cpu_${TAG}_c${c}_r${rep}.log &
    VP=$!
    TINY_PREFIX=base TINY_USERS=1000 TINY_LOG=raw/extra/${TAG}_c${c}_r${rep}.csv \
      python -m locust -f bench/locustfile.py --headless -u $c -r $c -t $DUR --only-summary --host "$URL" \
      >logs/extra_${TAG}_c${c}_r${rep}.log 2>&1
    kill $VP 2>/dev/null
  done
done
echo "DONE -> stop the version"
