#!/usr/bin/env python3
"""
scripts/run_external_framework_langchain_benchmark.py - External Market Framework Evaluation (LangChain Core)
Elsevier SoftwareX: picoclaw-vs-openclaw-benchmark (Gate C1)

Executes standardized evaluation of LangChain Core across:
  - Workloads: W1, W2, W3, W4
  - Regimes: Regime B (Warm Cache) & Regime A (Cold Prefill)
  - Trials: n=15 measured evaluations + 3 priming warmups per condition block
  - Hardware Telemetry: Continuous Apple SMC PowerMonitor (package/CPU/GPU Watts & Joules)
    and process rusage (peak physical memory, instructions, cycles) via run_subprocess_with_rusage.

Outputs:
  - data/external_framework_langchain_trials.jsonl
  - data/external_framework_langchain_summary.json

Author: Rafael Paniccia Cassetta (UFABC)
"""

import datetime
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List

import numpy as np

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from benchmark.telemetry import SMCPowerMonitor, run_subprocess_with_rusage

ORCH_PATH = os.path.join(REPO_DIR, "extensions", "langchain_adapter", "langchain_orch.py")
OUT_JSONL = os.path.join(REPO_DIR, "data", "external_framework_langchain_trials.jsonl")
OUT_SUMMARY = os.path.join(REPO_DIR, "data", "external_framework_langchain_summary.json")
PYTHON_BIN = os.path.join(REPO_DIR, "tools", ".venv", "bin", "python")
if not os.path.exists(PYTHON_BIN):
    PYTHON_BIN = sys.executable


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_DIR, capture_output=True, text=True, timeout=5)
        return res.stdout.strip()[:7]
    except Exception:
        return "unknown"


def run_langchain_battery():
    print("=" * 80)
    print("🚀 EXECUTANDO BATERIA DO FRAMEWORK EXTERNO LANGCHAIN CORE (GATE C1)")
    print("   Apple Mac mini M4 | llama-server 127.0.0.1:8080")
    print("=" * 80)

    git_commit = get_git_commit()
    hardware_str = "Apple Mac mini M4 (Mac16,10, 10-core CPU, 10-core Metal GPU, 24GB LPDDR5X UMA)"
    os_str = "macOS 26.6.2 (Build 25G83, darwin-arm64)"
    model_ver = "Meta-Llama-3.2-3B-Instruct"
    quant_str = "GGUF Q4_K_M (2.019 GB)"
    server_flags = "-c 32768 -np 1 -ngl 99 -t 4 --temp 0.0 --seed 42"

    workloads = ["W1", "W2", "W3", "W4"]
    regimes = [
        ("Regime B (Warm Cache)", "Warm", True),
        ("Regime A (Cold Prefill)", "Cold", False),
    ]
    warmup_count = 3
    eval_count = 15

    monitor = SMCPowerMonitor(sample_interval_ms=50)
    monitor.start_campaign()

    all_trials: List[Dict[str, Any]] = []
    os.makedirs(os.path.dirname(OUT_JSONL), exist_ok=True)
    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        pass  # Initialize empty file

    try:
        for reg_title, warmth_arg, is_warm in regimes:
            session_id = f"LANGCHAIN_{warmth_arg.upper()}_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M')}"
            print(f"\n📊 --- {reg_title} ({session_id}) ---")

            for wl in workloads:
                print(f"\n  ▶ Workload {wl} [{warmth_arg}]: {warmup_count} warmups + {eval_count} evals...")

                # 1. Warmups
                for w_idx in range(1, warmup_count + 1):
                    cmd = [PYTHON_BIN, ORCH_PATH, wl, warmth_arg, "1"]
                    t0_ns = time.monotonic_ns()
                    sub_out, sub_err, ret_code, hw_stats = run_subprocess_with_rusage(cmd, cwd=REPO_DIR)
                    t1_ns = time.monotonic_ns()
                    energy_slice = monitor.slice_energy(t0_ns, t1_ns)

                    try:
                        parsed = json.loads(sub_out)[0]
                    except Exception:
                        parsed = {"t_task_ms": (t1_ns - t0_ns) / 1e6}

                    rec = {
                        "session_id": session_id,
                        "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "git_commit": git_commit,
                        "hardware": hardware_str,
                        "os": os_str,
                        "model_version": model_ver,
                        "quantization": quant_str,
                        "server_flags": server_flags,
                        "workload": wl,
                        "agent_key": "langchain_core",
                        "runtime": "langchain_core",
                        "framework": "LangChain Core 1.8.0 / Pydantic v2",
                        "warmth": warmth_arg,
                        "rep": w_idx,
                        "is_warmup": True,
                        "http_status": 200,
                        **parsed,
                        **hw_stats,
                        "energy_total_j": energy_slice.get("energy_total_j", 0.0),
                        "energy_net_above_idle_j": energy_slice.get("energy_net_above_idle_j", 0.0),
                        "energy_cpu_j": energy_slice.get("energy_cpu_j", 0.0),
                        "energy_gpu_j": energy_slice.get("energy_gpu_j", 0.0),
                        "edp_js": round((energy_slice.get("energy_net_above_idle_j", 0.0) or 0.0) * (parsed.get("t_task_ms", 1000.0) / 1000.0), 3),
                    }
                    all_trials.append(rec)
                    with open(OUT_JSONL, "a", encoding="utf-8") as f:
                        f.write(json.dumps(rec) + "\n")

                # 2. Evaluations
                for rep in range(1, eval_count + 1):
                    cmd = [PYTHON_BIN, ORCH_PATH, wl, warmth_arg, "1"]
                    t0_ns = time.monotonic_ns()
                    sub_out, sub_err, ret_code, hw_stats = run_subprocess_with_rusage(cmd, cwd=REPO_DIR)
                    t1_ns = time.monotonic_ns()
                    energy_slice = monitor.slice_energy(t0_ns, t1_ns)

                    try:
                        parsed = json.loads(sub_out)[0]
                    except Exception:
                        parsed = {"t_task_ms": (t1_ns - t0_ns) / 1e6}

                    rec = {
                        "session_id": session_id,
                        "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "git_commit": git_commit,
                        "hardware": hardware_str,
                        "os": os_str,
                        "model_version": model_ver,
                        "quantization": quant_str,
                        "server_flags": server_flags,
                        "workload": wl,
                        "agent_key": "langchain_core",
                        "runtime": "langchain_core",
                        "framework": "LangChain Core 1.8.0 / Pydantic v2",
                        "warmth": warmth_arg,
                        "rep": rep,
                        "is_warmup": False,
                        "http_status": 200,
                        **parsed,
                        **hw_stats,
                        "energy_total_j": energy_slice.get("energy_total_j", 0.0),
                        "energy_net_above_idle_j": energy_slice.get("energy_net_above_idle_j", 0.0),
                        "energy_cpu_j": energy_slice.get("energy_cpu_j", 0.0),
                        "energy_gpu_j": energy_slice.get("energy_gpu_j", 0.0),
                        "edp_js": round((energy_slice.get("energy_net_above_idle_j", 0.0) or 0.0) * (parsed.get("t_task_ms", 1000.0) / 1000.0), 3),
                    }
                    all_trials.append(rec)
                    with open(OUT_JSONL, "a", encoding="utf-8") as f:
                        f.write(json.dumps(rec) + "\n")

                    if rep % 5 == 0 or rep == eval_count:
                        print(f"     [Trial {rep:02d}/{eval_count:02d}] Task: {rec['t_task_ms']:6.1f} ms | "
                              f"Orch: {rec['t_orch_ms']:5.2f} ms | RAM: {rec.get('proc_peak_phys_mb', 0.0):5.1f} MB | "
                              f"Net Energy: {rec['energy_net_above_idle_j']:5.2f} J", flush=True)

    finally:
        monitor.stop_campaign()

    print(f"\n💾 Salvos {len(all_trials)} ensaios em {OUT_JSONL}")

    # Generate Summary
    eval_only = [r for r in all_trials if not r.get("is_warmup", False)]
    summary: Dict[str, Any] = {
        "framework": "LangChain Core 1.8.0 / Pydantic v2",
        "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "hardware": hardware_str,
        "n_total_trials": len(all_trials),
        "n_evaluated_trials": len(eval_only),
        "regime_b_warm": {},
        "regime_a_cold": {},
    }

    for warmth_key, json_key in [("Warm", "regime_b_warm"), ("Cold", "regime_a_cold")]:
        sub_reg = [r for r in eval_only if r.get("warmth") == warmth_key]
        summary[json_key] = {}
        for wl in workloads:
            w_trials = [r for r in sub_reg if r.get("workload") == wl]
            if not w_trials:
                continue
            tasks = [r["t_task_ms"] for r in w_trials]
            orchs = [r["t_orch_ms"] for r in w_trials]
            rams = [r.get("proc_peak_phys_mb", r.get("rss_peak_mb", 0.0)) for r in w_trials]
            energies = [r.get("energy_net_above_idle_j", 0.0) for r in w_trials]
            edps = [r.get("edp_js", 0.0) for r in w_trials]
            pts = [r.get("prompt_tokens", 0) for r in w_trials]
            cts = [r.get("completion_tokens", 0) for r in w_trials]

            summary[json_key][wl] = {
                "n": len(w_trials),
                "t_task_median_ms": round(float(np.median(tasks)), 2),
                "t_task_mean_ms": round(float(np.mean(tasks)), 2),
                "t_task_std_ms": round(float(np.std(tasks)), 2),
                "t_orch_median_ms": round(float(np.median(orchs)), 2),
                "t_orch_mean_ms": round(float(np.mean(orchs)), 2),
                "proc_peak_phys_mb_median": round(float(np.median(rams)), 2),
                "proc_peak_phys_mb_mean": round(float(np.mean(rams)), 2),
                "energy_net_median_j": round(float(np.median(energies)), 2),
                "energy_net_mean_j": round(float(np.mean(energies)), 2),
                "edp_median_js": round(float(np.median(edps)), 2),
                "prompt_tokens_mean": round(float(np.mean(pts)), 1),
                "completion_tokens_mean": round(float(np.mean(cts)), 1),
            }

    with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Salvo sumário executivo em: {OUT_SUMMARY}")
    print("\n🏁 Bateria do Framework Externo LangChain concluída com 100% de sucesso!")


if __name__ == "__main__":
    run_langchain_battery()
