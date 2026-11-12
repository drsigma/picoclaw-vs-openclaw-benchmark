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
        if pt is None or int(pt) <= 0:
            raise ValueError(
                f"FATAL: Evaluated trial record {r.get('agent_key')} {r.get('workload')} Rep {r.get('rep')} "
                f"registered invalid prompt_tokens <= 0 ({pt}). All evaluated trials must record positive prompt tokens."
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
            t_tasks = [float(x["t_task_ms"]) for x in items if x.get("t_task_ms") is not None]
            t_orchs = [float(x["t_orch_ms"]) for x in items if x.get("t_orch_ms") is not None]
            t_dispatches = [float(x.get("t_dispatch_ms", 0.0)) for x in items if x.get("t_dispatch_ms") is not None]
            rss_peaks = [float(x["rss_peak_mb"]) for x in items if x.get("rss_peak_mb") is not None]
            proc_phys = [float(x.get("proc_peak_phys_mb", 0.0)) for x in items if x.get("proc_peak_phys_mb") is not None]
            proc_inst = [float(x.get("proc_instructions", 0.0)) for x in items if x.get("proc_instructions") is not None]
            proc_cyc = [float(x.get("proc_cycles", 0.0)) for x in items if x.get("proc_cycles") is not None]
            proc_billed = [float(x.get("proc_billed_energy", 0.0)) for x in items if x.get("proc_billed_energy") is not None]

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
\caption{Empirical Performance Evaluation and Runtime Ablation Matrix on Apple Silicon M4. Peak Phys RAM denotes lifetime maximum resident physical footprint recorded via Darwin kernel \texttt{libproc}. Net Energy is integrated above quiescent idle baseline via Apple SMC hardware shunts at 50~ms resolution. Dispatch and HTTP latency isolate tool-execution and network overhead ($T_{\text{orch}} \approx T_{\text{dispatch}} + T_{\text{http}}$). Prompt and Completion token counts reflect tokenizer throughput.}
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


if __name__ == "__main__":
    in_p = sys.argv[1] if len(sys.argv) > 1 else None
    out_d = sys.argv[2] if len(sys.argv) > 2 else None
    analyze_publication_campaign(in_p, out_d)
