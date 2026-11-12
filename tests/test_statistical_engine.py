"""
Unit Tests for Statistical Inference Engine & Metrics
Testes Unitários para Motor de Inferência Estatística e Métricas

Author / Autor: Rafael Paniccia Cassetta (UFABC)
Language / Idioma: Bilingual (PT-BR & EN-US comments, English code)
"""

import numpy as np
from scipy import stats

from benchmark.analyze_results import (
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
    """Verify Cliff's delta and Vargha-Delaney A12 for strictly dominated distributions."""
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
