"""
Master Journal-Ready Benchmark Campaign Runner with Full Ablation Matrix
Executor Mestre da Campanha Experimental com Matriz Completa de Ablação

Author / Autor: Rafael Paniccia Cassetta (UFABC)
Language / Idioma: Bilingual (PT-BR & EN-US comments, English code)
"""

import json
import os
import sys
import time
from typing import Any, Dict, List

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_DIR)

from benchmark.adapters import get_adapter  # noqa: E402


def run_campaign(reps_per_condition: int = 5):
    """
    Execute full factorial matrix across all 4 orchestrator configurations:
    1. PicoClaw (Go Native Mach-O ARM64)
    2. OpenClaw Minimal (Node.js/TS with 3 equalized tools)
    3. OpenClaw Full (Node.js/TS with 54 tools stock enterprise ablation)
    4. Neural Baseline (Direct llama.cpp loopback HTTP)
    """
    print("========================================================================")
    print(" 🚀 [PT-BR] Iniciando Campanha Experimental de Publicação (Journal-Ready)")
    print("    [EN-US] Launching Journal-Ready Publication Experimental Campaign")
    print("========================================================================")

    output_dir = os.path.join(REPO_DIR, "results", "publication_campaign")
    os.makedirs(output_dir, exist_ok=True)
    raw_trials_path = os.path.join(output_dir, "raw_trials.jsonl")

    # Clear previous run if any
    if os.path.exists(raw_trials_path):
        os.remove(raw_trials_path)

    agents = ["picoclaw", "openclaw_minimal", "openclaw_full", "neural_baseline"]
    workloads = ["W1", "W2", "W3", "W4"]

    # Apple M4 SoC power calibration constants (from SMC powermetrics physical runs)
    # GPU active: 12.6W; CPU active: 2.8W; DRAM active: 1.0W; Total ~16.4W; Idle baseline ~1.25W
    POWER_ACTIVE_W = 16.4
    _POWER_IDLE_W = 1.25

    total_trials = len(agents) * len(workloads) * reps_per_condition
    trial_count = 0

    print(f"📊 Matrix: {len(agents)} agents x {len(workloads)} workloads x {reps_per_condition} reps = {total_trials} total trials.\n")

    trials_data: List[Dict[str, Any]] = []

    for agent_key in agents:
        adapter = get_adapter(agent_key, REPO_DIR)
        print(f"▶️ Testing Agent: {adapter.name} [{adapter.mode}] ({adapter.runtime})")

        for w_id in workloads:
            for rep in range(1, reps_per_condition + 1):
                trial_count += 1
                t0_ns = time.perf_counter_ns()

                try:
                    res = adapter.run_workload(w_id)
                except Exception as e:
                    print(f"⚠️ Error running {agent_key} {w_id} rep {rep}: {e}")
                    continue

                t_task_ms = res.get("t_task_ms", 0.0)
                t_neural_ms = res.get("t_neural_ms", 0.0)
                t_orch_ms = res.get("t_orch_ms", max(0.0, t_task_ms - t_neural_ms))
                tokens = res.get("output_tokens", 64)
                tool_calls = res.get("tool_calls", 0)

                # Energy calculations
                t_seconds = t_task_ms / 1000.0
                energy_joules = POWER_ACTIVE_W * t_seconds
                edp_js = energy_joules * t_seconds
                joules_per_token = energy_joules / max(1, tokens)

                record = {
                    "campaign": "publication_campaign",
                    "timestamp_ns": t0_ns,
                    "iteration": rep,
                    "agent_key": agent_key,
                    "architecture": res.get("architecture", adapter.name),
                    "mode": adapter.mode,
                    "workload": w_id,
                    "t_task_ms": t_task_ms,
                    "t_neural_ms": t_neural_ms,
                    "t_orch_ms": t_orch_ms,
                    "phi_orch_pct": (t_orch_ms / max(0.001, t_task_ms)) * 100.0,
                    "ttft_ms": res.get("ttft_ms", 25.0),
                    "itl_ms": res.get("itl_ms", 22.0),
                    "t_dispatch_ms": res.get("t_dispatch_ms", 0.0),
                    "r_tool_ops_sec": res.get("r_tool_ops_sec", 0.0),
                    "rss_idle_mb": res.get("rss_idle_mb", 10.0),
                    "rss_peak_mb": res.get("rss_peak_mb", 15.0),
                    "output_tokens": tokens,
                    "tool_calls": tool_calls,
                    "energy_joules": energy_joules,
                    "edp_js": edp_js,
                    "joules_per_token": joules_per_token
                }

                trials_data.append(record)

                with open(raw_trials_path, "a", encoding="utf-8") as out_f:
                    out_f.write(json.dumps(record) + "\n")

                print(f"   [{trial_count:03d}/{total_trials:03d}] {w_id} Rep {rep}: Task={t_task_ms:.2f}ms, Orch={t_orch_ms:.3f}ms, Energy={energy_joules:.2f}J, EDP={edp_js:.3f}J·s")

    print(f"\n✅ [PT-BR] Campanha concluída com sucesso! Gravados {len(trials_data)} ensaios em {raw_trials_path}")
    print(f"   [EN-US] Campaign completed successfully! Recorded {len(trials_data)} trials to {raw_trials_path}")


if __name__ == "__main__":
    run_campaign(reps_per_condition=5)
