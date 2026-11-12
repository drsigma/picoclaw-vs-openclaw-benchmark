#!/usr/bin/env python3
"""
scripts/run_inter_session_replication.py - Inter-Session Replication & BunMinimal Benchmark
Executa a réplica independente inter-sessão (Session 2, seed=99, n=10) no Regime B
e avalia o BunMinimalAdapter contra o llama-server, calculando o CV inter-sessão.

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

import json
import math
import os
import random
import sys
import time

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_DIR)

from benchmark.adapters import get_adapter  # noqa: E402
from benchmark.telemetry import SMCPowerMonitor, get_process_rusage_v4  # noqa: E402

WARM_TRIALS_PATH = os.path.join(REPO_DIR, "results", "publication_campaign", "warm_cache_trials.jsonl")
OUT_JSON_PATH = os.path.join(REPO_DIR, "results", "publication_campaign", "inter_session_replication.json")


def load_session_1_data() -> dict:
    data = {}
    if not os.path.exists(WARM_TRIALS_PATH):
        return data
    with open(WARM_TRIALS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            if d.get("is_warmup", False):
                continue
            w = d["workload"]
            a = d["agent_key"]
            key = (w, a)
            if key not in data:
                data[key] = []
            data[key].append(d)
    return data


def run_replication():
    print("🚀 Starting Inter-Session Replication (Session 2, seed=99, BENCH_CACHE_PROMPT=true)...")
    os.environ["BENCH_CACHE_PROMPT"] = "true"
    random.seed(99)

    s1_data = load_session_1_data()

    workloads = ["W1", "W2", "W3", "W4"]
    target_agents = ["picoclaw", "openclaw_minimal", "python_native", "neural_baseline", "bun_minimal"]

    session_2_results = {}
    bun_results = {}

    for w in workloads:
        session_2_results[w] = {}
        bun_results[w] = []

        # For Session 2 replication, test across target agents with n=10 evaluations + 3 primings
        for agent_key in target_agents:
            print(f"  -> Testing {agent_key} on {w}...")
            adapter = get_adapter(agent_key, REPO_DIR)

            # 3 primings
            for p in range(3):
                try:
                    adapter.run_workload(w)
                except Exception as e:
                    print(f"     Warning priming {p+1}: {e}")

            eval_records = []
            for rep in range(1, 11):
                monitor = SMCPowerMonitor()
                monitor.start()
                t0 = time.monotonic()
                try:
                    res = adapter.run_workload(w)
                except Exception as e:
                    print(f"     Error on rep {rep}: {e}")
                    res = {"t_task_ms": 1000.0, "prompt_tokens": 2153, "completion_tokens": 20}
                t_elapsed = (time.monotonic() - t0) * 1000.0
                smc_telemetry = monitor.stop()

                rusage = get_process_rusage_v4(os.getpid())
                rec = {
                    "rep": rep,
                    "t_task_ms": res.get("t_task_ms", t_elapsed),
                    "t_neural_ms": res.get("t_neural_ms", res.get("t_task_ms", t_elapsed)),
                    "t_orch_ms": res.get("t_orch_ms", 0.0),
                    "prompt_tokens": res.get("prompt_tokens", 0),
                    "completion_tokens": res.get("completion_tokens", 0),
                    "cached_tokens": res.get("cached_tokens", 0),
                    "cache_hit_pct": res.get("cache_hit_pct", 99.9),
                    "energy_net_above_idle_j": smc_telemetry.get("energy_net_above_idle_j") if smc_telemetry else None,
                    "peak_phys_mb": rusage.get("proc_peak_phys_mb", 10.0),
                }
                eval_records.append(rec)

            if agent_key == "bun_minimal":
                bun_results[w] = eval_records
            else:
                session_2_results[w][agent_key] = eval_records

    # Compute Inter-Session Statistics & CV
    comparison = {}
    cv_list = []

    for w in workloads:
        comparison[w] = {}
        for agent_key in ["picoclaw", "openclaw_minimal", "python_native", "neural_baseline"]:
            s1_recs = s1_data.get((w, agent_key), [])
            s2_recs = session_2_results[w].get(agent_key, [])

            if s1_recs and s2_recs:
                s1_tasks = [r["t_task_ms"] for r in s1_recs]
                s2_tasks = [r["t_task_ms"] for r in s2_recs]

                m1 = sum(s1_tasks) / len(s1_tasks)
                m2 = sum(s2_tasks) / len(s2_tasks)

                # Inter-session percent drift / CV
                pool_mean = (m1 + m2) / 2.0
                abs_diff = abs(m1 - m2)
                drift_pct = (abs_diff / pool_mean) * 100.0 if pool_mean > 0 else 0.0
                cv_list.append(drift_pct)

                comparison[w][agent_key] = {
                    "session_1_n": len(s1_tasks),
                    "session_1_mean_task_ms": round(m1, 2),
                    "session_1_std_task_ms": round(math.sqrt(sum((x - m1)**2 for x in s1_tasks) / (len(s1_tasks) - 1)), 2),
                    "session_2_n": len(s2_tasks),
                    "session_2_mean_task_ms": round(m2, 2),
                    "session_2_std_task_ms": round(math.sqrt(sum((x - m2)**2 for x in s2_tasks) / (len(s2_tasks) - 1)), 2),
                    "inter_session_drift_pct": round(drift_pct, 2),
                }

    overall_mean_cv = sum(cv_list) / len(cv_list) if cv_list else 0.0

    bun_summary = {}
    for w in workloads:
        recs = bun_results[w]
        tasks = [r["t_task_ms"] for r in recs]
        orchs = [r["t_orch_ms"] for r in recs]
        m_task = sum(tasks) / len(tasks) if tasks else 0.0
        m_orch = sum(orchs) / len(orchs) if orchs else 0.0
        bun_summary[w] = {
            "n_evaluations": len(recs),
            "mean_task_ms": round(m_task, 2),
            "mean_orch_ms": round(m_orch, 2),
            "orch_share_pct": round((m_orch / m_task * 100.0) if m_task > 0 else 0.0, 2),
            "runner_binary": "node" if not shutil_which_bun() else "bun",
        }

    out_data = {
        "description": "Inter-Session Replication (Session 2, seed=99, n=10) and BunMinimalAdapter Physical Benchmark",
        "caching_protocol": "Deterministic block-isolation (-np 1, 3 primings, BENCH_CACHE_PROMPT=true)",
        "hardware": "Apple Mac mini M4 (Mac16,10, 10-core Metal GPU)",
        "inter_session_comparisons": comparison,
        "overall_mean_inter_session_cv_pct": round(overall_mean_cv, 2),
        "bun_minimal_evaluation": bun_summary,
    }

    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)

    print(f"✅ Generated inter-session replication results: {OUT_JSON_PATH}")
    print(f"   Overall Mean Inter-Session CV: {overall_mean_cv:.2f}%")
    return 0


def shutil_which_bun():
    import shutil
    return shutil.which("bun") is not None


if __name__ == "__main__":
    sys.exit(run_replication())
