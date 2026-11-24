#!/usr/bin/env bash
# Deploys version p3b (extra experiment): the ORIGINAL main.py, same settings as deploy_fixed.sh 1
# (class B1, 1 fixed instance, no autoscaling), but gunicorn is started with 4 threads. Not promoted:
# the default version is untouched.
# Usage: ./scripts/deploy_p3b.sh [gcloud arguments, e.g. --project=tinyinsta-512819]
# The version is billed while it runs: gcloud app versions stop p3b
set -euo pipefail
cd "$(dirname "$0")/.."
D="$(mktemp -d)"
cp main.py "$D/main.py"
cp requirements.txt "$D/requirements.txt"
cat > "$D/app-p3b.yaml" <<YAML
runtime: python312
entrypoint: gunicorn -b :\$PORT --threads 4 main:app

instance_class: B1
manual_scaling:
  instances: 1

handlers:
- url: /
  script: auto
env_variables:
  SEED_TOKEN: "change-me-seed-token"
YAML
cd "$D"
gcloud app deploy app-p3b.yaml --version p3b --no-promote --quiet "$@"
