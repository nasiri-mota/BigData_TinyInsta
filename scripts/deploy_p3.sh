#!/usr/bin/env bash
# Deploys version p3a: same settings as deploy_fixed.sh 1 (class B1, 1 fixed instance, no autoscaling),
# but with part3/main.py as main.py, from a minimal copy. Not promoted: the default version is untouched.
# Usage: ./scripts/deploy_p3.sh [gcloud arguments, e.g. --project=tinyinsta-512819]
# The version is billed while it runs: gcloud app versions stop p3a
set -euo pipefail
cd "$(dirname "$0")/.."
D="$(mktemp -d)"
cp part3/main.py "$D/main.py"
cp requirements.txt "$D/requirements.txt"
cat > "$D/app-p3a.yaml" <<YAML
runtime: python312
entrypoint: gunicorn -b :\$PORT main:app

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
gcloud app deploy app-p3a.yaml --version p3a --no-promote --quiet "$@"
