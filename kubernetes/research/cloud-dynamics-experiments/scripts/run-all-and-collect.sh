#!/bin/sh
# run-all-and-collect.sh -- Run all standard scenarios and collect Prometheus metrics.
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec "$ROOT_DIR/scripts/run-and-collect.sh" --all "$@"
