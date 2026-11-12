#!/usr/bin/env python3
"""
scripts/run_warm_cache_campaign.py - Full Warm-Cache Benchmark Campaign (n=30)
Executes publication campaign with BENCH_CACHE_PROMPT=true on Apple Silicon M4,
capturing SMC hardware energy, process memory, and token throughput.
Outputs:
  - results/publication_campaign/warm_cache_trials.jsonl
  - results/publication_campaign/warm_cache_summary.json
  - results/publication_campaign/warm_cache_statistical_tests.json
  - results/publication_campaign/tables/table_warm_cache.tex
  - results/publication_campaign/campaign_metadata.json
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
import urllib.request
from typing import Any

import numpy as np
from scipy import stats

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from benchmark.adapters import get_adapter  # noqa: E402
from benchmark.analyze_results import (  # noqa: E402
    bootstrap_ci,
    cliffs_delta,
    holm_bonferroni_adjust,
    vargha_delaney_a12,
)
from benchmark.run_unified_benchmark import collect_host_metadata  # noqa: E402
from benchmark.telemetry import SMCPowerMonitor  # noqa: E402


def check_server_health(url: str = "http://127.0.0.1:8080/health") -> bool:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def generate_warm_cache_latex_table(
    summary_stats: dict[str, dict[str, dict[str, Any]]],
    output_path: str,
    n_per_cond: int = 30,
    total_evals: int = 600,
    warmups_count: int = 60,
    telemetry_backend: str = "Apple Silicon SMC (50 ms)",
) -> str:
    workloads = ["W1", "W2", "W3", "W4"]
    configs = [
        ("neural_baseline", "Neural Baseline (Direct)"),
        ("picoclaw", "PicoClaw (Go Native)"),
        ("openclaw_minimal", "OpenClaw (Node.js Minimal)"),
        ("openclaw_full", "OpenClaw (Node.js Full 54-Tool)"),
        ("python_native", "PythonNative (CPython Reference)"),
    ]

    latex_table = r"""\begin{table*}[t]
\centering
\caption{Controlled Performance Evaluation under Realistic KV-Cache Reuse Regime (\texttt{cache\_prompt=true}) on Apple Silicon M4. When prompt prefill is amortized via KV-cache retention, orchestrator overhead ($\Phi_{\text{orch}} = T_{\text{orch}} / T_{\text{task}}$) becomes discriminative between compiled native and interpreted runtimes. Net Energy is integrated above quiescent idle baseline via Apple SMC hardware shunts at 50~ms resolution. Peak Phys RAM denotes lifetime maximum resident physical footprint via Darwin kernel \texttt{libproc}.}
\label{tab:evaluation_warm_cache_m4}
\small
\begin{tabular}{l l c r r r r r r}
\hline
\textbf{Workload} & \textbf{Configuration} & \textbf{Prompt/Comp} & \textbf{Median (IQR) [ms]} & \textbf{Disp / HTTP [ms]} & \textbf{Orch Share $\Phi_{\text{orch}}$ [\%]} & \textbf{Peak Phys [MB]} & \textbf{Net Energy [J]} & \textbf{EDP [J$\cdot$s]} \\
\hline
"""

    for w_idx, w in enumerate(workloads):
        for ak, label in configs:
            s = summary_stats.get(ak, {}).get(w, {})
            pt = int(round(s.get("prompt_tokens_mean", 0)))
            ct = int(round(s.get("completion_tokens_mean", 0)))
            tokens_str = f"{pt} / {ct}"

            task_med = s.get("t_task_median_ms", 0.0)
            task_iqr = s.get("t_task_iqr_ms", 0.0)
            lat_str = f"{task_med:.1f} ({task_iqr:.1f})"

            disp_m = s.get("t_dispatch_mean_ms", 0.0)
            http_m = s.get("t_http_mean_ms", 0.0)
            disp_http_str = f"{disp_m:.2f} / {http_m:.2f}"

            phi_orch = s.get("phi_orch_pct_mean", 0.0)
            phi_str = f"{phi_orch:.2f}\\%"

            phys_mb = s.get("proc_peak_phys_mb_mean", s.get("rss_peak_mb", 0.0))
            phys_str = f"{phys_mb:.1f}"

            e_net = s.get("energy_net_mean_j")
            e_str = f"{e_net:.2f}" if e_net is not None else r"\textbf{N/A}"

            edp = s.get("edp_net_mean_js")
            edp_str = f"{edp:.2f}" if edp is not None else r"\textbf{N/A}"

            latex_table += f"{w} & {label} & {tokens_str} & {lat_str} & {disp_http_str} & {phi_str} & {phys_str} & {e_str} & {edp_str} \\\\\n"

        if w_idx < len(workloads) - 1:
            latex_table += "\\hline\n"

    latex_table += "\\hline\n"
    latex_table += (
        f"\\multicolumn{{9}}{{l}}{{\\footnotesize $n = {n_per_cond}$ independent physical evaluations per condition "
        f"({total_evals} total evaluations, {warmups_count} warmups excluded).}} \\\\\n"
    )
    latex_table += (
        f"\\multicolumn{{9}}{{l}}{{\\footnotesize Telemetry Backend: {telemetry_backend}. "
        r"Data Source: \texttt{measured\_hardware\_warm\_cache}.}} \\\\" + "\n"
    )
    latex_table += "\\hline\n"
    latex_table += "\\end{tabular}\n\\end{table*}\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(latex_table)

    return latex_table


def main():
    print("========================================================================")
    print(" 🚀 Full Warm-Cache Benchmark Campaign (Apple Silicon M4)")
    print("    Regime B: Realistic KV-Cache Reuse (BENCH_CACHE_PROMPT=true)")
    print("========================================================================")

    output_dir = os.path.join(REPO_DIR, "results", "publication_campaign")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "tables"), exist_ok=True)
    warm_cache_trials_path = os.path.join(output_dir, "warm_cache_trials.jsonl")

    agents = ["picoclaw", "openclaw_minimal", "openclaw_full", "python_native", "neural_baseline"]
    workloads = ["W1", "W2", "W3", "W4"]
    reps_per_condition = 30
    total_evals = len(agents) * len(workloads) * reps_per_condition

    if "--analyze-only" in sys.argv:
        print("📊 [INFO] Running in --analyze-only mode on existing warm_cache_trials.jsonl...")
        if not os.path.exists(warm_cache_trials_path):
            print(f"❌ [FATAL] {warm_cache_trials_path} not found.")
            sys.exit(1)
        all_trials = []
        with open(warm_cache_trials_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_trials.append(json.loads(line))
        warmup_records = [t for t in all_trials if t.get("is_warmup")]
        eval_records = [t for t in all_trials if not t.get("is_warmup")]
        telemetry_backend = eval_records[0].get("telemetry_backend", "Apple Silicon SMC (50 ms)") if eval_records else "Apple Silicon SMC (50 ms)"
    else:
        # Enforce BENCH_CACHE_PROMPT=true
        os.environ["BENCH_CACHE_PROMPT"] = "true"

        health_url = "http://127.0.0.1:8080/health"
        if not check_server_health(health_url):
            print(f"❌ [FATAL] llama-server unreachable at {health_url}")
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

        _ = collect_host_metadata()

        adapter_instances = {}
        for ak in agents:
            ad = get_adapter(ak, REPO_DIR)
            if not ad.setup():
                raise RuntimeError(f"Failed to setup adapter '{ak}'.")
            adapter_instances[ak] = ad

        warmup_records = []
        eval_records = []
        rng = random.Random(42)

        try:
            # Phase 1: Warmups (3 per condition = 60 warmups)
            print("\n🔥 Executing warmup rounds (3 per condition, 60 total)...")
            for w in workloads:
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
                            "data_source": "measured_hardware_warm_cache_warmup",
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
                        warmup_records.append(rec)
                        print(
                            f"   [Warmup] {ak:16s} {w} Rep {w_rep+1}: Task={rec['t_task_ms']}ms, PromptTok={rec['prompt_tokens']}"
                        )

            # Phase 2: Main Evaluation Trials (30 reps x 20 conditions = 600 trials)
            print("\n▶️  Dispatching randomized evaluation blocks (30 reps x 20 conditions = 600 trials)...")
            trial_idx = 0

            for rep in range(1, reps_per_condition + 1):
                block = [(ak, w) for ak in agents for w in workloads]
                rng.shuffle(block)
                for ak, w in block:
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

                    if energy_dict is not None and energy_dict.get("energy_total_j") is not None:
                        energy_total_j = energy_dict["energy_total_j"]
                        energy_net_j = energy_dict["energy_net_above_idle_j"]
                        edp_js = round(energy_net_j * (t_task_ms / 1000.0), 4)

                    phi_orch_pct = (t_orch_ms / t_task_ms * 100.0) if t_task_ms > 0 else 0.0

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
                        "data_source": "measured_hardware_warm_cache",
                        "telemetry_backend": telemetry_backend,
                        "t_task_ms": round(t_task_ms, 2),
                        "t_neural_ms": round(t_neural_ms, 2),
                        "t_orch_ms": round(t_orch_ms, 3),
                        "phi_orch_pct": round(phi_orch_pct, 3),
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
                        "edp_net_js": edp_js,
                    }
                    eval_records.append(trial_record)

                    if trial_idx % 10 == 0 or trial_idx == total_evals:
                        e_disp = f"{energy_net_j:.2f}J" if energy_net_j is not None else "N/A"
                        print(
                            f"   [{trial_idx:03d}/{total_evals:03d}] {ak:16s} {w} Rep {rep}: "
                            f"Task={trial_record['t_task_ms']:6.1f}ms, Orch={trial_record['t_orch_ms']:5.2f}ms, "
                            f"Φ_orch={phi_orch_pct:4.1f}%, NetE={e_disp}"
                        )

                    # Small quiescence cooldown
                    time.sleep(0.05)

        finally:
            if smc_monitor.active:
                smc_monitor.stop_campaign()

        # Write all 660 trials to warm_cache_trials.jsonl
        all_trials = warmup_records + eval_records
        print(f"\n💾 Writing {len(all_trials)} total records to {warm_cache_trials_path}...")
        with open(warm_cache_trials_path, "w", encoding="utf-8") as f:
            for t in all_trials:
                f.write(json.dumps(t) + "\n")

    # Phase 3: Analytical Processing
    print("\n📈 Processing warm-cache summary statistics and hypothesis tests...")
    summary_stats = {ak: {} for ak in agents}

    for ak in agents:
        for w in workloads:
            subset = [r for r in eval_records if r["agent_key"] == ak and r["workload"] == w]
            if not subset:
                continue

            tasks = [r["t_task_ms"] for r in subset]
            orchs = [r["t_orch_ms"] for r in subset]
            phis = [r["phi_orch_pct"] for r in subset]
            disps = [r["t_dispatch_ms"] for r in subset]
            https = [r["t_http_ms"] for r in subset]
            phys = [r.get("proc_peak_phys_mb", r["rss_peak_mb"]) for r in subset]
            rsss = [r["rss_peak_mb"] for r in subset]
            pts = [r["prompt_tokens"] for r in subset]
            cts = [r["completion_tokens"] for r in subset]

            q25, q50, q75 = np.percentile(tasks, [25, 50, 75])
            iqr = q75 - q25

            energies_net = [r["energy_net_above_idle_j"] for r in subset if r.get("energy_net_above_idle_j") is not None]
            edps = [r["edp_js"] for r in subset if r.get("edp_js") is not None]

            summary_stats[ak][w] = {
                "t_task_median_ms": float(q50),
                "t_task_iqr_ms": float(iqr),
                "t_task_mean_ms": float(np.mean(tasks)),
                "t_task_std_ms": float(np.std(tasks, ddof=1)),
                "t_task_p95_ms": float(np.percentile(tasks, 95)),
                "t_orch_median_ms": float(np.median(orchs)),
                "t_orch_iqr_ms": float(np.percentile(orchs, 75) - np.percentile(orchs, 25)),
                "t_orch_mean_ms": float(np.mean(orchs)),
                "phi_orch_pct_mean": float(np.mean(phis)),
                "phi_orch_pct_median": float(np.median(phis)),
                "t_dispatch_mean_ms": float(np.mean(disps)),
                "t_http_mean_ms": float(np.mean(https)),
                "proc_peak_phys_mb_mean": float(np.mean(phys)),
                "proc_peak_phys_mb_max": float(np.max(phys)),
                "rss_peak_mb": float(np.mean(rsss)),
                "prompt_tokens_mean": float(np.mean(pts)),
                "completion_tokens_mean": float(np.mean(cts)),
                "energy_net_mean_j": float(np.mean(energies_net)) if energies_net else None,
                "energy_net_std_j": float(np.std(energies_net, ddof=1)) if len(energies_net) > 1 else None,
                "edp_net_mean_js": float(np.mean(edps)) if edps else None,
                "edp_net_median_js": float(np.median(edps)) if edps else None,
            }

    # Save warm_cache_summary.json
    summary_path = os.path.join(output_dir, "warm_cache_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_stats, f, indent=2)
    print(f"✅ Generated summary JSON: {summary_path}")

    # Hypothesis testing vs. PicoClaw
    raw_p_values = []
    comparison_meta = []
    comparisons = {}

    for w in workloads:
        pico_tasks = [r["t_task_ms"] for r in eval_records if r["agent_key"] == "picoclaw" and r["workload"] == w]
        for ak in ["openclaw_minimal", "openclaw_full", "python_native", "neural_baseline"]:
            other_tasks = [r["t_task_ms"] for r in eval_records if r["agent_key"] == ak and r["workload"] == w]
            u_stat, p_val = stats.mannwhitneyu(pico_tasks, other_tasks, alternative="two-sided")
            d_val = cliffs_delta(other_tasks, pico_tasks)
            a12_val = vargha_delaney_a12(other_tasks, pico_tasks)
            ci_low, ci_high = bootstrap_ci(other_tasks, n_resamples=2000, alpha=0.05, seed=42)

            comp_key = f"picoclaw_vs_{ak}_{w}"
            raw_p_values.append(p_val)
            comparison_meta.append((
                comp_key,
                {
                    "workload": w,
                    "reference": "picoclaw",
                    "comparison": ak,
                    "mann_whitney_u": float(u_stat),
                    "raw_p_value": float(p_val),
                    "cliffs_delta": round(float(d_val), 4),
                    "vargha_delaney_a12": round(float(a12_val), 4),
                    "bootstrap_ci_95": [round(float(ci_low), 4), round(float(ci_high), 4)],
                },
            ))

    adjusted_p = holm_bonferroni_adjust(raw_p_values)
    for (k, data), adj_p in zip(comparison_meta, adjusted_p):
        data["holm_bonferroni_p_value"] = float(adj_p)
        comparisons[k] = data

    tests_path = os.path.join(output_dir, "warm_cache_statistical_tests.json")
    with open(tests_path, "w", encoding="utf-8") as f:
        json.dump(comparisons, f, indent=2)
    print(f"✅ Generated statistical tests JSON: {tests_path}")

    # Generate table_warm_cache.tex
    tex_path = os.path.join(output_dir, "tables", "table_warm_cache.tex")
    generate_warm_cache_latex_table(
        summary_stats,
        tex_path,
        n_per_cond=reps_per_condition,
        total_evals=total_evals,
        warmups_count=len(warmup_records),
        telemetry_backend=telemetry_backend,
    )
    print(f"✅ Generated LaTeX table: {tex_path}")

    # Phase 4: Create campaign_metadata.json
    meta_path = os.path.join(output_dir, "campaign_metadata.json")
    metadata = {
        "model": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "model_architecture": "Llama-3.2 (3B parameters, GGUF Q4_K_M)",
        "server": {
            "engine": "llama.cpp b11887",
            "cli_arguments": "-c 32768 -np 1 -ngl 99 -t 4",
            "context_window_tokens": 32768,
            "gpu_layers": 99,
            "cpu_threads": 4,
            "parallel_slots": 1,
        },
        "hyperparameters": {
            "temperature": 0.0,
            "seed": 42,
        },
        "regimes": {
            "regime_a_cold_prefill": {
                "description": "Cold prompt prefill baseline without KV-cache reuse",
                "cache_prompt": False,
                "reps_per_condition": 30,
                "total_evaluations": 600,
                "warmups_per_condition": 3,
                "total_warmups": 60,
                "raw_file": "results/publication_campaign/raw_trials.jsonl",
                "table_file": "results/publication_campaign/tables/table_journal_ablation.tex",
            },
            "regime_b_warm_cache": {
                "description": "Realistic KV-cache prefix retention regime",
                "cache_prompt": True,
                "reps_per_condition": 30,
                "total_evaluations": 600,
                "warmups_per_condition": 3,
                "total_warmups": 60,
                "raw_file": "results/publication_campaign/warm_cache_trials.jsonl",
                "table_file": "results/publication_campaign/tables/table_warm_cache.tex",
            },
        },
        "hardware": {
            "platform": "Apple Mac mini M4 (Mac16,10)",
            "soc": "Apple M4 (10-Core CPU: 4 Performance + 6 Efficiency)",
            "gpu": "10-Core Apple Metal GPU",
            "memory": "24 GB Unified LPDDR5X UMA @ 120 GB/s bandwidth",
            "os": "macOS 15.x (darwin-arm64)",
            "telemetry": "Apple Silicon SMC (powermetrics 50 ms current shunts) + Darwin XNU libproc (RUSAGE_INFO_V4)",
        },
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Generated campaign metadata JSON: {meta_path}")

    print("\n========================================================================")
    print(" ✅ Warm-Cache Campaign and Artifacts Consolidated Successfully!")
    print("========================================================================")


if __name__ == "__main__":
    main()
