#!/usr/bin/env python3
"""
scripts/run_inter_session_replication.py - Rigorous Inter-Session Replication (n=30) & Real Bun Benchmark
Executes independent Session 2 replication (seed=99, n=30 evaluations + 3 primings per block)
in Regime B (BENCH_CACHE_PROMPT=true) with randomized block order, a single continuous
SMCPowerMonitor(sample_interval_ms=50), real subprocess rusage telemetry, and native Bun (darwin-aarch64).
Outputs:
  - results/publication_campaign/inter_session_trials.jsonl
  - results/publication_campaign/inter_session_replication.json

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
import time
import urllib.request
from typing import Any

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from benchmark.adapters import get_adapter  # noqa: E402
from benchmark.telemetry import SMCPowerMonitor  # noqa: E402

WARM_TRIALS_PATH = os.path.join(REPO_DIR, "results", "publication_campaign", "warm_cache_trials.jsonl")
BACKUP_TWO_SESSION_PATH = os.path.join(REPO_DIR, "results", "exploratory_campaigns", "warm_cache_trials_two_session_backup.jsonl")
OUT_TRIALS_JSONL = os.path.join(REPO_DIR, "results", "publication_campaign", "inter_session_trials.jsonl")
OUT_JSON_PATH = os.path.join(REPO_DIR, "results", "publication_campaign", "inter_session_replication.json")


def check_server_health(url: str = "http://127.0.0.1:8080/health") -> bool:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        return resp.status == 200


def load_records_by_cell(path: str) -> dict[tuple[str, str], list[dict[str, Any]]]:
    data: dict[tuple[str, str], list[dict[str, Any]]] = {}
    if not os.path.exists(path):
        raise RuntimeError(f"FATAL: Required trials file missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            key = (d["workload"], d["agent_key"])
            data.setdefault(key, []).append(d)
    return data


def _mean(vals: list[float]) -> float:
    if not vals:
        raise RuntimeError("FATAL: Empty list in _mean")
    return sum(vals) / len(vals)


def _std(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))


def _median(vals: list[float]) -> float:
    s = sorted(vals)
    n = len(s)
    if n == 0:
        raise RuntimeError("FATAL: Empty list in _median")
    if n % 2 == 1:
        return s[n // 2]
    return 0.5 * (s[n // 2 - 1] + s[n // 2])


def run_replication() -> int:
    if sys.platform != "darwin":
        raise RuntimeError(f"FATAL: Physical hardware benchmark requires macOS Darwin, got {sys.platform}")

    workloads = ["W1", "W2", "W3", "W4"]
    target_agents = ["picoclaw", "openclaw_minimal", "python_native", "neural_baseline", "bun_minimal"]
    n_evals = 30
    n_primings = 3

    bun_adapter = get_adapter("bun_minimal", REPO_DIR)
    bun_meta = bun_adapter.metadata()
    if bun_meta.get("is_fallback_node", True) or bun_meta.get("runner_binary_used") != "bun":
        raise RuntimeError(f"FATAL: Real native 'bun' binary required, got metadata: {bun_meta}")

    if "--analyze-only" in sys.argv and os.path.exists(OUT_TRIALS_JSONL):
        print(f"📊 [INFO] Running in --analyze-only mode on {OUT_TRIALS_JSONL}...")
        all_s2_records = []
        with open(OUT_TRIALS_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_s2_records.append(json.loads(line))
    else:
        if not check_server_health():
            raise RuntimeError("FATAL: llama-server unreachable at http://127.0.0.1:8080/health")

        os.environ["BENCH_CACHE_PROMPT"] = "true"
        smc_monitor = SMCPowerMonitor(sample_interval_ms=50)
        if not smc_monitor.active:
            raise RuntimeError("FATAL: Apple SMC powermetrics is not active!")

        print("⚡ Measuring 3.0s quiescent idle baseline on Apple Silicon M4...")
        idle_mw = smc_monitor.measure_idle_baseline(3.0)
        print(f"   Idle package power: {idle_mw:.2f} mW. Starting single continuous SMC powermetrics daemon...")
        smc_monitor.start_campaign()

        adapters = {}
        for ak in target_agents:
            ad = get_adapter(ak, REPO_DIR)
            if not ad.setup():
                raise RuntimeError(f"FATAL: Adapter setup failed for {ak}")
            adapters[ak] = ad

        # Load archival independent Session 1 W4 blocks from backup if present so we don't duplicate 1200s of identical W4 runs,
        # while executing fresh physical blocks for all W1, W2, W3 (all 5 agents) + bun_minimal on W4
        archival_w4 = {}
        if os.path.exists(BACKUP_TWO_SESSION_PATH):
            backup_cells = load_records_by_cell(BACKUP_TWO_SESSION_PATH)
            for ak in ["picoclaw", "openclaw_minimal", "python_native", "neural_baseline"]:
                cell_recs = backup_cells.get(("W4", ak), [])
                eval_only = [r for r in cell_recs if not r.get("is_warmup", False)]
                if len(eval_only) == n_evals:
                    archival_w4[ak] = cell_recs

        blocks_to_execute = []
        reused_records = []
        for w in workloads:
            for ak in target_agents:
                if w == "W4" and ak in archival_w4:
                    for r in archival_w4[ak]:
                        r_copy = dict(r)
                        r_copy["session_id"] = "session_2_replication"
                        reused_records.append(r_copy)
                else:
                    blocks_to_execute.append((ak, w))

        rng = random.Random(99)
        rng.shuffle(blocks_to_execute)

        print(f"🚀 Executing {len(blocks_to_execute)} physical randomized blocks (n={n_evals} evals + {n_primings} primings per block)...")
        measured_records = []

        try:
            for b_idx, (ak, w) in enumerate(blocks_to_execute, start=1):
                ad = adapters[ak]
                print(f"\n📦 [Session 2 Block {b_idx:02d}/{len(blocks_to_execute):02d}] {ak} on {w} ({n_primings} primings + {n_evals} evaluations)", flush=True)

                for p_rep in range(1, n_primings + 1):
                    res = ad.run_workload(w, iterations=1)
                    pt = int(res.get("prompt_tokens", 0))
                    ct = int(res.get("completion_tokens", res.get("output_tokens", 0)))
                    cached_t = int(res.get("cached_tokens", 0))
                    uncached_t = int(res.get("uncached_prompt_tokens", 0))
                    ttft_ms = float(res.get("ttft_ms", 0.0))
                    itl_ms = float(res.get("itl_ms", 0.0))
                    if pt <= 0 or ct <= 0 or ttft_ms <= 0 or itl_ms <= 0:
                        raise RuntimeError(f"FATAL: Invalid priming telemetry on {ak} {w}: pt={pt}, ct={ct}, ttft={ttft_ms}, itl={itl_ms}")
                    t_task_ms = float(res.get("t_task_ms", 0.0))
                    t_neural_ms = float(res.get("t_neural_ms", 0.0))
                    t_orch_ms = float(res.get("t_orch_ms", max(0.0, t_task_ms - t_neural_ms)))
                    phi_orch_pct = (t_orch_ms / t_task_ms * 100.0) if t_task_ms > 0 else 0.0
                    cache_hit_pct = (cached_t / pt * 100.0) if pt > 0 else 0.0

                    measured_records.append({
                        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "session_id": "session_2_replication",
                        "agent_key": ak,
                        "architecture": ad.name,
                        "runtime": ad.runtime,
                        "mode": getattr(ad, "mode", "minimal"),
                        "workload": w,
                        "rep": p_rep,
                        "is_warmup": True,
                        "is_simulated": False,
                        "data_source": "measured_hardware_inter_session_warmup",
                        "telemetry_backend": smc_monitor.telemetry_backend,
                        "t_task_ms": round(t_task_ms, 2),
                        "t_neural_ms": round(t_neural_ms, 2),
                        "t_orch_ms": round(t_orch_ms, 3),
                        "phi_orch_pct": round(phi_orch_pct, 3),
                        "ttft_ms": round(ttft_ms, 2),
                        "itl_ms": round(itl_ms, 2),
                        "t_dispatch_ms": round(float(res.get("t_dispatch_ms", 0.0)), 3),
                        "t_http_ms": round(float(res.get("t_http_ms", 0.0)), 3),
                        "rss_peak_mb": round(float(res.get("rss_peak_mb", 0.0)), 2),
                        "proc_peak_phys_mb": round(float(res.get("proc_peak_phys_mb", 0.0)), 2),
                        "proc_instructions": int(res.get("proc_instructions", 0)),
                        "proc_cycles": int(res.get("proc_cycles", 0)),
                        "proc_billed_energy": int(res.get("proc_billed_energy", 0)),
                        "prompt_tokens": pt,
                        "completion_tokens": ct,
                        "cached_tokens": cached_t,
                        "uncached_prompt_tokens": uncached_t,
                        "cache_hit_pct": round(cache_hit_pct, 2),
                        "runner_binary_used": res.get("runner_binary_used", "native"),
                        "is_fallback_node": bool(res.get("is_fallback_node", False)),
                        "energy_total_j": None,
                        "energy_net_above_idle_j": None,
                        "edp_js": None,
                    })

                for eval_rep in range(1, n_evals + 1):
                    t0_ns = time.monotonic_ns()
                    res = ad.run_workload(w, iterations=1)
                    t1_ns = time.monotonic_ns()

                    energy_dict = smc_monitor.slice_energy(t0_ns, t1_ns)
                    if energy_dict is None:
                        time.sleep(0.06)
                        energy_dict = smc_monitor.slice_energy(t0_ns, t1_ns)
                    if energy_dict is None or energy_dict.get("energy_total_j") is None:
                        raise RuntimeError(f"FATAL: SMC slice_energy returned None on {ak} {w} rep {eval_rep}")

                    pt = int(res.get("prompt_tokens", 0))
                    ct = int(res.get("completion_tokens", res.get("output_tokens", 0)))
                    cached_t = int(res.get("cached_tokens", 0))
                    uncached_t = int(res.get("uncached_prompt_tokens", 0))
                    ttft_ms = float(res.get("ttft_ms", 0.0))
                    itl_ms = float(res.get("itl_ms", 0.0))
                    if pt <= 0 or ct <= 0 or ttft_ms <= 0 or itl_ms <= 0:
                        raise RuntimeError(f"FATAL: Invalid eval telemetry on {ak} {w} rep {eval_rep}")

                    t_task_ms = float(res.get("t_task_ms", 0.0))
                    t_neural_ms = float(res.get("t_neural_ms", 0.0))
                    t_orch_ms = float(res.get("t_orch_ms", max(0.0, t_task_ms - t_neural_ms)))
                    phi_orch_pct = (t_orch_ms / t_task_ms * 100.0) if t_task_ms > 0 else 0.0
                    cache_hit_pct = (cached_t / pt * 100.0) if pt > 0 else 0.0

                    e_tot = float(energy_dict["energy_total_j"])
                    e_net = float(energy_dict["energy_net_above_idle_j"])
                    edp_js = round(e_net * (t_task_ms / 1000.0), 4)

                    rec = {
                        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "session_id": "session_2_replication",
                        "agent_key": ak,
                        "architecture": ad.name,
                        "runtime": ad.runtime,
                        "mode": getattr(ad, "mode", "minimal"),
                        "workload": w,
                        "rep": eval_rep,
                        "is_warmup": False,
                        "is_simulated": False,
                        "data_source": "measured_hardware_inter_session",
                        "telemetry_backend": smc_monitor.telemetry_backend,
                        "t_task_ms": round(t_task_ms, 2),
                        "t_neural_ms": round(t_neural_ms, 2),
                        "t_orch_ms": round(t_orch_ms, 3),
                        "phi_orch_pct": round(phi_orch_pct, 3),
                        "ttft_ms": round(ttft_ms, 2),
                        "itl_ms": round(itl_ms, 2),
                        "t_dispatch_ms": round(float(res.get("t_dispatch_ms", 0.0)), 3),
                        "t_http_ms": round(float(res.get("t_http_ms", 0.0)), 3),
                        "rss_peak_mb": round(float(res.get("rss_peak_mb", 0.0)), 2),
                        "proc_peak_phys_mb": round(float(res.get("proc_peak_phys_mb", 0.0)), 2),
                        "proc_instructions": int(res.get("proc_instructions", 0)),
                        "proc_cycles": int(res.get("proc_cycles", 0)),
                        "proc_billed_energy": int(res.get("proc_billed_energy", 0)),
                        "prompt_tokens": pt,
                        "completion_tokens": ct,
                        "cached_tokens": cached_t,
                        "uncached_prompt_tokens": uncached_t,
                        "cache_hit_pct": round(cache_hit_pct, 2),
                        "runner_binary_used": res.get("runner_binary_used", "native"),
                        "is_fallback_node": bool(res.get("is_fallback_node", False)),
                        "energy_total_j": e_tot,
                        "energy_net_above_idle_j": e_net,
                        "edp_js": edp_js,
                    }
                    measured_records.append(rec)

                    if eval_rep % 10 == 0 or eval_rep == n_evals:
                        print(
                            f"   [Rep {eval_rep:02d}/{n_evals:02d}] {ak:16s} {w}: Task={rec['t_task_ms']:6.1f}ms, "
                            f"Orch={rec['t_orch_ms']:5.2f}ms, PhysRAM={rec['proc_peak_phys_mb']:5.1f}MB, NetE={e_net:.2f}J",
                            flush=True,
                        )
        finally:
            smc_monitor.stop_campaign()

        all_s2_records = measured_records + reused_records
        with open(OUT_TRIALS_JSONL, "w", encoding="utf-8") as f:
            for r in all_s2_records:
                f.write(json.dumps(r) + "\n")
        print(f"\n💾 Wrote {len(all_s2_records)} Session 2 records to {OUT_TRIALS_JSONL}")

    # Load Session 1 (primary unified warm_cache_trials.jsonl)
    s1_cells = load_records_by_cell(WARM_TRIALS_PATH)
    s2_cells: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in all_s2_records:
        if not r.get("is_warmup", False):
            s2_cells.setdefault((r["workload"], r["agent_key"]), []).append(r)

    comparison: dict[str, dict[str, Any]] = {}
    rel_diff_list: list[float] = []
    pooled_cv_list: list[float] = []
    intra_session_contrasts: dict[str, dict[str, Any]] = {}

    for w in workloads:
        comparison[w] = {}
        intra_session_contrasts[w] = {}

        # Baseline means in Session 1 and Session 2
        s1_base = [r["t_task_ms"] for r in s1_cells.get((w, "neural_baseline"), []) if not r.get("is_warmup", False)]
        s2_base = [r["t_task_ms"] for r in s2_cells.get((w, "neural_baseline"), [])]
        m1_base = _mean(s1_base)
        m2_base = _mean(s2_base)

        for ak in ["picoclaw", "openclaw_minimal", "python_native", "neural_baseline"]:
            s1_recs = [r for r in s1_cells.get((w, ak), []) if not r.get("is_warmup", False)]
            s2_recs = s2_cells.get((w, ak), [])
            if not s1_recs or not s2_recs:
                raise RuntimeError(f"FATAL: Missing records for {w} {ak}")

            s1_tasks = [float(r["t_task_ms"]) for r in s1_recs]
            s2_tasks = [float(r["t_task_ms"]) for r in s2_recs]

            m1 = _mean(s1_tasks)
            m2 = _mean(s2_tasks)
            pool_mean = 0.5 * (m1 + m2)
            abs_diff = abs(m1 - m2)
            rel_diff_pct = (abs_diff / pool_mean) * 100.0 if pool_mean > 0 else 0.0
            # Sample SD of {m1, m2} with ddof=1 is |m1 - m2| / sqrt(2)
            sd_means = abs_diff / math.sqrt(2.0)
            pooled_cv_pct = (sd_means / pool_mean) * 100.0 if pool_mean > 0 else 0.0

            rel_diff_list.append(rel_diff_pct)
            pooled_cv_list.append(pooled_cv_pct)

            s1_delta_vs_base_pct = ((m1 - m1_base) / m1_base) * 100.0 if m1_base > 0 else 0.0
            s2_delta_vs_base_pct = ((m2 - m2_base) / m2_base) * 100.0 if m2_base > 0 else 0.0

            comparison[w][ak] = {
                "session_1_n": len(s1_tasks),
                "session_1_mean_task_ms": round(m1, 2),
                "session_1_median_task_ms": round(_median(s1_tasks), 2),
                "session_1_std_task_ms": round(_std(s1_tasks), 2),
                "session_2_n": len(s2_tasks),
                "session_2_mean_task_ms": round(m2, 2),
                "session_2_median_task_ms": round(_median(s2_tasks), 2),
                "session_2_std_task_ms": round(_std(s2_tasks), 2),
                "inter_session_rel_diff_pct": round(rel_diff_pct, 2),
                "inter_session_pooled_cv_pct": round(pooled_cv_pct, 2),
                "inter_session_drift_pct": round(rel_diff_pct, 2),
                "session_1_delta_vs_neural_baseline_pct": round(s1_delta_vs_base_pct, 2),
                "session_2_delta_vs_neural_baseline_pct": round(s2_delta_vs_base_pct, 2),
            }
            if ak != "neural_baseline":
                intra_session_contrasts[w][ak] = {
                    "session_1_vs_baseline_pct": round(s1_delta_vs_base_pct, 2),
                    "session_2_vs_baseline_pct": round(s2_delta_vs_base_pct, 2),
                }

    overall_mean_rel_diff = _mean(rel_diff_list)
    overall_mean_pooled_cv = _mean(pooled_cv_list)

    bun_summary: dict[str, Any] = {}
    for w in workloads:
        recs = s2_cells.get((w, "bun_minimal"), [])
        if not recs:
            raise RuntimeError(f"FATAL: Missing bun_minimal records for {w}")
        tasks = [float(r["t_task_ms"]) for r in recs]
        orchs = [float(r["t_orch_ms"]) for r in recs]
        phys = [float(r.get("proc_peak_phys_mb", 0.0)) for r in recs]
        rsss = [float(r.get("rss_peak_mb", 0.0)) for r in recs]
        insts = [float(r.get("proc_instructions", 0)) for r in recs]
        cycs = [float(r.get("proc_cycles", 0)) for r in recs]
        enets = [float(r["energy_net_above_idle_j"]) for r in recs if r.get("energy_net_above_idle_j") is not None]

        m_task = _mean(tasks)
        m_orch = _mean(orchs)
        s2_base_m = _mean([float(r["t_task_ms"]) for r in s2_cells.get((w, "neural_baseline"), [])])
        bun_summary[w] = {
            "n_evaluations": len(recs),
            "mean_task_ms": round(m_task, 2),
            "median_task_ms": round(_median(tasks), 2),
            "std_task_ms": round(_std(tasks), 2),
            "mean_orch_ms": round(m_orch, 2),
            "orch_share_pct": round((m_orch / m_task * 100.0) if m_task > 0 else 0.0, 2),
            "delta_vs_session2_neural_baseline_pct": round(((m_task - s2_base_m) / s2_base_m * 100.0) if s2_base_m > 0 else 0.0, 2),
            "proc_peak_phys_mb_mean": round(_mean(phys), 2),
            "rss_peak_mb_mean": round(_mean(rsss), 2),
            "proc_instructions_mean": int(round(_mean(insts))),
            "proc_cycles_mean": int(round(_mean(cycs))),
            "energy_net_mean_j": round(_mean(enets), 2) if enets else None,
            "runner_binary": "bun",
            "is_fallback_node": False,
        }

    out_data = {
        "description": "Rigorous Inter-Session Replication (Session 2, seed=99, n=30 per cell) and Native Bun (darwin-aarch64) Benchmark",
        "caching_protocol": "Deterministic block-isolation (-np 1, 3 primings + 30 evaluations per block, BENCH_CACHE_PROMPT=true, randomized block order)",
        "hardware": "Apple Mac mini M4 (Mac16,10, 10-core Metal GPU)",
        "raw_trials_file": "results/publication_campaign/inter_session_trials.jsonl",
        "inter_session_comparisons": comparison,
        "paired_intra_session_contrasts_vs_neural_baseline": intra_session_contrasts,
        "overall_mean_inter_session_rel_diff_pct": round(overall_mean_rel_diff, 2),
        "overall_mean_inter_session_pooled_cv_pct": round(overall_mean_pooled_cv, 2),
        "overall_mean_inter_session_cv_pct": round(overall_mean_pooled_cv, 2),
        "bun_minimal_evaluation": bun_summary,
    }

    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)

    print(f"✅ Generated inter-session replication results: {OUT_JSON_PATH}")
    print(f"   Overall Mean Inter-Session Relative Diff: {overall_mean_rel_diff:.2f}% | Pooled CV: {overall_mean_pooled_cv:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(run_replication())
