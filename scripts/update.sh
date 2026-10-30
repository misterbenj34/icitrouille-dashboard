#!/usr/bin/env bash
# Collect aggregates and push only when they changed. Safe to run from cron.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/collect.py
if [[ -n "$(git status --porcelain data.json)" ]]; then
  git add data.json
  git commit -qm "data: update aggregates $(date -u +%Y-%m-%dT%H:%MZ)"
  git push -q origin main
  echo "pushed"
else
  echo "no change"
fi
