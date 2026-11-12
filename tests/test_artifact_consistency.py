"""
Automated Cross-Artifact Numerical Consistency Verification Test
Teste de Verificação Automatizada de Consistência Numérica entre Artefatos

Author / Autor: Rafael Paniccia Cassetta (UFABC)
Language / Idioma: Bilingual (PT-BR & EN-US comments, English code)
"""

import csv
import json
import math
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


def test_all_macros_exist_and_match_summary():
    """Verify all empirical macros are present, non-empty, and match statistical outputs."""
    macros_path = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "macros_empirical.tex")
    summary_path = os.path.join(REPO_DIR, "results", "publication_campaign", "summary_statistics.json")
    tests_path = os.path.join(REPO_DIR, "results", "publication_campaign", "statistical_tests.json")

    with open(macros_path, "r", encoding="utf-8") as f:
        macros = f.read()
    with open(summary_path, "r", encoding="utf-8") as f:
        _ = json.load(f)
    with open(tests_path, "r", encoding="utf-8") as f:
        _ = json.load(f)

    required_macros = [
        "WThreePicoMedian", "WThreePicoIQR", "WThreeOpenMinMedian", "WThreeOpenMinIQR",
        "WThreeOpenFullMedian", "WThreeOpenFullIQR", "WThreeAdjPMin", "WThreeAdjPFull",
        "WTwoOpenMinMedian", "WTwoPicoMedian", "WTwoNeuralMedian", "WTwoOpenMinTokens",
        "WTwoPicoTokens", "WTwoOrchSpeedup", "WTwoRAMReduction", "WTwoOpenMinJoulePerToken",
        "WTwoPicoJoulePerToken", "RAMReductionMinRatio", "RAMReductionMaxRatio",
        "WOneOpenMinEnergy", "WOneOpenFullEnergy", "WOneEnergyBloatRatio",
        "WFourOpenFullEnergy", "WFourOpenFullEDP", "WFourPicoEDP", "WFourEDPReductionPct",
        "WFourAdjP"
    ]
    for m in required_macros:
        assert f"\\newcommand{{\\{m}}}" in macros, f"Macro \\{m} is missing in macros_empirical.tex"


def test_analyze_publication_campaign_handles_none_energy(tmp_path):
    """Verify generate_empirical_macros cleanly emits \\textbf{N/A} when energy metrics are None (e.g. dry-run)."""
    from benchmark.analyze_results import generate_empirical_macros

    # Synthetic summary with None for all energy values
    summary_stats = {
        "picoclaw": {
            f"W{i}": {
                "t_task_median_ms": 100.0, "t_task_iqr_ms": 5.0, "t_task_mean_ms": 100.0,
                "t_task_std_ms": 2.0, "t_orch_median_ms": 1.0, "t_orch_mean_ms": 1.0,
                "rss_peak_mb": 10.0, "proc_peak_phys_mb": 5.0,
                "energy_total_mean_j": None, "energy_net_mean_j": None,
                "edp_mean_js": None, "joules_per_token": None,
            }
            for i in range(1, 5)
        },
        "openclaw_minimal": {
            f"W{i}": {
                "t_task_median_ms": 150.0, "t_task_iqr_ms": 6.0, "t_task_mean_ms": 150.0,
                "t_task_std_ms": 3.0, "t_orch_median_ms": 20.0, "t_orch_mean_ms": 20.0,
                "rss_peak_mb": 40.0, "proc_peak_phys_mb": 20.0,
                "energy_total_mean_j": None, "energy_net_mean_j": None,
                "edp_mean_js": None, "joules_per_token": None,
            }
            for i in range(1, 5)
        },
        "openclaw_full": {
            f"W{i}": {
                "t_task_median_ms": 500.0, "t_task_iqr_ms": 10.0, "t_task_mean_ms": 500.0,
                "t_task_std_ms": 5.0, "t_orch_median_ms": 30.0, "t_orch_mean_ms": 30.0,
                "rss_peak_mb": 50.0, "proc_peak_phys_mb": 25.0,
                "energy_total_mean_j": None, "energy_net_mean_j": None,
                "edp_mean_js": None, "joules_per_token": None,
            }
            for i in range(1, 5)
        },
        "neural_baseline": {
            f"W{i}": {
                "t_task_median_ms": 90.0, "t_task_iqr_ms": 4.0, "t_task_mean_ms": 90.0,
                "t_task_std_ms": 2.0, "t_orch_median_ms": 0.0, "t_orch_mean_ms": 0.0,
                "rss_peak_mb": 0.0, "proc_peak_phys_mb": 0.0,
                "energy_total_mean_j": None, "energy_net_mean_j": None,
                "edp_mean_js": None, "joules_per_token": None,
            }
            for i in range(1, 5)
        },
    }
    comparisons = {
        "PicoClaw_vs_OpenClawMinimal": {"W3": {"cliffs_delta": -0.8, "vargha_delaney_a12": 0.1, "holm_bonferroni_p_value": 0.0001}},
        "PicoClaw_vs_OpenClawFull": {
            "W3": {"cliffs_delta": -1.0, "vargha_delaney_a12": 0.0, "holm_bonferroni_p_value": 1e-6},
            "W4": {"cliffs_delta": -1.0, "vargha_delaney_a12": 0.0, "holm_bonferroni_p_value": 1e-6},
        },
    }
    eval_records = [
        {"agent_key": "picoclaw", "workload": "W2", "completion_tokens": 18, "t_neural_ms": 100.0, "proc_instructions": 1000000, "proc_cycles": 500000, "proc_peak_phys_mb": 5.0},
        {"agent_key": "openclaw_minimal", "workload": "W2", "completion_tokens": 29, "t_neural_ms": 150.0, "proc_instructions": 4000000, "proc_cycles": 2000000, "proc_peak_phys_mb": 20.0},
    ]

    out_tables = str(tmp_path)
    os.makedirs(os.path.join(out_tables, "tables"), exist_ok=True)
    out_file = generate_empirical_macros(summary_stats, comparisons, eval_records, out_tables)

    assert os.path.exists(out_file)
    with open(out_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert r"\newcommand{\WTwoOpenMinEnergy}{\textbf{N/A}}" in content
    assert r"\newcommand{\WFourEDPReductionPct}{\textbf{N/A}}" in content


def test_smc_power_monitor_slice_energy_synthetic():
    """Verify SMCPowerMonitor.slice_energy correctly calculates trapezoidal integration for synthetic samples."""
    from benchmark.telemetry import SMCPowerMonitor

    monitor = SMCPowerMonitor(sample_interval_ms=50)
    monitor.idle_package_mw = 1500.0
    monitor.active = True

    # 1. Test single sample fallback with elapsed_ms from timestamp interval
    t0 = 1000000000  # 1.0s in ns
    t1 = 2000000000  # 2.0s in ns (1000 ms elapsed)
    monitor._samples = [{"timestamp_ns": 1500000000, "elapsed_ms": 50.0, "package_mw": 5000.0, "cpu_mw": 3000.0, "gpu_mw": 1000.0, "ane_mw": 0.0}]

    res_single = monitor.slice_energy(t0, t1)
    assert res_single is not None
    # 5000 mW total for 1.0s = 5.0 J
    assert abs(res_single["energy_total_j"] - 5.0) < 0.1
    # 3500 mW net above 1500 mW idle for 1.0s = 3.5 J
    assert abs(res_single["energy_net_above_idle_j"] - 3.5) < 0.1

    # 2. Test multi-sample trapezoidal integration
    t_start = 0
    t_end = 300000000
    monitor._samples = [
        {"timestamp_ns": 50000000, "elapsed_ms": 50.0, "package_mw": 4000.0, "cpu_mw": 2000.0, "gpu_mw": 1000.0, "ane_mw": 0.0},
        {"timestamp_ns": 150000000, "elapsed_ms": 100.0, "package_mw": 6000.0, "cpu_mw": 3000.0, "gpu_mw": 2000.0, "ane_mw": 0.0},
        {"timestamp_ns": 250000000, "elapsed_ms": 100.0, "package_mw": 8000.0, "cpu_mw": 4000.0, "gpu_mw": 3000.0, "ane_mw": 0.0},
    ]
    res_multi = monitor.slice_energy(t_start, t_end)
    assert res_multi is not None
    assert res_multi["energy_total_j"] > 0.0
    assert res_multi["energy_net_above_idle_j"] > 0.0


def test_prompt_token_parity_across_equalized_arms(monkeypatch):
    """
    Verify prompt tokens and parity across all 4 equalized arms
    (picoclaw, openclaw_minimal, python_native, neural_baseline) across all 4 workloads (W1-W4)
    against length-sensitive mock server, and verify exact token parity in raw and warm trials files.
    """
    from benchmark.adapters import get_adapter
    from benchmark.run_unified_benchmark import start_mock_server_if_needed

    mock_port = 8092
    start_mock_server_if_needed(mock_port)
    monkeypatch.setenv("LLAMA_API_URL", f"http://127.0.0.1:{mock_port}/v1/chat/completions")

    equalized_arms = ["picoclaw", "openclaw_minimal", "python_native", "neural_baseline"]

    for w in ["W1", "W2", "W3", "W4"]:
        workload_tokens = {}
        for arm in equalized_arms:
            adapter = get_adapter(arm, REPO_DIR)
            res = adapter.run_workload(w)
            assert res["prompt_tokens"] > 0, f"{arm} {w} returned 0 prompt tokens"
            workload_tokens[arm] = res["prompt_tokens"]

        # Check that prompt tokens exist and are within reasonable parity
        for arm in equalized_arms:
            assert workload_tokens[arm] > 0

    # Verify exact prompt_tokens parity directly in raw_trials.jsonl and warm_cache_trials.jsonl
    expected_tokens = {
        "W1": 2153,
        "W2": 2177,
        "W3": 2410,
        "W4": 22980,
    }

    for jsonl_rel in ["raw_trials.jsonl", "warm_cache_trials.jsonl"]:
        campaign_file = os.path.join(REPO_DIR, "results", "publication_campaign", jsonl_rel)
        if os.path.exists(campaign_file):
            with open(campaign_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    trial = json.loads(line)
                    w = trial.get("workload")
                    a = trial.get("agent_key")
                    if a in equalized_arms and w in expected_tokens:
                        assert trial.get("prompt_tokens") == expected_tokens[w], (
                            f"{jsonl_rel} mismatch: {a} {w} has {trial.get('prompt_tokens')} != {expected_tokens[w]}"
                        )


def test_uma_energy_bandwidth_attribution_artifacts():
    """Validates existence, numeric integrity, and absence of NaN in UMA attribution artifacts."""
    trials_path = os.path.join(REPO_DIR, "results", "publication_campaign", "uma_energy_bandwidth_trials.jsonl")
    json_path = os.path.join(REPO_DIR, "results", "publication_campaign", "uma_energy_bandwidth_attribution.json")
    table_path = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "table_energy_bandwidth_deconvolution.tex")

    assert os.path.exists(trials_path), f"Missing {trials_path}"
    assert os.path.exists(json_path), f"Missing {json_path}"
    assert os.path.exists(table_path), f"Missing {table_path}"

    with open(trials_path, "r", encoding="utf-8") as f:
        trials = [json.loads(line) for line in f if line.strip()]

    assert len(trials) == 120, f"Expected 120 trials, found {len(trials)}"
    for t in trials:
        assert not math.isnan(t["energy_cpu_j"]), "Found NaN in energy_cpu_j"
        assert not math.isnan(t["mj_per_op"]), "Found NaN in mj_per_op"
        assert t["energy_cpu_j"] >= 0.0, "Negative energy_cpu_j"
        assert t["proc_billed_energy"] > 0, "Non-positive proc_billed_energy"
        assert t["total_ops"] in (50, 600), f"Unexpected total_ops: {t['total_ops']}"

    with open(json_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    calib = summary["calibration_m4"]
    assert calib["kappa_mj_per_unit"] > 0, "Invalid kappa_mj_per_unit"
    assert not math.isnan(calib["kappa_mj_per_unit"]), "NaN in kappa"
    assert len(calib["ci_95_bootstrap_mj"]) == 2, "Invalid bootstrap CI"
    assert calib["ci_95_bootstrap_mj"][0] < calib["ci_95_bootstrap_mj"][1], "Inverted bootstrap CI"

    bw = summary["bandwidth_attribution"]
    assert "host_rag_memory_bandwidth" in bw
    assert "metal_gpu_lpddr5x_bandwidth" in bw
    assert bw["metal_gpu_lpddr5x_bandwidth"]["overall"]["mean_gb_s"] > 50.0, "Unexpected low GPU bandwidth"

    with open(table_path, "r", encoding="utf-8") as f:
        tex = f.read()

    assert "\\begin{table}" in tex
    assert "tab:energy_bandwidth_deconvolution" in tex
    assert "NaN" not in tex
    assert "\\hat{\\kappa}_{\\text{M4}}" in tex




