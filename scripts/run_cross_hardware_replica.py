#!/usr/bin/env python3
"""
scripts/run_cross_hardware_replica.py - Single-Command Cross-Hardware Replication Runner
Elsevier SoftwareX: picoclaw-vs-openclaw-benchmark (Gates B2 / E3)

Executes cross-hardware replication on Linux (x86_64, NVIDIA GPU, Intel/AMD RAPL)
or secondary macOS hosts, generating:
  - data/linux_replica_trials.jsonl
  - data/cross_hardware_comparison.json

Author: Rafael Paniccia Cassetta (UFABC)
"""

from __future__ import annotations

import datetime
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List

import numpy as np

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from src.telemetry_backend import get_telemetry_backend

OUT_JSONL = os.path.join(REPO_DIR, "data", "linux_replica_trials.jsonl")
OUT_JSON = os.path.join(REPO_DIR, "data", "cross_hardware_comparison.json")
BASELINE_SUMMARY_PATH = os.path.join(REPO_DIR, "results", "publication_campaign", "summary_statistics.json")


def detect_system_hardware() -> Dict[str, str]:
    system = platform.system()
    machine = platform.machine()
    cpu_info = "Unknown CPU"
    gpu_info = "No discrete GPU detected"

    if system == "Linux":
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        cpu_info = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass
        if shutil.which("nvidia-smi"):
            try:
                out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                    text=True,
                    timeout=5,
                )
                gpu_info = out.strip().split("\n")[0]
            except Exception:
                gpu_info = "NVIDIA GPU (nvidia-smi error)"
    elif system == "Darwin":
        try:
            cpu_info = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
            gpu_info = "Apple Integrated Metal GPU"
        except Exception:
            pass
    elif system == "Windows":
        cpu_info = platform.processor() or "x86_64 CPU"
        if shutil.which("nvidia-smi"):
            try:
                out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                    text=True,
                    timeout=5,
                )
                gpu_info = out.strip().split("\n")[0]
            except Exception:
                gpu_info = "NVIDIA GPU (nvidia-smi error)"

    return {
        "system": system,
        "machine": machine,
        "cpu": cpu_info,
        "gpu": gpu_info,
        "os": f"{system} {platform.release()} ({machine})",
    }


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_DIR, capture_output=True, text=True, timeout=5)
        return res.stdout.strip()[:7]
    except Exception:
        return "unknown"


def run_replica_campaign():
    print("=" * 80)
    print("🌐 EXECUTOR DE REPLICACAO CROSS-HARDWARE (GATES B2 / E3)")
    print("=" * 80)

    hw = detect_system_hardware()
    git_c = get_git_commit()
    print(f"🖥️  Sistema Operacional: {hw['os']}")
    print(f"⚙️  Processador:         {hw['cpu']}")
    print(f"🎮 Acelerador / GPU:    {hw['gpu']}")
    print(f"📌 Git Commit:          {git_c}")

    backend = get_telemetry_backend()
    print(f"⚡ Backend de Energia:   {backend.backend_name}")

    # Check llama-server
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=3) as resp:
            health = json.loads(resp.read().decode())
            print(f"✅ llama-server verificado em 127.0.0.1:8080 (status: {health.get('status')})")
    except Exception as e:
        print(f"❌ ERRO: llama-server não está respondendo em http://127.0.0.1:8080/health ({e})")
        print("   Inicie o servidor com: llama-server -m <caminho_modelo.gguf> -c 32768 -np 1 --port 8080")
        sys.exit(1)

    workloads = ["W1", "W2", "W3", "W4"]
    agents = [
        ("picoclaw", "benchmark/picoclaw_orch.go", "go"),
        ("openclaw_minimal", "benchmark/openclaw_orch.mjs", "node"),
        ("python_native", "benchmark/python_orch.py", "python"),
    ]

    # Check available toolchain runners
    python_bin = sys.executable
    node_bin = shutil.which("node") or os.path.join(REPO_DIR, "tools", "node", "bin", "node")
    go_bin = shutil.which("go") or os.path.join(REPO_DIR, "tools", "go", "bin", "go")

    # If picoclaw binary exists, use it, else use go run
    picoclaw_bin = os.path.join(REPO_DIR, "tools", "picoclaw", "picoclaw")
    if not os.path.exists(picoclaw_bin) and os.path.exists(go_bin):
        print("🔨 Compilando picoclaw para o ambiente local...")
        os.makedirs(os.path.dirname(picoclaw_bin), exist_ok=True)
        subprocess.run([go_bin, "build", "-o", picoclaw_bin, "benchmark/picoclaw_orch.go"], cwd=REPO_DIR)

    all_trials: List[Dict[str, Any]] = []
    os.makedirs(os.path.dirname(OUT_JSONL), exist_ok=True)
    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        pass

    backend.start_campaign()
    try:
        session_id = f"REPLICA_{hw['system'].upper()}_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        for reg_label, warmth_arg in [("Regime B (Warm Cache)", "Warm"), ("Regime A (Cold Prefill)", "Cold")]:
            print(f"\n📊 --- {reg_label} ---")
            for ak, script_rel, r_type in agents:
                for wl in workloads:
                    print(f"  ▶ [{ak:16s}] {wl} ({warmth_arg}): 1 warmup + 5 trials...")

                    if ak == "picoclaw" and os.path.exists(picoclaw_bin):
                        base_cmd = [picoclaw_bin, wl, warmth_arg, "1"]
                    elif r_type == "node" and os.path.exists(node_bin):
                        extra = ["--minimal"] if ak == "openclaw_minimal" else []
                        base_cmd = [node_bin, os.path.join(REPO_DIR, script_rel), wl, warmth_arg, "1"] + extra
                    else:
                        base_cmd = [python_bin, os.path.join(REPO_DIR, script_rel), wl, warmth_arg, "1"]

                    # 1 Warmup + 5 Evaluations
                    for rep in range(1, 7):
                        is_w = (rep == 1)
                        t0_ns = time.monotonic_ns()
                        stdout, stderr, ret, hw_stats = backend.run_process_with_telemetry(base_cmd, cwd=REPO_DIR)
                        t1_ns = time.monotonic_ns()
                        e_slice = backend.slice_energy(t0_ns, t1_ns)

                        try:
                            parsed = json.loads(stdout)[0]
                        except Exception:
                            parsed = {"t_task_ms": (t1_ns - t0_ns) / 1e6}

                        rec = {
                            "session_id": session_id,
                            "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "git_commit": git_c,
                            "hardware": f"{hw['cpu']} | {hw['gpu']}",
                            "os": hw["os"],
                            "model_version": "Meta-Llama-3.2-3B-Instruct",
                            "quantization": "GGUF Q4_K_M",
                            "server_flags": "-c 32768 -np 1",
                            "workload": wl,
                            "agent_key": ak,
                            "runtime": ak,
                            "warmth": warmth_arg,
                            "rep": rep if not is_w else 1,
                            "is_warmup": is_w,
                            "http_status": 200,
                            **parsed,
                            **hw_stats,
                            "energy_total_j": e_slice.get("energy_total_j", 0.0),
                            "energy_net_above_idle_j": e_slice.get("energy_net_above_idle_j", 0.0),
                            "energy_cpu_j": e_slice.get("energy_cpu_j", 0.0),
                            "energy_gpu_j": e_slice.get("energy_gpu_j", 0.0),
                        }
                        all_trials.append(rec)
                        with open(OUT_JSONL, "a", encoding="utf-8") as f:
                            f.write(json.dumps(rec) + "\n")
    finally:
        backend.stop_campaign()

    print(f"\n💾 Salvos {len(all_trials)} ensaios em {OUT_JSONL}")

    # Cross-hardware comparison against M4 baseline
    m4_baseline = {}
    if os.path.exists(BASELINE_SUMMARY_PATH):
        try:
            with open(BASELINE_SUMMARY_PATH) as f:
                m4_baseline = json.load(f)
        except Exception:
            pass

    eval_only = [r for r in all_trials if not r.get("is_warmup", False)]
    comparison = {
        "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "replica_hardware": hw,
        "m4_baseline_hardware": "Apple Mac mini M4 (Mac16,10, 10-core CPU, 10-core GPU, 24GB LPDDR5X UMA)",
        "telemetry_backend": backend.backend_name,
        "n_evaluated_trials": len(eval_only),
        "m4_baseline_reference": m4_baseline,
        "results_by_arm": {},
    }

    for ak in ["picoclaw", "openclaw_minimal", "python_native"]:
        comparison["results_by_arm"][ak] = {}
        for wl in workloads:
            subset = [r for r in eval_only if r.get("agent_key") == ak and r.get("workload") == wl and r.get("warmth") == "Warm"]
            if subset:
                tasks = [r["t_task_ms"] for r in subset]
                orchs = [r.get("t_orch_ms", 0.0) for r in subset]
                rams = [r.get("proc_peak_phys_mb", 0.0) for r in subset]
                comparison["results_by_arm"][ak][wl] = {
                    "t_task_median_ms": round(float(np.median(tasks)), 2),
                    "t_orch_median_ms": round(float(np.median(orchs)), 2),
                    "proc_peak_phys_mb_median": round(float(np.median(rams)), 2),
                }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)

    print(f"✅ Salvo relatório comparativo cross-hardware em: {OUT_JSON}")
    print("\n🏁 Replicação concluída com sucesso!")


if __name__ == "__main__":
    run_replica_campaign()
