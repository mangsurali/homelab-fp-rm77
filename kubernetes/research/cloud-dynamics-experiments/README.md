# Cloud Dynamics — Controlled Workload Experiments

This bundle provides a reproducible procedure for running **controlled workload experiments** against cloud applications.

It is designed to work with the companion `cloud-dynamics-applications` bundle, but it can also test any HTTP application reachable from the workload-generator machine.

The bundle is intentionally independent of stage numbering. It performs the workload-generation and experiment-provenance part of the Cloud Dynamics empirical research pipeline.

---

# 1. Purpose

The purpose of this experiment framework is to measure how an application behaves as its workload changes.

A typical experiment investigates relationships such as:

```text
offered workload
       |
       v
application demand
       |
       +--------> CPU / memory / network utilization
       |
       +--------> request throughput
       |
       +--------> latency
       |
       +--------> failures
```

The workload generator records the **input workload and client-side observations**.

Prometheus, Linkerd, Kubernetes, and application telemetry can subsequently provide the **system-side observations** for exactly the same measurement interval.

The complete research flow is:

```text
Application Under Test
         ^
         |
Controlled Workload
         |
         +---- workload.csv
         +---- metadata.json
         +---- measurement-window.env
                       |
                       v
               Prometheus export
                       |
                       v
                 combined dataset
                       |
                       v
                empirical analysis
```

---

# 2. Included workload profiles

Five workload profiles are included.

| Profile | Workload behavior | Typical research purpose |
|---|---|---|
| `constant` | Fixed request rate | baseline and steady-state behavior |
| `ramp` | Gradually increasing request rate | saturation and capacity behavior |
| `burst` | Temporary sharp increase | transient response and recovery |
| `periodic` | Repeated oscillation | recurring demand and response lag |
| `variable` | Reproducible irregular changes | variability and prediction |

The recommended order for a new application is:

```text
constant baseline
       |
       v
repeat baseline
       |
       v
ramp
       |
       v
identify useful operating range
       |
       +----> burst
       +----> periodic
       +----> variable
```

Do not begin by running every workload profile. First establish that the experimental system and workload range are valid.

---

# 3. Directory structure

After extracting the bundle:

```text
cloud-dynamics-experiments/
├── README.md
├── run-and-collect.sh            <-- Quick launcher for run-and-collect
├── config/
│   └── experiment.env
├── scenarios/
│   ├── constant.env
│   ├── ramp.env
│   ├── burst.env
│   ├── periodic.env
│   └── variable.env
├── scripts/
│   ├── check-environment.sh
│   ├── run-experiment.sh
│   ├── run-all.sh
│   ├── run-and-collect.sh        <-- Automated experiment + metrics collection
│   └── run-all-and-collect.sh    <-- Run all scenarios + collect metrics
├── loadgen/
│   └── loadgen.py
└── results/
```

Enter the directory:

```sh
cd cloud-dynamics-experiments
```

---

# 4. Prerequisites

The experiment runner itself requires:

```text
Python 3
curl
POSIX-compatible /bin/sh
```

Verify:

```sh
python3 --version
curl --version
```

The application under test must already be reachable through HTTP.

For the complete Cloud Dynamics environment, the typical platform is:

```text
kind Kubernetes cluster
nginx Ingress
application under test
Linkerd
Prometheus
Grafana
```

Linkerd and Prometheus are not installed by this bundle.

---

# 5. Prepare an application under test

The companion bundle `cloud-dynamics-applications` provides:

```text
stateless-api
cpu-bound
memory-stateful
database-api
cache-api
microservices
```

For example:

```sh
cd cloud-dynamics-applications

./scripts/build-and-load.sh stateless-api
./scripts/deploy.sh stateless-api
./scripts/smoke-test.sh stateless-api
```

If the Kubernetes cluster is reachable at another address, export the address once before using either bundle:

```sh
export HOST_IP=10.160.4.43
```

Then:

```sh
./scripts/deploy.sh stateless-api
./scripts/smoke-test.sh stateless-api
```

will use:

```text
http://stateless-api.10.28.84.254.sslip.io/
```

If `HOST_IP` is not exported, the default throughout the framework is:

```text
127.0.0.1
```

---

# 6. Global experiment configuration

Return to this bundle:

```sh
cd cloud-dynamics-experiments
```

Inspect:

```sh
cat config/experiment.env
```

The principal defaults are:

```sh
HOST_IP=127.0.0.1

REQUEST_TIMEOUT=5

WARMUP_SECONDS=30
WARMUP_RPS=5

COOLDOWN_SECONDS=15

SAMPLE_INTERVAL=1
```

The runner gives an already-exported `HOST_IP` precedence over the value stored in the configuration file.

Therefore this is sufficient for a remote cluster:

```sh
export HOST_IP=10.160.4.43
```

There is no need to edit the configuration merely to change the cluster address.

---

# 7. Select the target application

The most explicit way to select an application is `TARGET_URL`.

For the stateless application:

```sh
export TARGET_URL="http://stateless-api.${HOST_IP:-127.0.0.1}.sslip.io/"
```

Check:

```sh
echo "$TARGET_URL"
```

For the CPU-bound application:

```sh
export TARGET_URL="http://cpu-bound.${HOST_IP:-127.0.0.1}.sslip.io/?work=15000"
```

For the database application:

```sh
export TARGET_URL="http://database-api.${HOST_IP:-127.0.0.1}.sslip.io/"
```

Using `TARGET_URL` is recommended because the experiment bundle can then target applications with different hostnames and paths.

---

# 8. Verify the target manually

Before generating experimental traffic:

```sh
curl -i "$TARGET_URL"
```

A successful response must be obtained.

If the target is Kubernetes-based, inspect:

```sh
kubectl get pods -A
kubectl get svc -A
kubectl get ingress -A
```

If Linkerd is used:

```sh
linkerd check
linkerd viz check
```

Do not collect experimental data until basic reachability is working.

---

# 9. Record the application configuration

Edit:

```sh
config/experiment.env
```

and describe the experimental target.

Example:

```sh
APPLICATION_NAME=stateless-api
APPLICATION_ARCHITECTURE=stateless

REPLICAS=2

CPU_REQUEST=100m
CPU_LIMIT=500m

MEMORY_REQUEST=64Mi
MEMORY_LIMIT=256Mi
```

These fields document the experimental condition.

They do **not** modify Kubernetes.

The actual Kubernetes resources and the recorded metadata should agree.

---

# 10. Check the environment automatically

Run:

```sh
./scripts/check-environment.sh
```

If `TARGET_URL` is exported, the checker uses it.

A successful check resembles:

```text
Target: http://stateless-api.127.0.0.1.sslip.io/
OK: target is reachable.
```

For a remote environment:

```sh
export HOST_IP=10.160.4.43
export TARGET_URL="http://stateless-api.${HOST_IP}.sslip.io/"

./scripts/check-environment.sh
```

Do not proceed when this check fails.

---

# 11. Understand the experiment phases

Every experiment consists of:

```text
time ------------------------------------------------------>

       warm-up             measurement          cool-down
|-------------------|-----------------------|---------------|
 stabilization          recorded workload       separation
```

## Warm-up

Default:

```sh
WARMUP_SECONDS=30
WARMUP_RPS=5
```

Warm-up allows connections, caches, application processes, and monitoring components to reach an operational state.

Warm-up traffic is excluded from `workload.csv`.

## Measurement

The selected workload scenario runs during this interval.

The framework records:

```text
MEASUREMENT_START_EPOCH
MEASUREMENT_END_EPOCH
```

## Cool-down

Default:

```sh
COOLDOWN_SECONDS=15
```

Cool-down separates consecutive experiments and reduces carry-over effects.

Increase it if the application needs more time to return to baseline.

---

# 12. Inspect the constant baseline scenario

Open:

```sh
cat scenarios/constant.env
```

Default:

```sh
PROFILE=constant
DURATION=300
RPS=25
```

Interpretation:

```text
profile              constant
measurement duration 300 seconds
target workload      25 requests/second
```

For an unfamiliar application, begin with a workload that is expected to be comfortably below saturation.

The first experiment is a validation experiment, not a maximum-capacity test.

---

# 13. Run the first baseline experiment

With `TARGET_URL` already exported:

```sh
./scripts/run-experiment.sh scenarios/constant.env
```

The runner performs:

```text
1. load experiment configuration
2. load scenario
3. determine target URL
4. create a unique experiment ID
5. verify target reachability
6. generate warm-up traffic
7. record measurement start
8. execute workload
9. record workload observations
10. record measurement end
11. save metadata
12. save measurement window
13. perform cool-down
```

A typical experiment ID is:

```text
constant-20261006T020000Z-r1
```

and the result appears under:

```text
results/constant-20261006T020000Z-r1/
```

---

# 14. Inspect the result

List experiments:

```sh
ls -lah results/
```

Inspect one experiment:

```sh
ls -lah results/<experiment-id>/
```

The directory contains:

```text
experiment.env
scenario.env
metadata.json
workload.csv
run.log
measurement-window.env
```

Inspect the workload:

```sh
head results/<experiment-id>/workload.csv
```

Columns are:

```text
timestamp_epoch
elapsed_s
target_rps
sent
success
failed
achieved_rps
mean_latency_ms
p95_latency_ms
```

Inspect metadata:

```sh
cat results/<experiment-id>/metadata.json
```

Inspect the measurement window:

```sh
cat results/<experiment-id>/measurement-window.env
```

---

# 15. Interpret workload measurements correctly

Three quantities must remain distinct:

```text
target_rps
    =
workload requested by the experiment

achieved_rps
    =
workload actually generated by the client

server throughput
    =
requests actually processed by the application
```

They are not necessarily equal.

For example:

```text
target_rps        200
achieved_rps      190
server throughput 150
```

could indicate client limitations, queuing, application saturation, request timeouts, or downstream bottlenecks.

`server throughput` should therefore be measured independently through application/Linkerd/Prometheus telemetry rather than inferred from `target_rps`.

---

# 16. Validate the baseline

Do not automatically accept a run because the script completed.

Verify:

```text
[ ] target was reachable
[ ] requests were generated
[ ] achieved_rps is plausible
[ ] failures are understood
[ ] latency is plausible
[ ] measurement duration is correct
[ ] Prometheus operated throughout the run
[ ] no unintended infrastructure failure occurred
```

At low load:

```text
target_rps ≈ achieved_rps
```

is generally expected.

A large difference may indicate that the workload generator itself, networking, or the target system is constrained.

---

# 17. Repeat the baseline

A single run should normally not be treated as representative.

Example with five replicates:

```sh
for i in 1 2 3 4 5
do
    REPLICATE="$i" \
    ./scripts/run-experiment.sh scenarios/constant.env
done
```

Because `TARGET_URL` and `HOST_IP` can already be exported, they do not need to be repeated.

Replicates allow analysis of:

```text
run-to-run variability
confidence intervals
measurement stability
uncontrolled background effects
```

The number of repetitions should ultimately be justified by the statistical analysis.

---

# 18. Run a ramp experiment

Inspect:

```sh
cat scenarios/ramp.env
```

Default:

```sh
PROFILE=ramp
DURATION=600
START_RPS=10
END_RPS=200
```

Conceptually:

```text
RPS
 ^
 |                            /
 |                         /
 |                      /
 |                   /
 |                /
 |_____________/________________> time
```

Run:

```sh
./scripts/run-experiment.sh scenarios/ramp.env
```

The purpose is to observe how the system transitions from low demand toward a saturation region.

Potential behavior is:

```text
increasing workload
       |
       v
resource utilization rises
       |
       v
contention / queueing
       |
       +---- latency rises
       |
       +---- throughput approaches plateau
       |
       +---- failures may appear
```

This is a hypothesis to investigate, not behavior that should be assumed.

---

# 19. Adjust and repeat the ramp

If `END_RPS=200` never approaches an interesting operating region, increase it.

If the application is already overloaded at `START_RPS=10`, lower the range.

After selecting a meaningful range:

```sh
for i in 1 2 3 4 5
do
    REPLICATE="$i" \
    ./scripts/run-experiment.sh scenarios/ramp.env
done
```

Use the same range for comparisons where workload is intended to remain controlled.

---

# 20. Run a burst experiment

Inspect:

```sh
cat scenarios/burst.env
```

Default:

```sh
PROFILE=burst
DURATION=600

BASE_RPS=10
BURST_RPS=150

BURST_START=180
BURST_DURATION=120
```

Pattern:

```text
RPS
 ^
 |               +-----------+
 |               |           |
 |_______________|           |____________
 +------------------------------------------> time
```

Run:

```sh
./scripts/run-experiment.sh scenarios/burst.env
```

Useful research questions include:

```text
How quickly does latency react?
Does throughput recover?
Does autoscaling respond?
How long does recovery take?
Does the burst cause failures?
```

---

# 21. Run a periodic experiment

Inspect:

```sh
cat scenarios/periodic.env
```

Default:

```sh
PROFILE=periodic
DURATION=600
MIN_RPS=10
MAX_RPS=100
PERIOD_SECONDS=120
```

Run:

```sh
./scripts/run-experiment.sh scenarios/periodic.env
```

This profile is useful for studying:

```text
recurring workload
resource-response lag
autoscaling lag
correlation
prediction
```

---

# 22. Run a variable experiment

Inspect:

```sh
cat scenarios/variable.env
```

Default:

```sh
PROFILE=variable
DURATION=600
MIN_RPS=10
MAX_RPS=100
CHANGE_INTERVAL=30
SEED=42
```

Run:

```sh
./scripts/run-experiment.sh scenarios/variable.env
```

`SEED` makes the workload sequence reproducible.

Keep the same seed when exact workload reproduction is required.

Use different seeds only when workload randomness is intentionally an experimental factor.

---

# 23. Do not begin with `run-all.sh`

The bundle contains:

```sh
./scripts/run-all.sh
```

but the preferred initial procedure is:

```text
baseline
   ↓
validate
   ↓
repeat
   ↓
ramp
   ↓
validate range
   ↓
repeat
   ↓
additional profiles
```

`run-all.sh` is more appropriate after the experimental procedure and workload ranges have already been validated.

---

# 24. Test another application architecture

Suppose the baseline experiment used:

```text
stateless-api
```

Switch to the CPU-bound application using the companion applications bundle:

```sh
cd ../cloud-dynamics-applications

./scripts/build-and-load.sh cpu-bound
./scripts/deploy.sh cpu-bound
./scripts/smoke-test.sh cpu-bound
```

Then return:

```sh
cd ../cloud-dynamics-experiments
```

Set:

```sh
export TARGET_URL="http://cpu-bound.${HOST_IP:-127.0.0.1}.sslip.io/?work=15000"
```

Update application metadata:

```sh
APPLICATION_NAME=cpu-bound
APPLICATION_ARCHITECTURE=cpu-bound
```

and repeat the same experimental procedure.

This allows the **application architecture** to become an independent variable.

---

# 25. Example comparative study

A simple experiment can ask:

> How do different application architectures respond to equivalent workload dynamics?

Use:

```text
Applications:
    stateless-api
    cpu-bound
    database-api

Workloads:
    constant
    ramp

Replicates:
    5

Controlled where meaningful:
    workload duration
    sampling interval
    replica count
    CPU/memory limits
    cluster topology
    monitoring configuration
```

A minimal matrix is:

| ID | Application | Workload | Replicates |
|---|---|---|---:|
| E1 | stateless-api | constant | 5 |
| E2 | stateless-api | ramp | 5 |
| E3 | cpu-bound | constant | 5 |
| E4 | cpu-bound | ramp | 5 |
| E5 | database-api | constant | 5 |
| E6 | database-api | ramp | 5 |

After validating this matrix, extend it with burst, periodic, variable, memory-stateful, cache-api, and microservices experiments.

---

# 26. Experimental variables

Before executing a campaign, define:

## Independent variables

Factors deliberately changed.

Examples:

```text
offered workload
application architecture
replica count
CPU allocation
memory allocation
```

## Dependent variables

Measured responses.

Examples:

```text
throughput
latency
failure rate
CPU utilization
memory utilization
network traffic
```

## Controlled variables

Factors intended to remain unchanged.

Examples:

```text
application version
cluster topology
workload duration
sampling interval
Linkerd configuration
Prometheus configuration
workload generator machine
```

Avoid unintentionally changing several independent variables simultaneously.

---

# 27. Measurement-window handoff

Every accepted experiment contains:

```sh
results/<experiment-id>/measurement-window.env
```

Example:

```text
EXPERIMENT_ID=ramp-20261006T020000Z-r1
MEASUREMENT_START_EPOCH=1791252000
MEASUREMENT_END_EPOCH=1791252600
SAMPLE_INTERVAL=1
```

Use these timestamps to retrieve infrastructure and service metrics from Prometheus.

Conceptually:

```text
workload.csv
      |
      | timestamp
      +-------------------+
                          |
Prometheus metrics -------+
                          |
                          v
                   combined dataset
```

This prevents the workload and monitoring datasets from being aligned using approximate experiment times.

---

# 28. Recommended metrics for the combined dataset

The exact metrics depend on the research question.

## Workload-side

Already generated here:

```text
target_rps
achieved_rps
success
failed
mean_latency_ms
p95_latency_ms
```

## Service/application-side

Possible observations:

```text
request rate
success rate
response latency
application-specific timing
```

## Kubernetes/container-side

Typical observations:

```text
CPU usage
CPU throttling
memory usage
network receive
network transmit
pod count
container restart count
```

## Events/context

Potential observations:

```text
pod creation
pod termination
autoscaling
scheduling
restart
node-condition change
```

---

# 29. Accepting and rejecting experiments

Accept a run only when:

```text
[ ] intended configuration was active
[ ] target endpoint was reachable
[ ] workload generator completed
[ ] measurement duration was obtained
[ ] workload.csv was produced
[ ] metadata is correct
[ ] Prometheus was available
[ ] no unintended cluster failure occurred
```

Reject or separately label a run when, for example:

```text
application unexpectedly restarted
workload-generator machine became overloaded
network connectivity failed
Prometheus stopped collecting
configuration changed unintentionally
another workload interfered with the experiment
```

Do not silently include such runs in the primary dataset.

---

# 30. Reproducibility checklist

Every accepted experiment should preserve:

```text
[ ] experiment ID
[ ] application name
[ ] application architecture
[ ] application/image version
[ ] replica count
[ ] CPU/memory configuration
[ ] workload scenario
[ ] workload parameters
[ ] replicate number
[ ] workload.csv
[ ] metadata.json
[ ] measurement-window.env
[ ] corresponding monitoring data
[ ] validity status
```

Do not modify a completed result directory. Change the configuration and create a new run.

---

# 31. Typical local session

With no global variables set:

```sh
unset HOST_IP
export TARGET_URL="http://stateless-api.127.0.0.1.sslip.io/"

./scripts/check-environment.sh
./scripts/run-experiment.sh scenarios/constant.env
./scripts/run-experiment.sh scenarios/ramp.env
```

The default address is `127.0.0.1`.

---

# 32. Typical remote-cluster session

Set the cluster address once:

```sh
export HOST_IP=10.160.4.43
```

Select an application:

```sh
export TARGET_URL="http://stateless-api.${HOST_IP}.sslip.io/"
```

Verify:

```sh
./scripts/check-environment.sh
```

Run baseline:

```sh
./scripts/run-experiment.sh scenarios/constant.env
```

Repeat:

```sh
for i in 1 2 3 4 5
do
    REPLICATE="$i" ./scripts/run-experiment.sh scenarios/constant.env
done
```

Run ramp:

```sh
./scripts/run-experiment.sh scenarios/ramp.env
```

Repeat:

```sh
for i in 1 2 3 4 5
do
    REPLICATE="$i" ./scripts/run-experiment.sh scenarios/ramp.env
done
```

The address does not need to be repeated in each command.

---

# 33. Final output

After an experimental campaign:

```text
results/
├── constant-...-r1/
├── constant-...-r2/
├── constant-...-r3/
├── constant-...-r4/
├── constant-...-r5/
├── ramp-...-r1/
├── ramp-...-r2/
├── ramp-...-r3/
├── ramp-...-r4/
└── ramp-...-r5/
```

Each directory provides the controlled workload observations and exact measurement interval required to obtain corresponding system telemetry.

The next part of the Cloud Dynamics framework can therefore operate deterministically:

```text
for each experiment
       |
       v
read measurement-window.env
       |
       v
query Prometheus
       |
       +---- Kubernetes metrics
       +---- Linkerd metrics
       +---- application metrics
       |
       v
align by timestamp
       |
       v
combined.csv
       |
       v
empirical analysis
```

This preserves the separation between **controlled workload generation**, **system observation**, and **data analysis**, while keeping them linked by experiment identity and measurement time.

---

# 34. Automated End-to-End Workflow (`run-and-collect.sh`)

To streamline testing and metrics harvesting, the script `run-and-collect.sh` bridges this experiment bundle directly with `cloud-dynamics-metrics`.

It executes a scenario and immediately collects, aligns, and merges Prometheus metrics for the exact measurement window in a single automated step:

```text
Target Application & Prometheus Preflight Check
                    |
                    v
       Execute Workload Experiment (loadgen)
                    |
                    +--> workload.csv
                    +--> metadata.json
                    +--> measurement-window.env
                    |
                    v
    Query Prometheus for [start_epoch, end_epoch]
                    |
                    +--> metrics/*.csv
                    |
                    v
     Timestamp Join (workload + system metrics)
                    |
                    v
               combined.csv
```

### Quickstart

From the `cloud-dynamics-experiments` directory:

```sh
# 1. Run a single scenario (e.g. constant) and automatically collect metrics:
./scripts/run-and-collect.sh scenarios/constant.env

# Alternatively using the root wrapper:
./run-and-collect.sh scenarios/constant.env
```

### Specifying Target Application

By default, the script targets `stateless-api` (or infers the application name from `TARGET_URL`). To test another application (e.g., `cpu-bound`, `microservices`):

```sh
# Specify application as positional argument:
./scripts/run-and-collect.sh scenarios/ramp.env cpu-bound

# Or using the --app flag:
./scripts/run-and-collect.sh scenarios/ramp.env --app cpu-bound
```

### Running All Scenarios

To run all 5 standard scenarios (`constant`, `ramp`, `burst`, `periodic`, `variable`) sequentially and collect metrics for each:

```sh
./scripts/run-all-and-collect.sh stateless-api
# or:
./scripts/run-and-collect.sh --all stateless-api
```

### Options and Flags

```text
Usage:
  ./scripts/run-and-collect.sh [OPTIONS] <scenario> [app_name]
  ./scripts/run-and-collect.sh [OPTIONS] --all [app_name]

Arguments:
  <scenario>        Scenario file path (e.g. scenarios/constant.env)
                    or profile name (constant, ramp, burst, periodic, variable).
  [app_name]        Target application name (e.g. stateless-api, cpu-bound, microservices).
                    If omitted, inferred from TARGET_URL or defaults to stateless-api.

Options:
  --all             Run all 5 standard scenarios sequentially.
  --app <name>      Explicitly specify the application name.
  --target <url>    Explicitly specify the target URL.
  --prom <url>      Explicitly specify Prometheus URL (default: http://prometheus.${HOST_IP}.sslip.io).
  --namespace <ns>  Kubernetes namespace of the application (default: cloud-dynamics).
  --replicates <N>  Run N replicates for the specified scenario(s).
  --skip-warmup     Skip warmup period (WARMUP_SECONDS=0).
  --skip-cooldown   Skip cooldown period (COOLDOWN_SECONDS=0).
  --check-only      Run preflight reachability and readiness checks without running load.
  -h, --help        Show usage message.
```

### Output Structure

Each completed run produces a self-contained directory under `results/<experiment-id>/`:

```text
results/<experiment-id>/
├── experiment.env
├── scenario.env
├── metadata.json
├── run.log
├── workload.csv                  # Client-side observations (RPS, latency, errors)
├── measurement-window.env        # Exact timestamp boundary [start, end]
├── metrics/                      # Raw Prometheus metric exports
│   ├── cpu_usage.csv
│   ├── cpu_throttled.csv
│   ├── memory_working_set.csv
│   ├── network_rx.csv
│   ├── network_tx.csv
│   ├── restarts.csv
│   ├── ready_pods.csv
│   ├── linkerd_request_rate.csv     # Inbound total throughput (RPS)
│   ├── linkerd_goodput_rps.csv      # Inbound successful request rate (Goodput RPS)
│   ├── linkerd_success_rate.csv     # Success rate ratio (0.0 - 1.0)
│   ├── linkerd_failed_rps.csv       # Error / failed request rate
│   ├── linkerd_latency_p50.csv      # Median latency (ms)
│   ├── linkerd_latency_p95.csv      # P95 latency (ms)
│   ├── linkerd_latency_p99.csv      # P99 latency (ms)
│   ├── linkerd_throughput_bytes.csv # TCP write throughput delivered (bytes/s)
│   ├── linkerd_tcp_connections.csv  # Active TCP connections
│   ├── collection-status.csv
│   └── collection-metadata.json
└── combined.csv                  # Final merged research dataset!
```

### Inspecting the Merged Dataset

```sh
# View column headers:
head -n 1 results/<experiment-id>/combined.csv

# View first 10 data points:
head -n 11 results/<experiment-id>/combined.csv

# Check metric collection status:
cat results/<experiment-id>/metrics/collection-status.csv
```

