"""
Unit Tests for Statistical Inference Engine & Metrics
Testes Unitários para Motor de Inferência Estatística e Métricas

Author / Autor: Rafael Paniccia Cassetta (UFABC)
Language / Idioma: Bilingual (PT-BR & EN-US comments, English code)
"""

import os

for _env_var in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "GOTO_NUM_THREADS",
    "BLIS_NUM_THREADS",
):
    os.environ.setdefault(_env_var, "1")

import numpy as np  # noqa: E402
from benchmark import stats_core as stats  # noqa: E402

from benchmark.analyze_results import (  # noqa: E402
    bootstrap_ci,
    cliffs_delta,
    holm_bonferroni_adjust,
    vargha_delaney_a12,
)


def compute_edp(energy_joules: float, latency_seconds: float) -> float:
    """Compute Energy-Delay Product (EDP) in Joule-seconds."""
    return energy_joules * latency_seconds


def test_edp_calculation():
    """Verify Energy-Delay Product calculation (Gonzalez & Horowitz, 1996)."""
    e = 15.0  # Joules
    t = 2.0   # seconds
    edp = compute_edp(e, t)
    assert edp == 30.0


def test_cliffs_delta_and_a12_extremes():
    """Verify Cliff's delta and Vargha-Delaney A12 for dominated distributions."""
    sample_a = [10.0, 11.0, 12.0]
    sample_b = [20.0, 21.0, 22.0]

    # Every element in sample_a is less than every element in sample_b
    delta_ab = cliffs_delta(sample_a, sample_b)
    assert delta_ab == -1.0
    a12_ab = vargha_delaney_a12(sample_a, sample_b)
    assert a12_ab == 0.0

    # Inverted: sample_b vs sample_a
    delta_ba = cliffs_delta(sample_b, sample_a)
    assert delta_ba == 1.0
    a12_ba = vargha_delaney_a12(sample_b, sample_a)
    assert a12_ba == 1.0


def test_cliffs_delta_and_a12_identical():
    """Verify Cliff's delta and Vargha-Delaney A12 for identical distributions."""
    sample_a = [5.0, 5.0, 5.0]
    sample_b = [5.0, 5.0, 5.0]

    delta = cliffs_delta(sample_a, sample_b)
    assert delta == 0.0
    a12 = vargha_delaney_a12(sample_a, sample_b)
    assert a12 == 0.5


def test_bootstrap_ci_coverage():
    """Verify 95% bootstrap confidence interval contains the true population mean."""
    np.random.seed(42)
    # 50 samples from N(100, 5)
    data = np.random.normal(100.0, 5.0, size=50).tolist()
    low_ci, high_ci = bootstrap_ci(data, n_resamples=2000, alpha=0.05, seed=42)

    assert low_ci < 100.0 < high_ci


def test_holm_bonferroni_adjustment():
    """Verify family-wise error rate control via Holm-Bonferroni step-down adjustment."""
    # Raw p-values: smallest gets multiplied by m, second smallest by m-1, etc.
    # Also verify enforce monotonicity: adj_p[i] <= adj_p[i+1]
    raw_p = [0.005, 0.015, 0.040, 0.200]
    adj_p = holm_bonferroni_adjust(raw_p)

    assert len(adj_p) == len(raw_p)
    # Check that adjusted p-values are >= raw p-values and <= 1.0
    for r, a in zip(raw_p, adj_p):
        assert a >= r
        assert a <= 1.0

    # Check monotonicity
    for i in range(len(adj_p) - 1):
        assert adj_p[i] <= adj_p[i + 1]


def test_mann_whitney_significance():
    """Verify two-sided Mann-Whitney U test on separated samples."""
    sample_fast = [1.2, 1.3, 1.1, 1.4, 1.25]
    sample_slow = [5.2, 5.5, 5.3, 5.8, 5.4]

    u_stat, p_val = stats.mannwhitneyu(sample_fast, sample_slow, alternative="two-sided")
    assert p_val < 0.01
    d = cliffs_delta(sample_fast, sample_slow)
    assert d == -1.0


def test_pca_variance_decomposition_orthogonality_and_sum():
    """Verify that PCA variance decomposition explains 100% variance and maintains orthogonality."""
    import os
    import pytest
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_path = os.path.join(repo_dir, "results", "publication_campaign", "raw_trials.jsonl")
    if not os.path.exists(raw_path):
        pytest.skip("Pre-run package: PCA variance decomposition requires post-campaign trial datasets")

    from benchmark.analyze_results import compute_pca_variance_decomposition
    pca_res = compute_pca_variance_decomposition()
    assert "regime_a_cold_prefill" in pca_res
    assert "regime_b_warm_kv_cache" in pca_res

    for regime_key in ["regime_a_cold_prefill", "regime_b_warm_kv_cache"]:
        data = pca_res[regime_key]
        assert data["n_trials"] in (480, 600)
        assert data["n_variables"] == 12

        # 1. Verify sum of explained variance is 100%
        assert np.isclose(data["sum_explained_variance_pct"], 100.0, atol=1e-5)

        # 2. Verify maximum orthogonality deviation is negligible (V.T @ V == I)
        assert data["orthogonality_max_error"] < 1e-10

        # 3. Verify that for each component, variable contributions sum to 100%
        for comp in data["components"]:
            contribs = list(comp["contributions_pct"].values())
            assert np.isclose(sum(contribs), 100.0, atol=0.2)


def test_fixed_sesoi_mbb_tost_90ci_duality_and_three_states():
    """M2/M3/M4/M5: Verify fixed SESOI (+-5.0 ms), exact 90% CI <-> p_tost < 0.05 duality, and 3-state Lakens rule."""
    import os
    import sys
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.path.join(repo_dir, "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    from reproduce_quad_platform_analysis import (
        SESOI_MS,
        TOST_ALPHA,
        TOST_BLOCK_SIZE,
        moving_block_bootstrap_tost,
    )

    assert SESOI_MS == 5.0
    assert TOST_BLOCK_SIZE == 3
    assert TOST_ALPHA == 0.05

    rng = np.random.default_rng(123)
    # 1. Equivalent case: identical distributions within +-5.0 ms
    c1_eq = rng.normal(20.0, 0.5, size=30)
    c2_eq = rng.normal(20.3, 0.5, size=30)
    res_eq = moving_block_bootstrap_tost(c1_eq, c2_eq, sesoi=SESOI_MS, block_size=TOST_BLOCK_SIZE)
    assert res_eq["status"] == "Equivalent"
    assert res_eq["p_tost"] < TOST_ALPHA
    assert res_eq["ci_90_low"] > -SESOI_MS and res_eq["ci_90_high"] < SESOI_MS

    # 2. Different case: shifted well outside +-5.0 ms
    c1_diff = rng.normal(20.0, 0.5, size=30)
    c2_diff = rng.normal(35.0, 0.5, size=30)
    res_diff = moving_block_bootstrap_tost(c1_diff, c2_diff, sesoi=SESOI_MS, block_size=TOST_BLOCK_SIZE)
    assert res_diff["status"] == "Different"
    assert res_diff["p_tost"] >= TOST_ALPHA
    assert res_diff["ci_90_low"] > SESOI_MS or res_diff["ci_90_high"] < -SESOI_MS

    # 3. Inconclusive case: centered at the +5.0 ms SESOI boundary so 90% CI straddles +5.0 ms
    c1_inc = rng.normal(20.0, 6.0, size=30)
    c2_inc = rng.normal(25.0, 6.0, size=30)
    res_inc = moving_block_bootstrap_tost(c1_inc, c2_inc, sesoi=SESOI_MS, block_size=TOST_BLOCK_SIZE)
    assert res_inc["status"] == "Inconclusive"
    assert res_inc["p_tost"] >= TOST_ALPHA
    assert not (res_inc["ci_90_low"] > -SESOI_MS and res_inc["ci_90_high"] < SESOI_MS)
    assert not (res_inc["ci_90_low"] > SESOI_MS or res_inc["ci_90_high"] < -SESOI_MS)


def test_mann_whitney_r1_variance_adjustment_conservative():
    """M4: Verify positive r1 inflates MW variance (n_eff < n, p_r1 >= p_std) while negative r1 retains n_eff = n."""
    import os
    import sys
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.path.join(repo_dir, "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    from reproduce_quad_platform_analysis import lag1_autocorr, mann_whitney_r1_adjusted

    # Pure linear ramp has ~0 detrended r1 (linear detrending removes monotone drift)
    ramp = [10.0 + 0.5 * i for i in range(30)]
    assert abs(lag1_autocorr(ramp, detrend=True)) < 1e-6

    # Stationary positively autocorrelated series (smooth low-frequency wave + small offset, zero linear trend)
    import math
    x_pos = [10.0 + 2.0 * math.sin(2.0 * math.pi * i / 10.0) for i in range(30)]
    y_pos = [11.5 + 2.0 * math.sin(2.0 * math.pi * i / 10.0 + 0.4) for i in range(30)]
    res_pos = mann_whitney_r1_adjusted(x_pos, y_pos)
    assert res_pos["r1_x"] > 0.5 and res_pos["r1_y"] > 0.5
    assert res_pos["n_eff1"] < 30.0 and res_pos["n_eff2"] < 30.0
    assert res_pos["vif"] > 1.0
    assert res_pos["p_r1"] >= res_pos["p_std"]

    # Negatively autocorrelated alternating series -> conservative n_eff = n
    x_neg = [10.0 + (2.0 if i % 2 == 0 else -2.0) for i in range(30)]
    y_neg = [20.0 + (2.0 if i % 2 == 0 else -2.0) for i in range(30)]
    res_neg = mann_whitney_r1_adjusted(x_neg, y_neg)
    assert res_neg["r1_x"] < 0.0 and res_neg["r1_y"] < 0.0
    assert res_neg["n_eff1"] == 30.0 and res_neg["n_eff2"] == 30.0
    assert res_neg["vif"] == 1.0


def test_w5_python_native_segregation_and_t7_90ci_alignment_on_generated_tables():
    """Etapa 1/2: Verify generated Tables 2, 7, 8 enforce W5 python_native segregation, Holm-Bonferroni TOST 3-state alignment, and b in {2,3,5} sensitivity."""
    import csv
    import os
    import re
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    t2_path = os.path.join(repo_dir, "audit_export", "tables", "table2_statistical_tests.md")
    t7_path = os.path.join(repo_dir, "audit_export", "tables", "table7_session_replication_comparison.md")
    t8_md_path = os.path.join(repo_dir, "audit_export", "tables", "table8_w5_enterprise_workload.md")
    t8_tex_path = os.path.join(repo_dir, "audit_export", "tables", "table8_w5_enterprise_workload.tex")
    sens_path = os.path.join(repo_dir, "audit_export", "tost_block_sensitivity.csv")

    t2 = open(t2_path, encoding="utf-8").read()
    for line in t2.splitlines():
        if line.startswith("| ") and "| W5 |" in line:
            assert "PythonNative" not in line, f"Confounded W5 PythonNative leaked into Table 2: {line}"

    t7 = open(t7_path, encoding="utf-8").read()
    row_count = 0
    for line in t7.splitlines():
        if not line.startswith("| ") or line.startswith("| Platform") or line.startswith("| :---"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 11:
            continue
        row_count += 1
        wl, contrast, ci_str, p_str, pa_str, status = parts[2], parts[3], parts[7], parts[8], parts[9], parts[10]
        if wl == "W5":
            assert "PythonNative" not in contrast, f"Confounded W5 PythonNative leaked into Table 7: {line}"
        assert status in {"Equivalent", "Different", "Inconclusive"}, f"Unexpected Table 7 status: {status}"
        m = re.match(r"\[([+-]?\d+\.\d+),\s*([+-]?\d+\.\d+)\]", ci_str)
        assert m, f"Could not parse 90% CI in Table 7: {ci_str}"
        lo, hi = float(m.group(1)), float(m.group(2))
        p_adj = 0.0 if pa_str.startswith("<") else float(pa_str)
        if status == "Equivalent":
            assert lo > -5.0 and hi < 5.0 and p_adj < 0.05, f"90% CI / Holm TOST mismatch in Table 7: {line}"
        elif status == "Different":
            assert (lo > 5.0 or hi < -5.0) and p_adj >= 0.05, f"Different status mismatch in Table 7: {line}"
        else:
            assert not (lo > -5.0 and hi < 5.0 and p_adj < 0.05) and not (lo > 5.0 or hi < -5.0), f"Inconclusive mismatch: {line}"
    assert row_count == 95, f"Expected 95 valid Table 7 pairs (102 minus 7 W5 python_native), got {row_count}"

    assert os.path.exists(sens_path), f"Missing block-size sensitivity CSV: {sens_path}"
    with open(sens_path, encoding="utf-8") as sf:
        s_rows = list(csv.DictReader(sf))
    assert [int(r["block_size_b"]) for r in s_rows] == [2, 3, 5]
    for sr in s_rows:
        assert int(sr["n_pairs"]) == 95
        assert int(sr["holm_equivalent"]) + int(sr["holm_different"]) + int(sr["holm_inconclusive"]) == 95

    t8_md = open(t8_md_path, encoding="utf-8").read()
    assert "Part A: Comparable W5 Orchestrators" in t8_md
    assert "Part B: Segregated / Non-Comparable Arm" in t8_md
    assert "Prompt / Comp. Tokens" in t8_md

    t8_tex = open(t8_tex_path, encoding="utf-8").read()
    assert "Part B: Segregated Non-Comparable Arm" in t8_tex
    assert all(ord(c) <= 127 for c in t8_tex), "Non-ASCII character found in table8_w5_enterprise_workload.tex"

