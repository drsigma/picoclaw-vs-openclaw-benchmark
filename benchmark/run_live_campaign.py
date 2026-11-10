#!/usr/bin/env python3
"""
Live Physical Benchmark Campaign Runner
Executes 100% real, physical trials against llama-server (Metal GPU on port 8080)
and the native Go and Node.js agent orchestrator binaries.
Records live timestamps, memory footprints, and raw outputs for reproducibility.
"""
import ctypes
import json
import math
import os
import subprocess
import sys
import time
import numpy as np
from scipy import stats

REPO_DIR = "/Users/rafael/.gemini/antigravity/scratch/picoclaw-vs-openclaw-benchmark"
BENCH_DIR = os.path.join(REPO_DIR, "benchmark")
NODE_BIN = "/Users/rafael/.gemini/antigravity/scratch/picoclaw_vs_openclaw/tools/node-v26.12.1-darwin-arm64/bin/node"
PICOCLAW_BIN = os.path.join(BENCH_DIR, "picoclaw_orch")
OPENCLAW_SCRIPT = os.path.join(BENCH_DIR, "openclaw_orch.mjs")
BASE_DATA_DIR = "/Users/rafael/.gemini/antigravity/scratch/picoclaw_vs_openclaw/workload_data"

# Darwin libproc bindings for exact kernel RSS and physical footprint
libproc = ctypes.CDLL("/usr/lib/libproc.dylib")


class rusage_info_v4(ctypes.Structure):
    _fields_ = [
        ("ri_uuid", ctypes.c_uint8 * 16),
        ("ri_user_time", ctypes.c_uint64),
        ("ri_system_time", ctypes.c_uint64),
        ("ri_pkg_idle_wkups", ctypes.c_uint64),
        ("ri_interrupt_wkups", ctypes.c_uint64),
        ("ri_pageins", ctypes.c_uint64),
        ("ri_wired_size", ctypes.c_uint64),
        ("ri_resident_size", ctypes.c_uint64),
        ("ri_phys_footprint", ctypes.c_uint64),
        ("ri_proc_start_abstime", ctypes.c_uint64),
        ("ri_proc_exit_abstime", ctypes.c_uint64),
        ("ri_child_user_time", ctypes.c_uint64),
        ("ri_child_system_time", ctypes.c_uint64),
        ("ri_child_pkg_idle_wkups", ctypes.c_uint64),
        ("ri_child_interrupt_wkups", ctypes.c_uint64),
        ("ri_child_pageins", ctypes.c_uint64),
        ("ri_child_elapsed_abstime", ctypes.c_uint64),
        ("ri_diskio_bytesread", ctypes.c_uint64),
        ("ri_diskio_byteswritten", ctypes.c_uint64),
        ("ri_cpu_time_qos_default", ctypes.c_uint64),
        ("ri_cpu_time_qos_maintenance", ctypes.c_uint64),
        ("ri_cpu_time_qos_background", ctypes.c_uint64),
        ("ri_cpu_time_qos_utility", ctypes.c_uint64),
        ("ri_cpu_time_qos_legacy", ctypes.c_uint64),
        ("ri_cpu_time_qos_user_initiated", ctypes.c_uint64),
        ("ri_cpu_time_qos_user_interactive", ctypes.c_uint64),
        ("ri_billed_system_time", ctypes.c_uint64),
        ("ri_serviced_system_time", ctypes.c_uint64),
        ("ri_logical_writes", ctypes.c_uint64),
        ("ri_lifetime_max_phys_footprint", ctypes.c_uint64),
        ("ri_instructions", ctypes.c_uint64),
        ("ri_cycles", ctypes.c_uint64),
        ("ri_billed_energy", ctypes.c_uint64),
        ("ri_serviced_energy", ctypes.c_uint64),
        ("ri_interval_max_phys_footprint", ctypes.c_uint64),
        ("ri_runnable_time", ctypes.c_uint64),
    ]


def get_pid_rusage(pid):
    info = rusage_info_v4()
    if libproc.proc_pid_rusage(pid, 4, ctypes.byref(info)) == 0:
        return {
            "rss_mb": round(info.ri_resident_size / (1024 * 1024), 2),
            "phys_mb": round(info.ri_phys_footprint / (1024 * 1024), 2),
            "instructions": info.ri_instructions,
            "cycles": info.ri_cycles,
        }
    return None


def run_live_subprocess(cmd_args):
    t_start = time.perf_counter_ns()
    p = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = p.communicate()
    t_end = time.perf_counter_ns()
    wall_ms = (t_end - t_start) / 1e6
    if p.returncode != 0:
        raise RuntimeError(f"Command failed (exit {p.returncode}): {stderr}")
    try:
        data = json.loads(stdout.strip())
        return data, wall_ms
    except Exception as e:
        raise RuntimeError(f"Failed to parse JSON output: {stdout[:200]} - error: {e}")


def execute_campaign(campaign_name, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    raw_log_path = os.path.join(target_dir, "raw_trials.jsonl")
    summary_path = os.path.join(target_dir, f"summary_{campaign_name}.json")
    print(f"\n========================================================================")
    print(f" STARTING 100% REAL PHYSICAL BENCHMARK CAMPAIGN: {campaign_name}")
    print(f" Target Directory: {target_dir}")
    print(f"========================================================================")

    trials_log = open(raw_log_path, "w", buffering=1)
    results_by_treatment = {}

    # Define test matrix: Workloads W1, W2, W3, W4 under Cold and Warm
    # Repetitions: W1 (n=5), W2 (n=5), W3 (n=3), W4 (n=2) - 100% real physical executions on GPU!
    workload_plan = [
        ("W1", "Cold", 5),
        ("W1", "Warm", 5),
        ("W2", "Cold", 5),
        ("W2", "Warm", 5),
        ("W3", "Cold", 3),
        ("W3", "Warm", 3),
        ("W4", "Cold", 2),
        ("W4", "Warm", 2),
    ]

    for tier, warmth, reps in workload_plan:
        print(f"\n---> Executing Workload {tier} ({warmth} Start, {reps} live physical repetitions)...")

        # 1. PicoClaw (Go native binary)
        pico_cmd = [PICOCLAW_BIN, tier, warmth, str(reps)]
        print(f"  [PicoClaw Go] Running live: {' '.join(pico_cmd)}...")
        pico_out, pico_wall_ms = run_live_subprocess(pico_cmd)
        for i, item in enumerate(pico_out):
            trial_record = {
                "campaign": campaign_name,
                "timestamp_ns": time.time_ns(),
                "iteration": i + 1,
                **item,
            }
            trials_log.write(json.dumps(trial_record) + "\n")
            print(f"    Trial {i+1}/{reps}: T_task={item['t_task_ms']:.1f}ms | T_neural={item['t_neural_ms']:.1f}ms | T_orch={item['t_orch_ms']:.2f}ms | TTFT={item['ttft_ms']:.1f}ms | RAM={item['rss_peak_mb']:.1f}MB")

        key_pico = f"PicoClaw_{tier}_{warmth}"
        results_by_treatment[key_pico] = {
            "n": len(pico_out),
            "t_task_ms_mean": float(np.mean([x["t_task_ms"] for x in pico_out])),
            "t_orch_ms_mean": float(np.mean([x["t_orch_ms"] for x in pico_out])),
            "phi_orch_pct_mean": float(np.mean([x["phi_orch_pct"] for x in pico_out])),
            "ttft_ms_mean": float(np.mean([x["ttft_ms"] for x in pico_out])),
            "itl_ms_mean": float(np.mean([x["itl_ms"] for x in pico_out])),
            "rss_peak_mb_mean": float(np.mean([x["rss_peak_mb"] for x in pico_out])),
            "r_tool_ops_sec_mean": float(np.mean([x["r_tool_ops_sec"] for x in pico_out])),
            "trials": pico_out,
        }

        # 2. OpenClaw (Node.js/TypeScript)
        open_cmd = [NODE_BIN, OPENCLAW_SCRIPT, tier, warmth, str(reps)]
        print(f"  [OpenClaw Node.js] Running live: {' '.join(open_cmd)}...")
        open_out, open_wall_ms = run_live_subprocess(open_cmd)
        for i, item in enumerate(open_out):
            trial_record = {
                "campaign": campaign_name,
                "timestamp_ns": time.time_ns(),
                "iteration": i + 1,
                **item,
            }
            trials_log.write(json.dumps(trial_record) + "\n")
            print(f"    Trial {i+1}/{reps}: T_task={item['t_task_ms']:.1f}ms | T_neural={item['t_neural_ms']:.1f}ms | T_orch={item['t_orch_ms']:.2f}ms | TTFT={item['ttft_ms']:.1f}ms | RAM={item['rss_peak_mb']:.1f}MB")

        key_open = f"OpenClaw_{tier}_{warmth}"
        results_by_treatment[key_open] = {
            "n": len(open_out),
            "t_task_ms_mean": float(np.mean([x["t_task_ms"] for x in open_out])),
            "t_orch_ms_mean": float(np.mean([x["t_orch_ms"] for x in open_out])),
            "phi_orch_pct_mean": float(np.mean([x["phi_orch_pct"] for x in open_out])),
            "ttft_ms_mean": float(np.mean([x["ttft_ms"] for x in open_out])),
            "itl_ms_mean": float(np.mean([x["itl_ms"] for x in open_out])),
            "rss_peak_mb_mean": float(np.mean([x["rss_peak_mb"] for x in open_out])),
            "r_tool_ops_sec_mean": float(np.mean([x["r_tool_ops_sec"] for x in open_out])),
            "trials": open_out,
        }

    # High-Assertiveness Live Poisson Tool Calling Campaign (n=100 tool iterations)
    print("\n---> Running Live High-Assertiveness Poisson Tool Dispatches (100 physical iterations per agent)...")
    pico_tool_cmd = [PICOCLAW_BIN, "W2", "Warm", "100"]
    open_tool_cmd = [NODE_BIN, OPENCLAW_SCRIPT, "W2", "Warm", "100"]

    t0_pico = time.perf_counter_ns()
    pico_tool_out, _ = run_live_subprocess(pico_tool_cmd)
    t1_pico = time.perf_counter_ns()
    pico_total_sec = (t1_pico - t0_pico) / 1e9

    t0_open = time.perf_counter_ns()
    open_tool_out, _ = run_live_subprocess(open_tool_cmd)
    t1_open = time.perf_counter_ns()
    open_total_sec = (t1_open - t0_open) / 1e9

    # W2 has 3 tool calls per run: 100 runs = 300 tool invocations!
    pico_k = 300
    open_k = 300
    # Effective dispatch times
    pico_dispatch_sec = sum(x["t_dispatch_ms"] for x in pico_tool_out) / 1000.0
    open_dispatch_sec = sum(x["t_dispatch_ms"] for x in open_tool_out) / 1000.0

    pico_rate = pico_k / pico_dispatch_sec if pico_dispatch_sec > 0 else 0.0
    open_rate = open_k / open_dispatch_sec if open_dispatch_sec > 0 else 0.0

    # Garwood 90% Exact CI for Poisson rate
    def garwood(k, t_sec, conf=0.90):
        a = 1.0 - conf
        low = 0.5 * stats.chi2.ppf(a / 2.0, 2 * k) / t_sec
        high = 0.5 * stats.chi2.ppf(1.0 - a / 2.0, 2 * (k + 1)) / t_sec
        r = k / t_sec
        hw = (high - low) / 2.0
        rel_err = (hw / r) * 100.0
        return {
            "rate": round(r, 2),
            "ci_lower": round(low, 2),
            "ci_upper": round(high, 2),
            "relative_error_pct": round(rel_err, 2),
            "assertiveness_pct": round(100.0 - rel_err, 2),
        }

    poisson_eval = {
        "pico_w2_k300": garwood(pico_k, pico_dispatch_sec, 0.90),
        "open_w2_k300": garwood(open_k, open_dispatch_sec, 0.90),
        "rate_ratio_pico_over_open": round(pico_rate / open_rate, 2),
    }

    print(f"  PicoClaw Live Poisson Rate: {poisson_eval['pico_w2_k300']['rate']} ops/s (Assertiveness: {poisson_eval['pico_w2_k300']['assertiveness_pct']}%)")
    print(f"  OpenClaw Live Poisson Rate: {poisson_eval['open_w2_k300']['rate']} ops/s (Assertiveness: {poisson_eval['open_w2_k300']['assertiveness_pct']}%)")
    print(f"  Live Rate Ratio Advantage: {poisson_eval['rate_ratio_pico_over_open']}x")

    summary_data = {
        "campaign": campaign_name,
        "completed_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "hardware": "Apple Mac mini M4 (Mac16,10), 24 GB Unified Memory, 10-core GPU Metal",
        "neural_backend": "llama.cpp b11887 Metal GPU (127.0.0.1:8080)",
        "treatments": results_by_treatment,
        "live_poisson_evaluation": poisson_eval,
    }

    with open(summary_path, "w") as fp:
        json.dump(summary_data, fp, indent=2)

    trials_log.close()
    print(f"\n========================================================================")
    print(f" CAMPAIGN {campaign_name} SUCCESSFULLY COMPLETED!")
    print(f" Raw Trials: {raw_log_path}")
    print(f" Summary JSON: {summary_path}")
    print(f"========================================================================")
    return summary_data


if __name__ == "__main__":
    c_name = sys.argv[1] if len(sys.argv) > 1 else "campaign_run_2"
    t_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO_DIR, c_name)
    execute_campaign(c_name, t_dir)
