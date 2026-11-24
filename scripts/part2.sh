#!/usr/bin/env bash
# Part 2: capacity. Version fixedN already started, dataset "base" (U=1000).
# Usage: ./scripts/part2.sh N URL [REPETITIONS]
# For each C in {1,2,4,8,16,32,64}: C simultaneous Locust users for 75 s (random order).
# Client CPU is sampled every 5 s during each run (logs/part2_cpu_*.log).
# Remember to stop the version at the end: gcloud app versions stop fixedN
set -u
N="${1:?usage: ./scripts/part2.sh N URL [REPETITIONS]}"; URL="${2:?missing URL}"; REPS="${3:-2}"
DUR=75s
mkdir -p raw/part2 raw/pilot logs
# discarded warm-up
TINY_PREFIX=base TINY_USERS=1000 TINY_LOG=raw/pilot/warmup_n${N}.csv \
  python -m locust -f bench/locustfile.py --headless -u 4 -r 4 -t 20s --only-summary --host "$URL" >/dev/null 2>&1
for rep in $(seq 1 $REPS); do
  for c in $(echo 1 2 4 8 16 32 64 | tr ' ' '\n' | shuf); do
    echo "$(date -u +%T) N=$N rep$rep C=$c"
    vmstat 5 > logs/part2_cpu_n${N}_c${c}_r${rep}.log &
    VP=$!
    TINY_PREFIX=base TINY_USERS=1000 TINY_LOG=raw/part2/n${N}_c${c}_r${rep}.csv \
      python -m locust -f bench/locustfile.py --headless -u $c -r $c -t $DUR --only-summary --host "$URL" \
      >logs/part2_n${N}_c${c}_r${rep}.log 2>&1
    kill $VP 2>/dev/null
  done
done
echo "DONE -> stop the version: gcloud app versions stop fixed${N}"
