#!/usr/bin/env bash
# Regenerates every figure, every plotted-values CSV and the summary tables from the raw logs in raw/.
# No measurement is run and nothing is deployed. Usage: bash scripts/make_all.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs figures
python scripts/check_runs.py raw/part1 > logs/check_part1.txt
python scripts/plot_part1.py
python scripts/part1_cout.py 0.06 > logs/part1_cout.log
python scripts/plot_part2.py > logs/part2_summary_all.txt
python scripts/part2_capacity.py > logs/part2_capacity_summary.txt
python scripts/part2_server_time.py > logs/part2_server_time.txt
python scripts/part2_little_saturation.py > logs/part2_little_saturation.txt
python scripts/plot_part3.py > logs/part3_summary.txt
python scripts/plot_extra.py > logs/extra_summary.txt
python scripts/plot_extra2.py > logs/extra2_summary.txt
echo "done: figures/*.png, figures/*.csv, logs/check_part1.txt, logs/part*_summary*.txt"
