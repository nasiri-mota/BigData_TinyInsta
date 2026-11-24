#!/usr/bin/env bash
# Extra experiment, attempt 2: fixed1 (original start command) and p3b (4 threads) are measured ALTERNATELY, so
# that a drift of the platform affects both versions the same way. Both versions must already be running.
# Usage: ./scripts/part2_extra_interleaved.sh URL_FIXED1 URL_P3B [REPETITIONS]
# For each repetition and each C (random order), the two versions are measured one after the other, in a random
# order. Same protocol as scripts/part2.sh: C simultaneous Locust users, 75 s per run, dataset base.
# Results: raw/extra2/<version>_c<C>_r<rep>.csv ; CPU of the client: logs/extra2_cpu_*.log
set -u
UA="${1:?usage: ./scripts/part2_extra_interleaved.sh URL_FIXED1 URL_P3B [REPETITIONS]}"; UB="${2:?missing URL_P3B}"
REPS="${3:-2}"
DUR=75s
mkdir -p raw/extra2 raw/pilot logs
# discarded warm-ups
for v in fixed1 p3b; do
  if [ "$v" = fixed1 ]; then URL="$UA"; else URL="$UB"; fi
  TINY_PREFIX=base TINY_USERS=1000 TINY_LOG=raw/pilot/warmup_extra2_${v}.csv \
    python -m locust -f bench/locustfile.py --headless -u 4 -r 4 -t 20s --only-summary --host "$URL" >/dev/null 2>&1
done
for rep in $(seq 1 $REPS); do
  for c in $(echo 1 2 4 8 16 32 64 | tr ' ' '\n' | shuf); do
    if [ $((RANDOM % 2)) -eq 0 ]; then order="fixed1 p3b"; else order="p3b fixed1"; fi
    for v in $order; do
      if [ "$v" = fixed1 ]; then URL="$UA"; else URL="$UB"; fi
      echo "$(date -u +%T) $v rep$rep C=$c"
      vmstat 5 > logs/extra2_cpu_${v}_c${c}_r${rep}.log &
      VP=$!
      TINY_PREFIX=base TINY_USERS=1000 TINY_LOG=raw/extra2/${v}_c${c}_r${rep}.csv \
        python -m locust -f bench/locustfile.py --headless -u $c -r $c -t $DUR --only-summary --host "$URL" \
        >logs/extra2_${v}_c${c}_r${rep}.log 2>&1
      kill $VP 2>/dev/null
    done
  done
done
echo "DONE"
