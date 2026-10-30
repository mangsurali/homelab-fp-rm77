#!/usr/bin/env python3
"""
loadgen_v2.py
High-Performance Open-Loop Asynchronous Workload Generator for Cloud Dynamics Experiments.

Key Improvements over loadgen.py (v1):
1. Eliminates Client-Side Queueing (Coordinated Omission):
   Replaces the blocking ThreadPoolExecutor(256) with an open-loop asyncio + aiohttp engine.
   Scheduled requests are dispatched immediately onto the network without waiting in an internal queue.
2. Real-World System Queueing:
   Unbounded concurrency (aiohttp.TCPConnector(limit=0)) pushes the actual queue backlog into the
   Kubernetes network (NGINX Ingress socket backlog, Linkerd proxy buffers, and Linux kernel buffers).
3. Schedule-Time Latency Tracking:
   Measures true end-to-end user-perceived response time: latency = (finish_time - scheduled_time).
4. True Absolute Deadline / Timeout:
   If a request is not completed within --timeout seconds from its scheduled arrival time,
   it is immediately aborted/cancelled and recorded as FAILED (TIMEOUT).
5. Clean Termination & Bounded Drain:
   Grace period at test end is bounded to at most --timeout seconds, completely eliminating
   uncontrolled multi-hour ghost drains.
"""

import argparse
import asyncio
import csv
import math
import os
import random
import resource
import statistics
import sys
import time

try:
    import aiohttp
except ImportError:
    sys.exit(
        "ERROR: aiohttp is required for loadgen_v2.py.\n"
        "Please install it via: pip install aiohttp"
    )

def parse_arguments():
    p = argparse.ArgumentParser(description="Cloud Dynamics Open-Loop HTTP Workload Generator v2")
    p.add_argument("--url", required=True, help="Target HTTP URL")
    p.add_argument("--profile", choices=["constant", "ramp", "burst", "periodic", "variable"], required=True)
    p.add_argument("--duration", type=float, required=True, help="Test duration in seconds")
    p.add_argument("--timeout", type=float, default=5.0, help="Absolute request timeout in seconds (default: 5.0)")
    p.add_argument("--sample-interval", type=float, default=1.0, help="Sampling interval in seconds (default: 1.0)")
    p.add_argument("--output", help="Output CSV path for workload metrics")
    p.add_argument("--discard-output", action="store_true", help="Discard output (useful for warmup)")
    
    # Workload profile parameters
    p.add_argument("--rps", type=float, help="RPS for constant profile")
    p.add_argument("--start-rps", type=float, help="Starting RPS for ramp profile")
    p.add_argument("--end-rps", type=float, help="Ending RPS for ramp profile")
    p.add_argument("--base-rps", type=float, help="Baseline RPS for burst profile")
    p.add_argument("--burst-rps", type=float, help="Burst RPS for burst profile")
    p.add_argument("--burst-start", type=float, default=0.0, help="Burst start time in seconds")
    p.add_argument("--burst-duration", type=float, default=0.0, help="Burst duration in seconds")
    p.add_argument("--min-rps", type=float, help="Minimum RPS for periodic/variable profile")
    p.add_argument("--max-rps", type=float, help="Maximum RPS for periodic/variable profile")
    p.add_argument("--period-seconds", type=float, default=60.0, help="Period in seconds for periodic profile")
    p.add_argument("--change-interval", type=float, default=30.0, help="Step change interval for variable profile")
    p.add_argument("--seed", type=int, default=42, help="Random seed for variable profile")
    
    # Engine tuning options
    p.add_argument("--workers", type=int, default=256, help="Legacy compatibility flag (ignored in v2)")
    p.add_argument("--concurrency-limit", type=int, default=0, help="Max in-flight connections (0 = unlimited)")
    p.add_argument("--disable-keepalive", action="store_true", help="Disable HTTP keep-alive (force close per request)")
    p.add_argument("--user-agent", default="cloud-dynamics-stage3/2.0", help="HTTP User-Agent header")
    return p.parse_args()

def adjust_file_descriptor_limit():
    """Raise soft RLIMIT_NOFILE to maximum available hard limit to allow thousands of open sockets."""
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        target = min(65535, hard)
        if soft < target:
            resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
    except Exception as e:
        print(f"[WARN] Failed to adjust RLIMIT_NOFILE: {e}", file=sys.stderr)

def percentile(vals, q):
    if not vals:
        return 0.0
    s = sorted(vals)
    i = min(len(s) - 1, max(0, math.ceil(q * len(s)) - 1))
    return s[i]

def target_rate(a, elapsed, rng, variable_state):
    if a.profile == "constant":
        return max(0.0, a.rps or 0.0)
    if a.profile == "ramp":
        f = min(1.0, max(0.0, elapsed / max(a.duration, 1e-9)))
        start_rps = a.start_rps or 0.0
        end_rps = a.end_rps or 0.0
        return max(0.0, start_rps + (end_rps - start_rps) * f)
    if a.profile == "burst":
        inside = a.burst_start <= elapsed < a.burst_start + a.burst_duration
        return max(0.0, (a.burst_rps or 0.0) if inside else (a.base_rps or 0.0))
    if a.profile == "periodic":
        min_rps = a.min_rps or 0.0
        max_rps = a.max_rps or 0.0
        mid = (min_rps + max_rps) / 2.0
        amp = (max_rps - min_rps) / 2.0
        return max(0.0, mid + amp * math.sin(2.0 * math.pi * elapsed / max(a.period_seconds, 1e-9)))
    # variable profile
    min_rps = a.min_rps or 0.0
    max_rps = a.max_rps or 0.0
    bucket = int(elapsed // max(a.change_interval, 1e-9))
    if variable_state[0] != bucket:
        variable_state[:] = [bucket, rng.uniform(min_rps, max_rps)]
    return max(0.0, variable_state[1])

class SampleTracker:
    """Tracks interval-level telemetry and in-flight request status."""
    def __init__(self):
        self.interval_sent = 0
        self.interval_results = []
        self.in_flight = 0
        self.total_sent = 0
        self.total_success = 0
        self.total_failed = 0

    def record_sent(self):
        self.interval_sent += 1
        self.total_sent += 1
        self.in_flight += 1

    def record_result(self, ok, latency_ms, status_code, error):
        self.in_flight = max(0, self.in_flight - 1)
        if ok:
            self.total_success += 1
        else:
            self.total_failed += 1
        self.interval_results.append((ok, latency_ms, status_code, error))

    def flush_interval(self):
        sent = self.interval_sent
        results = self.interval_results
        self.interval_sent = 0
        self.interval_results = []
        return sent, results, self.in_flight

async def send_request(session, url, t_sched, timeout, sample_tracker, headers, sem=None):
    """
    Executes a single HTTP request with strict deadline enforcement from t_sched.
    Eliminates Coordinated Omission by computing latency from t_sched.
    """
    if sem:
        await sem.acquire()

    sample_tracker.record_sent()
    now = time.monotonic()
    deadline = t_sched + timeout
    remaining = deadline - now

    if remaining <= 0:
        # Request could not be dispatched before its deadline expired (extreme client overload)
        if sem:
            sem.release()
        sample_tracker.record_result(ok=False, latency_ms=(now - t_sched) * 1000.0, status_code=504, error="dispatch_timeout")
        return

    req_timeout = aiohttp.ClientTimeout(total=remaining)
    try:
        async with session.get(url, headers=headers, timeout=req_timeout) as resp:
            # Read first byte to ensure server produced body bytes
            await resp.content.read(1)
            t_done = time.monotonic()
            latency_ms = (t_done - t_sched) * 1000.0
            status = resp.status
            ok = 200 <= status < 400
            sample_tracker.record_result(ok=ok, latency_ms=latency_ms, status_code=status, error=None)
    except asyncio.TimeoutError:
        t_done = time.monotonic()
        latency_ms = (t_done - t_sched) * 1000.0
        sample_tracker.record_result(ok=False, latency_ms=latency_ms, status_code=504, error="timeout")
    except (aiohttp.ClientError, OSError, asyncio.CancelledError) as e:
        t_done = time.monotonic()
        latency_ms = (t_done - t_sched) * 1000.0
        sample_tracker.record_result(ok=False, latency_ms=latency_ms, status_code=502, error=str(e))
    finally:
        if sem:
            sem.release()

async def sampler_loop(tracker, sample_interval, duration, timeout, target_rate_fn, writer, out_file, stop_event):
    """Periodically writes per-interval telemetry rows to CSV."""
    start_mono = time.monotonic()
    next_sample = start_mono + sample_interval

    while True:
        now = time.monotonic()
        sleep_dur = next_sample - now
        if sleep_dur > 0:
            await asyncio.sleep(sleep_dur)

        now = time.monotonic()
        elapsed = now - start_mono
        sent, results, in_flight = tracker.flush_interval()

        success = sum(1 for ok, _, _, _ in results if ok)
        failed = len(results) - success
        latencies = [lat for _, lat, _, _ in results]

        mean_lat = statistics.mean(latencies) if latencies else 0.0
        p95_lat = percentile(latencies, 0.95) if latencies else 0.0
        sample_rate = target_rate_fn(min(elapsed, duration))

        row = [
            f"{time.time():.6f}",
            f"{elapsed:.3f}",
            f"{sample_rate:.3f}",
            sent,
            success,
            failed,
            f"{sent / sample_interval:.3f}",
            f"{mean_lat:.3f}",
            f"{p95_lat:.3f}"
        ]
        if writer:
            writer.writerow(row)
            out_file.flush()

        next_sample += sample_interval

        # Check for clean termination:
        # Stop if scheduling is done, grace period elapsed or in_flight reached 0
        if stop_event.is_set():
            if in_flight == 0 or elapsed >= (duration + timeout):
                # Write final flush if any trailing results completed
                if tracker.interval_results or tracker.interval_sent:
                    now = time.monotonic()
                    elapsed = now - start_mono
                    sent, results, in_flight = tracker.flush_interval()
                    success = sum(1 for ok, _, _, _ in results if ok)
                    failed = len(results) - success
                    latencies = [lat for _, lat, _, _ in results]
                    mean_lat = statistics.mean(latencies) if latencies else 0.0
                    p95_lat = percentile(latencies, 0.95) if latencies else 0.0
                    sample_rate = target_rate_fn(min(elapsed, duration))
                    row = [
                        f"{time.time():.6f}",
                        f"{elapsed:.3f}",
                        f"{sample_rate:.3f}",
                        sent,
                        success,
                        failed,
                        f"{sent / sample_interval:.3f}",
                        f"{mean_lat:.3f}",
                        f"{p95_lat:.3f}"
                    ]
                    if writer:
                        writer.writerow(row)
                        out_file.flush()
                break

async def async_main():
    args = parse_arguments()
    adjust_file_descriptor_limit()

    rng = random.Random(args.seed)
    variable_state = [-1, 0.0]

    out_file = None
    writer = None
    if not args.discard_output:
        if not args.output:
            sys.exit("ERROR: --output is required unless --discard-output is used")
        out_file = open(args.output, "w", newline="")
        writer = csv.writer(out_file)
        writer.writerow([
            "timestamp_epoch", "elapsed_s", "target_rps", "sent", "success", "failed",
            "achieved_rps", "mean_latency_ms", "p95_latency_ms"
        ])

    tracker = SampleTracker()
    stop_event = asyncio.Event()

    def get_rate(elapsed_s):
        return target_rate(args, elapsed_s, rng, variable_state)

    # Concurrency control (unlimited by default)
    sem = asyncio.Semaphore(args.concurrency_limit) if args.concurrency_limit > 0 else None

    # aiohttp connector with unlimited connections
    connector = aiohttp.TCPConnector(
        limit=0,
        limit_per_host=0,
        force_close=args.disable_keepalive,
        enable_cleanup_closed=True
    )
    headers = {"User-Agent": args.user_agent}

    async with aiohttp.ClientSession(connector=connector) as session:
        # Start background sampler loop
        sampler = asyncio.create_task(
            sampler_loop(
                tracker, args.sample_interval, args.duration, args.timeout,
                get_rate, writer, out_file, stop_event
            )
        )

        start_mono = time.monotonic()
        next_send = start_mono
        active_tasks = set()

        # Open-Loop Dispatch Loop
        while True:
            now = time.monotonic()
            elapsed = now - start_mono
            if elapsed >= args.duration:
                break

            rate = get_rate(elapsed)
            if rate <= 0:
                await asyncio.sleep(min(0.05, args.duration - elapsed))
                now = time.monotonic()
                next_send = max(next_send, now)
                continue

            # Catch up on any scheduled dispatches due up to current time
            while next_send <= now and (now - start_mono) < args.duration:
                task = asyncio.create_task(
                    send_request(session, args.url, next_send, args.timeout, tracker, headers, sem)
                )
                active_tasks.add(task)
                task.add_done_callback(active_tasks.discard)

                next_send += (1.0 / rate)
                now = time.monotonic()

            sleep_dur = max(0.0, min(0.005, next_send - now))
            if sleep_dur > 0:
                await asyncio.sleep(sleep_dur)

        # Dispatch phase complete. Signal sampler and wait for active in-flight requests up to timeout grace period
        stop_event.set()
        grace_start = time.monotonic()
        while active_tasks and (time.monotonic() - grace_start) < (args.timeout + 0.5):
            await asyncio.sleep(0.05)

        # Cancel any lingering tasks that exceeded timeout
        for t in list(active_tasks):
            if not t.done():
                t.cancel()

        await sampler

    if out_file:
        out_file.close()

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
