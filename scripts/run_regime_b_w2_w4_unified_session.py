#!/usr/bin/env python3
"""
scripts/run_regime_b_w2_w4_unified_session.py - Unified Single-Session Regime B Resampling for W2 & W4
Executes all 5 arms (picoclaw, openclaw_minimal, openclaw_full, python_native, neural_baseline)
across W2 and W4 (3 primings + 30 evaluations per block = 300 evaluations + 30 primings) plus
W1 and W3 priming warmups in a single continuous randomized session on Apple Silicon M4 with
continuous SMCPowerMonitor(sample_interval_ms=50), guaranteeing 100% intra-session contrasts
per workload and 100% populated ttft_ms > 0 and itl_ms > 0 across all 660 records.

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""
from __future__ import annotations

import json
import os
import random
import shutil
import sys
import time
import urllib.request

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from benchmark.adapters import get_adapter  # noqa: E402
from benchmark.telemetry import SMCPowerMonitor  # noqa: E402

WARM_TRIALS_PATH = os.path.join(REPO_DIR, "results", "publication_campaign", "warm_cache_trials.jsonl")
BACKUP_PATH = os.path.join(REPO_DIR, "results", "exploratory_campaigns", "warm_cache_trials_two_session_backup.jsonl")


def check_server_health(url: str = "http://127.0.0.1:8080/health") -> bool:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        return resp.status == 200


def main() -> int:
    if sys.platform != "darwin":
        raise RuntimeError(f"FATAL: Physical hardware execution requires macOS Darwin, got {sys.platform}")

    if not check_server_health():
        raise RuntimeError("FATAL: llama-server is not reachable at http://127.0.0.1:8080/health")

    os.makedirs(os.path.dirname(BACKUP_PATH), exist_ok=True)
    if not os.path.exists(BACKUP_PATH) and os.path.exists(WARM_TRIALS_PATH):
        shutil.copy2(WARM_TRIALS_PATH, BACKUP_PATH)
        print(f"📦 Preserved two-session backup at: {BACKUP_PATH}")

    # Load existing W1 and W3 evaluated records (which were already collected in a single session)
    existing_w1_w3_evals = []
    with open(WARM_TRIALS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("workload") in ("W1", "W3") and not rec.get("is_warmup", False):
                if rec.get("ttft_ms", 0.0) <= 0 or rec.get("itl_ms", 0.0) <= 0:
                    raise RuntimeError(f"FATAL: Existing W1/W3 eval record missing ttft_ms/itl_ms: {rec}")
                existing_w1_w3_evals.append(rec)

    if len(existing_w1_w3_evals) != 300:
        raise RuntimeError(f"FATAL: Expected 300 evaluated W1/W3 records, found {len(existing_w1_w3_evals)}")

    os.environ["BENCH_CACHE_PROMPT"] = "true"

    smc_monitor = SMCPowerMonitor(sample_interval_ms=50)
    if not smc_monitor.active:
        raise RuntimeError("FATAL: Apple SMC powermetrics is not active (sudo -n powermetrics required)!")

    print("⚡ Measuring 3.0s quiescent idle baseline on Apple Silicon M4...")
    idle_mw = smc_monitor.measure_idle_baseline(3.0)
    print(f"   Idle package power: {idle_mw:.2f} mW. Starting continuous 50ms SMC sampler...")
    smc_monitor.start_campaign()

    agents = ["picoclaw", "openclaw_minimal", "openclaw_full", "python_native", "neural_baseline"]
    adapters = {}
    for ak in agents:
        ad = get_adapter(ak, REPO_DIR)
        if not ad.setup():
            raise RuntimeError(f"FATAL: Failed to setup adapter {ak}")
        adapters[ak] = ad

    rng = random.Random(20261112)
    w1_w3_warmup_blocks = [(ak, w) for ak in agents for w in ("W1", "W3")]
    w2_w4_blocks = [(ak, w) for ak in agents for w in ("W2", "W4")]
    rng.shuffle(w2_w4_blocks)

    new_warmups = []
    new_w2_w4_evals = []

    try:
        # 1. Measure W1 and W3 priming warmups with full ttft_ms and itl_ms telemetry
        print("\n▶️  [Phase 1] Recording W1 & W3 Priming Warmups (10 blocks x 3 primings = 30 warmups) with full TTFT/ITL...")
        for ak, w in w1_w3_warmup_blocks:
            ad = adapters[ak]
            for w_rep in range(1, 4):
                res = ad.run_workload(w, iterations=1)
                prompt_tokens = int(res.get("prompt_tokens", 0))
                cached_tokens = int(res.get("cached_tokens", 0))
                uncached_tokens = int(res.get("uncached_prompt_tokens", 0))
                ttft_ms = float(res.get("ttft_ms", 0.0))
                itl_ms = float(res.get("itl_ms", 0.0))
                if prompt_tokens <= 0 or ttft_ms <= 0 or itl_ms <= 0:
                    raise RuntimeError(f"FATAL: Invalid warmup telemetry for {ak} {w}: pt={prompt_tokens}, ttft={ttft_ms}, itl={itl_ms}")
                cache_hit_pct = (cached_tokens / prompt_tokens * 100.0) if prompt_tokens > 0 else 0.0
                t_task_ms = float(res.get("t_task_ms", 0.0))
                t_neural_ms = float(res.get("t_neural_ms", 0.0))
                t_orch_ms = float(res.get("t_orch_ms", max(0.0, t_task_ms - t_neural_ms)))
                phi_orch_pct = (t_orch_ms / t_task_ms * 100.0) if t_task_ms > 0 else 0.0

                new_warmups.append({
                    "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "agent_key": ak,
                    "architecture": ad.name,
                    "runtime": ad.runtime,
                    "mode": getattr(ad, "mode", "standard"),
                    "workload": w,
                    "rep": w_rep,
                    "is_warmup": True,
                    "is_simulated": False,
                    "data_source": "measured_hardware_warm_cache_warmup",
                    "telemetry_backend": smc_monitor.telemetry_backend,
                    "t_task_ms": round(t_task_ms, 2),
                    "t_neural_ms": round(t_neural_ms, 2),
                    "t_orch_ms": round(t_orch_ms, 3),
                    "phi_orch_pct": round(phi_orch_pct, 3),
                    "ttft_ms": round(ttft_ms, 2),
                    "itl_ms": round(itl_ms, 2),
                    "t_dispatch_ms": round(float(res.get("t_dispatch_ms", 0.0)), 3),
                    "t_http_ms": round(float(res.get("t_http_ms", 0.0)), 3),
                    "r_tool_ops_sec": round(float(res.get("r_tool_ops_sec", 0.0)), 2),
                    "rss_idle_mb": round(float(res.get("rss_idle_mb", 0.0)), 2),
                    "rss_peak_mb": round(float(res.get("rss_peak_mb", 0.0)), 2),
                    "proc_rss_mb": round(float(res.get("proc_rss_mb", res.get("rss_peak_mb", 0.0))), 2),
                    "proc_instructions": int(res.get("proc_instructions", 0)),
                    "proc_cycles": int(res.get("proc_cycles", 0)),
                    "proc_billed_energy": int(res.get("proc_billed_energy", 0)),
                    "proc_peak_phys_mb": round(float(res.get("proc_peak_phys_mb", 0.0)), 2),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": int(res.get("completion_tokens", res.get("output_tokens", 0))),
                    "output_tokens": int(res.get("output_tokens", 0)),
                    "cached_tokens": cached_tokens,
                    "uncached_prompt_tokens": uncached_tokens,
                    "cache_hit_pct": round(cache_hit_pct, 2),
                    "tool_calls": int(res.get("tool_calls", 0)),
                    "http_status": int(res.get("http_status", 200)),
                    "finish_reason": str(res.get("finish_reason", "stop")),
                    "energy_total_j": None,
                    "energy_net_above_idle_j": None,
                    "edp_js": None,
                })

        # 2. Execute randomized W2 and W4 blocks (10 blocks x (3 primings + 30 evaluations))
        print("\n▶️  [Phase 2] Executing 10 Randomized Blocks for W2 & W4 (30 primings + 300 evaluations)...")
        for b_idx, (ak, w) in enumerate(w2_w4_blocks, start=1):
            ad = adapters[ak]
            print(f"\n📦 [Block {b_idx:02d}/10] {ak} on {w} (3 Primings + 30 Evaluations)", flush=True)
            for w_rep in range(1, 4):
                res = ad.run_workload(w, iterations=1)
                prompt_tokens = int(res.get("prompt_tokens", 0))
                cached_tokens = int(res.get("cached_tokens", 0))
                uncached_tokens = int(res.get("uncached_prompt_tokens", 0))
                ttft_ms = float(res.get("ttft_ms", 0.0))
                itl_ms = float(res.get("itl_ms", 0.0))
                if prompt_tokens <= 0 or ttft_ms <= 0 or itl_ms <= 0:
                    raise RuntimeError(f"FATAL: Invalid warmup telemetry for {ak} {w}: pt={prompt_tokens}, ttft={ttft_ms}, itl={itl_ms}")
                cache_hit_pct = (cached_tokens / prompt_tokens * 100.0) if prompt_tokens > 0 else 0.0
                t_task_ms = float(res.get("t_task_ms", 0.0))
                t_neural_ms = float(res.get("t_neural_ms", 0.0))
                t_orch_ms = float(res.get("t_orch_ms", max(0.0, t_task_ms - t_neural_ms)))
                phi_orch_pct = (t_orch_ms / t_task_ms * 100.0) if t_task_ms > 0 else 0.0

                new_warmups.append({
                    "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "agent_key": ak,
                    "architecture": ad.name,
                    "runtime": ad.runtime,
                    "mode": getattr(ad, "mode", "standard"),
                    "workload": w,
                    "rep": w_rep,
                    "is_warmup": True,
                    "is_simulated": False,
                    "data_source": "measured_hardware_warm_cache_warmup",
                    "telemetry_backend": smc_monitor.telemetry_backend,
                    "t_task_ms": round(t_task_ms, 2),
                    "t_neural_ms": round(t_neural_ms, 2),
                    "t_orch_ms": round(t_orch_ms, 3),
                    "phi_orch_pct": round(phi_orch_pct, 3),
                    "ttft_ms": round(ttft_ms, 2),
                    "itl_ms": round(itl_ms, 2),
                    "t_dispatch_ms": round(float(res.get("t_dispatch_ms", 0.0)), 3),
                    "t_http_ms": round(float(res.get("t_http_ms", 0.0)), 3),
                    "r_tool_ops_sec": round(float(res.get("r_tool_ops_sec", 0.0)), 2),
                    "rss_idle_mb": round(float(res.get("rss_idle_mb", 0.0)), 2),
                    "rss_peak_mb": round(float(res.get("rss_peak_mb", 0.0)), 2),
                    "proc_rss_mb": round(float(res.get("proc_rss_mb", res.get("rss_peak_mb", 0.0))), 2),
                    "proc_instructions": int(res.get("proc_instructions", 0)),
                    "proc_cycles": int(res.get("proc_cycles", 0)),
                    "proc_billed_energy": int(res.get("proc_billed_energy", 0)),
                    "proc_peak_phys_mb": round(float(res.get("proc_peak_phys_mb", 0.0)), 2),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": int(res.get("completion_tokens", res.get("output_tokens", 0))),
                    "output_tokens": int(res.get("output_tokens", 0)),
                    "cached_tokens": cached_tokens,
                    "uncached_prompt_tokens": uncached_tokens,
                    "cache_hit_pct": round(cache_hit_pct, 2),
                    "tool_calls": int(res.get("tool_calls", 0)),
                    "http_status": int(res.get("http_status", 200)),
                    "finish_reason": str(res.get("finish_reason", "stop")),
                    "energy_total_j": None,
                    "energy_net_above_idle_j": None,
                    "edp_js": None,
                })
                print(f"   [Priming {w_rep}/3] {ak:16s} {w}: Task={t_task_ms:.1f}ms, CacheHit={cache_hit_pct:.1f}%, TTFT={ttft_ms:.1f}ms, ITL={itl_ms:.2f}ms", flush=True)

            for eval_rep in range(1, 31):
                t0_ns = time.monotonic_ns()
                res = ad.run_workload(w, iterations=1)
                t1_ns = time.monotonic_ns()

                energy_dict = smc_monitor.slice_energy(t0_ns, t1_ns)
                if energy_dict is None:
                    time.sleep(0.06)
                    energy_dict = smc_monitor.slice_energy(t0_ns, t1_ns)
                if energy_dict is None or energy_dict.get("energy_total_j") is None:
                    raise RuntimeError(f"FATAL: SMC slice_energy returned None on {ak} {w} rep {eval_rep}")

                prompt_tokens = int(res.get("prompt_tokens", 0))
                cached_tokens = int(res.get("cached_tokens", 0))
                uncached_tokens = int(res.get("uncached_prompt_tokens", 0))
                ttft_ms = float(res.get("ttft_ms", 0.0))
                itl_ms = float(res.get("itl_ms", 0.0))
                if prompt_tokens <= 0 or ttft_ms <= 0 or itl_ms <= 0:
                    raise RuntimeError(f"FATAL: Missing ttft_ms/itl_ms on {ak} {w} rep {eval_rep}: pt={prompt_tokens}, ttft={ttft_ms}, itl={itl_ms}")

                t_task_ms = float(res.get("t_task_ms", 0.0))
                t_neural_ms = float(res.get("t_neural_ms", 0.0))
                t_orch_ms = float(res.get("t_orch_ms", max(0.0, t_task_ms - t_neural_ms)))
                t_dispatch_ms = float(res.get("t_dispatch_ms", 0.0))
                t_http_ms = float(res.get("t_http_ms", max(0.0, t_orch_ms - t_dispatch_ms)))
                phi_orch_pct = (t_orch_ms / t_task_ms * 100.0) if t_task_ms > 0 else 0.0
                cache_hit_pct = (cached_tokens / prompt_tokens * 100.0) if prompt_tokens > 0 else 0.0

                energy_total_j = float(energy_dict["energy_total_j"])
                energy_net_j = float(energy_dict["energy_net_above_idle_j"])
                edp_js = round(energy_net_j * (t_task_ms / 1000.0), 4)

                rss_peak = float(res.get("rss_peak_mb", 0.0))
                tokens = int(res.get("output_tokens", 0))
                completion_tokens = int(res.get("completion_tokens", tokens))

                rec = {
                    "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "agent_key": ak,
                    "architecture": ad.name,
                    "runtime": ad.runtime,
                    "mode": getattr(ad, "mode", "standard"),
                    "workload": w,
                    "rep": eval_rep,
                    "is_warmup": False,
                    "is_simulated": False,
                    "data_source": "measured_hardware_warm_cache",
                    "telemetry_backend": smc_monitor.telemetry_backend,
                    "t_task_ms": round(t_task_ms, 2),
                    "t_neural_ms": round(t_neural_ms, 2),
                    "t_orch_ms": round(t_orch_ms, 3),
                    "phi_orch_pct": round(phi_orch_pct, 3),
                    "ttft_ms": round(ttft_ms, 2),
                    "itl_ms": round(itl_ms, 2),
                    "t_dispatch_ms": round(t_dispatch_ms, 3),
                    "t_http_ms": round(t_http_ms, 3),
                    "r_tool_ops_sec": round(float(res.get("r_tool_ops_sec", 0.0)), 2),
                    "rss_idle_mb": round(float(res.get("rss_idle_mb", 0.0)), 2),
                    "rss_peak_mb": round(rss_peak, 2),
                    "proc_rss_mb": round(float(res.get("proc_rss_mb", rss_peak)), 2),
                    "proc_instructions": int(res.get("proc_instructions", 0)),
                    "proc_cycles": int(res.get("proc_cycles", 0)),
                    "proc_billed_energy": int(res.get("proc_billed_energy", 0)),
                    "proc_peak_phys_mb": round(float(res.get("proc_peak_phys_mb", 0.0)), 2),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "output_tokens": tokens,
                    "cached_tokens": cached_tokens,
                    "uncached_prompt_tokens": uncached_tokens,
                    "cache_hit_pct": round(cache_hit_pct, 2),
                    "tool_calls": int(res.get("tool_calls", 0)),
                    "http_status": int(res.get("http_status", 200)),
                    "finish_reason": str(res.get("finish_reason", "stop")),
                    "energy_total_j": energy_total_j,
                    "energy_net_above_idle_j": energy_net_j,
                    "edp_js": edp_js,
                    "edp_net_js": edp_js,
                }
                new_w2_w4_evals.append(rec)

                if eval_rep % 10 == 0 or eval_rep == 30:
                    print(
                        f"   [Rep {eval_rep:02d}/30] {ak:16s} {w}: Task={rec['t_task_ms']:6.1f}ms, "
                        f"Orch={rec['t_orch_ms']:5.2f}ms, TTFT={rec['ttft_ms']:5.1f}ms, ITL={rec['itl_ms']:5.2f}ms, NetE={energy_net_j:.2f}J",
                        flush=True,
                    )
    finally:
        smc_monitor.stop_campaign()

    all_records = new_warmups + existing_w1_w3_evals + new_w2_w4_evals
    if len(all_records) != 660:
        raise RuntimeError(f"FATAL: Expected 660 total records, got {len(all_records)}")

    for idx, r in enumerate(all_records):
        if r.get("ttft_ms") is None or r.get("ttft_ms", 0.0) <= 0 or r.get("itl_ms") is None or r.get("itl_ms", 0.0) <= 0:
            raise RuntimeError(f"FATAL: Record #{idx} missing positive ttft_ms/itl_ms: {r}")

    with open(WARM_TRIALS_PATH, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r) + "\n")

    print(f"\n✅ Successfully wrote 660 verified records (100% TTFT/ITL populated, unified W2/W4 session) to {WARM_TRIALS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
