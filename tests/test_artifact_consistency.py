"""
Automated Cross-Artifact Numerical Consistency Verification Test
Teste de Verificação Automatizada de Consistência Numérica entre Artefatos

Author / Autor: Rafael Paniccia Cassetta (UFABC)
Language / Idioma: Bilingual (PT-BR & EN-US comments, English code)
"""

import csv
import json
import os

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_summary_statistics_matches_csv_table():
    """Verify metrics in summary_statistics.json match metrics_summary.csv exactly across all 20 cells."""
    json_path = os.path.join(REPO_DIR, "results", "publication_campaign", "summary_statistics.json")
    csv_path = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "metrics_summary.csv")

    assert os.path.exists(json_path), f"Missing {json_path}"
    assert os.path.exists(csv_path), f"Missing {csv_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        stats_data = json.load(f)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        csv_rows = list(reader)

    # 5 agents x 4 workloads = 20 rows
    assert len(csv_rows) == 20, f"Expected 20 rows (5 agents x 4 workloads), got {len(csv_rows)}"

    for row in csv_rows:
        ak = row["agent"]
        w = row["workload"]
        assert ak in stats_data, f"Agent {ak} missing from summary JSON"
        assert w in stats_data[ak], f"Workload {w} missing from agent {ak} in summary JSON"
        expected = stats_data[ak][w]

        # Verify numerical consistency between CSV and JSON
        assert abs(float(row["t_task_median_ms"]) - expected["t_task_median_ms"]) < 1e-2
        assert abs(float(row["rss_peak_mb"]) - expected["rss_peak_mb"]) < 1e-2


def test_latex_table_contains_summary_data():
    """Verify table_journal_ablation.tex reflects all 4 workloads and registered agent configurations."""
    tex_path = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "table_journal_ablation.tex")
    assert os.path.exists(tex_path), f"Missing {tex_path}"

    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "W1 & PicoClaw (Go Native)" in content
    assert "W4 & PicoClaw (Go Native)" in content
    assert "W4 & OpenClaw (Node.js Full 54-Tool)" in content
    assert "W4 & PythonNative (CPython Reference)" in content
    assert "Neural Baseline" in content


def test_figures_exist_and_non_empty():
    """Verify all 6 publication figures are present and non-empty in figures/."""
    figures_dir = os.path.join(REPO_DIR, "figures")
    expected_figures = [
        "fig1_architecture_topology.png",
        "fig2_exp1_cold_start_rss.png",
        "fig3_exp2_latency_overhead.png",
        "fig4_exp3_energy_edp.png",
        "fig5_exp4_tools_and_bloat.png",
        "fig6_pmc_hardware_counters.png",
    ]
    for fig_name in expected_figures:
        fig_path = os.path.join(figures_dir, fig_name)
        assert os.path.exists(fig_path), f"Figure {fig_name} missing from {figures_dir}"
        assert os.path.getsize(fig_path) > 1000, f"Figure {fig_name} is too small or empty"


def test_macros_empirical_consistent_with_summary_statistics():
    """Verify that macros_empirical.tex exists and matches summary_statistics.json."""
    macros_path = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "macros_empirical.tex")
    summary_path = os.path.join(REPO_DIR, "results", "publication_campaign", "summary_statistics.json")

    assert os.path.exists(macros_path), f"Missing {macros_path}"
    assert os.path.exists(summary_path), f"Missing {summary_path}"

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    with open(macros_path, "r", encoding="utf-8") as f:
        macros_content = f.read()

    # Check that key values in summary appear in macros
    w3_pico_median = f"{summary['picoclaw']['W3']['t_task_median_ms']:.1f}"
    assert f"\\newcommand{{\\WThreePicoMedian}}{{{w3_pico_median}}}" in macros_content

    w2_open_median = f"{summary['openclaw_minimal']['W2']['t_task_median_ms']:.1f}"
    assert f"\\newcommand{{\\WTwoOpenMinMedian}}{{{w2_open_median}}}" in macros_content

