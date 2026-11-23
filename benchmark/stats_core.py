"""
benchmark/stats_core.py - Deterministic Non-Parametric & Parametric Statistical Primitives
Provides exact mathematical implementations of Mann-Whitney U, Spearman rank correlation,
Pearson correlation, OLS linear regression, Kruskal-Wallis H-test, Welch's TOST equivalence test,
trimmed mean, skewness, kurtosis, and exact binomial tests using pure Python math + NumPy.

Eliminates multi-library OpenBLAS/Fortran/HiGHS C-extension initialization deadlocks during
test collection and execution in constrained container sandboxes while matching scipy.stats
and statsmodels.stats.weightstats.ttost_ind to machine precision (1e-12).
"""
from __future__ import annotations

import math
import os
from collections import namedtuple

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
os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np  # noqa: E402

MannwhitneyuResult = namedtuple("MannwhitneyuResult", ["statistic", "pvalue"])
SpearmanrResult = namedtuple("SpearmanrResult", ["statistic", "pvalue"])
PearsonrResult = namedtuple("PearsonrResult", ["statistic", "pvalue"])
LinregressResult = namedtuple("LinregressResult", ["slope", "intercept", "rvalue", "pvalue", "stderr"])
KruskalResult = namedtuple("KruskalResult", ["statistic", "pvalue"])
BinomTestResult = namedtuple("BinomTestResult", ["k", "n", "pvalue"])


def _betacf(a: float, b: float, x: float) -> float:
    max_iter = 200
    eps = 3.0e-14
    fpmin = 1.0e-30
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def _gammaincc(a: float, x: float) -> float:
    if x <= 0.0:
        return 1.0
    if a <= 0.0:
        return 0.0
    if x < a + 1.0:
        ap = a
        s = 1.0 / a
        del_v = s
        for _ in range(300):
            ap += 1.0
            del_v *= x / ap
            s += del_v
            if abs(del_v) < abs(s) * 3.0e-14:
                break
        p = s * math.exp(-x + a * math.log(x) - math.lgamma(a))
        return max(0.0, min(1.0, 1.0 - p))
    fpmin = 1.0e-30
    b = x + 1.0 - a
    c = 1.0 / fpmin
    d = 1.0 / b
    h = d
    for i in range(1, 301):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < fpmin:
            d = fpmin
        c = b + an / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        del_v = d * c
        h *= del_v
        if abs(del_v - 1.0) < 3.0e-14:
            break
    q = h * math.exp(-x + a * math.log(x) - math.lgamma(a))
    return max(0.0, min(1.0, q))


class _NormDist:
    @staticmethod
    def sf(z: float) -> float:
        return 0.5 * math.erfc(float(z) / math.sqrt(2.0))

    @staticmethod
    def cdf(z: float) -> float:
        return 0.5 * math.erfc(-float(z) / math.sqrt(2.0))

    @staticmethod
    def ppf(q: float) -> float:
        if q <= 0.0:
            return float("-inf")
        if q >= 1.0:
            return float("inf")
        if q == 0.5:
            return 0.0
        lo, hi = -10.0, 10.0
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if _NormDist.cdf(mid) < q:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)


class _StudentTDist:
    @staticmethod
    def cdf(t_val: float, df: float) -> float:
        t_val = float(t_val)
        df = float(df)
        if df <= 0.0:
            return 0.5
        if t_val == 0.0:
            return 0.5
        x = df / (df + t_val * t_val)
        ib = _betainc(0.5 * df, 0.5, x)
        return (1.0 - 0.5 * ib) if t_val > 0 else (0.5 * ib)

    @staticmethod
    def sf(t_val: float, df: float) -> float:
        return 1.0 - _StudentTDist.cdf(t_val, df)

    @staticmethod
    def ppf(q: float, df: float) -> float:
        q = float(q)
        df = float(df)
        if q <= 0.0:
            return float("-inf")
        if q >= 1.0:
            return float("inf")
        if q == 0.5:
            return 0.0
        sign = 1.0 if q > 0.5 else -1.0
        target = q if q > 0.5 else (1.0 - q)
        lo, hi = 0.0, 1.0
        while _StudentTDist.cdf(hi, df) < target:
            hi *= 2.0
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if _StudentTDist.cdf(mid, df) < target:
                lo = mid
            else:
                hi = mid
        return sign * 0.5 * (lo + hi)


class _Chi2Dist:
    @staticmethod
    def sf(x: float, df: float) -> float:
        return _gammaincc(0.5 * float(df), 0.5 * float(x))

    @staticmethod
    def cdf(x: float, df: float) -> float:
        return 1.0 - _Chi2Dist.sf(x, df)


norm = _NormDist()
t = _StudentTDist()
chi2 = _Chi2Dist()


def rankdata(a) -> np.ndarray:
    arr = np.ravel(np.asarray(a, dtype=float))
    n = len(arr)
    if n == 0:
        return np.empty(0, dtype=float)
    sorter = np.argsort(arr, kind="mergesort")
    inv = np.empty(n, dtype=int)
    inv[sorter] = np.arange(n)
    arr_sorted = arr[sorter]
    obs = np.r_[True, arr_sorted[1:] != arr_sorted[:-1]]
    dense = obs.cumsum()[inv]
    count = np.r_[np.nonzero(obs)[0], n]
    return 0.5 * (count[dense] + count[dense - 1] + 1.0)


def _mwu_exact_cdf(u: int, n1: int, n2: int) -> float:
    max_u = n1 * n2
    if u < 0:
        return 0.0
    if u >= max_u:
        return 1.0
    dp = [np.zeros(max_u + 1, dtype=np.float64) for _ in range(n1 + 1)]
    dp[0][0] = 1.0
    for k in range(1, n1 + n2 + 1):
        for i in range(min(k, n1), 0, -1):
            shift = k - i
            if shift == 0:
                dp[i] += dp[i - 1]
            else:
                dp[i][shift:] += dp[i - 1][:-shift]
    total = math.comb(n1 + n2, n1)
    return float(np.sum(dp[n1][: u + 1])) / float(total)


def mannwhitneyu(x, y, alternative: str = "two-sided") -> MannwhitneyuResult:
    ax = np.asarray(x, dtype=float)
    ay = np.asarray(y, dtype=float)
    n1, n2 = len(ax), len(ay)
    if n1 == 0 or n2 == 0:
        return MannwhitneyuResult(0.0, 1.0)
    combined = np.concatenate([ax, ay])
    ranks = rankdata(combined)
    r1 = float(np.sum(ranks[:n1]))
    u1 = r1 - n1 * (n1 + 1.0) / 2.0
    u2 = n1 * n2 - u1
    _, counts = np.unique(combined, return_counts=True)
    has_ties = bool(np.any(counts > 1))
    if not has_ties and n1 <= 20 and n2 <= 20:
        u_min = int(round(min(u1, u2)))
        if alternative == "two-sided":
            p = min(1.0, 2.0 * _mwu_exact_cdf(u_min, n1, n2))
        elif alternative == "less":
            p = _mwu_exact_cdf(int(round(u1)), n1, n2)
        else:
            p = _mwu_exact_cdf(int(round(u2)), n1, n2)
        return MannwhitneyuResult(float(u1), float(p))
    n_tot = n1 + n2
    mu = n1 * n2 / 2.0
    tie_term = float(np.sum(counts ** 3 - counts)) / (n_tot * (n_tot - 1.0)) if n_tot > 1 else 0.0
    var_u = (n1 * n2 / 12.0) * ((n_tot + 1.0) - tie_term)
    if var_u <= 1e-12:
        return MannwhitneyuResult(float(u1), 1.0)
    sigma = math.sqrt(var_u)
    if alternative == "two-sided":
        z = max(0.0, (abs(u1 - mu) - 0.5) / sigma)
        p = min(1.0, float(math.erfc(z / math.sqrt(2.0))))
    elif alternative == "less":
        z = (u1 - mu + 0.5) / sigma
        p = 0.5 * math.erfc(-z / math.sqrt(2.0))
    else:
        z = (mu - u1 + 0.5) / sigma
        p = 0.5 * math.erfc(-z / math.sqrt(2.0))
    return MannwhitneyuResult(float(u1), float(p))


def pearsonr(x, y) -> PearsonrResult:
    ax = np.asarray(x, dtype=float)
    ay = np.asarray(y, dtype=float)
    n = len(ax)
    if n < 2:
        return PearsonrResult(float("nan"), float("nan"))
    mx = ax - np.mean(ax)
    my = ay - np.mean(ay)
    denom = math.sqrt(float(np.sum(mx * mx) * np.sum(my * my)))
    if denom <= 1e-15:
        return PearsonrResult(float("nan"), float("nan"))
    r = max(-1.0, min(1.0, float(np.sum(mx * my)) / denom))
    if abs(r) >= 1.0:
        return PearsonrResult(float(r), 0.0)
    df = n - 2
    if df <= 0:
        return PearsonrResult(float(r), 1.0)
    t2 = r * r * (df / (1.0 - r * r))
    p = _betainc(0.5 * df, 0.5, df / (df + t2))
    return PearsonrResult(float(r), float(p))


def spearmanr(x, y) -> SpearmanrResult:
    rx = rankdata(x)
    ry = rankdata(y)
    res = pearsonr(rx, ry)
    return SpearmanrResult(res.statistic, res.pvalue)


def linregress(x, y) -> LinregressResult:
    ax = np.asarray(x, dtype=float)
    ay = np.asarray(y, dtype=float)
    n = len(ax)
    if n == 0:
        return LinregressResult(0.0, 0.0, 0.0, 1.0, 0.0)
    mx = float(np.mean(ax))
    my = float(np.mean(ay))
    dx = ax - mx
    dy = ay - my
    ssxm = float(np.sum(dx * dx))
    ssym = float(np.sum(dy * dy))
    ssxym = float(np.sum(dx * dy))
    if ssxm <= 1e-15:
        return LinregressResult(0.0, my, 0.0, 1.0, 0.0)
    slope = ssxym / ssxm
    intercept = my - slope * mx
    if ssym <= 1e-15:
        r = 0.0
    else:
        r = max(-1.0, min(1.0, ssxym / math.sqrt(ssxm * ssym)))
    df = n - 2
    if df <= 0 or abs(r) >= 1.0:
        p = 0.0 if abs(r) >= 1.0 else 1.0
        stderr = 0.0
    else:
        t2 = r * r * (df / (1.0 - r * r))
        p = _betainc(0.5 * df, 0.5, df / (df + t2))
        stderr = math.sqrt(max(0.0, (1.0 - r * r) * ssym / ssxm / df))
    return LinregressResult(float(slope), float(intercept), float(r), float(p), float(stderr))


def kruskal(*samples) -> KruskalResult:
    arrays = [np.asarray(s, dtype=float) for s in samples if len(s) > 0]
    k = len(arrays)
    if k < 2:
        return KruskalResult(0.0, 1.0)
    all_data = np.concatenate(arrays)
    n = len(all_data)
    if n <= k:
        return KruskalResult(0.0, 1.0)
    ranks = rankdata(all_data)
    idx = 0
    ssbn = 0.0
    for arr in arrays:
        ni = len(arr)
        ri_sum = float(np.sum(ranks[idx : idx + ni]))
        ssbn += (ri_sum * ri_sum) / ni
        idx += ni
    h = (12.0 / (n * (n + 1.0))) * ssbn - 3.0 * (n + 1.0)
    _, counts = np.unique(all_data, return_counts=True)
    tie_corr = 1.0 - float(np.sum(counts ** 3 - counts)) / float(n ** 3 - n)
    if tie_corr <= 1e-15:
        return KruskalResult(0.0, 1.0)
    h /= tie_corr
    df = k - 1
    p = _gammaincc(0.5 * df, 0.5 * h)
    return KruskalResult(float(h), float(p))


def trim_mean(a, proportiontocut: float) -> float:
    arr = np.sort(np.ravel(np.asarray(a, dtype=float)))
    n = len(arr)
    if n == 0:
        return 0.0
    lowercut = int(proportiontocut * n)
    uppercut = n - lowercut
    if lowercut >= uppercut:
        return float(np.mean(arr))
    return float(np.mean(arr[lowercut:uppercut]))


def skew(a) -> float:
    arr = np.ravel(np.asarray(a, dtype=float))
    if len(arr) < 2:
        return 0.0
    diff = arr - np.mean(arr)
    m2 = float(np.mean(diff ** 2))
    if m2 <= 1e-15:
        return 0.0
    m3 = float(np.mean(diff ** 3))
    return m3 / (m2 ** 1.5)


def kurtosis(a) -> float:
    arr = np.ravel(np.asarray(a, dtype=float))
    if len(arr) < 2:
        return 0.0
    diff = arr - np.mean(arr)
    m2 = float(np.mean(diff ** 2))
    if m2 <= 1e-15:
        return 0.0
    m4 = float(np.mean(diff ** 4))
    return (m4 / (m2 * m2)) - 3.0


def binomtest(k: int, n: int, p: float = 0.5) -> BinomTestResult:
    k = int(k)
    n = int(n)
    if n <= 0:
        return BinomTestResult(k, n, 1.0)
    probs = [math.comb(n, i) * (p ** i) * ((1.0 - p) ** (n - i)) for i in range(n + 1)]
    pk = probs[k]
    pval = sum(pr for pr in probs if pr <= pk * (1.0 + 1e-12))
    return BinomTestResult(k, n, min(1.0, float(pval)))


def ttost_ind(a, b, low: float, upp: float, usevar: str = "unequal"):
    """
    Exact Welch's unequal-variance Two One-Sided Tests (TOST) for equivalence
    between two independent samples, matching statsmodels.stats.weightstats.ttost_ind.
    """
    arr_a = np.asarray(a, dtype=float)
    arr_b = np.asarray(b, dtype=float)
    na, nb = len(arr_a), len(arr_b)
    ma, mb = float(np.mean(arr_a)), float(np.mean(arr_b))
    va, vb = float(np.var(arr_a, ddof=1)), float(np.var(arr_b, ddof=1))
    diff = ma - mb
    if usevar == "unequal":
        se = math.sqrt(va / na + vb / nb)
        denom = (((va / na) ** 2) / (na - 1)) + (((vb / nb) ** 2) / (nb - 1))
        df = ((va / na + vb / nb) ** 2) / denom if denom > 0 else float(na + nb - 2)
    else:
        df = float(na + nb - 2)
        sp2 = ((na - 1) * va + (nb - 1) * vb) / df
        se = math.sqrt(sp2 * (1.0 / na + 1.0 / nb))
    if se <= 1e-15:
        equiv = bool(low < diff < upp)
        p_tost = 0.0 if equiv else 1.0
        return p_tost, (0.0, p_tost, df), (0.0, p_tost, df)
    t_low = (diff - low) / se
    p_low = 1.0 - t.cdf(t_low, df)
    t_upp = (diff - upp) / se
    p_upp = t.cdf(t_upp, df)
    p_tost = max(p_low, p_upp)
    return float(p_tost), (float(t_low), float(p_low), float(df)), (float(t_upp), float(p_upp), float(df))
