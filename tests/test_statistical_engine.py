"""
Unit Tests for Statistical Inference Engine & Metrics
Testes Unitários para Motor de Inferência Estatística e Métricas

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

import numpy as np
import pytest
from scipy import stats


def garwood_poisson_interval(k: int, confidence: float = 0.95):
    """
    Compute exact Poisson fiducial confidence interval using Garwood's (1936) Chi-Square formulation.
    """
    alpha = 1.0 - confidence
    if k == 0:
        lower = 0.0
    else:
        lower = 0.5 * stats.chi2.ppf(alpha / 2.0, 2 * k)
    upper = 0.5 * stats.chi2.ppf(1.0 - alpha / 2.0, 2 * (k + 1))
    return lower, upper


def compute_edp(energy_joules: float, latency_seconds: float) -> float:
    """Compute Energy-Delay Product (EDP) in Joule-seconds."""
    return energy_joules * latency_seconds


def cliffs_delta(lst1, lst2):
    """
    Compute Cliff's Delta non-parametric effect size d in [-1, 1].
    """
    n1, n2 = len(lst1), len(lst2)
    more = sum(1 for x in lst1 for y in lst2 if x > y)
    less = sum(1 for x in lst1 for y in lst2 if x < y)
    return (more - less) / (n1 * n2)


def vargha_delaney_a12(lst1, lst2):
    """
    Compute Vargha-Delaney A12 effect size metric in [0, 1].
    A12 = 0.5 implies stochastic equivalence; > 0.5 implies lst1 is stochastically larger.
    """
    d = cliffs_delta(lst1, lst2)
    return (d + 1.0) / 2.0


def test_garwood_bounds_accuracy():
    """Verify Garwood bounds against known mathematical values."""
    # For k=0 at 95% confidence (alpha=0.05), lower=0, upper ~ 3.688879
    l0, u0 = garwood_poisson_interval(0, 0.95)
    assert l0 == 0.0
    assert pytest.approx(u0, 0.001) == 3.689

    # For k=10 at 95% confidence, lower ~ 4.795, upper ~ 18.390
    l10, u10 = garwood_poisson_interval(10, 0.95)
    assert l10 < 10 < u10
    assert pytest.approx(l10, 0.01) == 4.795
    assert pytest.approx(u10, 0.01) == 18.390


def test_edp_calculation():
    """Verify Energy-Delay Product calculation."""
    e = 15.0  # Joules
    t = 2.0   # seconds
    edp = compute_edp(e, t)
    assert edp == 30.0


def test_mann_whitney_and_cliffs_delta():
    """Verify non-parametric Mann-Whitney U test and Cliff's Delta effect size."""
    # Sample A clearly faster than Sample B
    picoclaw_latencies = [1440.0, 1445.0, 1450.0, 1442.0, 1448.0]
    openclaw_latencies = [1650.0, 1680.0, 1690.0, 1670.0, 1660.0]

    u_stat, p_val = stats.mannwhitneyu(picoclaw_latencies, openclaw_latencies, alternative="two-sided")
    assert p_val < 0.01, "Expected statistically significant difference"

    d = cliffs_delta(picoclaw_latencies, openclaw_latencies)
    assert d == -1.0, f"Expected Cliff's delta of -1.0, got {d}"

    a12 = vargha_delaney_a12(picoclaw_latencies, openclaw_latencies)
    assert a12 == 0.0, f"Expected A12 of 0.0, got {a12}"


def test_cameron_trivedi_equidispersion_test():
    """Verify Cameron & Trivedi auxiliary regression diagnostic for Poisson overdispersion."""
    np.random.seed(42)
    # Generate authentic Poisson data
    poisson_samples = np.random.poisson(lam=10.0, size=100)
    mu_hat = np.mean(poisson_samples)

    # Dependent variable in auxiliary regression
    dep = ((poisson_samples - mu_hat) ** 2 - poisson_samples) / mu_hat
    indep = mu_hat * np.ones_like(dep)

    slope, intercept, r_value, p_value, std_err = stats.linregress(indep, dep)
    # Under true Poisson, slope should be statistically indistinguishable from 0
    t_stat = slope / max(std_err, 1e-6)
    assert abs(t_stat) < 1.96, f"t-statistic {t_stat} exceeds critical value 1.96"
