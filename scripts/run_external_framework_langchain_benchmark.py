#!/usr/bin/env python3
"""
scripts/run_external_framework_langchain_benchmark.py - External Market Framework Evaluation (LangChain Core)
Empirical Systems Benchmarking: picoclaw-vs-openclaw-benchmark (Gate C1)

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

import argparse
import datetime
import json
import os
import platform
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
PUB_JSONL = os.path.join(REPO_DIR, "results", "publication_campaign", "external_framework_langchain_trials.jsonl")
PUB_SUMMARY = os.path.join(REPO_DIR, "results", "publication_campaign", "external_framework_langchain_summary.json")
PYTHON_BIN = os.path.join(REPO_DIR, "tools", ".venv", "bin", "python")
if not os.path.exists(PYTHON_BIN):
    PYTHON_BIN = sys.executable


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_DIR, capture_output=True, text=True, timeout=5)
        return res.stdout.strip()[:7]
    except Exception:
        return "unknown"


def run_langchain_battery(eval_count: int = 15, warmup_count: int = 3, out_jsonl: str = OUT_JSONL, out_summary: str = OUT_SUMMARY):
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

    monitor = SMCPowerMonitor(sample_interval_ms=50)
    monitor.start_campaign()

    all_trials: List[Dict[str, Any]] = []

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
                    energy_slice = monitor.slice_energy(t0_ns, t1_ns) or {}

                    if ret_code != 0:
                        raise RuntimeError(
                            f"LangChain warmup failed with exit code {ret_code} in {wl} ({warmth_arg}). "
                            f"stderr: {sub_err.strip()}"
                        )
                    if not sub_out or not sub_out.strip():
                        raise RuntimeError(f"LangChain warmup produced empty output in {wl} ({warmth_arg}).")

                    try:
                        parsed_raw = json.loads(sub_out)
                        parsed = parsed_raw[0] if isinstance(parsed_raw, list) and parsed_raw else parsed_raw
                    except Exception as e:
                        raise RuntimeError(f"Failed to parse LangChain output in {wl}: {e}\nRaw: {sub_out}")

                    http_status = parsed.get("http_status")
                    if http_status != 200:
                        raise RuntimeError(f"Invalid HTTP status {http_status} in LangChain warmup {wl}")

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
                        "http_status": http_status,
                        "subprocess_returncode": ret_code,
                        "subprocess_stderr": sub_err.strip()[:500] if sub_err else "",
                        **parsed,
                        **hw_stats,
                        "energy_total_j": energy_slice.get("energy_total_j"),
                        "energy_net_above_idle_j": energy_slice.get("energy_net_above_idle_j"),
                        "energy_cpu_j": energy_slice.get("energy_cpu_j"),
                        "energy_gpu_j": energy_slice.get("energy_gpu_j"),
                        "edp_js": round((energy_slice.get("energy_net_above_idle_j") or 0.0) * (parsed.get("t_task_ms", 1000.0) / 1000.0), 3) if energy_slice.get("energy_net_above_idle_j") is not None else None,
                    }
                    all_trials.append(rec)

                # 2. Evaluations
                for rep in range(1, eval_count + 1):
                    cmd = [PYTHON_BIN, ORCH_PATH, wl, warmth_arg, "1"]
                    t0_ns = time.monotonic_ns()
                    sub_out, sub_err, ret_code, hw_stats = run_subprocess_with_rusage(cmd, cwd=REPO_DIR)
                    t1_ns = time.monotonic_ns()
                    energy_slice = monitor.slice_energy(t0_ns, t1_ns) or {}

                    if ret_code != 0:
                        raise RuntimeError(
                            f"LangChain evaluation failed with exit code {ret_code} in {wl} ({warmth_arg}) rep {rep}. "
                            f"stderr: {sub_err.strip()}"
                        )
                    if not sub_out or not sub_out.strip():
                        raise RuntimeError(f"LangChain evaluation produced empty output in {wl} ({warmth_arg}) rep {rep}.")

                    try:
                        parsed_raw = json.loads(sub_out)
                        parsed = parsed_raw[0] if isinstance(parsed_raw, list) and parsed_raw else parsed_raw
                    except Exception as e:
                        raise RuntimeError(f"Failed to parse LangChain output in {wl} rep {rep}: {e}\nRaw: {sub_out}")

                    http_status = parsed.get("http_status")
                    if http_status != 200:
                        raise RuntimeError(f"Invalid HTTP status {http_status} in LangChain evaluation {wl} rep {rep}")

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
                        "http_status": http_status,
                        "subprocess_returncode": ret_code,
                        "subprocess_stderr": sub_err.strip()[:500] if sub_err else "",
                        **parsed,
                        **hw_stats,
                        "energy_total_j": energy_slice.get("energy_total_j"),
                        "energy_net_above_idle_j": energy_slice.get("energy_net_above_idle_j"),
                        "energy_cpu_j": energy_slice.get("energy_cpu_j"),
                        "energy_gpu_j": energy_slice.get("energy_gpu_j"),
                        "edp_js": round((energy_slice.get("energy_net_above_idle_j") or 0.0) * (parsed.get("t_task_ms", 1000.0) / 1000.0), 3) if energy_slice.get("energy_net_above_idle_j") is not None else None,
                    }
                    all_trials.append(rec)

                    if rep % 5 == 0 or rep == eval_count:
                        print(f"     [Trial {rep:02d}/{eval_count:02d}] Task: {rec['t_task_ms']:6.1f} ms | "
                              f"Orch: {rec['t_orch_ms']:5.2f} ms | RAM: {rec.get('proc_peak_phys_mb', 0.0):5.1f} MB | "
                              f"Net Energy: {rec['energy_net_above_idle_j']:5.2f} J", flush=True)

    finally:
        monitor.stop_campaign()

    if not all_trials:
        raise RuntimeError("Zero valid trials collected; refusing to write or accept empty JSONL dataset.")

    os.makedirs(os.path.dirname(out_jsonl), exist_ok=True)
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for r in all_trials:
            f.write(json.dumps(r) + "\n")

    print(f"\n💾 Salvos {len(all_trials)} ensaios em {out_jsonl}")

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

    with open(out_summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    if out_jsonl == OUT_JSONL:
        with open(PUB_SUMMARY, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        if os.path.exists(OUT_JSONL):
            import shutil
            shutil.copy2(OUT_JSONL, PUB_JSONL)
    print(f"✅ Salvo sumário executivo em: {out_summary}")
    print("\n🏁 Bateria do Framework Externo LangChain concluída com 100% de sucesso!")


def main():
    parser = argparse.ArgumentParser(description="External Framework LangChain Core Evaluation")
    parser.add_argument("--dry-run", action="store_true", help="Print execution plan and exit immediately with code 0")
    parser.add_argument("--smoke-test", action="store_true", help="Run 1 warmup + 1 evaluation per condition")
    parser.add_argument("--reps", type=int, default=15, help="Number of measured evaluations per condition (default: 15)")
    parser.add_argument("--output-jsonl", type=str, default=OUT_JSONL, help="Custom output JSONL path")
    parser.add_argument("--output-summary", type=str, default=OUT_SUMMARY, help="Custom output summary path")
    args = parser.parse_args()

    if args.dry_run:
        print("⚡ [DRY-RUN] Execution plan: External Framework LangChain Core Evaluation")
        print(f"⚡ [DRY-RUN] Target: Apple Mac mini M4 | llama-server 127.0.0.1:8080")
        print(f"⚡ [DRY-RUN] Workloads: W1, W2, W3, W4 | Regimes: Warm, Cold | Reps: {args.reps}")
        print(f"⚡ [DRY-RUN] Output JSONL: {args.output_jsonl}")
        print("⚡ [DRY-RUN] Plan verified successfully. Exiting code 0.")
        sys.exit(0)

    is_dry_or_help = any(arg in sys.argv for arg in ["--dry-run", "-h", "--help"])
    if platform.system() != "Darwin" and not is_dry_or_help:
        print(
            f"FATAL: Native platform mismatch! LangChain SMC benchmark requires macOS (Darwin) ARM64. "
            f"Detected: {platform.system()} {platform.machine()}",
            file=sys.stderr,
        )
        sys.exit(1)

    eval_count = 1 if args.smoke_test else args.reps
    warmup_count = 1 if args.smoke_test else 3
    run_langchain_battery(eval_count=eval_count, warmup_count=warmup_count, out_jsonl=args.output_jsonl, out_summary=args.output_summary)


if __name__ == "__main__":
    main()
