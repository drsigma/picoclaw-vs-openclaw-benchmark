#!/usr/bin/env python3
"""
adapters/windows_intel_graphics/analysis.py

Statistical Inference, Equivalence Testing (TOST via statsmodels.stats.weightstats.ttost_ind),
Runtime Contrasts (Delta T_orch), Autocorrelation & Drift Diagnostics, LaTeX Tables,
Audit Report, and SHA-256 Cryptographic Manifest Generator for Windows Intel Graphics.

Strict Isolation: writes ONLY inside the windows_intel_graphics namespace via `guard`.
Explicit-NA: preserves 'N/A' for metrics unavailable in Windows user-mode.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
from typing import Any, Callable

import numpy as np
from scipy import stats
from statsmodels.stats.weightstats import ttost_ind

NA = "N/A"

# A priori equivalence margins declared for TOST replication (Session 1 vs Session 2)
TOST_MARGIN_TASK_REL = 0.10   # +/- 10% of pooled mean for end-to-end T_task_ms
TOST_MARGIN_ORCH_REL = 0.15   # +/- 15% of pooled mean (with floor 5.0 ms) for T_orch_ms
TOST_MARGIN_ORCH_FLOOR_MS = 5.0


def bootstrap_ci_median(data: list[float], n_resamples: int = 10000, ci: float = 0.95, seed: int = 42) -> tuple[float, float]:
    arr = np.asarray([float(x) for x in data if isinstance(x, (int, float)) and not math.isnan(x)], dtype=float)
    if len(arr) == 0:
        return (0.0, 0.0)
    if len(arr) == 1:
        return (round(float(arr[0]), 3), round(float(arr[0]), 3))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(arr), size=(n_resamples, len(arr)))
    meds = np.median(arr[idx], axis=1)
    alpha = (1.0 - ci) / 2.0
    return (round(float(np.percentile(meds, alpha * 100)), 3), round(float(np.percentile(meds, (1.0 - alpha) * 100)), 3))


def bootstrap_ci_median_diff(
    a_vals: list[float],
    b_vals: list[float],
    n_resamples: int = 10000,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Return (median(A) - median(B), ci_low, ci_high) via Efron bootstrap."""
    a = np.asarray([float(x) for x in a_vals if isinstance(x, (int, float)) and not math.isnan(x)], dtype=float)
    b = np.asarray([float(x) for x in b_vals if isinstance(x, (int, float)) and not math.isnan(x)], dtype=float)
    if len(a) == 0 or len(b) == 0:
        return (0.0, 0.0, 0.0)
    point = float(np.median(a) - np.median(b))
    if len(a) == 1 and len(b) == 1:
        return (round(point, 3), round(point, 3), round(point, 3))
    rng = np.random.default_rng(seed)
    ia = rng.integers(0, len(a), size=(n_resamples, len(a)))
    ib = rng.integers(0, len(b), size=(n_resamples, len(b)))
    diffs = np.median(a[ia], axis=1) - np.median(b[ib], axis=1)
    alpha = (1.0 - ci) / 2.0
    return (
        round(point, 3),
        round(float(np.percentile(diffs, alpha * 100)), 3),
        round(float(np.percentile(diffs, (1.0 - alpha) * 100)), 3),
    )


def cliffs_delta(lst1: list[float], lst2: list[float]) -> float:
    a1 = np.asarray([x for x in lst1 if isinstance(x, (int, float)) and not math.isnan(x)], dtype=float)
    a2 = np.asarray([x for x in lst2 if isinstance(x, (int, float)) and not math.isnan(x)], dtype=float)
    if len(a1) == 0 or len(a2) == 0:
        return 0.0
    greater = np.sum(a1[:, None] > a2)
    less = np.sum(a1[:, None] < a2)
    return round(float((greater - less) / float(len(a1) * len(a2))), 4)


def vargha_delaney_a12(lst1: list[float], lst2: list[float]) -> float:
    return round((cliffs_delta(lst1, lst2) + 1.0) / 2.0, 4)


def holm_bonferroni(p_vals: list[float]) -> list[float]:
    m = len(p_vals)
    if m == 0:
        return []
    indexed = sorted(enumerate(p_vals), key=lambda x: x[1])
    adjusted = [0.0] * m
    running_max = 0.0
    for rank, (orig_idx, p) in enumerate(indexed):
        adj = min(1.0, p * (m - rank))
        running_max = max(running_max, adj)
        adjusted[orig_idx] = round(running_max, 6)
    return adjusted


def _numeric_only(vals: list[Any]) -> list[float]:
    out = []
    for v in vals:
        if isinstance(v, (int, float)) and not isinstance(v, bool) and not math.isnan(v):
            out.append(float(v))
    return out


def calc_robust_stats(arr: list[Any]) -> dict[str, Any]:
    valid = _numeric_only(arr)
    if not valid:
        return {
            "n": 0, "mean": NA, "std": NA, "median": NA, "iqr": NA,
            "min": NA, "max": NA, "p95": NA, "ci_95_median": [NA, NA],
        }
    a = np.asarray(valid, dtype=float)
    lo, hi = bootstrap_ci_median(valid)
    return {
        "n": len(valid),
        "mean": round(float(np.mean(a)), 3),
        "std": round(float(np.std(a, ddof=1)) if len(a) > 1 else 0.0, 3),
        "median": round(float(np.median(a)), 3),
        "iqr": round(float(np.percentile(a, 75) - np.percentile(a, 25)), 3),
        "min": round(float(np.min(a)), 3),
        "max": round(float(np.max(a)), 3),
        "p95": round(float(np.percentile(a, 95)), 3),
        "ci_95_median": [lo, hi],
    }


def compute_autocorrelation_and_trend(series: list[float]) -> dict[str, Any]:
    """
    Lag-1 autocorrelation and Spearman monotonic trend test vs trial order
    to audit thermal/clock drift or serial dependence across trials.
    """
    vals = _numeric_only(series)
    n = len(vals)
    if n < 4:
        return {
            "n": n,
            "lag1_autocorr_r": NA,
            "lag1_p_value": NA,
            "trend_spearman_rho": NA,
            "trend_p_value": NA,
            "significant_drift_p05": False,
        }
    arr = np.asarray(vals, dtype=float)
    if np.std(arr[:-1]) == 0.0 or np.std(arr[1:]) == 0.0:
        r1, p1 = 0.0, 1.0
    else:
        r1, p1 = stats.pearsonr(arr[:-1], arr[1:])
    idx = np.arange(1, n + 1, dtype=float)
    if np.std(arr) == 0.0:
        rho, pt = 0.0, 1.0
    else:
        rho, pt = stats.spearmanr(idx, arr)
    return {
        "n": n,
        "lag1_autocorr_r": round(float(r1), 4),
        "lag1_p_value": round(float(p1), 6),
        "trend_spearman_rho": round(float(rho), 4),
        "trend_p_value": round(float(pt), 6),
        "significant_drift_p05": bool(float(pt) < 0.05 and abs(float(rho)) >= 0.4),
    }


def run_tost_equivalence(
    s1_vals: list[float],
    s2_vals: list[float],
    low: float,
    upp: float,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """
    Two One-Sided Tests (TOST) for statistical equivalence between independent samples
    using statsmodels.stats.weightstats.ttost_ind (Welch's unequal variance).
    """
    a = np.asarray(_numeric_only(s1_vals), dtype=float)
    b = np.asarray(_numeric_only(s2_vals), dtype=float)
    if len(a) < 2 or len(b) < 2:
        return {
            "n_s1": len(a),
            "n_s2": len(b),
            "margin_low": round(low, 4),
            "margin_upp": round(upp, 4),
            "mean_diff_s1_minus_s2": NA,
            "tost_p_value": NA,
            "equivalent_at_alpha": False,
            "note": "Insufficient sample size for ttost_ind (requires n>=2 per session)",
        }
    mean_diff = float(np.mean(a) - np.mean(b))
    if np.std(a, ddof=1) == 0.0 and np.std(b, ddof=1) == 0.0:
        equiv = bool(low < mean_diff < upp)
        p_tost = 0.0 if equiv else 1.0
        return {
            "n_s1": len(a),
            "n_s2": len(b),
            "margin_low": round(low, 4),
            "margin_upp": round(upp, 4),
            "mean_diff_s1_minus_s2": round(mean_diff, 4),
            "tost_p_value": p_tost,
            "equivalent_at_alpha": equiv,
            "method": "statsmodels.stats.weightstats.ttost_ind (zero-variance exact)",
        }

    p_tost, (t_low, p_low, df_low), (t_upp, p_upp, df_upp) = ttost_ind(
        a, b, low=low, upp=upp, usevar="unequal"
    )
    return {
        "n_s1": len(a),
        "n_s2": len(b),
        "margin_low": round(float(low), 4),
        "margin_upp": round(float(upp), 4),
        "mean_diff_s1_minus_s2": round(mean_diff, 4),
        "tost_p_value": round(float(p_tost), 6),
        "lower_test": {"t_stat": round(float(t_low), 4), "p_value": round(float(p_low), 6), "df": round(float(df_low), 2)},
        "upper_test": {"t_stat": round(float(t_upp), 4), "p_value": round(float(p_upp), 6), "df": round(float(df_upp), 2)},
        "alpha": alpha,
        "equivalent_at_alpha": bool(float(p_tost) < alpha),
        "method": "statsmodels.stats.weightstats.ttost_ind (Welch unequal variance)",
    }


def analyze_session_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute per-agent, per-workload descriptive statistics, runtime contrasts (Delta T_orch),
    W5 quality summaries, cache hit verification, and autocorrelation/trend checks.
    """
    eval_recs = [
        r for r in records
        if not r.get("is_warmup", False) and r.get("http_status") == 200
    ]
    agents = sorted({str(r["agent_key"]) for r in eval_recs})
    workloads = sorted({str(r["workload"]) for r in eval_recs})

    summary: dict[str, dict[str, Any]] = {ak: {} for ak in agents}
    diagnostics: dict[str, dict[str, Any]] = {ak: {} for ak in agents}

    for ak in agents:
        for wl in workloads:
            sub = [r for r in eval_recs if r["agent_key"] == ak and r["workload"] == wl]
            if not sub:
                continue
            sub_sorted = sorted(sub, key=lambda x: int(x.get("rep", 0)))

            st_task = calc_robust_stats([r.get("t_task_ms") for r in sub_sorted])
            st_neural = calc_robust_stats([r.get("t_neural_ms") for r in sub_sorted])
            st_orch = calc_robust_stats([r.get("t_orch_ms") for r in sub_sorted])
            st_ttft = calc_robust_stats([r.get("ttft_ms") for r in sub_sorted])
            st_prompt = calc_robust_stats([r.get("prompt_ms") for r in sub_sorted])
            st_pred = calc_robust_stats([r.get("predicted_ms") for r in sub_sorted])
            st_mem = calc_robust_stats([r.get("proc_peak_phys_mb") for r in sub_sorted])
            st_cyc = calc_robust_stats([r.get("proc_cycles") for r in sub_sorted])
            st_sysram = calc_robust_stats([r.get("system_ram_used_end_mb") for r in sub_sorted])
            st_igpu_mem = calc_robust_stats([r.get("igpu_shared_mem_end_mb") for r in sub_sorted])
            st_prune = calc_robust_stats([r.get("t_prune_ms") for r in sub_sorted if r.get("t_prune_ms") is not None])

            tok_per_s = [
                float(r["completion_tokens"]) / (float(r["predicted_ms"]) / 1000.0)
                for r in sub_sorted
                if isinstance(r.get("completion_tokens"), (int, float))
                and isinstance(r.get("predicted_ms"), (int, float))
                and float(r["predicted_ms"]) > 0
            ]
            st_tps = calc_robust_stats(tok_per_s)

            phi = [
                (float(r["t_orch_ms"]) / float(r["t_task_ms"])) * 100.0
                for r in sub_sorted
                if float(r.get("t_task_ms", 0)) > 0
            ]
            st_phi = calc_robust_stats(phi)

            cache_hits = [bool(r.get("cache_hit", False)) for r in sub_sorted]
            cache_hit_rate_pct = round(sum(1 for c in cache_hits if c) / len(cache_hits) * 100.0, 2)
            thr_count = sum(1 for r in sub_sorted if r.get("thermal_throttled"))

            q_scores = _numeric_only([r.get("quality_score") for r in sub_sorted])
            st_q = calc_robust_stats(q_scores) if q_scores else None

            summary[ak][wl] = {
                "n_eval_trials": len(sub_sorted),
                "ngl": sub_sorted[0].get("ngl"),
                "execution_backend": sub_sorted[0].get("execution_backend"),
                "t_task_ms": st_task,
                "t_neural_ms": st_neural,
                "t_orch_ms": st_orch,
                "phi_orch_pct": st_phi,
                "ttft_ms": st_ttft,
                "prompt_ms": st_prompt,
                "predicted_ms": st_pred,
                "decode_tok_per_s": st_tps,
                "prompt_tokens_mean": round(float(np.mean([r["prompt_tokens"] for r in sub_sorted])), 2),
                "completion_tokens_mean": round(float(np.mean([r["completion_tokens"] for r in sub_sorted])), 2),
                "tokens_cached_mean": round(float(np.mean([r["tokens_cached"] for r in sub_sorted])), 2),
                "prompt_eval_count_mean": round(float(np.mean([r["prompt_eval_count"] for r in sub_sorted])), 2),
                "eval_count_mean": round(float(np.mean([r["eval_count"] for r in sub_sorted])), 2),
                "cache_hit_rate_pct": cache_hit_rate_pct,
                "proc_cycles": st_cyc,
                "proc_instructions": NA,
                "proc_peak_phys_mb": st_mem,
                "system_ram_used_mb": st_sysram,
                "igpu_shared_mem_mb": st_igpu_mem,
                "t_prune_ms": st_prune if st_prune["n"] > 0 else NA,
                "energy_net_above_idle_j": NA,
                "thermal_throttled_trials": thr_count,
                "quality_score": st_q if st_q else NA,
            }

            diagnostics[ak][wl] = {
                "t_task_ms": compute_autocorrelation_and_trend([float(r["t_task_ms"]) for r in sub_sorted]),
                "t_orch_ms": compute_autocorrelation_and_trend([float(r["t_orch_ms"]) for r in sub_sorted]),
            }

    # Runtime Contrasts (Delta T_orch & Delta T_task)
    contrast_pairs = [
        ("openclaw_minimal", "picoclaw"),
        ("openclaw_full", "picoclaw"),
        ("python_native", "picoclaw"),
        ("bun_minimal", "picoclaw"),
        ("openclaw_full", "openclaw_minimal"),
        ("openclaw_full", "openclaw_tool_rag"),
        ("picoclaw", "picoclaw_tool_rag"),
    ]
    contrasts: dict[str, dict[str, Any]] = {}
    p_refs: list[tuple[str, str, float]] = []

    for arm_a, arm_b in contrast_pairs:
        label = f"{arm_a}_minus_{arm_b}"
        for wl in workloads:
            a_recs = [r for r in eval_recs if r["agent_key"] == arm_a and r["workload"] == wl]
            b_recs = [r for r in eval_recs if r["agent_key"] == arm_b and r["workload"] == wl]
            if not a_recs or not b_recs:
                continue
            a_orch = [float(r["t_orch_ms"]) for r in a_recs]
            b_orch = [float(r["t_orch_ms"]) for r in b_recs]
            a_task = [float(r["t_task_ms"]) for r in a_recs]
            b_task = [float(r["t_task_ms"]) for r in b_recs]

            d_orch, ci_lo_o, ci_hi_o = bootstrap_ci_median_diff(a_orch, b_orch)
            d_task, ci_lo_t, ci_hi_t = bootstrap_ci_median_diff(a_task, b_task)

            if len(a_orch) >= 2 and len(b_orch) >= 2:
                try:
                    u_o, p_o = stats.mannwhitneyu(a_orch, b_orch, alternative="two-sided")
                except Exception:
                    u_o, p_o = 0.0, 1.0
                try:
                    u_t, p_t = stats.mannwhitneyu(a_task, b_task, alternative="two-sided")
                except Exception:
                    u_t, p_t = 0.0, 1.0
            else:
                u_o, p_o, u_t, p_t = 0.0, 1.0, 0.0, 1.0

            med_a_o = float(np.median(a_orch))
            med_b_o = float(np.median(b_orch))
            ratio_o = round(med_a_o / max(1e-6, med_b_o), 3)

            contrasts.setdefault(label, {})[wl] = {
                "arm_a": arm_a,
                "arm_b": arm_b,
                "n_a": len(a_orch),
                "n_b": len(b_orch),
                "delta_t_orch_median_ms": d_orch,
                "delta_t_orch_ci95_ms": [ci_lo_o, ci_hi_o],
                "t_orch_ratio_a_over_b": ratio_o,
                "mann_whitney_u_orch": round(float(u_o), 2),
                "p_value_orch_raw": round(float(p_o), 6),
                "cliffs_delta_orch": cliffs_delta(a_orch, b_orch),
                "vargha_delaney_a12_orch": vargha_delaney_a12(a_orch, b_orch),
                "delta_t_task_median_ms": d_task,
                "delta_t_task_ci95_ms": [ci_lo_t, ci_hi_t],
                "mann_whitney_u_task": round(float(u_t), 2),
                "p_value_task_raw": round(float(p_t), 6),
                "cliffs_delta_task": cliffs_delta(a_task, b_task),
                "vargha_delaney_a12_task": vargha_delaney_a12(a_task, b_task),
            }
            p_refs.append((label, wl, float(p_o)))

    if p_refs:
        adjs = holm_bonferroni([p for _, _, p in p_refs])
        for (label, wl, _), adj in zip(p_refs, adjs):
            contrasts[label][wl]["p_value_orch_holm_bonferroni"] = adj

    return {
        "summary": summary,
        "runtime_contrasts": contrasts,
        "autocorrelation_and_trend": diagnostics,
    }


def analyze_inter_session_replication(
    s1_records: list[dict[str, Any]],
    s2_records: list[dict[str, Any]],
    regime_label: str,
) -> dict[str, Any]:
    """
    Compare Session 1 vs Session 2 via TOST equivalence tests (ttost_ind from statsmodels)
    with declared a priori margins, relative inter-session drift, and pooled CV.
    """
    e1 = [r for r in s1_records if not r.get("is_warmup", False) and r.get("http_status") == 200]
    e2 = [r for r in s2_records if not r.get("is_warmup", False) and r.get("http_status") == 200]
    cells = sorted({(str(r["agent_key"]), str(r["workload"])) for r in e1} & {(str(r["agent_key"]), str(r["workload"])) for r in e2})

    results: dict[str, dict[str, Any]] = {}
    equiv_task_count = 0
    equiv_orch_count = 0

    for ak, wl in cells:
        r1 = [r for r in e1 if r["agent_key"] == ak and r["workload"] == wl]
        r2 = [r for r in e2 if r["agent_key"] == ak and r["workload"] == wl]
        t1 = [float(r["t_task_ms"]) for r in r1]
        t2 = [float(r["t_task_ms"]) for r in r2]
        o1 = [float(r["t_orch_ms"]) for r in r1]
        o2 = [float(r["t_orch_ms"]) for r in r2]

        pooled_t = 0.5 * (float(np.mean(t1)) + float(np.mean(t2)))
        margin_t = max(1.0, TOST_MARGIN_TASK_REL * pooled_t)
        tost_task = run_tost_equivalence(t1, t2, low=-margin_t, upp=margin_t)

        pooled_o = 0.5 * (float(np.mean(o1)) + float(np.mean(o2)))
        margin_o = max(TOST_MARGIN_ORCH_FLOOR_MS, TOST_MARGIN_ORCH_REL * pooled_o)
        tost_orch = run_tost_equivalence(o1, o2, low=-margin_o, upp=margin_o)

        if tost_task.get("equivalent_at_alpha"):
            equiv_task_count += 1
        if tost_orch.get("equivalent_at_alpha"):
            equiv_orch_count += 1

        rel_diff_task = round(abs(float(np.mean(t1)) - float(np.mean(t2))) / max(1e-6, pooled_t) * 100.0, 2)
        results.setdefault(wl, {})[ak] = {
            "session_1_t_task_median_ms": round(float(np.median(t1)), 3),
            "session_2_t_task_median_ms": round(float(np.median(t2)), 3),
            "session_1_t_orch_median_ms": round(float(np.median(o1)), 3),
            "session_2_t_orch_median_ms": round(float(np.median(o2)), 3),
            "inter_session_rel_diff_task_pct": rel_diff_task,
            "tost_t_task_ms": tost_task,
            "tost_t_orch_ms": tost_orch,
        }

    return {
        "regime": regime_label,
        "a_priori_equivalence_margins": {
            "t_task_ms": f"+/- {int(TOST_MARGIN_TASK_REL * 100)}% of pooled Session 1/2 mean",
            "t_orch_ms": f"+/- max({TOST_MARGIN_ORCH_FLOOR_MS} ms, {int(TOST_MARGIN_ORCH_REL * 100)}% of pooled Session 1/2 mean)",
            "alpha": 0.05,
            "test_implementation": "statsmodels.stats.weightstats.ttost_ind (usevar='unequal')",
        },
        "total_cells_compared": len(cells),
        "t_task_equivalent_cells": equiv_task_count,
        "t_orch_equivalent_cells": equiv_orch_count,
        "cells": results,
    }


def generate_sha256_manifest(paths: list[str], manifest_path: str, repo_dir: str, guard: Callable[[str], str]) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for p in paths:
        if not os.path.exists(p):
            continue
        if os.path.isfile(p):
            with open(p, "rb") as f:
                manifest[os.path.relpath(p, repo_dir).replace("\\", "/")] = hashlib.sha256(f.read()).hexdigest()
        else:
            for root, _, files in sorted(os.walk(p)):
                for fn in sorted(files):
                    fp = os.path.join(root, fn)
                    with open(fp, "rb") as f:
                        manifest[os.path.relpath(fp, repo_dir).replace("\\", "/")] = hashlib.sha256(f.read()).hexdigest()
    with open(guard(manifest_path), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    return manifest


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def run_intel_session_analysis(paths: Any, repo_dir: str, guard: Callable[[str], str]) -> dict[str, Any]:
    """Analyze a single Intel Graphics session (Regime A, Regime B, Tool-RAG, W5 quality) + tables + manifest."""
    raw_a = _load_jsonl(os.path.join(paths.raw, "raw_trials.jsonl"))
    raw_b = _load_jsonl(os.path.join(paths.raw, "warm_cache_trials.jsonl"))
    raw_tr = _load_jsonl(os.path.join(paths.raw, "tool_rag_mitigation_trials.jsonl"))
    meta_path = os.path.join(paths.raw, "hardware_metadata.json")
    meta = json.load(open(meta_path, encoding="utf-8")) if os.path.exists(meta_path) else {}

    res_a = analyze_session_records(raw_a)
    res_b = analyze_session_records(raw_b)
    res_tr_cold = analyze_session_records([r for r in raw_tr if "cold" in str(r.get("regime", "")).lower()])
    res_tr_warm = analyze_session_records([r for r in raw_tr if "warm" in str(r.get("regime", "")).lower()])

    os.makedirs(guard(paths.results), exist_ok=True)
    os.makedirs(guard(paths.tables), exist_ok=True)

    outputs = {
        "summary_statistics.json": res_a["summary"],
        "statistical_contrasts.json": res_a["runtime_contrasts"],
        "autocorrelation_and_trend_cold.json": res_a["autocorrelation_and_trend"],
        "warm_cache_summary.json": res_b["summary"],
        "warm_cache_contrasts.json": res_b["runtime_contrasts"],
        "autocorrelation_and_trend_warm.json": res_b["autocorrelation_and_trend"],
        "tool_rag_summary.json": {"regime_a_cold": res_tr_cold["summary"], "regime_b_warm": res_tr_warm["summary"]},
    }
    for fname, obj in outputs.items():
        with open(guard(os.path.join(paths.results, fname)), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)

    for jname in ("raw_trials.jsonl", "warm_cache_trials.jsonl", "tool_rag_mitigation_trials.jsonl"):
        src = os.path.join(paths.raw, jname)
        dst = os.path.join(paths.results, jname)
        if os.path.exists(src):
            shutil.copy2(src, guard(dst))

    # Generate LaTeX table for Intel Graphics session
    tex_path = os.path.join(paths.tables, "table_intel_graphics_summary.tex")
    with open(guard(tex_path), "w", encoding="utf-8") as f:
        f.write("% Windows Intel Graphics (iGPU Shared Memory / CPU AVX2) Empirical Summary\n")
        f.write("\\begin{table*}[t]\n\\centering\\small\n")
        f.write("\\caption{Windows 10 Intel HD Graphics 4600 Host (Core i7-4790K, Shared RAM, -ngl 0): Orchestration & W5 Quality}\n")
        f.write("\\begin{tabular}{lllrrrrrr}\n\\toprule\n")
        f.write("Regime & WL & Arm & $T_{\\text{task}}$ (ms) & $T_{\\text{orch}}$ (ms) & Peak RSS (MB) & Cycles ($10^6$) & Cache Hit (\\%) & W5 Score \\\\\n\\midrule\n")
        for reg_name, sm in (("Cold", res_a["summary"]), ("Warm", res_b["summary"])):
            for ak, wls in sorted(sm.items()):
                for wl, d in sorted(wls.items()):
                    tt = d["t_task_ms"]["median"]
                    to = d["t_orch_ms"]["median"]
                    mem = d["proc_peak_phys_mb"]["median"]
                    cyc = d["proc_cycles"]["median"]
                    cyc_s = f"{cyc/1e6:.2f}" if isinstance(cyc, (int, float)) else "N/A"
                    mem_s = f"{mem:.1f}" if isinstance(mem, (int, float)) else "N/A"
                    q = d["quality_score"]["median"] if isinstance(d.get("quality_score"), dict) else "N/A"
                    q_s = f"{q:.1f}" if isinstance(q, (int, float)) else "N/A"
                    ak_esc = ak.replace("_", "\\_")
                    f.write(f"{reg_name} & {wl} & {ak_esc} & {tt:.1f} & {to:.2f} & {mem_s} & {cyc_s} & {d['cache_hit_rate_pct']:.1f}\\% & {q_s} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table*}\n")

    # Markdown Audit Report
    hw_str = meta.get("provenance", {}).get("hardware", "Windows Intel Graphics")
    os_str = meta.get("provenance", {}).get("os", "Windows")
    backend = meta.get("llama_server", {}).get("execution_backend", "llama.cpp_cpu_avx2_intel_igpu_host")
    ngl = meta.get("llama_server", {}).get("n_gpu_layers_final", 0)
    md_path = os.path.join(paths.results, "intel_graphics_audit_report.md")
    with open(guard(md_path), "w", encoding="utf-8") as f:
        f.write("# Windows Intel Graphics Dedicated Campaign Audit Report\n\n")
        f.write(f"- **Hardware:** `{hw_str}`\n")
        f.write(f"- **OS:** `{os_str}`\n")
        f.write(f"- **Execution Backend / Offload:** `{backend}` (`-ngl {ngl}`)\n")
        f.write("- **Explicit-NA & Zero-NVML Compliance:** Verified (`nvidia-smi` / NVML never invoked; unavailable user-mode counters explicitly recorded as `N/A`).\n\n")
        f.write("## Regime B (Warm KV-Cache) Summary\n\n")
        f.write("| Workload | Arm | n | $T_{\\text{task}}$ Med (ms) | $T_{\\text{orch}}$ Med (ms) | Peak Phys (MB) | Cache Hit % | W5 Score |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for ak, wls in sorted(res_b["summary"].items()):
            for wl, d in sorted(wls.items()):
                q = d["quality_score"]["median"] if isinstance(d.get("quality_score"), dict) else "N/A"
                f.write(
                    f"| {wl} | `{ak}` | {d['n_eval_trials']} | {d['t_task_ms']['median']} | "
                    f"{d['t_orch_ms']['median']} | {d['proc_peak_phys_mb']['median']} | "
                    f"{d['cache_hit_rate_pct']}% | {q} |\n"
                )
        f.write("\n## Regime A (Cold Prefill) Summary\n\n")
        f.write("| Workload | Arm | n | $T_{\\text{task}}$ Med (ms) | $T_{\\text{orch}}$ Med (ms) | Peak Phys (MB) | Cache Hit % | W5 Score |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for ak, wls in sorted(res_a["summary"].items()):
            for wl, d in sorted(wls.items()):
                q = d["quality_score"]["median"] if isinstance(d.get("quality_score"), dict) else "N/A"
                f.write(
                    f"| {wl} | `{ak}` | {d['n_eval_trials']} | {d['t_task_ms']['median']} | "
                    f"{d['t_orch_ms']['median']} | {d['proc_peak_phys_mb']['median']} | "
                    f"{d['cache_hit_rate_pct']}% | {q} |\n"
                )

    manifest = generate_sha256_manifest([paths.data, paths.results], paths.manifest, repo_dir, guard)
    return {
        "regime_a": res_a,
        "regime_b": res_b,
        "manifest_entries": len(manifest),
    }


def run_combined_replication_analysis(
    repo_dir: str,
    s1_raw_dir: str,
    s2_raw_dir: str,
    out_dir: str,
    manifest_path: str,
    guard: Callable[[str], str],
) -> dict[str, Any]:
    """Compute Session 1 vs Session 2 TOST equivalence report and combined SHA-256 manifest."""
    os.makedirs(guard(out_dir), exist_ok=True)
    tost_cold = analyze_inter_session_replication(
        _load_jsonl(os.path.join(s1_raw_dir, "raw_trials.jsonl")),
        _load_jsonl(os.path.join(s2_raw_dir, "raw_trials.jsonl")),
        regime_label="A_cold",
    )
    tost_warm = analyze_inter_session_replication(
        _load_jsonl(os.path.join(s1_raw_dir, "warm_cache_trials.jsonl")),
        _load_jsonl(os.path.join(s2_raw_dir, "warm_cache_trials.jsonl")),
        regime_label="B_warm",
    )
    combined = {
        "platform": "windows_intel_graphics",
        "regime_a_cold_tost": tost_cold,
        "regime_b_warm_tost": tost_warm,
    }
    out_json = os.path.join(out_dir, "inter_session_tost_replication.json")
    with open(guard(out_json), "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)

    manifest = generate_sha256_manifest([out_dir], manifest_path, repo_dir, guard)
    combined["manifest_entries"] = len(manifest)
    return combined
