#!/bin/sh
# run-and-collect.sh -- Run a controlled workload experiment and immediately
# collect and merge Prometheus metrics for the recorded measurement window.
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
METRICS_DIR=$(CDPATH= cd -- "$ROOT_DIR/../cloud-dynamics-metrics" && pwd)

# -----------------------------------------------------------------------------
# Terminal styling
# -----------------------------------------------------------------------------
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    YELLOW='\033[1;33m'
    CYAN='\033[0;36m'
    RED='\033[0;31m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    GREEN=''
    BLUE=''
    YELLOW=''
    CYAN=''
    RED=''
    BOLD=''
    NC=''
fi

log_step() {
    echo
    echo "${BLUE}${BOLD}============================================================${NC}"
    echo "${BLUE}${BOLD} $1${NC}"
    echo "${BLUE}${BOLD}============================================================${NC}"
}

log_info() {
    echo "${CYAN}==>${NC} $1"
}

log_warn() {
    echo "${YELLOW}WARNING:${NC} $1"
}

log_error() {
    echo "${RED}ERROR:${NC} $1" >&2
}

log_success() {
    echo "${GREEN}${BOLD}✓ $1${NC}"
}

usage() {
    cat <<EOF
Usage:
  $0 [OPTIONS] <scenario> [app_name]
  $0 [OPTIONS] --all [app_name]

Arguments:
  <scenario>        Scenario file path (e.g. scenarios/constant.env)
                    or profile name (constant, ramp, burst, periodic, variable).
  [app_name]        Target application name (e.g. stateless-api, cpu-bound, microservices).
                    If omitted, inferred from TARGET_URL or defaults to stateless-api.

Options:
  --all             Run all 5 standard scenarios sequentially (constant, ramp, burst, periodic, variable).
  --app <name>      Explicitly specify the application name.
  --target <url>    Explicitly specify the target URL (e.g. http://stateless-api.10.160.4.43.sslip.io/).
  --prom <url>      Explicitly specify Prometheus URL (default: http://prometheus.\${HOST_IP}.sslip.io).
  --namespace <ns>  Kubernetes namespace of the application (default: cloud-dynamics).
  --replicates <N>  Run N replicates for the specified scenario(s).
  --skip-warmup     Skip warmup period (WARMUP_SECONDS=0).
  --skip-cooldown   Skip cooldown period (COOLDOWN_SECONDS=0).
  --check-only      Run preflight reachability and readiness checks without running load.
  -h, --help        Show this help message and exit.

Examples:
  # 1. Run constant scenario against default target and collect metrics:
  $0 scenarios/constant.env

  # 2. Run ramp scenario against cpu-bound application:
  $0 scenarios/ramp.env cpu-bound

  # 3. Run all scenarios against stateless-api:
  $0 --all stateless-api

  # 4. Run with custom target URL and replicate count:
  TARGET_URL="http://stateless-api.10.160.4.43.sslip.io/" REPLICATE=2 $0 scenarios/burst.env
EOF
}

# -----------------------------------------------------------------------------
# Parse options and arguments
# -----------------------------------------------------------------------------
RUN_ALL=0
CHECK_ONLY=0
CLI_SCENARIO=""
CLI_APP=""
CLI_TARGET=""
CLI_PROM=""
CLI_NAMESPACE=""
CLI_REPLICATES=""
CLI_SKIP_WARMUP=0
CLI_SKIP_COOLDOWN=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --all)
            RUN_ALL=1
            shift
            ;;
        --check-only)
            CHECK_ONLY=1
            shift
            ;;
        --skip-warmup)
            CLI_SKIP_WARMUP=1
            shift
            ;;
        --skip-cooldown)
            CLI_SKIP_COOLDOWN=1
            shift
            ;;
        --app)
            [ "$#" -ge 2 ] || { log_error "Option --app requires an argument"; exit 2; }
            CLI_APP="$2"
            shift 2
            ;;
        --target)
            [ "$#" -ge 2 ] || { log_error "Option --target requires an argument"; exit 2; }
            CLI_TARGET="$2"
            shift 2
            ;;
        --prom)
            [ "$#" -ge 2 ] || { log_error "Option --prom requires an argument"; exit 2; }
            CLI_PROM="$2"
            shift 2
            ;;
        --namespace)
            [ "$#" -ge 2 ] || { log_error "Option --namespace requires an argument"; exit 2; }
            CLI_NAMESPACE="$2"
            shift 2
            ;;
        --replicates|--replicate)
            [ "$#" -ge 2 ] || { log_error "Option $1 requires an argument"; exit 2; }
            CLI_REPLICATES="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            log_error "Unknown option: $1"
            usage >&2
            exit 2
            ;;
        *)
            if [ -z "$CLI_SCENARIO" ] && [ "$RUN_ALL" -eq 0 ]; then
                CLI_SCENARIO="$1"
            elif [ -z "$CLI_APP" ]; then
                CLI_APP="$1"
            else
                log_error "Unexpected argument: $1"
                usage >&2
                exit 2
            fi
            shift
            ;;
    esac
done

if [ "$RUN_ALL" -eq 0 ] && [ -z "$CLI_SCENARIO" ] && [ "$CHECK_ONLY" -eq 0 ]; then
    log_error "Missing required scenario argument or --all flag."
    echo
    usage >&2
    exit 2
fi

# -----------------------------------------------------------------------------
# Resolve Configuration & Environment
# -----------------------------------------------------------------------------
[ -d "$METRICS_DIR" ] || {
    log_error "Companion metrics bundle not found at: $METRICS_DIR"
    exit 1
}

CONFIG_FILE="$ROOT_DIR/config/experiment.env"
[ -f "$CONFIG_FILE" ] || { log_error "Missing config file: $CONFIG_FILE"; exit 1; }

# Determine HOST_IP
if [ -n "${HOST_IP-}" ]; then
    CURRENT_HOST_IP="$HOST_IP"
else
    # Auto-detect IP or fallback to 10.160.4.43 / 127.0.0.1
    CURRENT_HOST_IP="$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}')"
    CURRENT_HOST_IP="${CURRENT_HOST_IP:-10.160.4.43}"
fi
export HOST_IP="$CURRENT_HOST_IP"

# Determine target URL & application name
if [ -n "$CLI_TARGET" ]; then
    CURRENT_TARGET_URL="$CLI_TARGET"
elif [ -n "${TARGET_URL-}" ]; then
    CURRENT_TARGET_URL="$TARGET_URL"
else
    CURRENT_TARGET_URL=""
fi

if [ -n "$CLI_APP" ]; then
    APP_NAME="$CLI_APP"
elif [ -n "${APPLICATION_NAME-}" ] && [ "$APPLICATION_NAME" != "cloud-dynamics-app" ] && [ "$APPLICATION_NAME" != "unspecified" ]; then
    APP_NAME="$APPLICATION_NAME"
elif [ -n "$CURRENT_TARGET_URL" ]; then
    # Infer app name from hostname prefix (e.g. http://stateless-api.10.160.4.43.sslip.io/ -> stateless-api)
    INFERRED=$(echo "$CURRENT_TARGET_URL" | sed -E 's|^https?://([^./:]+).*|\1|')
    if [ -n "$INFERRED" ]; then
        APP_NAME="$INFERRED"
    else
        APP_NAME="stateless-api"
    fi
else
    APP_NAME="stateless-api"
fi

if [ -z "$CURRENT_TARGET_URL" ]; then
    CURRENT_TARGET_URL="http://${APP_NAME}.${HOST_IP}.sslip.io/"
fi
export TARGET_URL="$CURRENT_TARGET_URL"
export APPLICATION_NAME="$APP_NAME"

# Determine Prometheus URL
if [ -n "$CLI_PROM" ]; then
    PROM_URL="$CLI_PROM"
elif [ -n "${PROMETHEUS_URL-}" ]; then
    PROM_URL="$PROMETHEUS_URL"
else
    PROM_URL="http://prometheus.${HOST_IP}.sslip.io"
fi
export PROMETHEUS_URL="$PROM_URL"

# Determine Namespace
if [ -n "$CLI_NAMESPACE" ]; then
    NS="$CLI_NAMESPACE"
elif [ -n "${NAMESPACE-}" ]; then
    NS="$NAMESPACE"
else
    NS="cloud-dynamics"
fi
export NAMESPACE="$NS"

if [ "$CLI_SKIP_WARMUP" -eq 1 ]; then
    export WARMUP_SECONDS=0
fi
if [ "$CLI_SKIP_COOLDOWN" -eq 1 ]; then
    export COOLDOWN_SECONDS=0
fi

# -----------------------------------------------------------------------------
# Preflight Verification
# -----------------------------------------------------------------------------
log_step "Preflight Environment Checks"

log_info "Host IP        : $HOST_IP"
log_info "Application    : $APP_NAME"
log_info "Namespace      : $NAMESPACE"
log_info "Target URL     : $TARGET_URL"
log_info "Prometheus URL : $PROMETHEUS_URL"

for cmd in python3 curl; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        log_error "Required command not found in PATH: $cmd"
        exit 1
    fi
done

# 1. Check Target Application
printf "Checking Target Application (%s)... " "$TARGET_URL"
if curl -fsS --max-time 5 "$TARGET_URL" >/dev/null 2>&1; then
    printf "${GREEN}OK${NC}\n"
else
    printf "${RED}FAILED${NC}\n"
    log_error "Target application at $TARGET_URL is not reachable."
    log_warn "Make sure the application is deployed and ingress is functioning."
    exit 1
fi

# 2. Check Prometheus
printf "Checking Prometheus (%s/-/ready)... " "$PROMETHEUS_URL"
if curl -fsS --max-time 5 "$PROMETHEUS_URL/-/ready" >/dev/null 2>&1; then
    printf "${GREEN}OK${NC}\n"
else
    printf "${RED}FAILED${NC}\n"
    log_error "Prometheus at $PROMETHEUS_URL is not ready or unreachable."
    log_warn "Make sure Prometheus is running and port 80/ingress is accessible."
    exit 1
fi

log_success "All preflight checks passed."

if [ "$CHECK_ONLY" -eq 1 ]; then
    log_info "Preflight check-only mode requested. Exiting."
    exit 0
fi

# -----------------------------------------------------------------------------
# Helper: Run Single Scenario & Collect Metrics
# -----------------------------------------------------------------------------
run_single_experiment() {
    SCENARIO_INPUT="$1"
    REPLICATE_NUM="$2"

    # Resolve scenario path
    case "$SCENARIO_INPUT" in
        /*) SCENARIO_FILE="$SCENARIO_INPUT" ;;
        scenarios/*) SCENARIO_FILE="$ROOT_DIR/$SCENARIO_INPUT" ;;
        *.env) SCENARIO_FILE="$ROOT_DIR/scenarios/$SCENARIO_INPUT" ;;
        *) SCENARIO_FILE="$ROOT_DIR/scenarios/$SCENARIO_INPUT.env" ;;
    esac

    [ -f "$SCENARIO_FILE" ] || {
        log_error "Scenario file not found: $SCENARIO_FILE"
        exit 1
    }

    SCENARIO_NAME=$(basename "$SCENARIO_FILE" .env)

    log_step "Executing Scenario: $SCENARIO_NAME (Replicate: $REPLICATE_NUM)"
    log_info "Scenario file : $SCENARIO_FILE"
    log_info "Target URL    : $TARGET_URL"
    log_info "Application   : $APP_NAME"

    export REPLICATE="$REPLICATE_NUM"

    TMP_RUN_LOG=$(mktemp)
    # Execute run-experiment.sh while streaming logs to stdout and capturing
    set +e
    "$ROOT_DIR/scripts/run-experiment.sh" "$SCENARIO_FILE" 2>&1 | tee "$TMP_RUN_LOG"
    RUN_EXIT_CODE="$?"
    set -e

    EXP_ID=$(grep "^Completed: " "$TMP_RUN_LOG" | tail -n 1 | awk '{print $2}')
    rm -f "$TMP_RUN_LOG"

    if [ -z "$EXP_ID" ] || [ "$RUN_EXIT_CODE" -ne 0 ]; then
        log_error "Experiment run failed or incomplete."
        return 1
    fi

    if [ -z "$EXP_ID" ]; then
        # Fallback: identify newest directory under results/
        EXP_OUT=$(ls -td "$ROOT_DIR/results"/*/ 2>/dev/null | head -n 1 | sed 's|/$||')
        EXP_ID=$(basename "$EXP_OUT")
    else
        EXP_OUT="$ROOT_DIR/results/$EXP_ID"
    fi

    [ -d "$EXP_OUT" ] || {
        log_error "Experiment result directory not found: $EXP_OUT"
        return 1
    }

    log_success "Experiment finished. ID: $EXP_ID"

    # -------------------------------------------------------------------------
    # Metrics Collection Phase
    # -------------------------------------------------------------------------
    log_step "Collecting Prometheus Metrics for $EXP_ID"

    # Brief pause to allow Prometheus to scrape the latest metrics from the measurement window
    log_info "Waiting 3s for Prometheus scrape synchronization..."
    sleep 3

    set +e
    "$METRICS_DIR/scripts/collect-experiment.sh" "$EXP_OUT" "$APP_NAME"
    COLLECT_EXIT_CODE="$?"
    set -e

    if [ "$COLLECT_EXIT_CODE" -ne 0 ]; then
        log_error "Metrics collection failed for $EXP_ID"
        return "$COLLECT_EXIT_CODE"
    fi

    # -------------------------------------------------------------------------
    # Verification & Summary Phase
    # -------------------------------------------------------------------------
    COMBINED_FILE="$EXP_OUT/combined.csv"
    if [ ! -f "$COMBINED_FILE" ]; then
        log_error "Combined dataset missing: $COMBINED_FILE"
        return 1
    fi

    TOTAL_ROWS=$(wc -l < "$COMBINED_FILE" | tr -d ' ')
    WORKLOAD_ROWS=$(wc -l < "$EXP_OUT/workload.csv" | tr -d ' ')

    echo
    echo "${GREEN}${BOLD}============================================================${NC}"
    echo "${GREEN}${BOLD} Run and Collection Completed Successfully!${NC}"
    echo "${GREEN}${BOLD}============================================================${NC}"
    echo "  ${BOLD}Experiment ID${NC}     : $EXP_ID"
    echo "  ${BOLD}Scenario${NC}          : $SCENARIO_NAME"
    echo "  ${BOLD}Application${NC}       : $APP_NAME"
    echo "  ${BOLD}Target URL${NC}        : $TARGET_URL"
    echo "  ${BOLD}Workload Samples${NC}  : $((WORKLOAD_ROWS - 1)) observations"
    echo "  ${BOLD}Combined Rows${NC}     : $((TOTAL_ROWS - 1)) joined data points"
    echo
    echo "  ${BOLD}Generated Artifacts:${NC}"
    echo "    - Workload client log : $EXP_OUT/workload.csv"
    echo "    - System metrics dir  : $EXP_OUT/metrics/"
    echo "    - Merged dataset      : ${BOLD}${GREEN}$EXP_OUT/combined.csv${NC}"
    echo "    - Metadata            : $EXP_OUT/metadata.json"
    echo

    if [ -f "$EXP_OUT/metrics/collection-status.csv" ]; then
        echo "  ${BOLD}Prometheus Metrics Status:${NC}"
        while IFS=, read -r m_name m_status m_rows m_query; do
            [ "$m_name" = "metric" ] && continue
            if [ "$m_status" = "ok" ]; then
                printf "    %-24s : ${GREEN}%s${NC} (%s rows)\n" "$m_name" "$m_status" "$m_rows"
            else
                printf "    %-24s : ${YELLOW}%s${NC} (%s rows)\n" "$m_name" "$m_status" "$m_rows"
            fi
        done < "$EXP_OUT/metrics/collection-status.csv"
        echo
    fi
}

# -----------------------------------------------------------------------------
# Main Execution Loop
# -----------------------------------------------------------------------------
REPS="${CLI_REPLICATES:-${REPLICATE:-1}}"

if [ "$RUN_ALL" -eq 1 ]; then
    ALL_SCENARIOS="constant ramp burst periodic variable"
    log_info "Running ALL 5 standard scenarios: $ALL_SCENARIOS"
    log_info "Total replicates per scenario: $REPS"

    rep=1
    while [ "$rep" -le "$REPS" ]; do
        for sc in $ALL_SCENARIOS; do
            run_single_experiment "$sc" "$rep"
        done
        rep=$((rep + 1))
    done
else
    rep=1
    while [ "$rep" -le "$REPS" ]; do
        run_single_experiment "$CLI_SCENARIO" "$rep"
        rep=$((rep + 1))
    done
fi

log_success "All requested experiment runs and metrics collections finished!"
