"""
benchmark/analyze_results.py - Rigorous Non-Parametric Statistical Analysis
Calculates median (p50), interquartile range (IQR), Mann-Whitney U tests with
Holm-Bonferroni correction, Cliff's Delta, Vargha-Delaney A12 effect sizes with
Bootstrap 95% Confidence Intervals (2,000 resamples), and produces publication tables.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

import numpy as np
from scipy import stats

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cliffs_delta(lst1: list[float], lst2: list[float]) -> float:
    """
    Compute Cliff's Delta non-parametric effect size d in [-1, 1].
    - d = +1.0: lst1 is strictly greater than lst2 in all pairwise comparisons.
    - d = -1.0: lst1 is strictly smaller than lst2 in all pairwise comparisons.
    - d = 0.0: No stochastic dominance.
    """
    n1, n2 = len(lst1), len(lst2)
    if n1 == 0 or n2 == 0:
        return 0.0
    more = sum(1 for x in lst1 for y in lst2 if x > y)
    less = sum(1 for x in lst1 for y in lst2 if x < y)
    return (more - less) / float(n1 * n2)


def vargha_delaney_a12(lst1: list[float], lst2: list[float]) -> float:
    """
    Compute Vargha-Delaney A12 effect size statistic in [0, 1].
    A12 = P(X > Y) + 0.5 * P(X == Y) = (d + 1) / 2.
    """
    d = cliffs_delta(lst1, lst2)
    return (d + 1.0) / 2.0


def bootstrap_ci(
    data: list[float],
    n_resamples: int = 2000,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float]:
    """
    Computes empirical 95% bootstrap confidence interval for the sample median.
    """
    if len(data) == 0:
        return 0.0, 0.0
    if len(data) == 1:
        return float(data[0]), float(data[0])

    rng = np.random.default_rng(seed)
    arr = np.array(data, dtype=np.float64)
    boot_medians = np.empty(n_resamples, dtype=np.float64)

    for i in range(n_resamples):
        sample = rng.choice(arr, size=len(arr), replace=True)
        boot_medians[i] = np.median(sample)

    lower = float(np.percentile(boot_medians, 100.0 * (alpha / 2.0)))
    upper = float(np.percentile(boot_medians, 100.0 * (1.0 - alpha / 2.0)))
    return round(lower, 4), round(upper, 4)


def holm_bonferroni_adjust(p_values: list[float]) -> list[float]:
    """
    Adjusts a list of p-values using the step-down Holm-Bonferroni method.
    Guarantees strong family-wise error rate control under multiple comparisons.
    """
    m = len(p_values)
    if m == 0:
        return []

    # Sort indices by original p-value
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m
    running_max = 0.0

    for rank, (orig_idx, p_val) in enumerate(indexed):
        # Step-down multiplier: (m - rank)
        adj_p = p_val * (m - rank)
        adj_p = min(1.0, max(running_max, adj_p))
        running_max = adj_p
        adjusted[orig_idx] = round(adj_p, 6)

    return adjusted


def analyze_publication_campaign(input_path: str | None = None, output_dir: str | None = None):
    if input_path is None:
        input_path = os.path.join(REPO_DIR, "results", "publication_campaign", "raw_trials.jsonl")
    if output_dir is None:
        output_dir = os.path.join(REPO_DIR, "results", "publication_campaign")

    os.makedirs(os.path.join(output_dir, "tables"), exist_ok=True)

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found. Please run benchmark/run_unified_benchmark.py first.")
        return

    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass

    # Filter out warmup runs if marked
    eval_records = [r for r in records if not r.get("is_warmup", False)]
    if not eval_records:
        eval_records = records

    # Audit and filter invalid/failed trials
    valid_records = []
    for r in eval_records:
        status = r.get("http_status", 200)
        fr = r.get("finish_reason", "stop")
        if status != 200:
            print(f"⚠️  [WARNING] Dropping trial with non-200 HTTP status: {status}")
            continue
        if fr not in ("stop", "length", "tool_calls"):
            print(f"⚠️  [NOTICE] Unconventional finish_reason in trial: {fr}")
        pt = r.get("prompt_tokens", 0)
        ct = r.get("completion_tokens") or r.get("output_tokens", 0)
        if pt is None or int(pt) <= 0:
            raise ValueError(
                f"FATAL: Evaluated trial record {r.get('agent_key')} {r.get('workload')} Rep {r.get('rep')} "
                f"registered invalid prompt_tokens <= 0 ({pt}). All evaluated trials must record positive prompt tokens."
            )
        if ct is None or int(ct) <= 0:
            raise ValueError(
                f"FATAL: Evaluated trial record {r.get('agent_key')} {r.get('workload')} Rep {r.get('rep')} "
                f"registered invalid completion_tokens <= 0 ({ct}). All evaluated trials must record positive completion tokens."
            )
        valid_records.append(r)
    eval_records = valid_records

    print(f"Loaded {len(eval_records)} evaluated trial records (filtered {len(records) - len(eval_records)} warmups).")

    # Group by (agent_key, workload)
    groups: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for r in eval_records:
        ak = r.get("agent_key") or r.get("architecture", "unknown")
        w = r.get("workload", "W1")
        groups.setdefault(ak, {}).setdefault(w, []).append(r)

    summary_stats: dict[str, Any] = {}
    csv_rows = [
        "agent,workload,n,t_task_median_ms,t_task_iqr_ms,t_task_mean_ms,t_task_std_ms,t_task_p95_ms,"
        "t_orch_median_ms,rss_peak_mb,energy_total_mean_j,energy_net_mean_j,edp_mean_js,joules_per_token"
    ]

    for ak, w_dict in groups.items():
        summary_stats[ak] = {}
        for w, items in w_dict.items():
            for item in items:
                pt_val = item.get("prompt_tokens", 0)
                ct_val = item.get("completion_tokens") or item.get("output_tokens", 0)
                assert pt_val is not None and int(pt_val) > 0, f"Invariant violation: prompt_tokens <= 0 in {ak} {w}"
                assert ct_val is not None and int(ct_val) > 0, f"Invariant violation: completion_tokens <= 0 in {ak} {w}"

            t_tasks = [float(x["t_task_ms"]) for x in items if x.get("t_task_ms") is not None]
            t_orchs = [float(x["t_orch_ms"]) for x in items if x.get("t_orch_ms") is not None]
            t_dispatches = [float(x.get("t_dispatch_ms", 0.0)) for x in items if x.get("t_dispatch_ms") is not None]
            rss_peaks = [float(x["rss_peak_mb"]) for x in items if x.get("rss_peak_mb") is not None]
            proc_phys = [float(x.get("proc_peak_phys_mb", 0.0)) for x in items if x.get("proc_peak_phys_mb") is not None]
            proc_inst = [float(x.get("proc_instructions", 0.0)) for x in items if x.get("proc_instructions") is not None]
            proc_cyc = [float(x.get("proc_cycles", 0.0)) for x in items if x.get("proc_cycles") is not None]
            proc_billed = [float(x.get("proc_billed_energy", 0.0)) for x in items if x.get("proc_billed_energy") is not None]
            pts = [int(x.get("prompt_tokens", 0)) for x in items]
            cts = [int(x.get("completion_tokens") or x.get("output_tokens", 0)) for x in items]
            frs = [str(x.get("finish_reason", "stop")) for x in items]

            # Collect energy metrics (handling None for unprivileged runs)
            energies_total = [float(x["energy_total_j"]) for x in items if x.get("energy_total_j") is not None]
            energies_net = [float(x["energy_net_above_idle_j"]) for x in items if x.get("energy_net_above_idle_j") is not None]
            edps_net = [
                float(x["energy_net_above_idle_j"]) * (float(x["t_task_ms"]) / 1000.0)
                for x in items
                if x.get("energy_net_above_idle_j") is not None and x.get("t_task_ms") is not None
            ]
            j_tokens_net = [
                float(x["energy_net_above_idle_j"]) / float(x.get("completion_tokens") or x.get("output_tokens") or 1)
                for x in items
                if x.get("energy_net_above_idle_j") is not None and (x.get("completion_tokens") or x.get("output_tokens", 0)) > 0
            ]

            # Primary non-parametric metrics
            p50_t = float(np.percentile(t_tasks, 50)) if t_tasks else 0.0
            q25_t = float(np.percentile(t_tasks, 25)) if t_tasks else 0.0
            q75_t = float(np.percentile(t_tasks, 75)) if t_tasks else 0.0
            iqr_t = q75_t - q25_t
            p95_t = float(np.percentile(t_tasks, 95)) if t_tasks else 0.0
            mean_t = float(np.mean(t_tasks)) if t_tasks else 0.0
            std_t = float(np.std(t_tasks, ddof=1)) if len(t_tasks) > 1 else 0.0

            p50_orch = float(np.percentile(t_orchs, 50)) if t_orchs else 0.0
            mean_orch = float(np.mean(t_orchs)) if t_orchs else 0.0
            p50_disp = float(np.percentile(t_dispatches, 50)) if t_dispatches else 0.0
            mean_rss = float(np.mean(rss_peaks)) if rss_peaks else 0.0
            mean_phys = float(np.mean(proc_phys)) if proc_phys else mean_rss
            mean_inst = int(np.mean(proc_inst)) if proc_inst else 0
            mean_cyc = int(np.mean(proc_cyc)) if proc_cyc else 0
            mean_billed = int(np.mean(proc_billed)) if proc_billed else 0

            mean_e_total = float(np.mean(energies_total)) if energies_total else None
            mean_e_net = float(np.mean(energies_net)) if energies_net else None
            mean_edp = float(np.mean(edps_net)) if edps_net else None
            mean_jtok = float(np.mean(j_tokens_net)) if j_tokens_net else None

            ci_low, ci_high = bootstrap_ci(t_tasks)

            summary_stats[ak][w] = {
                "sample_count": len(t_tasks),
                "t_task_median_ms": round(p50_t, 2),
                "t_task_iqr_ms": round(iqr_t, 2),
                "t_task_bootstrap_ci_95": [ci_low, ci_high],
                "t_task_mean_ms": round(mean_t, 2),
                "t_task_std_ms": round(std_t, 2),
                "t_task_p95_ms": round(p95_t, 2),
                "t_orch_median_ms": round(p50_orch, 3),
                "t_orch_mean_ms": round(mean_orch, 3),
                "t_dispatch_median_ms": round(p50_disp, 3),
                "rss_peak_mb": round(mean_rss, 2),
                "proc_peak_phys_mb": round(mean_phys, 2),
                "proc_instructions": mean_inst,
                "proc_cycles": mean_cyc,
                "proc_billed_energy": mean_billed,
                "prompt_tokens_mean": round(float(np.mean(pts)), 2) if pts else 0,
                "completion_tokens_mean": round(float(np.mean(cts)), 2) if cts else 0,
                "finish_reason": frs[0] if frs else "stop",
                "energy_total_mean_j": round(mean_e_total, 3) if mean_e_total is not None else None,
                "energy_net_mean_j": round(mean_e_net, 3) if mean_e_net is not None else None,
                "edp_mean_js": round(mean_edp, 3) if mean_edp is not None else None,
                "joules_per_token": round(mean_jtok, 4) if mean_jtok is not None else None,
            }

            e_str = f"{mean_e_total:.3f}" if mean_e_total is not None else "N/A"
            enet_str = f"{mean_e_net:.3f}" if mean_e_net is not None else "N/A"
            edp_str = f"{mean_edp:.3f}" if mean_edp is not None else "N/A"
            jtok_str = f"{mean_jtok:.4f}" if mean_jtok is not None else "N/A"

            csv_rows.append(
                f"{ak},{w},{len(t_tasks)},{p50_t:.2f},{iqr_t:.2f},{mean_t:.2f},{std_t:.2f},{p95_t:.2f},"
                f"{p50_orch:.3f},{mean_rss:.2f},{e_str},{enet_str},{edp_str},{jtok_str}"
            )

    # Statistical comparisons with Holm-Bonferroni correction
    comparisons: dict[str, Any] = {}
    pairs = [
        ("picoclaw", "openclaw_minimal", "PicoClaw_vs_OpenClawMinimal"),
        ("picoclaw", "openclaw_full", "PicoClaw_vs_OpenClawFull"),
        ("picoclaw", "python_native", "PicoClaw_vs_PythonNative"),
        ("openclaw_minimal", "openclaw_full", "OpenClawAblation_Minimal_vs_Full"),
        ("neural_baseline", "picoclaw", "NeuralBaseline_vs_PicoClaw"),
    ]

    all_p_entries = []
    for a1, a2, label in pairs:
        comparisons[label] = {}
        for w in ["W1", "W2", "W3", "W4"]:
            vals1 = [float(x["t_task_ms"]) for x in groups.get(a1, {}).get(w, []) if x.get("t_task_ms") is not None]
            vals2 = [float(x["t_task_ms"]) for x in groups.get(a2, {}).get(w, []) if x.get("t_task_ms") is not None]
            if len(vals1) > 0 and len(vals2) > 0:
                try:
                    u_stat, raw_p = stats.mannwhitneyu(vals1, vals2, alternative="two-sided")
                except Exception:
                    u_stat, raw_p = 0.0, 1.0

                d = cliffs_delta(vals1, vals2)
                a12 = vargha_delaney_a12(vals1, vals2)

                entry = {
                    "u_statistic": float(u_stat),
                    "raw_p_value": float(raw_p),
                    "cliffs_delta": round(float(d), 4),
                    "vargha_delaney_a12": round(float(a12), 4),
                }
                comparisons[label][w] = entry
                all_p_entries.append((label, w, raw_p))

    # Apply Holm-Bonferroni correction across all hypotheses
    if all_p_entries:
        raw_p_list = [item[2] for item in all_p_entries]
        adj_p_list = holm_bonferroni_adjust(raw_p_list)
        for idx, (lbl, w, _) in enumerate(all_p_entries):
            adj_p = adj_p_list[idx]
            comparisons[lbl][w]["holm_bonferroni_p_value"] = adj_p
            comparisons[lbl][w]["significant_alpha_0_05"] = bool(adj_p < 0.05)

    # Save JSON summary & statistical tests
    stats_out = os.path.join(output_dir, "summary_statistics.json")
    with open(stats_out, "w", encoding="utf-8") as f:
        json.dump(summary_stats, f, indent=2)

    tests_out = os.path.join(output_dir, "statistical_tests.json")
    with open(tests_out, "w", encoding="utf-8") as f:
        json.dump(comparisons, f, indent=2)

    # Save CSV
    csv_out = os.path.join(output_dir, "tables", "metrics_summary.csv")
    with open(csv_out, "w", encoding="utf-8") as f:
        f.write("\n".join(csv_rows) + "\n")

    # Generate LaTeX Table (table_journal_ablation.tex) with complete 9 columns and dynamic footer metadata
    latex_table = r"""\begin{table*}[t]
\centering
\caption{Empirical Performance Evaluation and Runtime Ablation Matrix on Apple Silicon M4. Peak Phys RAM denotes lifetime maximum resident physical footprint recorded via Darwin kernel \texttt{libproc}. Net Energy is integrated above quiescent idle baseline via Apple SMC hardware shunts at 50~ms resolution. Dispatch and HTTP latency isolate tool-execution and network overhead ($T_{\text{orch}} \approx T_{\text{dispatch}} + T_{\text{http}}$). Prompt and Completion token counts reflect tokenizer throughput. Note: Regime A preserves the pre-equalization serialization baseline (where formatting differences in tool descriptions and Python JSON separators yielded 2,153 vs. 2,273 tokens in W1, 2,297 vs. 2,321 in W2, 2,410 vs. 2,530 in W3, and 22,980 vs. 23,255 vs. 24,180 in W4; $\le 5.2\%$ variance), whereas Regime B (\texttt{table\_warm\_cache.tex}) enforces strict byte-and-token parity (2,153, 2,177, 2,410, and 22,980 tokens) across all 15-tool arms.}
\label{tab:evaluation_ablation_m4}
\small
\begin{tabular}{l l c r r r r r r}
\hline
\textbf{Workload} & \textbf{Configuration} & \textbf{Prompt/Comp} & \textbf{Median (IQR) [ms]} & \textbf{Disp / HTTP [ms]} & \textbf{Peak Phys [MB]} & \textbf{Net Energy [J]} & \textbf{EDP [J$\cdot$s]} & \textbf{Billed / Cycles} \\
\hline
"""
    agents_order = [
        ("neural_baseline", "Neural Baseline (Direct)"),
        ("picoclaw", "PicoClaw (Go Native)"),
        ("openclaw_minimal", "OpenClaw (Node.js Minimal)"),
        ("openclaw_full", "OpenClaw (Node.js Full 54-Tool)"),
        ("python_native", "PythonNative (CPython Reference)"),
    ]

    for w in ["W1", "W2", "W3", "W4"]:
        for ak, label in agents_order:
            entry = summary_stats.get(ak, {}).get(w)
            if entry:
                items = groups.get(ak, {}).get(w, [])
                p_tok = int(round(np.mean([float(x.get("prompt_tokens", 0)) for x in items]))) if items else 0
                c_tok = int(round(np.mean([float(x.get("completion_tokens") or x.get("output_tokens", 0)) for x in items]))) if items else 0
                p50 = entry["t_task_median_ms"]
                iqr = entry["t_task_iqr_ms"]
                d_m = entry.get("t_dispatch_median_ms", 0.0)
                h_m = float(np.percentile([float(x.get("t_http_ms", 0.0)) for x in items if x.get("t_http_ms") is not None], 50)) if items else 0.0
                disp_http = f"{d_m:.2f} / {h_m:.2f}"
                ram = entry.get("proc_peak_phys_mb", entry["rss_peak_mb"])
                enet_val = entry.get("energy_net_mean_j")
                enet_str = f"{enet_val:.2f}" if enet_val is not None else "N/A"
                edp_val = entry.get("edp_mean_js")
                edp_str = f"{edp_val:.2f}" if edp_val is not None else "N/A"
                billed = entry.get("proc_billed_energy", 0)
                cyc = entry.get("proc_cycles", 0)
                cyc_str = f"{cyc/1e6:.1f}M" if cyc > 0 else "0"
                billed_cyc_str = f"{billed} / {cyc_str}" if billed > 0 or cyc > 0 else "N/A"
                latex_table += f"{w} & {label} & {p_tok} / {c_tok} & {p50:.1f} ({iqr:.1f}) & {disp_http} & {ram:.1f} & {enet_str} & {edp_str} & {billed_cyc_str} \\\\\n"
        latex_table += r"\hline" + "\n"

    total_evals = len(eval_records)
    warmups_count = len(records) - len(eval_records)
    cond_count = len(groups) * 4 if groups else 1
    n_per_cond = int(total_evals / cond_count) if cond_count > 0 else 0
    backends = sorted(list({str(r.get("telemetry_backend", "apple_smc_powermetrics")) for r in eval_records}))
    backend_str = "Apple Silicon SMC (\\texttt{powermetrics} 50~ms current shunt sampling) + Darwin XNU \\texttt{libproc}" if "apple_smc_powermetrics" in backends else ", ".join(backends)
    datasources = sorted(list({str(r.get("data_source", "measured_hardware")) for r in eval_records}))
    datasource_str = ", ".join(datasources).replace("_", r"\_")

    latex_table += f"""\\multicolumn{{9}}{{l}}{{\\footnotesize $n = {n_per_cond}$ independent physical evaluations per condition ({total_evals} total evaluations, {warmups_count} warmups excluded).}} \\\\
\\multicolumn{{9}}{{l}}{{\\footnotesize Telemetry Backend: {backend_str}. Data Source: \\texttt{{{datasource_str}}}.}} \\\\
\\hline
\\end{{tabular}}
\\end{{table*}}
"""

    tex_out = os.path.join(output_dir, "tables", "table_journal_ablation.tex")
    with open(tex_out, "w", encoding="utf-8") as f:
        f.write(latex_table)

    # Generate macros_empirical.tex with all prose-cited empirical numbers
    generate_empirical_macros(summary_stats, comparisons, eval_records, output_dir)

    # Compute Spearman rank correlation matrix across regimes
    compute_spearman_correlation_matrix(
        regime_a_path=input_path,
        regime_b_path=os.path.join(output_dir, "warm_cache_trials.jsonl"),
        output_dir=output_dir,
    )

    # Compute Principal Component Analysis (PCA) variance decomposition across regimes
    compute_pca_variance_decomposition(
        regime_a_path=input_path,
        regime_b_path=os.path.join(output_dir, "warm_cache_trials.jsonl"),
        output_dir=output_dir,
    )

    print(f"✅ Generated summary JSON: {stats_out}")
    print(f"✅ Generated statistical tests JSON: {tests_out}")
    print(f"✅ Generated CSV table: {csv_out}")
    print(f"✅ Generated LaTeX table: {tex_out}")


def generate_empirical_macros(
    summary_stats: dict[str, Any],
    comparisons: dict[str, Any],
    eval_records: list[dict[str, Any]],
    output_dir: str,
) -> str:
    # Mandatory agent and workload validation
    for ak in ["picoclaw", "openclaw_minimal", "openclaw_full", "neural_baseline"]:
        if ak not in summary_stats:
            raise KeyError(f"Missing mandatory agent in summary_statistics: {ak}")
        for w in ["W1", "W2", "W3", "W4"]:
            if w not in summary_stats[ak]:
                raise KeyError(f"Missing mandatory workload '{w}' for agent '{ak}' in summary_statistics")

    pico_w2 = summary_stats["picoclaw"]["W2"]
    pico_w3 = summary_stats["picoclaw"]["W3"]
    pico_w4 = summary_stats["picoclaw"]["W4"]

    open_min_w1 = summary_stats["openclaw_minimal"]["W1"]
    open_min_w2 = summary_stats["openclaw_minimal"]["W2"]
    open_min_w3 = summary_stats["openclaw_minimal"]["W3"]

    open_full_w1 = summary_stats["openclaw_full"]["W1"]
    open_full_w3 = summary_stats["openclaw_full"]["W3"]
    open_full_w4 = summary_stats["openclaw_full"]["W4"]

    neural_w2 = summary_stats["neural_baseline"]["W2"]

    cmp_w3_min = comparisons.get("PicoClaw_vs_OpenClawMinimal", {}).get("W3")
    cmp_w3_full = comparisons.get("PicoClaw_vs_OpenClawFull", {}).get("W3")
    cmp_w4 = comparisons.get("PicoClaw_vs_OpenClawFull", {}).get("W4")

    if cmp_w3_min is None or cmp_w3_full is None or cmp_w4 is None:
        raise KeyError("Missing mandatory statistical comparison in comparisons")

    pico_trials = [r for r in eval_records if r.get("agent_key") == "picoclaw"]
    open_min_trials = [r for r in eval_records if r.get("agent_key") == "openclaw_minimal"]

    if not pico_trials or not open_min_trials:
        raise ValueError("Missing trial records for picoclaw or openclaw_minimal in eval_records")

    pico_w2_trials = [r for r in pico_trials if r.get("workload") == "W2"]
    open_min_w2_trials = [r for r in open_min_trials if r.get("workload") == "W2"]

    if not pico_w2_trials or not open_min_w2_trials:
        raise ValueError("Missing W2 trial records for picoclaw or openclaw_minimal")

    pico_w2_tokens = float(np.mean([r["completion_tokens"] for r in pico_w2_trials]))
    open_min_w2_tokens = float(np.mean([r["completion_tokens"] for r in open_min_w2_trials]))
    pico_w2_neural_mean = float(np.mean([r["t_neural_ms"] for r in pico_w2_trials]))
    open_min_w2_neural_mean = float(np.mean([r["t_neural_ms"] for r in open_min_w2_trials]))

    pico_inst_m = float(np.mean([r.get("proc_instructions", 0) for r in pico_trials])) / 1e6
    pico_cyc_m = float(np.mean([r.get("proc_cycles", 0) for r in pico_trials])) / 1e6
    open_min_inst_m = float(np.mean([r.get("proc_instructions", 0) for r in open_min_trials])) / 1e6
    open_min_cyc_m = float(np.mean([r.get("proc_cycles", 0) for r in open_min_trials])) / 1e6

    inst_ratio = open_min_inst_m / pico_inst_m if pico_inst_m > 0 else 0.0
    cyc_ratio = open_min_cyc_m / pico_cyc_m if pico_cyc_m > 0 else 0.0

    pico_rss_all = [summary_stats["picoclaw"][w]["rss_peak_mb"] for w in ["W1", "W2", "W3", "W4"]]
    open_rss_all = [summary_stats["openclaw_minimal"][w]["rss_peak_mb"] for w in ["W1", "W2", "W3", "W4"]]

    pico_phys_all = [summary_stats["picoclaw"][w].get("proc_peak_phys_mb", summary_stats["picoclaw"][w]["rss_peak_mb"]) for w in ["W1", "W2", "W3", "W4"]]
    open_phys_all = [summary_stats["openclaw_minimal"][w].get("proc_peak_phys_mb", summary_stats["openclaw_minimal"][w]["rss_peak_mb"]) for w in ["W1", "W2", "W3", "W4"]]

    ram_ratios = [open_rss_all[i] / pico_rss_all[i] for i in range(4)]
    phys_ratios = [open_phys_all[i] / pico_phys_all[i] for i in range(4)]

    pico_phys_m = float(np.mean([r.get("proc_peak_phys_mb", 0) for r in pico_trials]))
    open_min_phys_m = float(np.mean([r.get("proc_peak_phys_mb", 0) for r in open_min_trials]))
    phys_ratio = open_min_phys_m / pico_phys_m if pico_phys_m > 0 else 0.0

    w2_orch_speedup = open_min_w2["t_orch_median_ms"] / pico_w2["t_orch_median_ms"] if pico_w2["t_orch_median_ms"] > 0 else 1.0
    w2_ram_reduction = open_min_w2["rss_peak_mb"] / pico_w2["rss_peak_mb"] if pico_w2["rss_peak_mb"] > 0 else 1.0

    def _fmt_energy(val: float | None) -> str:
        if val is None:
            return r"\textbf{N/A}"
        return f"{val:.2f}"

    def _fmt_ratio(num: float | None, den: float | None) -> str:
        if num is None or den is None or den == 0.0:
            return r"\textbf{N/A}"
        return f"{(num / den):.2f}"

    def _fmt_pct(num: float | None, den: float | None) -> str:
        if num is None or den is None or den == 0.0:
            return r"\textbf{N/A}"
        return f"{((den - num) / den * 100.0):.2f}"

    def _format_p_val(p_val: float) -> str:
        if p_val < 1e-5:
            return r"< 10^{-5}"
        else:
            return f"= {p_val:.4f}"

    p_w3_full_str = _format_p_val(cmp_w3_full["holm_bonferroni_p_value"])
    p_w3_min_str = _format_p_val(cmp_w3_min["holm_bonferroni_p_value"])
    p_w4_str = _format_p_val(cmp_w4["holm_bonferroni_p_value"])

    macros_path = os.path.join(output_dir, "tables", "macros_empirical.tex")
    lines = [
        "% Automatically generated macros from publication campaign empirical results",
        "% DO NOT EDIT MANUALLY - Generated by benchmark/analyze_results.py",
        f"\\newcommand{{\\WThreePicoMedian}}{{{pico_w3['t_task_median_ms']:.1f}}}",
        f"\\newcommand{{\\WThreePicoIQR}}{{{pico_w3['t_task_iqr_ms']:.1f}}}",
        f"\\newcommand{{\\WThreePicoMean}}{{{pico_w3['t_task_mean_ms']:.1f}}}",
        f"\\newcommand{{\\WThreePicoSD}}{{{pico_w3['t_task_std_ms']:.1f}}}",
        f"\\newcommand{{\\WThreeOpenMinMedian}}{{{open_min_w3['t_task_median_ms']:.1f}}}",
        f"\\newcommand{{\\WThreeOpenMinIQR}}{{{open_min_w3['t_task_iqr_ms']:.1f}}}",
        f"\\newcommand{{\\WThreeOpenFullMedian}}{{{open_full_w3['t_task_median_ms']:.1f}}}",
        f"\\newcommand{{\\WThreeOpenFullIQR}}{{{open_full_w3['t_task_iqr_ms']:.1f}}}",
        f"\\newcommand{{\\WThreeCliffsDeltaMin}}{{{cmp_w3_min['cliffs_delta']:.3f}}}",
        f"\\newcommand{{\\WThreeAOneTwoMin}}{{{cmp_w3_min['vargha_delaney_a12']:.3f}}}",
        f"\\newcommand{{\\WThreeAdjPMin}}{{{p_w3_min_str}}}",
        f"\\newcommand{{\\WThreeCliffsDeltaFull}}{{{cmp_w3_full['cliffs_delta']:.3f}}}",
        f"\\newcommand{{\\WThreeAOneTwoFull}}{{{cmp_w3_full['vargha_delaney_a12']:.3f}}}",
        f"\\newcommand{{\\WThreeAdjPFull}}{{{p_w3_full_str}}}",
        f"\\newcommand{{\\WThreePicoOrchMedian}}{{{pico_w3['t_orch_median_ms']:.2f}}}",
        f"\\newcommand{{\\WThreeOpenMinOrchMedian}}{{{open_min_w3['t_orch_median_ms']:.2f}}}",
        f"\\newcommand{{\\WThreeOpenFullOrchMedian}}{{{open_full_w3['t_orch_median_ms']:.2f}}}",
        "",
        f"\\newcommand{{\\WTwoOpenMinMedian}}{{{open_min_w2['t_task_median_ms']:.1f}}}",
        f"\\newcommand{{\\WTwoOpenMinMean}}{{{open_min_w2['t_task_mean_ms']:.1f}}}",
        f"\\newcommand{{\\WTwoOpenMinEnergy}}{{{_fmt_energy(open_min_w2.get('energy_net_mean_j'))}}}",
        f"\\newcommand{{\\WTwoPicoMedian}}{{{pico_w2['t_task_median_ms']:.1f}}}",
        f"\\newcommand{{\\WTwoPicoMean}}{{{pico_w2['t_task_mean_ms']:.1f}}}",
        f"\\newcommand{{\\WTwoPicoEnergy}}{{{_fmt_energy(pico_w2.get('energy_net_mean_j'))}}}",
        f"\\newcommand{{\\WTwoNeuralMedian}}{{{neural_w2['t_task_median_ms']:.1f}}}",
        f"\\newcommand{{\\WTwoNeuralMean}}{{{neural_w2['t_task_mean_ms']:.1f}}}",
        f"\\newcommand{{\\WTwoNeuralEnergy}}{{{_fmt_energy(neural_w2.get('energy_net_mean_j'))}}}",
        f"\\newcommand{{\\WTwoOpenMinTokens}}{{{open_min_w2_tokens:.1f}}}",
        f"\\newcommand{{\\WTwoPicoTokens}}{{{pico_w2_tokens:.1f}}}",
        f"\\newcommand{{\\WTwoNeuralPico}}{{{pico_w2_neural_mean:.1f}}}",
        f"\\newcommand{{\\WTwoNeuralOpenMin}}{{{open_min_w2_neural_mean:.1f}}}",
        f"\\newcommand{{\\WTwoPicoOrchMedian}}{{{pico_w2['t_orch_median_ms']:.2f}}}",
        f"\\newcommand{{\\WTwoPicoOrchMean}}{{{pico_w2['t_orch_mean_ms']:.2f}}}",
        f"\\newcommand{{\\WTwoOpenMinOrchMedian}}{{{open_min_w2['t_orch_median_ms']:.2f}}}",
        f"\\newcommand{{\\WTwoOpenMinOrchMean}}{{{open_min_w2['t_orch_mean_ms']:.2f}}}",
        f"\\newcommand{{\\WTwoOrchSpeedup}}{{{round(w2_orch_speedup)}}}",
        f"\\newcommand{{\\WTwoPicoRSS}}{{{pico_w2['rss_peak_mb']:.2f}}}",
        f"\\newcommand{{\\WTwoOpenMinRSS}}{{{open_min_w2['rss_peak_mb']:.2f}}}",
        f"\\newcommand{{\\WTwoRAMReduction}}{{{w2_ram_reduction:.1f}}}",
        f"\\newcommand{{\\WTwoOpenMinJoulePerToken}}{{{_fmt_energy(open_min_w2.get('joules_per_token'))}}}",
        f"\\newcommand{{\\WTwoPicoJoulePerToken}}{{{_fmt_energy(pico_w2.get('joules_per_token'))}}}",
        "",
        f"\\newcommand{{\\PicoInstructionsMeanM}}{{{pico_inst_m:.1f}}}",
        f"\\newcommand{{\\PicoCyclesMeanM}}{{{pico_cyc_m:.1f}}}",
        f"\\newcommand{{\\OpenMinInstructionsMeanM}}{{{open_min_inst_m:.1f}}}",
        f"\\newcommand{{\\OpenMinCyclesMeanM}}{{{open_min_cyc_m:.1f}}}",
        f"\\newcommand{{\\InstructionOverheadRatio}}{{{inst_ratio:.2f}}}",
        f"\\newcommand{{\\CyclesOverheadRatio}}{{{cyc_ratio:.2f}}}",
        "",
        f"\\newcommand{{\\PicoRSSMin}}{{{min(pico_rss_all):.2f}}}",
        f"\\newcommand{{\\PicoRSSMax}}{{{max(pico_rss_all):.2f}}}",
        f"\\newcommand{{\\PicoRSSWThree}}{{{pico_w3['rss_peak_mb']:.2f}}}",
        f"\\newcommand{{\\PicoRSSWFour}}{{{pico_w4['rss_peak_mb']:.2f}}}",
        f"\\newcommand{{\\PicoRSSOverallMean}}{{{float(np.mean(pico_rss_all)):.2f}}}",
        f"\\newcommand{{\\OpenRSSMin}}{{{min(open_rss_all):.2f}}}",
        f"\\newcommand{{\\OpenRSSMax}}{{{max(open_rss_all):.2f}}}",
        f"\\newcommand{{\\OpenRSSOverallMean}}{{{float(np.mean(open_rss_all)):.2f}}}",
        f"\\newcommand{{\\RAMReductionMinRatio}}{{{min(ram_ratios):.2f}}}",
        f"\\newcommand{{\\RAMReductionMaxRatio}}{{{max(ram_ratios):.2f}}}",
        f"\\newcommand{{\\PeakPhysReductionMinRatio}}{{{min(phys_ratios):.2f}}}",
        f"\\newcommand{{\\PeakPhysReductionMaxRatio}}{{{max(phys_ratios):.2f}}}",
        f"\\newcommand{{\\PicoPeakPhysMean}}{{{pico_phys_m:.2f}}}",
        f"\\newcommand{{\\OpenMinPeakPhysMean}}{{{open_min_phys_m:.2f}}}",
        f"\\newcommand{{\\PeakPhysLeanerRatio}}{{{phys_ratio:.2f}}}",
        "",
        f"\\newcommand{{\\WOneOpenMinMean}}{{{open_min_w1['t_task_mean_ms']:.1f}}}",
        f"\\newcommand{{\\WOneOpenFullMean}}{{{open_full_w1['t_task_mean_ms']:.1f}}}",
        f"\\newcommand{{\\WOneOpenMinEnergy}}{{{_fmt_energy(open_min_w1.get('energy_net_mean_j'))}}}",
        f"\\newcommand{{\\WOneOpenFullEnergy}}{{{_fmt_energy(open_full_w1.get('energy_net_mean_j'))}}}",
        f"\\newcommand{{\\WOneEnergyBloatRatio}}{{{_fmt_ratio(open_full_w1.get('energy_net_mean_j'), open_min_w1.get('energy_net_mean_j'))}}}",
        f"\\newcommand{{\\WFourOpenFullEnergy}}{{{_fmt_energy(open_full_w4.get('energy_net_mean_j'))}}}",
        f"\\newcommand{{\\WFourOpenFullEDP}}{{{_fmt_energy(open_full_w4.get('edp_mean_js'))}}}",
        f"\\newcommand{{\\WFourOpenFullMedian}}{{{open_full_w4['t_task_median_ms']:.1f}}}",
        f"\\newcommand{{\\WFourPicoMedian}}{{{pico_w4['t_task_median_ms']:.1f}}}",
        f"\\newcommand{{\\WFourPicoEDP}}{{{_fmt_energy(pico_w4.get('edp_mean_js'))}}}",
        f"\\newcommand{{\\WFourEDPReductionPct}}{{{_fmt_pct(pico_w4.get('edp_mean_js'), open_full_w4.get('edp_mean_js'))}}}",
        f"\\newcommand{{\\WFourCliffsDelta}}{{{cmp_w4['cliffs_delta']:.1f}}}",
        f"\\newcommand{{\\WFourAOneTwo}}{{{cmp_w4['vargha_delaney_a12']:.1f}}}",
        f"\\newcommand{{\\WFourAdjP}}{{{p_w4_str}}}",
        "",
    ]

    with open(macros_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ Generated LaTeX macros: {macros_path}")
    return macros_path


def compute_spearman_correlation_matrix(
    regime_a_path: str | None = None,
    regime_b_path: str | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """
    Computes pairwise Spearman rank correlation matrix (rho and two-tailed p-values)
    across 12 critical systems telemetry dimensions for Regime A (Cold Prefill)
    and Regime B (Realistic KV-Cache Reuse).
    Outputs results/publication_campaign/spearman_correlation_matrix.json
    and results/publication_campaign/tables/table_spearman_correlation.tex.
    """
    if regime_a_path is None:
        regime_a_path = os.path.join(REPO_DIR, "results", "publication_campaign", "raw_trials.jsonl")
    if regime_b_path is None:
        regime_b_path = os.path.join(REPO_DIR, "results", "publication_campaign", "warm_cache_trials.jsonl")
    if output_dir is None:
        output_dir = os.path.join(REPO_DIR, "results", "publication_campaign")

    def load_trials(p: str) -> list[dict]:
        if not os.path.exists(p):
            return []
        with open(p, "r", encoding="utf-8") as f:
            return [
                json.loads(line)
                for line in f
                if line.strip() and not json.loads(line).get("is_warmup", False)
            ]

    recs_a = load_trials(regime_a_path)
    recs_b = load_trials(regime_b_path)

    metric_defs = [
        ("t_task_ms", "Task Latency", "$T_{\\text{task}}$"),
        ("t_neural_ms", "Neural Latency", "$T_{\\text{neural}}$"),
        ("t_orch_ms", "Orch Overhead", "$T_{\\text{orch}}$"),
        ("t_dispatch_ms", "Dispatch Latency", "$T_{\\text{disp}}$"),
        ("t_http_ms", "HTTP Latency", "$T_{\\text{http}}$"),
        ("rss_peak_mb", "Peak RSS", "RSS"),
        ("proc_peak_phys_mb", "Peak Phys RAM", "PhysRAM"),
        ("proc_instructions", "Retired Instructions", "Instr"),
        ("proc_cycles", "CPU Cycles", "Cycles"),
        ("prompt_tokens", "Prompt Tokens", "$N_{\\text{prompt}}$"),
        ("energy_net_above_idle_j", "Net Energy", "$E_{\\text{net}}$"),
        ("edp_js", "Energy-Delay Product", "EDP"),
    ]

    def build_matrix(records: list[dict]):
        matrix = {}
        for m1, name1, sym1 in metric_defs:
            matrix[m1] = {}
            for m2, name2, sym2 in metric_defs:
                # Strict record-level pairwise extraction
                pairs = [(float(r[m1]), float(r[m2])) for r in records if r.get(m1) is not None and r.get(m2) is not None]
                if len(pairs) > 2:
                    vals1 = [p[0] for p in pairs]
                    vals2 = [p[1] for p in pairs]
                    rho, p_val = stats.spearmanr(vals1, vals2)
                    matrix[m1][m2] = {
                        "rho": round(float(rho), 4),
                        "p_value": round(float(p_val), 6),
                        "significant_001": bool(p_val < 0.001),
                    }
                else:
                    matrix[m1][m2] = {"rho": None, "p_value": None, "significant_001": False}
        return matrix

    mat_a = build_matrix(recs_a) if recs_a else {}
    mat_b = build_matrix(recs_b) if recs_b else {}

    # Define analytical non-tautological pairs for publication table (M4, X6)
    analytical_pairs = [
        ("t_task_ms", "prompt_tokens", "$T_{\\text{task}}$ vs $N_{\\text{prompt}}$ (Prompt Token Length)"),
        ("t_task_ms", "energy_net_above_idle_j", "$T_{\\text{task}}$ vs $E_{\\text{net}}$ (Active Package Energy)"),
        ("t_task_ms", "t_orch_ms", "$T_{\\text{task}}$ vs $T_{\\text{orch}}$ (Orchestrator Overhead Share)"),
        ("t_neural_ms", "prompt_tokens", "$T_{\\text{neural}}$ vs $N_{\\text{prompt}}$ (Attention Prefill Duration)"),
        ("energy_net_above_idle_j", "prompt_tokens", "$E_{\\text{net}}$ vs $N_{\\text{prompt}}$ (Prefill Energy Drain)"),
        ("proc_instructions", "proc_cycles", "Retired Instructions vs CPU Cycles"),
        ("proc_instructions", "t_orch_ms", "Retired Instructions vs $T_{\\text{orch}}$"),
        ("proc_instructions", "rss_peak_mb", "Retired Instructions vs Peak RSS"),
        ("proc_peak_phys_mb", "t_orch_ms", "Peak Phys RAM vs $T_{\\text{orch}}$"),
        ("t_dispatch_ms", "t_orch_ms", "$T_{\\text{disp}}$ vs $T_{\\text{orch}}$ (Dispatch Dominance)"),
        ("cond_means", "task_tokens", "Condition Means ($n=20$): $T_{\\text{task}}$ vs $N_{\\text{prompt}}$"),
        ("intra_w2", "orch_instr", "Intra-Workload W2 (Fixed $N_{\\text{prompt}}$): $T_{\\text{orch}}$ vs Instr"),
        ("intra_w3", "disp_task", "Intra-Workload W3 (Vector I/O): $T_{\\text{disp}}$ vs $T_{\\text{task}}$"),
    ]

    def evaluate_pair(records: list[dict], p_type: str, m1: str, m2: str):
        if not records:
            return 0.0, 1.0
        if p_type == "standard":
            pairs = [(float(r[m1]), float(r[m2])) for r in records if r.get(m1) is not None and r.get(m2) is not None]
            if len(pairs) < 3:
                return 0.0, 1.0
            r, p = stats.spearmanr([x[0] for x in pairs], [x[1] for x in pairs])
            return float(r), float(p)
        elif p_type == "cond_means":
            conds = {}
            for r in records:
                k = (r.get("workload"), r.get("agent_key"))
                if k not in conds:
                    conds[k] = {"tasks": [], "tokens": []}
                if r.get("t_task_ms") is not None and r.get("prompt_tokens") is not None:
                    conds[k]["tasks"].append(float(r["t_task_ms"]))
                    conds[k]["tokens"].append(float(r["prompt_tokens"]))
            mean_tasks = [sum(v["tasks"]) / len(v["tasks"]) for v in conds.values() if v["tasks"]]
            mean_tokens = [sum(v["tokens"]) / len(v["tokens"]) for v in conds.values() if v["tokens"]]
            if len(mean_tasks) < 3:
                return 0.0, 1.0
            r, p = stats.spearmanr(mean_tasks, mean_tokens)
            return float(r), float(p)
        elif p_type == "intra_w2":
            w2_recs = [r for r in records if r.get("workload") == "W2"]
            pairs = [(float(r["t_orch_ms"]), float(r["proc_instructions"])) for r in w2_recs if r.get("t_orch_ms") is not None and r.get("proc_instructions") is not None]
            if len(pairs) < 3:
                return 0.0, 1.0
            r, p = stats.spearmanr([x[0] for x in pairs], [x[1] for x in pairs])
            return float(r), float(p)
        elif p_type == "intra_w3":
            w3_recs = [r for r in records if r.get("workload") == "W3"]
            pairs = [(float(r["t_dispatch_ms"]), float(r["t_task_ms"])) for r in w3_recs if r.get("t_dispatch_ms") is not None and r.get("t_task_ms") is not None]
            if len(pairs) < 3:
                return 0.0, 1.0
            r, p = stats.spearmanr([x[0] for x in pairs], [x[1] for x in pairs])
            return float(r), float(p)
        return 0.0, 1.0

    table_data = []
    p_vals_a = []
    p_vals_b = []

    for item in analytical_pairs:
        k1, k2, label = item
        if k1 == "cond_means":
            ra, pa = evaluate_pair(recs_a, "cond_means", "", "")
            rb, pb = evaluate_pair(recs_b, "cond_means", "", "")
        elif k1 == "intra_w2":
            ra, pa = evaluate_pair(recs_a, "intra_w2", "", "")
            rb, pb = evaluate_pair(recs_b, "intra_w2", "", "")
        elif k1 == "intra_w3":
            ra, pa = evaluate_pair(recs_a, "intra_w3", "", "")
            rb, pb = evaluate_pair(recs_b, "intra_w3", "", "")
        else:
            ra, pa = evaluate_pair(recs_a, "standard", k1, k2)
            rb, pb = evaluate_pair(recs_b, "standard", k1, k2)

        table_data.append((label, ra, pa, rb, pb))
        p_vals_a.append(pa)
        p_vals_b.append(pb)

    adj_p_a = holm_bonferroni_adjust(p_vals_a)
    adj_p_b = holm_bonferroni_adjust(p_vals_b)

    reported_pairs = []
    for idx, (label, ra, pa, rb, pb) in enumerate(table_data):
        reported_pairs.append({
            "interaction": label,
            "regime_a_cold": {
                "rho": round(float(ra), 4),
                "p_raw": float(pa),
                "p_adj_holm": float(adj_p_a[idx]),
            },
            "regime_b_warm": {
                "rho": round(float(rb), 4),
                "p_raw": float(pb),
                "p_adj_holm": float(adj_p_b[idx]),
            },
        })

    out_json_path = os.path.join(output_dir, "spearman_correlation_matrix.json")
    full_output = {
        "description": "Pairwise Spearman Rank Correlation Matrix across 12 Systems Dimensions with Holm-Bonferroni Adjustment",
        "n_evaluations_regime_a": len(recs_a),
        "n_evaluations_regime_b": len(recs_b),
        "metrics": [m[0] for m in metric_defs],
        "metric_labels": {m[0]: m[1] for m in metric_defs},
        "table_reported_pairs_with_holm": reported_pairs,
        "regime_a_cold_prefill": mat_a,
        "regime_b_warm_kv_cache": mat_b,
    }
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)
    print(f"✅ Generated Spearman correlation matrix JSON: {out_json_path}")

    # Generate LaTeX Table
    tex_path = os.path.join(output_dir, "tables", "table_spearman_correlation.tex")
    latex = r"""\begin{table*}[t]
\centering
\caption{Non-Parametric Spearman Rank Correlation Matrix ($\rho$) across Critical Systems Telemetry Dimensions on Apple Silicon M4. Contrasts Regime A (Cold Prefill, $n=600$) and Regime B (Warm KV-Cache Reuse, $n=600$). Tautological identities ($T_{\text{task}}$ vs $T_{\text{neural}}$, $T_{\text{task}}$ vs EDP, RSS vs PhysRAM) are excluded in favor of non-trivial architectural interactions, condition-level aggregation ($n=20$), and intra-workload controls. $p$-values are adjusted for family-wise error rate control via step-down Holm-Bonferroni: $^{***}p_{\text{adj}} < 0.001$, $^{**}p_{\text{adj}} < 0.01$, $^{*}p_{\text{adj}} < 0.05$.}
\label{tab:spearman_correlation}
\small
\begin{tabular}{l r r r r}
\hline
\textbf{Systems Interaction} & \textbf{Regime A ($\rho_{\text{cold}}$)} & \textbf{Holm-adj. $p$ (A)} & \textbf{Regime B ($\rho_{\text{warm}}$)} & \textbf{Holm-adj. $p$ (B)} \\
\hline
"""

    def fmt_cell(r, p_adj):
        stars = "***" if p_adj < 0.001 else ("**" if p_adj < 0.01 else ("*" if p_adj < 0.05 else ""))
        p_str = "$< 10^{-5}$" if p_adj < 0.00001 else f"{p_adj:.4f}"
        return f"{r:+.3f}$^{{{stars}}}$", p_str

    for idx, (label, ra, pa, rb, pb) in enumerate(table_data):
        str_ra, str_pa = fmt_cell(ra, adj_p_a[idx])
        str_rb, str_pb = fmt_cell(rb, adj_p_b[idx])
        latex += f"{label} & {str_ra} & {str_pa} & {str_rb} & {str_pb} \\\\\n"

    latex += r"""\hline
\multicolumn{5}{l}{\footnotesize Non-parametric Spearman rank correlation with step-down Holm-Bonferroni family-wise error adjustment ($1{,}200$ total physical evaluations).} \\
\hline
\end{tabular}
\end{table*}
"""
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex)
    print(f"✅ Generated Spearman correlation LaTeX table: {tex_path}")
    return full_output


def compute_pca_variance_decomposition(
    regime_a_path: str | None = None,
    regime_b_path: str | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """
    Computes Principal Component Analysis (PCA) variance decomposition and factor loadings
    via Singular Value Decomposition (np.linalg.svd) on Z-score standardized observations
    across evaluated agent runtimes (picoclaw, openclaw_minimal, openclaw_full, python_native).

    Outputs results/publication_campaign/pca_variance_decomposition.json
    and results/publication_campaign/tables/table_pca_loadings.tex.
    """
    if regime_a_path is None:
        regime_a_path = os.path.join(REPO_DIR, "results", "publication_campaign", "raw_trials.jsonl")
    if regime_b_path is None:
        regime_b_path = os.path.join(REPO_DIR, "results", "publication_campaign", "warm_cache_trials.jsonl")
    if output_dir is None:
        output_dir = os.path.join(REPO_DIR, "results", "publication_campaign")

    target_agents = ["picoclaw", "openclaw_minimal", "openclaw_full", "python_native"]
    metric_defs = [
        ("prompt_tokens", "Prompt Tokens", "$N_{\\text{prompt}}$"),
        ("t_neural_ms", "Neural Latency", "$T_{\\text{neural}}$"),
        ("t_task_ms", "Task Latency", "$T_{\\text{task}}$"),
        ("energy_net_above_idle_j", "Net Energy", "$E_{\\text{net}}$"),
        ("edp_js", "Energy-Delay Product", "EDP"),
        ("t_orch_ms", "Orchestrator Overhead", "$T_{\\text{orch}}$"),
        ("t_http_ms", "HTTP Latency", "$T_{\\text{http}}$"),
        ("t_dispatch_ms", "Dispatch Latency", "$T_{\\text{disp}}$"),
        ("rss_peak_mb", "Peak RSS", "RSS"),
        ("proc_peak_phys_mb", "Peak Phys RAM", "PhysRAM"),
        ("proc_instructions", "Retired Instructions", "Instr"),
        ("proc_cycles", "CPU Cycles", "Cycles"),
    ]
    metrics = [m[0] for m in metric_defs]

    def load_clean_trials(p: str) -> list[dict]:
        if not os.path.exists(p):
            return []
        with open(p, "r", encoding="utf-8") as f:
            records = []
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                if d.get("is_warmup", False):
                    continue
                if d.get("agent_key") not in target_agents:
                    continue
                if any(d.get(m) is None for m in metrics):
                    continue
                records.append(d)
            return records

    def run_pca_on_records(records: list[dict]):
        if not records or len(records) < len(metrics):
            return {}
        n = len(records)
        p = len(metrics)
        X = np.array([[float(r[m]) for m in metrics] for r in records], dtype=np.float64)
        mean = np.mean(X, axis=0)
        std = np.std(X, axis=0, ddof=1)
        std[std == 0.0] = 1.0
        Z = (X - mean) / std

        U, S, Vt = np.linalg.svd(Z, full_matrices=False)
        V = Vt.T  # shape (p, p), columns are principal axes

        # Standardize signs for deterministic, intuitive presentation:
        # PC1: prompt_tokens positive
        if V[0, 0] < 0:
            V[:, 0] = -V[:, 0]
        # PC2: proc_instructions positive
        if V[10, 1] < 0:
            V[:, 1] = -V[:, 1]
        # PC3: t_dispatch_ms positive
        if V[7, 2] < 0:
            V[:, 2] = -V[:, 2]

        lambdas = (S ** 2) / (n - 1)
        total_var = float(np.sum(lambdas))
        var_exp_ratio = lambdas / total_var
        var_exp_pct = var_exp_ratio * 100.0
        cum_var_pct = np.cumsum(var_exp_pct)

        components = []
        for k in range(p):
            c_dict = {
                "component": f"PC{k+1}",
                "eigenvalue": round(float(lambdas[k]), 4),
                "explained_variance_pct": round(float(var_exp_pct[k]), 2),
                "cumulative_variance_pct": round(float(cum_var_pct[k]), 2),
                "loadings": {},
                "contributions_pct": {},
            }
            for j, m in enumerate(metrics):
                load_val = float(V[j, k])
                contrib_val = float((V[j, k] ** 2) * 100.0)
                c_dict["loadings"][m] = round(load_val, 4)
                c_dict["contributions_pct"][m] = round(contrib_val, 2)
            components.append(c_dict)

        return {
            "n_trials": n,
            "n_variables": p,
            "eigenvalues": [round(float(x), 4) for x in lambdas],
            "explained_variance_pct": [round(float(x), 2) for x in var_exp_pct],
            "cumulative_variance_pct": [round(float(x), 2) for x in cum_var_pct],
            "components": components,
            "orthogonality_max_error": float(np.max(np.abs(np.dot(V.T, V) - np.eye(p)))),
            "sum_explained_variance_pct": float(np.sum(var_exp_pct)),
        }

    recs_a = load_clean_trials(regime_a_path)
    recs_b = load_clean_trials(regime_b_path)

    pca_a = run_pca_on_records(recs_a)
    pca_b = run_pca_on_records(recs_b)

    def run_within_workload_pca(records: list[dict]):
        if not records or len(records) < len(metrics):
            return {}
        workload_groups = {}
        for r in records:
            w = r.get("workload")
            if w not in workload_groups:
                workload_groups[w] = []
            workload_groups[w].append(r)

        z_blocks = []
        for w, w_recs in sorted(workload_groups.items()):
            X_w = np.array([[float(r[m]) for m in metrics] for r in w_recs], dtype=np.float64)
            mean_w = np.mean(X_w, axis=0)
            std_w = np.std(X_w, axis=0, ddof=1)
            std_w[std_w == 0.0] = 1.0
            Z_w = (X_w - mean_w) / std_w
            z_blocks.append(Z_w)

        Z_within = np.vstack(z_blocks)
        n = Z_within.shape[0]
        p = len(metrics)

        U, S, Vt = np.linalg.svd(Z_within, full_matrices=False)
        V = Vt.T

        if V[10, 0] < 0:
            V[:, 0] = -V[:, 0]
        if V[7, 1] < 0:
            V[:, 1] = -V[:, 1]
        if V[8, 2] < 0:
            V[:, 2] = -V[:, 2]

        lambdas = (S ** 2) / (n - 1)
        total_var = float(np.sum(lambdas))
        var_exp_pct = (lambdas / total_var) * 100.0
        cum_var_pct = np.cumsum(var_exp_pct)

        components = []
        for k in range(min(p, 5)):
            c_dict = {
                "component": f"Within_PC{k+1}",
                "eigenvalue": round(float(lambdas[k]), 4),
                "explained_variance_pct": round(float(var_exp_pct[k]), 2),
                "cumulative_variance_pct": round(float(cum_var_pct[k]), 2),
                "loadings": {},
                "contributions_pct": {},
            }
            for j, m in enumerate(metrics):
                c_dict["loadings"][m] = round(float(V[j, k]), 4)
                c_dict["contributions_pct"][m] = round(float((V[j, k] ** 2) * 100.0), 2)
            components.append(c_dict)

        return {
            "description": "Within-workload Z-score normalized PCA removing cross-tier scaling effects",
            "n_trials": n,
            "eigenvalues": [round(float(x), 4) for x in lambdas[:5]],
            "explained_variance_pct": [round(float(x), 2) for x in var_exp_pct[:5]],
            "cumulative_variance_pct": [round(float(x), 2) for x in cum_var_pct[:5]],
            "components": components,
        }

    within_pca_a = run_within_workload_pca(recs_a)
    within_pca_b = run_within_workload_pca(recs_b)

    out_json_path = os.path.join(output_dir, "pca_variance_decomposition.json")
    full_output = {
        "description": "Principal Component Analysis (PCA) Variance Decomposition on Apple Silicon M4 across 12 Telemetry Dimensions",
        "method": "SVD on Z-score standardized observation matrix Z = (X - mu) / sigma",
        "evaluated_agents": target_agents,
        "n_trials_explanation": "Evaluates N=480 trials per regime across 4 agent runtimes. The neural_baseline (120 trials) is omitted from PCA due to structural zeros in host orchestration metrics (T_orch=0, RSS=0, Instructions=0, Cycles=0).",
        "metrics": metrics,
        "regime_a_cold_prefill": pca_a,
        "regime_b_warm_kv_cache": pca_b,
        "within_workload_normalized_pca": {
            "regime_a_cold_prefill": within_pca_a,
            "regime_b_warm_kv_cache": within_pca_b,
        },
    }
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)
    print(f"✅ Generated PCA variance decomposition JSON: {out_json_path}")

    # Generate LaTeX Table
    tex_path = os.path.join(output_dir, "tables", "table_pca_loadings.tex")
    latex = r"""\begin{table*}[t]
\centering
\caption{Principal Component Analysis (PCA) Variance Decomposition and Factor Loadings across Telemetry Dimensions on Apple Silicon M4. Evaluates $N=480$ trials per regime across compiled and interpreted agent runtimes (\texttt{picoclaw}, \texttt{openclaw\_minimal}, \texttt{openclaw\_full}, \texttt{python\_native}). $\text{PC}_1$ captures prompt prefill scale and energy dissipation; $\text{PC}_2$ isolates host runtime microarchitectural footprint (RAM, CPU cycles, instructions); $\text{PC}_3$ isolates tool dispatch and I/O execution. Values in parentheses denote relative variable contribution (\%).}
\label{tab:pca_loadings}
\small
\begin{tabular}{l c r r r r r r}
\hline
 & & \multicolumn{3}{c}{\textbf{Regime A: Cold Prefill}} & \multicolumn{3}{c}{\textbf{Regime B: Warm KV-Cache}} \\
\cmidrule(lr){3-5} \cmidrule(lr){6-8}
\textbf{Systems Dimension} & \textbf{Symbol} & \textbf{$\text{PC}_1$ (Load / \%)} & \textbf{$\text{PC}_2$ (Load / \%)} & \textbf{$\text{PC}_3$ (Load / \%)} & \textbf{$\text{PC}_1$ (Load / \%)} & \textbf{$\text{PC}_2$ (Load / \%)} & \textbf{$\text{PC}_3$ (Load / \%)} \\
\hline
"""

    def get_comp(pca_res, idx):
        if not pca_res or "components" not in pca_res or len(pca_res["components"]) <= idx:
            return None
        return pca_res["components"][idx]

    c1_a = get_comp(pca_a, 0)
    c2_a = get_comp(pca_a, 1)
    c3_a = get_comp(pca_a, 2)
    c1_b = get_comp(pca_b, 0)
    c2_b = get_comp(pca_b, 1)
    c3_b = get_comp(pca_b, 2)

    def fmt_cell(comp, m):
        if not comp:
            return "N/A"
        loading_val = comp["loadings"].get(m, 0.0)
        c = comp["contributions_pct"].get(m, 0.0)
        return f"{loading_val:+.3f} ({c:4.1f}\\%)"

    for m, name, sym in metric_defs:
        row_str = f"{name} & {sym} & "
        row_str += f"{fmt_cell(c1_a, m)} & {fmt_cell(c2_a, m)} & {fmt_cell(c3_a, m)} & "
        row_str += f"{fmt_cell(c1_b, m)} & {fmt_cell(c2_b, m)} & {fmt_cell(c3_b, m)} \\\\\n"
        latex += row_str

    latex += r"""\hline
"""
    # Summary rows
    def fmt_stat(pca_res, key, fmt_spec):
        if not pca_res or key not in pca_res:
            return ["N/A", "N/A", "N/A"]
        vals = pca_res[key][:3]
        return [fmt_spec.format(v) for v in vals]

    ev_a = fmt_stat(pca_a, "eigenvalues", "{:.2f}")
    ev_b = fmt_stat(pca_b, "eigenvalues", "{:.2f}")
    latex += f"\\multicolumn{{2}}{{l}}{{\\textbf{{Eigenvalue ($\\lambda_k$)}}}} & {ev_a[0]} & {ev_a[1]} & {ev_a[2]} & {ev_b[0]} & {ev_b[1]} & {ev_b[2]} \\\\\n"

    var_a = fmt_stat(pca_a, "explained_variance_pct", "{:.1f}\\%")
    var_b = fmt_stat(pca_b, "explained_variance_pct", "{:.1f}\\%")
    latex += f"\\multicolumn{{2}}{{l}}{{\\textbf{{Explained Variance [\\%]}}}} & {var_a[0]} & {var_a[1]} & {var_a[2]} & {var_b[0]} & {var_b[1]} & {var_b[2]} \\\\\n"

    cum_a = fmt_stat(pca_a, "cumulative_variance_pct", "{:.1f}\\%")
    cum_b = fmt_stat(pca_b, "cumulative_variance_pct", "{:.1f}\\%")
    latex += f"\\multicolumn{{2}}{{l}}{{\\textbf{{Cumulative Variance [\\%]}}}} & {cum_a[0]} & {cum_a[1]} & {cum_a[2]} & {cum_b[0]} & {cum_b[1]} & {cum_b[2]} \\\\\n"

    latex += r"""\hline
\multicolumn{8}{l}{\footnotesize Principal component analysis via SVD on Z-score standardized observations ($N=480$ per regime across 4 agent runtimes).} \\
\multicolumn{8}{l}{\footnotesize Values denote factor loadings (eigenvector entries) and relative contribution percentages: $\text{contrib}_j = v_{jk}^2 \times 100\%$.} \\
\hline
\end{tabular}
\end{table*}
"""
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex)
    print(f"✅ Generated PCA loadings LaTeX table: {tex_path}")
    return full_output


if __name__ == "__main__":
    in_p = sys.argv[1] if len(sys.argv) > 1 else None
    out_d = sys.argv[2] if len(sys.argv) > 2 else None
    analyze_publication_campaign(in_p, out_d)
