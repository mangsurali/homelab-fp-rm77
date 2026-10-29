#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
RESULTS=${1:?Usage: collect-all.sh /path/to/cloud-dynamics-experiments/results [APP_NAME]}
APP=${2-}
if [ "$APP" = "--app" ]; then
  APP=${3-}
fi

found=0
for exp in "$RESULTS"/*; do
  [ -d "$exp" ] || continue
  [ -f "$exp/measurement-window.env" ] || continue
  [ -f "$exp/metadata.json" ] || continue
  [ -f "$exp/workload.csv" ] || continue
  found=1
  echo "=== $(basename "$exp") ==="
  if [ -n "$APP" ]; then
    "$ROOT/scripts/collect-experiment.sh" "$exp" "$APP"
  else
    "$ROOT/scripts/collect-experiment.sh" "$exp"
  fi
done
[ "$found" -eq 1 ] || { echo "No valid experiment directories found in $RESULTS." >&2; exit 1; }
