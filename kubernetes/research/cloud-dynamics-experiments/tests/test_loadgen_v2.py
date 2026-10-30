#!/usr/bin/env python3
"""
Unit test suite for loadgen_v2.py.
Validates open-loop rate dispatch, concurrency, true timeout enforcement, and CSV format.
Uses multiprocessing to ensure the mock server runs independently of test execution.
"""

import csv
import multiprocessing
import os
import subprocess
import sys
import time
from aiohttp import web

HOST = "127.0.0.1"
PORT = 18080
BASE_URL = f"http://{HOST}:{PORT}"

async def handle_fast(request):
    return web.Response(text="OK fast", status=200)

async def handle_slow(request):
    # 500ms server delay
    import asyncio
    await asyncio.sleep(0.5)
    return web.Response(text="OK slow", status=200)

async def handle_timeout(request):
    # 3.0s delay (exceeds 1.0s client timeout)
    import asyncio
    await asyncio.sleep(3.0)
    return web.Response(text="OK delayed", status=200)

async def handle_error(request):
    return web.Response(text="Internal Server Error", status=503)

def run_server():
    app = web.Application()
    app.router.add_get("/fast", handle_fast)
    app.router.add_get("/slow", handle_slow)
    app.router.add_get("/timeout", handle_timeout)
    app.router.add_get("/error", handle_error)
    web.run_app(app, host=HOST, port=PORT, access_log=None)

def run_loadgen(args):
    cmd = [sys.executable, "kubernetes/research/cloud-dynamics-experiments/loadgen/loadgen_v2.py"] + args
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - t0
    return res.returncode, res.stdout, res.stderr, duration

def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

def main():
    print("=== Starting Mock HTTP Server in Background Process ===")
    server_proc = multiprocessing.Process(target=run_server, daemon=True)
    server_proc.start()
    time.sleep(1.0)  # Wait for server to bind

    try:
        # TEST 1: Constant fast rate
        print("\n[TEST 1] Testing Constant Profile at 50 RPS (Fast Server)...")
        code, out, err, dur = run_loadgen([
            "--url", f"{BASE_URL}/fast",
            "--profile", "constant",
            "--duration", "3",
            "--rps", "50",
            "--timeout", "2",
            "--output", "/tmp/test_v2_constant.csv"
        ])
        assert code == 0, f"loadgen_v2 failed: {err}"
        rows = read_csv("/tmp/test_v2_constant.csv")
        total_sent = sum(int(r["sent"]) for r in rows)
        total_succ = sum(int(r["success"]) for r in rows)
        total_fail = sum(int(r["failed"]) for r in rows)
        print(f"  Result: Sent={total_sent}, Success={total_succ}, Failed={total_fail}, Duration={dur:.2f}s")
        assert total_sent >= 140, f"Expected ~150 sent, got {total_sent}"
        assert total_succ >= 140, f"Expected ~150 success, got {total_succ}"
        assert total_fail == 0, f"Expected 0 failed, got {total_fail}"
        print("  -> TEST 1 PASSED: Fast response handled with 100% success.")

        # TEST 2: Ramp profile
        print("\n[TEST 2] Testing Ramp Profile (10 to 50 RPS)...")
        code, out, err, dur = run_loadgen([
            "--url", f"{BASE_URL}/fast",
            "--profile", "ramp",
            "--duration", "4",
            "--start-rps", "10",
            "--end-rps", "50",
            "--timeout", "2",
            "--output", "/tmp/test_v2_ramp.csv"
        ])
        assert code == 0, f"loadgen_v2 failed: {err}"
        rows = read_csv("/tmp/test_v2_ramp.csv")
        rates = [float(r["target_rps"]) for r in rows]
        print(f"  Target RPS progression: {rates}")
        assert rates[-1] > rates[0], "Target RPS should increase during ramp"
        print("  -> TEST 2 PASSED: Ramp target RPS calculated properly.")

        # TEST 3: Slow Server (500ms delay) - High Concurrency Verification
        print("\n[TEST 3] Testing Slow Server with 500ms Delay at 50 RPS (Little's Law L ~ 25)...")
        code, out, err, dur = run_loadgen([
            "--url", f"{BASE_URL}/slow",
            "--profile", "constant",
            "--duration", "3",
            "--rps", "50",
            "--timeout", "2",
            "--output", "/tmp/test_v2_slow.csv"
        ])
        assert code == 0, f"loadgen_v2 failed: {err}"
        rows = read_csv("/tmp/test_v2_slow.csv")
        latencies = [float(r["mean_latency_ms"]) for r in rows if float(r["mean_latency_ms"]) > 0]
        mean_lat = sum(latencies) / len(latencies) if latencies else 0
        total_succ = sum(int(r["success"]) for r in rows)
        print(f"  Result: Success={total_succ}, Mean Latency={mean_lat:.1f}ms (expected ~500ms)")
        assert 450 <= mean_lat <= 650, f"Expected latency around 500ms, got {mean_lat}"
        print("  -> TEST 3 PASSED: In-flight concurrency handled without client blocking.")

        # TEST 4: Strict Timeout Enforcement (Server 3.0s delay, Client timeout 1.0s)
        print("\n[TEST 4] Testing Strict Timeout Enforcement (Server Delay 3s, Timeout 1s)...")
        code, out, err, dur = run_loadgen([
            "--url", f"{BASE_URL}/timeout",
            "--profile", "constant",
            "--duration", "3",
            "--rps", "30",
            "--timeout", "1.0",
            "--output", "/tmp/test_v2_timeout.csv"
        ])
        assert code == 0, f"loadgen_v2 failed: {err}"
        rows = read_csv("/tmp/test_v2_timeout.csv")
        total_sent = sum(int(r["sent"]) for r in rows)
        total_succ = sum(int(r["success"]) for r in rows)
        total_fail = sum(int(r["failed"]) for r in rows)
        print(f"  Result: Sent={total_sent}, Success={total_succ}, Failed={total_fail}, Duration={dur:.2f}s")
        assert total_fail >= 80, f"Expected all ~90 requests to fail due to timeout, got failed={total_fail}"
        assert total_succ == 0, f"Expected 0 success, got {total_succ}"
        assert dur < 5.0, f"Test duration should be bounded (< 5s), got {dur:.2f}s"
        print("  -> TEST 4 PASSED: Requests exceeding timeout are immediately recorded as FAILED.")

        # TEST 5: CSV Format Compatibility with collect.py
        print("\n[TEST 5] Checking CSV Header & Column Schema Compatibility...")
        expected_cols = [
            "timestamp_epoch", "elapsed_s", "target_rps", "sent", "success", "failed",
            "achieved_rps", "mean_latency_ms", "p95_latency_ms"
        ]
        assert list(rows[0].keys()) == expected_cols, f"Mismatch in CSV columns: {list(rows[0].keys())}"
        print(f"  CSV Columns: {list(rows[0].keys())}")
        print("  -> TEST 5 PASSED: CSV schema is 100% compatible with collect.py.")

        print("\n=======================================================")
        print("ALL 5 UNIT TESTS PASSED FOR loadgen_v2.py!")
        print("=======================================================")

    finally:
        server_proc.terminate()
        server_proc.join()

if __name__ == "__main__":
    main()
