"""
Statistical Analysis and Paper-Ready Tables Generator
Análise Estatística e Gerador de Tabelas Prontas para o Artigo Científico

Author / Autor: Rafael Paniccia Cassetta (UFABC)
Language / Idioma: Bilingual (PT-BR & EN-US comments, English code)
"""

import json
import os
from typing import Any, Dict, List

import numpy as np
from scipy import stats

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cliffs_delta(lst1: List[float], lst2: List[float]) -> float:
    """
    Compute Cliff's Delta non-parametric effect size d in [-1, 1].

    Sign Convention / Convenção de Sinal:
    - d = +1.0: lst1 is strictly greater than lst2 in all pairwise comparisons.
    - d = -1.0: lst1 is strictly smaller than lst2 in all pairwise comparisons
      (e.g., PicoClaw < OpenClaw in 100% of paired trials for latency, EDP, and RAM).
    - d = 0.0: No stochastic dominance.
    Thresholds: |d| < 0.147 (negligible), < 0.33 (small), < 0.474 (medium), >= 0.474 (large)
    (Cliff, 1993; Romano et al., 2006).
    """
    n1, n2 = len(lst1), len(lst2)
    if n1 == 0 or n2 == 0:
        return 0.0
    more = sum(1 for x in lst1 for y in lst2 if x > y)
    less = sum(1 for x in lst1 for y in lst2 if x < y)
    return (more - less) / (n1 * n2)


def vargha_delaney_a12(lst1: List[float], lst2: List[float]) -> float:
    """
    Compute Vargha-Delaney A12 effect size statistic in [0, 1].

    Direction Convention / Convenção de Direção:
    - A12 = P(X > Y) + 0.5 * P(X == Y) = (d + 1) / 2
    - A12 = 0.0: X (PicoClaw) is strictly smaller than Y (OpenClaw) across all trials.
    - A12 = 0.5: Stochastic equality between distributions.
    - A12 = 1.0: X is strictly greater than Y across all trials.
    (Vargha & Delaney, 2000).
    """
    d = cliffs_delta(lst1, lst2)
    return (d + 1.0) / 2.0


def garwood_poisson_interval(k: int, confidence: float = 0.95):
    """Compute exact Garwood (1936) Poisson fiducial confidence bounds."""
    alpha = 1.0 - confidence
    if k == 0:
        lower = 0.0
    else:
        lower = 0.5 * stats.chi2.ppf(alpha / 2.0, 2 * k)
    upper = 0.5 * stats.chi2.ppf(1.0 - alpha / 2.0, 2 * (k + 1))
    return float(lower), float(upper)


def analyze_publication_campaign():
    input_path = os.path.join(REPO_DIR, "results", "publication_campaign", "raw_trials.jsonl")
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found. Please run benchmark/run_unified_benchmark.py first.")
        return

    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print(f"Loaded {len(records)} trial records.")

    # Group by (agent_key, workload)
    groups: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for r in records:
        ak = r["agent_key"]
        w = r["workload"]
        if ak not in groups:
            groups[ak] = {}
        if w not in groups[ak]:
            groups[ak][w] = []
        groups[ak][w].append(r)

    summary_stats: Dict[str, Any] = {}
    csv_rows = [
        "agent,workload,t_task_mean_ms,t_task_std_ms,t_task_p50_ms,t_task_p95_ms,t_orch_mean_ms,rss_peak_mb,energy_mean_j,edp_mean_js,joules_per_token"
    ]

    for ak, w_dict in groups.items():
        summary_stats[ak] = {}
        for w, items in w_dict.items():
            t_tasks = [x["t_task_ms"] for x in items]
            t_orchs = [x["t_orch_ms"] for x in items]
            energies = [x["energy_joules"] for x in items]
            edps = [x["edp_js"] for x in items]
            rss_peaks = [x["rss_peak_mb"] for x in items]
            j_tokens = [x["joules_per_token"] for x in items]

            mean_t = float(np.mean(t_tasks))
            std_t = float(np.std(t_tasks, ddof=1)) if len(t_tasks) > 1 else 0.0
            p50_t = float(np.percentile(t_tasks, 50))
            p95_t = float(np.percentile(t_tasks, 95))
            mean_orch = float(np.mean(t_orchs))
            mean_rss = float(np.mean(rss_peaks))
            mean_e = float(np.mean(energies))
            mean_edp = float(np.mean(edps))
            mean_jtok = float(np.mean(j_tokens))

            summary_stats[ak][w] = {
                "t_task_mean_ms": mean_t,
                "t_task_std_ms": std_t,
                "t_task_p50_ms": p50_t,
                "t_task_p95_ms": p95_t,
                "t_orch_mean_ms": mean_orch,
                "rss_peak_mb": mean_rss,
                "energy_mean_j": mean_e,
                "edp_mean_js": mean_edp,
                "joules_per_token": mean_jtok,
                "sample_count": len(t_tasks)
            }

            csv_rows.append(
                f"{ak},{w},{mean_t:.2f},{std_t:.2f},{p50_t:.2f},{p95_t:.2f},{mean_orch:.3f},{mean_rss:.2f},{mean_e:.3f},{mean_edp:.3f},{mean_jtok:.4f}"
            )

    # Statistical comparisons (Mann-Whitney U & Cliff's Delta)
    comparisons = {}
    pairs = [
        ("picoclaw", "openclaw_minimal", "PicoClaw_vs_OpenClawMinimal"),
        ("picoclaw", "openclaw_full", "PicoClaw_vs_OpenClawFull"),
        ("openclaw_minimal", "openclaw_full", "OpenClawAblation_Minimal_vs_Full"),
        ("neural_baseline", "picoclaw", "NeuralBaseline_vs_PicoClaw")
    ]

    for a1, a2, label in pairs:
        comparisons[label] = {}
        for w in ["W1", "W2", "W3", "W4"]:
            vals1 = [x["t_task_ms"] for x in groups.get(a1, {}).get(w, [])]
            vals2 = [x["t_task_ms"] for x in groups.get(a2, {}).get(w, [])]
            if len(vals1) > 0 and len(vals2) > 0:
                u_stat, p_val = stats.mannwhitneyu(vals1, vals2, alternative="two-sided")
                d = cliffs_delta(vals1, vals2)
                a12 = vargha_delaney_a12(vals1, vals2)
                comparisons[label][w] = {
                    "u_statistic": float(u_stat),
                    "p_value": float(p_val),
                    "cliffs_delta": float(d),
                    "vargha_delaney_a12": float(a12),
                    "significant_alpha_0_05": bool(p_val < 0.05)
                }

    # Save JSON files
    stats_out = os.path.join(REPO_DIR, "results", "publication_campaign", "summary_statistics.json")
    with open(stats_out, "w", encoding="utf-8") as f:
        json.dump(summary_stats, f, indent=2)

    tests_out = os.path.join(REPO_DIR, "results", "publication_campaign", "statistical_tests.json")
    with open(tests_out, "w", encoding="utf-8") as f:
        json.dump(comparisons, f, indent=2)

    # Save CSV
    csv_out = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "metrics_summary.csv")
    with open(csv_out, "w", encoding="utf-8") as f:
        f.write("\n".join(csv_rows) + "\n")

    # Generate LaTeX Table
    latex_table = r"""\begin{table*}[t]
\centering
\caption{Empirical Performance Evaluation and Ablation Matrix on Apple Silicon M4 (Mean $\pm$ Std. Dev.)}
\label{tab:evaluation_ablation_m4}
\small
\begin{tabular}{l l r r r r r}
\hline
\textbf{Workload Tier} & \textbf{Configuration} & \textbf{Task Time (ms)} & \textbf{Orch. Delay (ms)} & \textbf{Peak RAM (MB)} & \textbf{Energy (J)} & \textbf{EDP (J$\cdot$s)} \\
\hline
"""
    for w in ["W1", "W2", "W3", "W4"]:
        for ak, label in [
            ("neural_baseline", "Neural Baseline (Direct)"),
            ("picoclaw", "PicoClaw (Go Native)"),
            ("openclaw_minimal", "OpenClaw (Node.js Minimal)"),
            ("openclaw_full", "OpenClaw (Node.js Full Ablation)"),
        ]:
            entry = summary_stats.get(ak, {}).get(w, {})
            if entry:
                t_m = entry["t_task_mean_ms"]
                t_s = entry["t_task_std_ms"]
                o_m = entry["t_orch_mean_ms"]
                ram = entry["rss_peak_mb"]
                e = entry["energy_mean_j"]
                edp = entry["edp_mean_js"]
                latex_table += f"{w} & {label} & {t_m:.1f} $\\pm$ {t_s:.1f} & {o_m:.3f} & {ram:.1f} & {e:.2f} & {edp:.3f} \\\\\n"
        latex_table += r"\hline" + "\n"

    latex_table += r"""\end{tabular}
\end{table*}
"""

    tex_out = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "table_journal_ablation.tex")
    with open(tex_out, "w", encoding="utf-8") as f:
        f.write(latex_table)

    print(f"✅ Generated summary JSON: {stats_out}")
    print(f"✅ Generated statistical tests JSON: {tests_out}")
    print(f"✅ Generated CSV table: {csv_out}")
    print(f"✅ Generated LaTeX table: {tex_out}")


if __name__ == "__main__":
    analyze_publication_campaign()
