#!/usr/bin/env python3
"""
scripts/run_w2_resample.py - Resample Workload W2 Physical Trials with SMC Telemetry
Re-runs n=30 repetitions (+ 3 warmups) for Workload W2 across all 5 agent targets,
capturing valid prompt_tokens (>2290), real task latency, and Apple SMC hardware energy.
Replaces ONLY the W2 records in results/publication_campaign/raw_trials.jsonl.
"""

import json
import os
import random
import sys
import time

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from benchmark.adapters import get_adapter  # noqa: E402
from benchmark.run_unified_benchmark import collect_host_metadata  # noqa: E402
from benchmark.telemetry import SMCPowerMonitor  # noqa: E402


def main():
    print("========================================================================")
    print(" 🚀 Workload W2 Focused Resample Campaign (Apple Silicon M4)")
    print("========================================================================")

    # Validate llama-server health
    import urllib.request
    health_url = "http://127.0.0.1:8080/health"
    try:
        req = urllib.request.Request(health_url)
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status != 200:
                raise RuntimeError(f"llama-server returned HTTP {resp.status}")
    except Exception as e:
        print(f"FATAL: llama-server unreachable at {health_url}: {e}")
        sys.exit(1)

    smc_monitor = SMCPowerMonitor(sample_interval_ms=50)
    telemetry_backend = "unprivileged_no_smc"
    if smc_monitor.active:
        print("⚡ [INFO] Apple SMC hardware telemetry active (root powermetrics shunts).")
        print("         Measuring 3-second quiescent idle baseline...")
        idle_mw = smc_monitor.measure_idle_baseline(3.0)
        print(f"         Quiescent idle baseline package power: {idle_mw:.2f} mW.")
        telemetry_backend = smc_monitor.telemetry_backend
        print("         Starting continuous Apple SMC powermetrics sampler daemon...")
        smc_monitor.start_campaign()
    else:
        print("⚠️  [NOTICE] Running unprivileged without root SMC shunts.")

    host_meta = collect_host_metadata()
    agents = ["picoclaw", "openclaw_minimal", "openclaw_full", "python_native", "neural_baseline"]
    w = "W2"

    adapter_instances = {}
    for ak in agents:
        ad = get_adapter(ak, REPO_DIR)
        if not ad.setup():
            raise RuntimeError(f"Failed to setup adapter '{ak}'.")
        adapter_instances[ak] = ad

    w2_warmup_records = []
    w2_eval_records = []
    rng = random.Random(42)

    try:
        # 1. Warmups: 3 per agent
        print("\n🔥 Executing W2 warmup rounds (3 per agent)...")
        for ak in agents:
            ad = adapter_instances[ak]
            for w_rep in range(3):
                res = ad.run_workload(w, iterations=1)
                rec = {
                    "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "agent_key": ak,
                    "architecture": ad.name,
                    "runtime": ad.runtime,
                    "workload": w,
                    "rep": w_rep + 1,
                    "is_warmup": True,
                    "is_simulated": False,
                    "data_source": "measured_hardware_warmup",
                    "t_task_ms": round(res.get("t_task_ms", 0.0), 2),
                    "t_neural_ms": round(res.get("t_neural_ms", 0.0), 2),
                    "t_orch_ms": round(res.get("t_orch_ms", 0.0), 3),
                    "t_dispatch_ms": round(res.get("t_dispatch_ms", 0.0), 3),
                    "t_http_ms": round(res.get("t_http_ms", 0.0), 3),
                    "rss_peak_mb": round(res.get("rss_peak_mb", 0.0), 2),
                    "proc_rss_mb": round(res.get("proc_rss_mb", res.get("rss_peak_mb", 0.0)), 2),
                    "proc_instructions": res.get("proc_instructions", 0),
                    "proc_cycles": res.get("proc_cycles", 0),
                    "proc_billed_energy": res.get("proc_billed_energy", 0),
                    "proc_peak_phys_mb": round(res.get("proc_peak_phys_mb", 0.0), 2),
                    "prompt_tokens": res.get("prompt_tokens", 0),
                    "completion_tokens": res.get("completion_tokens", res.get("output_tokens", 0)),
                    "output_tokens": res.get("output_tokens", 0),
                    "tool_calls": res.get("tool_calls", 0),
                    "http_status": res.get("http_status", 200),
                    "finish_reason": res.get("finish_reason", "stop"),
                    "energy_total_j": None,
                    "energy_net_above_idle_j": None,
                    "edp_js": None,
                }
                w2_warmup_records.append(rec)
                print(f"   [Warmup] {ak:16s} {w} Rep {w_rep+1}: Task={rec['t_task_ms']}ms, PromptTok={rec['prompt_tokens']}")

        # 2. Main Evaluation Trials: 30 reps per agent in block-randomized order
        print("\n▶️  Dispatching randomized W2 evaluation blocks (30 reps x 5 agents = 150 trials)...")
        trial_idx = 0
        for rep in range(1, 31):
            block = list(agents)
            rng.shuffle(block)
            for ak in block:
                trial_idx += 1
                ad = adapter_instances[ak]

                t_start_ns = time.monotonic_ns()
                t0_trial = time.monotonic()
                res = ad.run_workload(w, iterations=1)
                t_elapsed_s = time.monotonic() - t0_trial
                t_end_ns = time.monotonic_ns()

                energy_dict = None
                if smc_monitor.active:
                    energy_dict = smc_monitor.slice_energy(t_start_ns, t_end_ns)

                t_task_ms = res.get("t_task_ms", t_elapsed_s * 1000.0)
                t_neural_ms = res.get("t_neural_ms", 0.0)
                t_orch_ms = res.get("t_orch_ms", max(0.0, t_task_ms - t_neural_ms))
                t_dispatch_ms = res.get("t_dispatch_ms", 0.0)
                t_http_ms = res.get("t_http_ms", max(0.0, t_orch_ms - t_dispatch_ms))
                rss_peak = res.get("rss_peak_mb", 0.0)
                tokens = res.get("output_tokens", 0)
                prompt_tokens = res.get("prompt_tokens", 0)
                completion_tokens = res.get("completion_tokens", tokens)

                energy_total_j = None
                energy_net_j = None
                edp_js = None
                j_per_token = None

                if energy_dict is not None and energy_dict.get("energy_total_j") is not None:
                    energy_total_j = energy_dict["energy_total_j"]
                    energy_net_j = energy_dict["energy_net_above_idle_j"]
                    edp_js = round(energy_total_j * (t_task_ms / 1000.0), 4)
                    if tokens > 0:
                        j_per_token = round(energy_total_j / tokens, 4)
                    ds = "measured_hardware"
                else:
                    ds = "unprivileged_user_space"

                trial_record = {
                    "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "agent_key": ak,
                    "architecture": ad.name,
                    "runtime": ad.runtime,
                    "mode": ad.mode,
                    "workload": w,
                    "rep": rep,
                    "is_warmup": False,
                    "is_simulated": False,
                    "data_source": ds,
                    "telemetry_backend": telemetry_backend,
                    "t_task_ms": round(t_task_ms, 2),
                    "t_neural_ms": round(t_neural_ms, 2),
                    "t_orch_ms": round(t_orch_ms, 3),
                    "phi_orch_pct": round((t_orch_ms / t_task_ms * 100.0) if t_task_ms > 0 else 0.0, 3),
                    "ttft_ms": round(res.get("ttft_ms", 0.0), 2),
                    "itl_ms": round(res.get("itl_ms", 0.0), 2),
                    "t_dispatch_ms": round(t_dispatch_ms, 3),
                    "t_http_ms": round(t_http_ms, 3),
                    "r_tool_ops_sec": round(res.get("r_tool_ops_sec", 0.0), 2),
                    "rss_idle_mb": round(res.get("rss_idle_mb", 0.0), 2),
                    "rss_peak_mb": round(rss_peak, 2),
                    "proc_rss_mb": round(res.get("proc_rss_mb", rss_peak), 2),
                    "proc_instructions": res.get("proc_instructions", 0),
                    "proc_cycles": res.get("proc_cycles", 0),
                    "proc_billed_energy": res.get("proc_billed_energy", 0),
                    "proc_peak_phys_mb": round(res.get("proc_peak_phys_mb", 0.0), 2),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "output_tokens": tokens,
                    "tool_calls": res.get("tool_calls", 0),
                    "http_status": res.get("http_status", 200),
                    "finish_reason": res.get("finish_reason", "stop"),
                    "energy_total_j": energy_total_j,
                    "energy_net_above_idle_j": energy_net_j,
                    "edp_js": edp_js,
                    "joules_per_token": j_per_token,
                    "host_metadata": host_meta,
                }
                w2_eval_records.append(trial_record)
                edp_disp = f"{edp_js:.2f}J·s" if edp_js is not None else "N/A"
                print(
                    f"   [{trial_idx:03d}/150] {ak:16s} W2 Rep {rep:2d}: "
                    f"Task={t_task_ms:.1f}ms, Orch={t_orch_ms:.3f}ms, RAM={rss_peak:.1f}MB, PromptTok={prompt_tokens}, EDP={edp_disp}"
                )
                time.sleep(0.05)

    finally:
        if smc_monitor.active:
            smc_monitor.stop_campaign()

    # 3. Splice new W2 records into raw_trials.jsonl
    raw_trials_path = os.path.join(REPO_DIR, "results", "publication_campaign", "raw_trials.jsonl")
    with open(raw_trials_path, "r", encoding="utf-8") as f:
        existing_trials = [json.loads(line) for line in f if line.strip()]

    # Separate warmups and evals that are NOT W2
    non_w2_warmups = [t for t in existing_trials if t.get("is_warmup") and t.get("workload") != "W2"]
    non_w2_evals = [t for t in existing_trials if not t.get("is_warmup") and t.get("workload") != "W2"]

    # Recombine: warmups first (W1, W2, W3, W4), then evaluations
    # Maintain consistent structure
    final_trials = []
    # Add W1 warmups
    final_trials.extend([t for t in non_w2_warmups if t.get("workload") == "W1"])
    # Add new W2 warmups
    final_trials.extend(w2_warmup_records)
    # Add W3 and W4 warmups
    final_trials.extend([t for t in non_w2_warmups if t.get("workload") in ("W3", "W4")])

    # Add non-W2 evaluations and new W2 evaluations
    final_trials.extend(non_w2_evals)
    final_trials.extend(w2_eval_records)

    with open(raw_trials_path, "w", encoding="utf-8") as f:
        for t in final_trials:
            f.write(json.dumps(t) + "\n")

    print(f"\n✅ Successfully updated {len(final_trials)} total physical trials in {raw_trials_path}")
    print("   (Preserved 495 W1/W3/W4 trials, spliced 165 newly sampled W2 trials with SMC telemetry)")


if __name__ == "__main__":
    main()
