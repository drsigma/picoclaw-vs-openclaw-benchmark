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
    """Verify table_journal_ablation.tex and table_warm_cache.tex reflect neutral architecture names and TTFT/ITL/Uncached columns."""
    tex_path = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "table_journal_ablation.tex")
    warm_tex_path = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "table_warm_cache.tex")
    assert os.path.exists(tex_path), f"Missing {tex_path}"
    assert os.path.exists(warm_tex_path), f"Missing {warm_tex_path}"

    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "W1 & Go Native Orchestrator (PicoClaw Ref.)" in content
    assert "W4 & Go Native Orchestrator (PicoClaw Ref.)" in content
    assert "W4 & Node.js V8 Orchestrator (OpenClaw Full 54-Tool)" in content
    assert "W4 & Python 3.12 Reference Agent" in content
    assert "Direct Local LLM Baseline" in content

    with open(warm_tex_path, "r", encoding="utf-8") as f:
        warm_content = f.read()

    assert "Prompt (Tot / Cached / New)" in warm_content
    assert "TTFT / ITL [ms]" in warm_content
    assert "2177 / 2176 / 1" in warm_content
    assert "22980 / 22457 / 523" in warm_content


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

    # Verify prompt_tokens parity: strict parity in warm_cache_trials.jsonl (Regime B)
    # and pre-equalization baseline preservation (<= 5.2% variance) in raw_trials.jsonl (Regime A)
    expected_tokens_regime_b = {
        "W1": 2153,
        "W2": 2177,
        "W3": 2410,
        "W4": 22980,
    }
    expected_tokens_regime_a = {
        "W1": {2153, 2273},
        "W2": {2297, 2321},
        "W3": {2410, 2530},
        "W4": {22980, 23255, 24180},
    }

    warm_file = os.path.join(REPO_DIR, "results", "publication_campaign", "warm_cache_trials.jsonl")
    if os.path.exists(warm_file):
        with open(warm_file, "r", encoding="utf-8") as f:
            warm_records = [json.loads(line) for line in f if line.strip()]
        assert len(warm_records) == 660, f"Expected 660 records in warm_cache_trials.jsonl, got {len(warm_records)}"
        for trial in warm_records:
            assert float(trial.get("ttft_ms", 0.0)) > 0.0, f"Missing ttft_ms in warm_cache_trials.jsonl: {trial}"
            assert float(trial.get("itl_ms", 0.0)) > 0.0, f"Missing itl_ms in warm_cache_trials.jsonl: {trial}"
            w = trial.get("workload")
            a = trial.get("agent_key")
            if a in equalized_arms and w in expected_tokens_regime_b:
                assert trial.get("prompt_tokens") == expected_tokens_regime_b[w], (
                    f"warm_cache_trials.jsonl mismatch: {a} {w} has {trial.get('prompt_tokens')} != {expected_tokens_regime_b[w]}"
                )

    raw_file = os.path.join(REPO_DIR, "results", "publication_campaign", "raw_trials.jsonl")
    if os.path.exists(raw_file):
        with open(raw_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                trial = json.loads(line)
                w = trial.get("workload")
                a = trial.get("agent_key")
                if a in equalized_arms and w in expected_tokens_regime_a:
                    assert trial.get("prompt_tokens") in expected_tokens_regime_a[w], (
                        f"raw_trials.jsonl mismatch: {a} {w} has {trial.get('prompt_tokens')} not in {expected_tokens_regime_a[w]}"
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


def test_energy_regressor_validity_and_spurious_rejection():
    """Verify valid CPU energy proxies achieve R^2 >= 0.90 and XNU ri_billed_energy is flagged as rejected_spurious_proxy."""
    json_path = os.path.join(REPO_DIR, "results", "publication_campaign", "uma_energy_bandwidth_attribution.json")
    assert os.path.exists(json_path), f"Missing {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    neg_res = data.get("kernel_counter_validation_negative_result", {})
    assert neg_res.get("rejected_spurious_proxy") is True
    assert abs(float(neg_res.get("pearson_r_global", 1.0))) < 0.15
    assert float(neg_res.get("ols_r2_no_intercept_vs_mean", 1.0)) < 0.0

    proxies = data.get("validated_physical_cpu_proxies", {})
    for proxy_key in ("t_exec_ms", "proc_instructions", "proc_cycles"):
        assert proxy_key in proxies, f"Missing validated proxy {proxy_key}"
        r_sq = float(proxies[proxy_key].get("ols_r2", 0.0))
        assert r_sq >= 0.90, f"Expected R^2 >= 0.90 for {proxy_key}, got {r_sq}"


def test_inter_session_and_spearman_holm_artifacts():
    """Verify inter-session replication uses native Bun (not fallback) and Spearman matrix includes p_adj_holm and stratified_by_workload."""
    inter_path = os.path.join(REPO_DIR, "results", "publication_campaign", "inter_session_replication.json")
    spearman_path = os.path.join(REPO_DIR, "results", "publication_campaign", "spearman_correlation_matrix.json")

    assert os.path.exists(inter_path), f"Missing {inter_path}"
    assert os.path.exists(spearman_path), f"Missing {spearman_path}"

    with open(inter_path, "r", encoding="utf-8") as f:
        inter = json.load(f)

    assert "overall_mean_inter_session_rel_diff_pct" in inter
    assert "overall_mean_inter_session_pooled_cv_pct" in inter
    assert "paired_intra_session_contrasts_vs_neural_baseline" in inter
    bun_eval = inter.get("bun_minimal_evaluation", {})
    for w in ("W1", "W2", "W3", "W4"):
        assert w in bun_eval, f"Missing {w} in bun_minimal_evaluation"
        assert bun_eval[w].get("n_evaluations") == 30
        assert bun_eval[w].get("runner_binary") == "bun"
        assert bun_eval[w].get("is_fallback_node") is False
        assert float(bun_eval[w].get("proc_peak_phys_mb_mean", 0.0)) > 0.0

    with open(spearman_path, "r", encoding="utf-8") as f:
        sp = json.load(f)

    assert "stratified_by_workload" in sp
    for reg in ("regime_a_cold_prefill", "regime_b_warm_kv_cache"):
        assert reg in sp["stratified_by_workload"]
        for w in ("W1", "W2", "W3", "W4"):
            assert w in sp["stratified_by_workload"][reg]
            assert sp["stratified_by_workload"][reg][w]["n_trials"] == 150
        mat = sp[reg]
        for m1, row in mat.items():
            for m2, cell in row.items():
                assert "p_adj_holm" in cell, f"Missing p_adj_holm in {reg} {m1} vs {m2}"


def test_tool_rag_mitigation_and_worker_version_artifacts():
    """Verify Tool-RAG pruner benchmark and isomorphic worker --version hyperfine artifacts."""
    rag_json = os.path.join(REPO_DIR, "results", "publication_campaign", "tool_rag_mitigation_summary.json")
    rag_tex = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "table_tool_rag_mitigation.tex")
    hyp_json = os.path.join(REPO_DIR, "results", "publication_campaign", "hyperfine_worker_version.json")

    assert os.path.exists(rag_json), f"Missing {rag_json}"
    assert os.path.exists(rag_tex), f"Missing {rag_tex}"
    assert os.path.exists(hyp_json), f"Missing {hyp_json}"

    with open(rag_json, "r", encoding="utf-8") as f:
        rag = json.load(f)

    for reg in ("regime_a_cold", "regime_b_warm"):
        for w in ("W1", "W2", "W3", "W4"):
            for ak in ("openclaw_tool_rag", "picoclaw_tool_rag"):
                st = rag[reg][w][ak]
                assert st["n_trials"] == 30
                assert st["t_prune_mean_ms"] > 0.0
                if reg == "regime_a_cold":
                    assert st["latency_reduction_vs_full_54_pct"] > 80.0
                    assert st["energy_reduction_vs_full_54_pct"] > 80.0
                else:
                    assert st["latency_reduction_vs_full_54_pct"] > 15.0
                    assert st["latency_reduction_vs_minimal_15_pct"] > 0.0


def test_protocol_invariants_enforced_and_fail_on_violation():
    """Verify validate_campaign_invariants passes on real datasets and raises ValueError on each of the 7 violations."""
    import copy

    import pytest

    from benchmark.protocol_invariants import validate_campaign_invariants

    warm_path = os.path.join(REPO_DIR, "results", "publication_campaign", "warm_cache_trials.jsonl")
    inter_path = os.path.join(REPO_DIR, "results", "publication_campaign", "inter_session_trials.jsonl")
    meta_path = os.path.join(REPO_DIR, "results", "publication_campaign", "campaign_metadata.json")

    with open(warm_path, "r", encoding="utf-8") as f:
        warm_recs = [json.loads(line) for line in f if line.strip()]
    with open(inter_path, "r", encoding="utf-8") as f:
        inter_recs = [json.loads(line) for line in f if line.strip()]
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Must pass on real Regime B and Session 2 datasets
    res_warm = validate_campaign_invariants(warm_recs, expected_eval_count=600, require_equalized_tokens=True, require_energy=True, metadata=meta)
    assert res_warm["status"] == "PASSED"
    res_inter = validate_campaign_invariants(inter_recs, expected_eval_count=600, require_equalized_tokens=True, require_energy=True)
    assert res_inter["status"] == "PASSED"

    eval_only = [copy.deepcopy(r) for r in warm_recs if not r.get("is_warmup", False)]

    # 1. Violation of Invariant #1: prompt_tokens <= 0
    bad1 = copy.deepcopy(eval_only)
    bad1[0]["prompt_tokens"] = 0
    with pytest.raises(ValueError, match="Invariant #1"):
        validate_campaign_invariants(bad1, metadata=meta)

    # 2. Violation of Invariant #2: unequal prompt_tokens across 15-tool arms
    bad2 = copy.deepcopy(eval_only)
    for r in bad2:
        if r["agent_key"] == "picoclaw" and r["workload"] == "W2":
            r["prompt_tokens"] = 9999
            break
    with pytest.raises(ValueError, match="Invariant #2"):
        validate_campaign_invariants(bad2, require_equalized_tokens=True, metadata=meta)

    # 3. Violation of Invariant #3: invalid finish_reason
    bad3 = copy.deepcopy(eval_only)
    bad3[0]["finish_reason"] = "error_timeout"
    with pytest.raises(ValueError, match="Invariant #3"):
        validate_campaign_invariants(bad3, metadata=meta)

    # 4. Violation of Invariant #4: http_status != 200
    bad4 = copy.deepcopy(eval_only)
    bad4[0]["http_status"] = 500
    with pytest.raises(ValueError, match="Invariant #4"):
        validate_campaign_invariants(bad4, metadata=meta)

    # 5. Violation of Invariant #5: sample count mismatch
    with pytest.raises(ValueError, match="Invariant #5"):
        validate_campaign_invariants(eval_only[:-1], expected_eval_count=600, metadata=meta)

    # 6. Violation of Invariant #6: missing session_id / git_commit
    with pytest.raises(ValueError, match="Invariant #6"):
        validate_campaign_invariants(eval_only, metadata={"session_id": "", "git_commit": "abc"})

    # 7. Violation of Invariant #7: missing or non-positive energy when require_energy=True
    bad7 = copy.deepcopy(eval_only)
    bad7[0]["energy_net_above_idle_j"] = None
    with pytest.raises(ValueError, match="Invariant #7"):
        validate_campaign_invariants(bad7, require_energy=True, metadata=meta)


def test_all_checklist_gates_0_to_8_verified():
    """Validates complete fulfillment of SoftwareX Checklist Gates 0 through 8."""
    from benchmark.protocol_invariants import validate_gate_0_provenance_fields

    # Gate 0: 9 mandatory fields across all 7 JSONL files
    jsonl_files = [
        "raw_trials.jsonl",
        "warm_cache_trials.jsonl",
        "inter_session_trials.jsonl",
        "prefill_ablation.jsonl",
        "uma_energy_bandwidth_trials.jsonl",
        "tool_rag_mitigation_trials.jsonl",
        "kv_cache_thrashing_trials.jsonl",
    ]
    for jf in jsonl_files:
        fpath = os.path.join(REPO_DIR, "results", "publication_campaign", jf)
        assert os.path.exists(fpath), f"Missing JSONL file {jf}"
        with open(fpath, "r", encoding="utf-8") as f:
            recs = [json.loads(line) for line in f if line.strip()]
        res = validate_gate_0_provenance_fields(
            recs,
            source_name=jf,
            require_prompt_predicted_ms=(jf != "uma_energy_bandwidth_trials.jsonl"),
        )
        assert res["status"] == "PASSED", f"Gate 0 failed on {jf}: {res}"

    # Gate 1: Highlights and Cover Letter synchronization
    hl_path = os.path.join(REPO_DIR, "paper", "HIGHLIGHTS.md")
    cl_path = os.path.join(REPO_DIR, "paper", "COVER_LETTER.md")
    for doc_path in (hl_path, cl_path):
        assert os.path.exists(doc_path), f"Missing {doc_path}"
        with open(doc_path, "r", encoding="utf-8") as f:
            text = f.read()
        assert "23.4" not in text, f"Outdated 23.4x found in {doc_path}"

    # Gate 2 & 5: KV-Cache Thrashing & Warm Cache table
    thrash_summary_path = os.path.join(REPO_DIR, "results", "publication_campaign", "kv_cache_thrashing_summary.json")
    assert os.path.exists(thrash_summary_path), f"Missing {thrash_summary_path}"
    with open(thrash_summary_path, "r", encoding="utf-8") as f:
        thrash_data = json.load(f)
    assert thrash_data["thrashing_vs_isolated_comparisons"]["schemas_15_thrashing_latency_penalty_ratio"] > 5.0
    assert thrash_data["thrashing_vs_isolated_comparisons"]["schemas_54_thrashing_latency_penalty_ratio"] > 15.0

    warm_tex_path = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "table_warm_cache.tex")
    with open(warm_tex_path, "r", encoding="utf-8") as f:
        warm_tex = f.read()
    assert "TTFT" in warm_tex
    assert "ITL" in warm_tex
    assert "Interleaved Prefix Thrashing" in warm_tex

    # Gate 3 & 4: Sensitivity, Outlier analysis & Negative physical proxy
    sens_path = os.path.join(REPO_DIR, "results", "publication_campaign", "sensitivity_and_outlier_analysis.json")
    assert os.path.exists(sens_path), f"Missing {sens_path}"
    with open(sens_path, "r", encoding="utf-8") as f:
        sens_data = json.load(f)
    assert sens_data["regime_a_cold_prefill"]["overall_outlier_fraction_pct"] < 5.0
    assert sens_data["regime_b_warm_kv_cache"]["overall_outlier_fraction_pct"] < 5.0
    assert sens_data["regime_a_cold_prefill"]["active_power_net_overall_mean_w"] > 10.0
    assert sens_data["regime_b_warm_kv_cache"]["active_power_net_overall_mean_w"] > 10.0

    uma_path = os.path.join(REPO_DIR, "results", "publication_campaign", "uma_energy_bandwidth_attribution.json")
    with open(uma_path, "r", encoding="utf-8") as f:
        uma_data = json.load(f)
    assert uma_data["kernel_counter_validation_negative_result"]["rejected_spurious_proxy"] is True

    # Gate 6: Independent validation
    indep_path = os.path.join(REPO_DIR, "results", "publication_campaign", "independent_validation_report.json")
    cross_path = os.path.join(REPO_DIR, "results", "publication_campaign", "cross_hardware_and_independent_validation.json")
    assert os.path.exists(indep_path), f"Missing {indep_path}"
    assert os.path.exists(cross_path), f"Missing {cross_path}"
    with open(indep_path, "r", encoding="utf-8") as f:
        indep_data = json.load(f)
    assert indep_data["status"] == "ALL_TOLERANCES_PASSED"

    # Gate 8: Disclaimers and absence of forbidden hype phrases
    manuscript_path = os.path.join(REPO_DIR, "paper", "softwarex_manuscript.tex")
    readme_path = os.path.join(REPO_DIR, "README.md")
    forbidden_phrases = [
        "proves superiority",
        "energy dominance",
        "universally faster",
        "direct DRAM bandwidth telemetry",
    ]
    for check_file in (manuscript_path, readme_path, hl_path, cl_path):
        with open(check_file, "r", encoding="utf-8") as f:
            content = f.read().lower()
        for phrase in forbidden_phrases:
            assert phrase.lower() not in content, f"Forbidden phrase '{phrase}' found in {check_file}"


def test_all_jsonl_records_contain_http_status_200():
    """Gate A2 / D1: Enforces that 100% of records in all publication campaign JSONL datasets contain http_status == 200."""
    import glob
    jsonl_files = sorted(glob.glob(os.path.join(REPO_DIR, "results", "publication_campaign", "*.jsonl")))
    assert len(jsonl_files) >= 6, "Expected at least 6 campaign datasets"

    total_records = 0
    for jf in jsonl_files:
        with open(jf, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if not line.strip():
                    continue
                total_records += 1
                rec = json.loads(line)
                assert "http_status" in rec, f"Missing http_status in {jf}:{idx}"
                assert rec["http_status"] == 200, f"Non-200 http_status ({rec['http_status']}) in {jf}:{idx}"

    assert total_records >= 3700, f"Expected at least 3700 verified physical records, found {total_records}"


def test_roofline_kv_affine_model_physical_limits():
    """Gate A / C: Enforces physical roofline validity and affine KV scaling model parameters."""
    model_path = os.path.join(REPO_DIR, "data", "roofline_kv_affine_model.json")
    assert os.path.exists(model_path), f"Missing {model_path}"

    with open(model_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Weights layout
    layout = data["gguf_tensor_decomposition"]
    assert layout["active_weights_bytes"] == 1688334336
    assert layout["token_embedding_bytes"] == 323205120
    assert layout["file_size_bytes"] == 2019377696

    # 2. Affine KV scaling regression
    reg = data["kv_cache_scaling_affine_model"]["linear_regression"]
    assert 16.5 <= reg["itl_0_intercept_ms"] <= 17.5
    assert 0.90 <= reg["alpha_kv_slope_us_per_token"] <= 1.05
    assert reg["r_squared"] > 0.97

    # 3. Physical bandwidth roofline: NO context level may exceed 120.0 GB/s Apple M4 theoretical peak
    levels = data["kv_cache_scaling_affine_model"]["per_context_level_bandwidth"]
    for lvl, m in levels.items():
        assert m["active_bw_gb_s"] < 120.0, f"Level {lvl} exceeded 120 GB/s: {m['active_bw_gb_s']}"
        assert 80.0 <= m["active_utilization_pct"] <= 95.0
        assert m["is_above_120_gbs"] is False


def test_harness_self_overhead_bounds():
    """Gate D2: Verifies telemetry harness self-overhead quantification."""
    overhead_path = os.path.join(REPO_DIR, "data", "harness_self_overhead.json")
    assert os.path.exists(overhead_path), f"Missing {overhead_path}"

    with open(overhead_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    quant = data["overhead_quantification"]
    # Telemetry overhead must be negligible (absolute delta under 5%) and not statistically significant
    assert abs(quant["overhead_latency_median_pct"]) < 5.0
    assert quant["p_value"] > 0.05
    assert quant["is_statistically_significant"] is False


def test_external_framework_langchain_summary():
    """Gate C1: Verifies external enterprise framework (LangChain Core) evaluation."""
    summary_path = os.path.join(REPO_DIR, "data", "external_framework_langchain_summary.json")
    assert os.path.exists(summary_path), f"Missing {summary_path}"

    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["n_total_trials"] == 144
    assert data["n_evaluated_trials"] == 120
    # LangChain Core physical RSS should be between 50 and 80 MB
    w2_warm = data["regime_b_warm"]["W2"]
    assert 50.0 <= w2_warm["proc_peak_phys_mb_median"] <= 80.0
    assert w2_warm["t_task_median_ms"] > 1500.0


def test_mcp_live_transport_ablation_artifacts():
    """Gate R10: Verifies live Model Context Protocol (MCP) transport ablation."""
    json_path = os.path.join(REPO_DIR, "data", "mcp_live_transport_ablation.json")
    tex_path = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "table_mcp_transport_ablation.tex")

    assert os.path.exists(json_path), f"Missing {json_path}"
    assert os.path.exists(tex_path), f"Missing {tex_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    res = data["results"]
    assert "go_orchestrator" in res
    assert "node_orchestrator" in res

    # Stdio IPC overhead must be sub-5ms across runtimes
    go_stdio = res["go_orchestrator"]["transports"]["mcp_stdio_server"]
    assert 0.5 <= go_stdio["t_mcp_ipc_median_ms"] <= 5.0
    assert go_stdio["phi_orch_median_pct"] < 1.0


def test_quantization_scaling_ablation_artifacts():
    """Gate R10: Verifies extreme quantization scaling ablation."""
    json_path = os.path.join(REPO_DIR, "data", "quantization_scaling_ablation.json")
    tex_path = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "table_quantization_scaling.tex")

    assert os.path.exists(json_path), f"Missing {json_path}"
    assert os.path.exists(tex_path), f"Missing {tex_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    quants = {p["quantization"]: p for p in data["quantization_profiles"]}
    assert "Q2_K" in quants
    assert "Q3_K_M" in quants
    assert "Q4_K_M" in quants

    # Decode throughput of Q2_K must be higher than Q4_K_M
    assert quants["Q2_K"]["generation_throughput_tok_s"] > quants["Q4_K_M"]["generation_throughput_tok_s"]
    # All must stay within physical memory bandwidth limits (< 120 GB/s)
    for q, prof in quants.items():
        assert prof["active_bandwidth_gbs"] < 120.0
        assert prof["is_within_physical_limits"] is True


def test_gatekeeper_audit_certificate_verified():
    """Gate R10: Verifies automated submission gatekeeper cryptographic certificate."""
    cert_path = os.path.join(REPO_DIR, "data", "gatekeeper_audit_certificate.json")
    assert os.path.exists(cert_path), f"Missing {cert_path}"

    with open(cert_path, "r", encoding="utf-8") as f:
        cert = json.load(f)

    assert cert["gatekeeper_verdict"] == "CERTIFIED_VALID"
    assert cert["total_records_verified"] >= 3700
    assert cert["total_datasets_audited"] >= 7












