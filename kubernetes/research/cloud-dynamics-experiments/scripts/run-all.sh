#!/bin/sh
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

LOG="$ROOT_DIR/results/tahap-b.log"

run() {   # $1 = URL, $2 = scenario, $3 = replicate
  echo "===== $(date '+%H:%M:%S') START $2 r$3 $1" | tee -a $LOG
  TARGET_URL=$1 REPLICATE=$3 sh scripts/run-experiment.sh scenarios/$2.env 2>&1 | tee -a $LOG
  sleep 120
}

M=http://microservices.10.160.4.43.sslip.io/
S=http://stateless-api.10.160.4.43.sslip.io/
C=http://cpu-bound.10.160.4.43.sslip.io/

# run $S constant 1
# for i in 1 2 3; do run $S ramp $i; done
# for i in 1 2 3; do run $S burst $i; done

# run $C constant 1
# for i in 1 2 3; do run $C ramp $i; done
for i in 1 2 3; do run $C burst $i; done

# run $M constant 1
# for i in 1 2 3; do run $M ramp $i; done
# for i in 1 2 3; do run $M burst $i; done

echo "===== $(date '+%H:%M:%S') SEMUA SELESAI" | tee -a $LOG