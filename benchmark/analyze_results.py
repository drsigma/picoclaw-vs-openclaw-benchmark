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
            rss_peaks = [float(x["rss_peak_mb"]) for x in items if x.get("rss_peak_mb") is not None]

            # Collect energy metrics (handling None for unprivileged runs)
            energies_total = [float(x["energy_total_j"]) for x in items if x.get("energy_total_j") is not None]
            energies_net = [float(x["energy_net_above_idle_j"]) for x in items if x.get("energy_net_above_idle_j") is not None]
            edps = [float(x["edp_js"]) for x in items if x.get("edp_js") is not None]
            j_tokens = [float(x["joules_per_token"]) for x in items if x.get("joules_per_token") is not None]

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
            mean_rss = float(np.mean(rss_peaks)) if rss_peaks else 0.0

            mean_e_total = float(np.mean(energies_total)) if energies_total else None
            mean_e_net = float(np.mean(energies_net)) if energies_net else None
            mean_edp = float(np.mean(edps)) if edps else None
            mean_jtok = float(np.mean(j_tokens)) if j_tokens else None

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
                "rss_peak_mb": round(mean_rss, 2),
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

    # Generate LaTeX Table
    latex_table = r"""\begin{table*}[t]
\centering
\caption{Empirical Performance Evaluation and Runtime Ablation Matrix (Median, IQR, and Mean $\pm$ SD). Note: 0.0 MB Peak RAM for Neural Baseline indicates zero orchestrator process footprint (direct HTTP pass-through), excluding the unified memory allocation (UMA) of the background \texttt{llama-server} daemon. Energy values are computed via composite trapezoidal integration from Apple Silicon SMC hardware telemetry.}
\label{tab:evaluation_ablation_m4}
\small
\begin{tabular}{l l r r r r r}
\hline
\textbf{Workload} & \textbf{Configuration} & \textbf{Median (IQR) [ms]} & \textbf{Mean $\pm$ SD [ms]} & \textbf{Orch Delay [ms]} & \textbf{Peak RAM [MB]} & \textbf{Energy [J]} \\
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
                p50 = entry["t_task_median_ms"]
                iqr = entry["t_task_iqr_ms"]
                t_m = entry["t_task_mean_ms"]
                t_s = entry["t_task_std_ms"]
                o_m = entry["t_orch_mean_ms"]
                ram = entry["rss_peak_mb"]
                e_val = entry.get("energy_total_mean_j")
                e_str = f"{e_val:.2f}" if e_val is not None else "N/A"
                latex_table += f"{w} & {label} & {p50:.1f} ({iqr:.1f}) & {t_m:.1f} $\\pm$ {t_s:.1f} & {o_m:.3f} & {ram:.1f} & {e_str} \\\\\n"
        latex_table += r"\hline" + "\n"

    latex_table += r"""\end{tabular}
\end{table*}
"""

    tex_out = os.path.join(output_dir, "tables", "table_journal_ablation.tex")
    with open(tex_out, "w", encoding="utf-8") as f:
        f.write(latex_table)

    print(f"✅ Generated summary JSON: {stats_out}")
    print(f"✅ Generated statistical tests JSON: {tests_out}")
    print(f"✅ Generated CSV table: {csv_out}")
    print(f"✅ Generated LaTeX table: {tex_out}")


if __name__ == "__main__":
    in_p = sys.argv[1] if len(sys.argv) > 1 else None
    out_d = sys.argv[2] if len(sys.argv) > 2 else None
    analyze_publication_campaign(in_p, out_d)
