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
    """Verify metrics in summary_statistics.json match metrics_summary.csv exactly."""
    json_path = os.path.join(REPO_DIR, "results", "publication_campaign", "summary_statistics.json")
    csv_path = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "metrics_summary.csv")

    assert os.path.exists(json_path), f"Missing {json_path}"
    assert os.path.exists(csv_path), f"Missing {csv_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        stats_data = json.load(f)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        csv_rows = list(reader)

    assert len(csv_rows) == 16, f"Expected 16 rows (4 agents x 4 workloads), got {len(csv_rows)}"

    for row in csv_rows:
        ak = row["agent"]
        w = row["workload"]
        expected = stats_data[ak][w]

        assert abs(float(row["t_task_mean_ms"]) - expected["t_task_mean_ms"]) < 1e-2
        assert abs(float(row["rss_peak_mb"]) - expected["rss_peak_mb"]) < 1e-2
        assert abs(float(row["energy_mean_j"]) - expected["energy_mean_j"]) < 1e-2
        assert abs(float(row["edp_mean_js"]) - expected["edp_mean_js"]) < 1e-2


def test_latex_table_contains_summary_data():
    """Verify table_journal_ablation.tex reflects all 4 workloads and configurations."""
    tex_path = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "table_journal_ablation.tex")
    assert os.path.exists(tex_path), f"Missing {tex_path}"

    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "W1 & PicoClaw (Go Native)" in content
    assert "W4 & PicoClaw (Go Native)" in content
    assert "W4 & OpenClaw (Node.js Full Ablation)" in content
    assert "2010.352" in content or "2010.35" in content or "2010.4" in content
    assert "2454.313" in content or "2454.31" in content or "2454.3" in content
    assert "0.0 MB Peak RAM for Neural Baseline indicates zero orchestrator process footprint" in content


def test_readme_results_matrix_consistency():
    """Verify README.md contains exact empirical figures cited across all workloads."""
    readme_path = os.path.join(REPO_DIR, "README.md")
    assert os.path.exists(readme_path), f"Missing {readme_path}"

    with open(readme_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Core empirical values from summary_statistics.json
    assert "1444{,}7" in text  # W1 PicoClaw & OpenClaw Full
    assert "11{,}1" in text    # W1 PicoClaw RAM
    assert "86{,}0" in text    # W1 OpenClaw RAM
    assert "2979{,}1" in text  # W2 PicoClaw
    assert "6423{,}1" in text  # W3 PicoClaw Mean
    assert "11071{,}3" in text # W4 PicoClaw Task
    assert "12233{,}1" in text # W4 OpenClaw Full Task
    assert "16{,}7" in text    # W4 PicoClaw RAM
    assert "93{,}7" in text    # W4 OpenClaw Full RAM
    assert "2010{,}352" in text # W4 PicoClaw EDP
    assert "2454{,}313" in text # W4 OpenClaw Full EDP

    # Key findings references
    assert "18,1% menor Produto Energia-Atraso" in text
    assert "18.1% lower Energy-Delay Product" in text
    assert "Cliff's Delta $d = -1{,}0$" in text
    assert "Cliff's Delta $d = -1.0$" in text
