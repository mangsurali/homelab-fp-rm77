#!/bin/sh
# run-all-and-collect.sh -- Run multiple scenarios sequentially and collect
# Prometheus metrics for each one, with a 2-minute cooldown between runs.
#
# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION – Edit the variables below to suit your experiment session.
# ─────────────────────────────────────────────────────────────────────────────

# Target application name.
# Available apps (examples): stateless-api | cpu-bound | microservices
APP_NAME="microservices"

# Ordered list of scenarios to run (space-separated).
# Available profiles: constant | ramp | burst | periodic | variable
SCENARIOS="constant ramp burst"

# Number of replicates per scenario.
REPLICATES=3

# Cooldown pause between consecutive scenarios (in seconds).
BETWEEN_COOLDOWN=120   # 2 minutes

# Optional overrides – leave empty to auto-detect / use defaults.
TARGET_URL=""          # e.g. "http://stateless-api.10.160.4.43.sslip.io/"
PROMETHEUS_URL=""      # e.g. "http://prometheus.10.160.4.43.sslip.io"
NAMESPACE=""           # e.g. "cloud-dynamics"

# Skip warmup / cooldown inside each individual experiment run?
SKIP_WARMUP=0          # set to 1 to skip
SKIP_COOLDOWN=0        # set to 1 to skip

# ─────────────────────────────────────────────────────────────────────────────
# END OF USER CONFIGURATION – No changes needed below this line.
# ─────────────────────────────────────────────────────────────────────────────
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SCRIPT="$ROOT_DIR/scripts/run-and-collect.sh"

# ── Terminal styling ──────────────────────────────────────────────────────────
if [ -t 1 ]; then
    GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'
    CYAN='\033[0;36m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
else
    GREEN=''; BLUE=''; YELLOW=''; CYAN=''; RED=''; BOLD=''; NC=''
fi

log_step() {
    echo
    echo "${BLUE}${BOLD}============================================================${NC}"
    echo "${BLUE}${BOLD} $1${NC}"
    echo "${BLUE}${BOLD}============================================================${NC}"
}
log_info()    { echo "${CYAN}==>${NC} $1"; }
log_warn()    { echo "${YELLOW}WARNING:${NC} $1"; }
log_success() { echo "${GREEN}${BOLD}✓ $1${NC}"; }
log_error()   { echo "${RED}ERROR:${NC} $1" >&2; }

# ── Sanity checks ─────────────────────────────────────────────────────────────
[ -f "$SCRIPT" ] || { log_error "run-and-collect.sh not found at: $SCRIPT"; exit 1; }
[ -n "$APP_NAME" ] || { log_error "APP_NAME must not be empty."; exit 1; }
[ -n "$SCENARIOS" ] || { log_error "SCENARIOS must not be empty."; exit 1; }

# ── Build common flags to forward to run-and-collect.sh ───────────────────────
COMMON_FLAGS="--app $APP_NAME"

[ -n "$TARGET_URL" ]     && COMMON_FLAGS="$COMMON_FLAGS --target $TARGET_URL"
[ -n "$PROMETHEUS_URL" ] && COMMON_FLAGS="$COMMON_FLAGS --prom $PROMETHEUS_URL"
[ -n "$NAMESPACE" ]      && COMMON_FLAGS="$COMMON_FLAGS --namespace $NAMESPACE"
[ "$SKIP_WARMUP" -eq 1 ] && COMMON_FLAGS="$COMMON_FLAGS --skip-warmup"
[ "$SKIP_COOLDOWN" -eq 1 ] && COMMON_FLAGS="$COMMON_FLAGS --skip-cooldown"

# ── Count total scenarios ─────────────────────────────────────────────────────
TOTAL=0
for _sc in $SCENARIOS; do TOTAL=$((TOTAL + 1)); done

# ── Session header ────────────────────────────────────────────────────────────
log_step "Batch Experiment Session"
log_info "Application      : ${BOLD}$APP_NAME${NC}"
log_info "Scenarios (${TOTAL})    : $SCENARIOS"
log_info "Replicates       : $REPLICATES"
log_info "Between cooldown : ${BETWEEN_COOLDOWN}s"
[ -n "$TARGET_URL" ]     && log_info "Target URL       : $TARGET_URL"
[ -n "$PROMETHEUS_URL" ] && log_info "Prometheus URL   : $PROMETHEUS_URL"
[ -n "$NAMESPACE" ]      && log_info "Namespace        : $NAMESPACE"
echo

# ── Main loop ─────────────────────────────────────────────────────────────────
FAILED_SCENARIOS=""
SCENARIO_INDEX=0

for SCENARIO in $SCENARIOS; do
    SCENARIO_INDEX=$((SCENARIO_INDEX + 1))

    log_step "Scenario ${SCENARIO_INDEX}/${TOTAL}: ${SCENARIO}  (app: ${APP_NAME})"

    # shellcheck disable=SC2086
    if "$SCRIPT" $COMMON_FLAGS --replicates "$REPLICATES" "$SCENARIO"; then
        log_success "Scenario '${SCENARIO}' completed successfully."
    else
        log_error "Scenario '${SCENARIO}' failed. Continuing to next scenario..."
        FAILED_SCENARIOS="${FAILED_SCENARIOS} ${SCENARIO}"
    fi

    # Inter-scenario cooldown (skip after the last scenario)
    if [ "$SCENARIO_INDEX" -lt "$TOTAL" ]; then
        echo
        log_info "Cooldown: waiting ${BETWEEN_COOLDOWN}s before next scenario..."
        REMAINING="$BETWEEN_COOLDOWN"
        while [ "$REMAINING" -gt 0 ]; do
            printf "\r  ${CYAN}%3ds remaining...${NC}   " "$REMAINING"
            sleep 1
            REMAINING=$((REMAINING - 1))
        done
        printf "\r  ${GREEN}Cooldown complete.${NC}            \n"
    fi
done

# ── Final summary ─────────────────────────────────────────────────────────────
echo
echo "${GREEN}${BOLD}============================================================${NC}"
echo "${GREEN}${BOLD} Batch Session Complete${NC}"
echo "${GREEN}${BOLD}============================================================${NC}"
echo "  ${BOLD}Application${NC}  : $APP_NAME"
echo "  ${BOLD}Scenarios run${NC}: $SCENARIOS"
echo "  ${BOLD}Replicates${NC}   : $REPLICATES"

if [ -n "$FAILED_SCENARIOS" ]; then
    echo
    log_warn "The following scenarios reported failures:${FAILED_SCENARIOS}"
    echo "${YELLOW}${BOLD}Session finished with errors.${NC}"
    exit 1
else
    echo
    log_success "All scenarios and metrics collections finished successfully!"
fi
