"""
Unit Tests for Dedicated Windows Intel Graphics Adapter, Extraction Validator,
Per-Trial Retry, Delta Telemetry, Strict Isolation Guard, and TOST Statistical Engine.
"""
from __future__ import annotations

import math
import os
import pytest

from adapters.windows_intel_graphics.analysis import (
    analyze_inter_session_replication,
    analyze_session_records,
    compute_autocorrelation_and_trend,
    run_tost_equivalence,
)
from adapters.windows_intel_graphics.telemetry import NA, IntelGraphicsThermalAndLoadMonitor
from adapters.windows_intel_graphics.validator import (
    compute_deterministic_cache_hit,
    execute_trial_with_retry,
    validate_trial_extraction,
)

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _valid_record(
    *,
    regime: str = "B_warm",
    agent_key: str = "picoclaw",
    workload: str = "W2",
    cache_prompt: bool = True,
    tokens_cached: int = 2170,
    prompt_eval_count: int = 2,
    prompt_tokens: int = 2172,
    completion_tokens: int = 29,
    quality_score=NA,
) -> dict:
    return {
        "session_id": "session_windows_intel_graphics_test",
        "timestamp_iso": "2026-11-19T22:00:00Z",
        "git_commit": "0" * 40,
        "hardware": "MSI Z97 XPOWER AC | Intel i7-4790K | Intel HD Graphics 4600 (iGPU UMA)",
        "os": "Microsoft Windows 10 Pro 22H2",
        "model_version": "Llama-3.2-3B-Instruct",
        "quantization": "GGUF Q4_K_M (2.019 GB)",
        "server_flags": "-c 32768 -np 1 -ngl 0 -t 4 --temp 0.0 --seed 42",
        "workload": workload,
        "regime": regime,
        "agent_key": agent_key,
        "is_warmup": False,
        "is_simulated": False,
        "nvml_used": False,
        "cache_prompt": cache_prompt,
        "ngl": 0,
        "execution_backend": "llama.cpp_cpu_avx2_intel_igpu_host",
        "offload_mode": "cpu_avx2_ngl_0_shared_ddr3_no_vulkan_icd_on_igpu",
        "t_task_ms": 3510.5,
        "t_neural_ms": 3500.0,
        "t_orch_ms": 10.5,
        "prompt_ms": 200.0,
        "predicted_ms": 3300.0,
        "ttft_ms": 210.0,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "tokens_cached": tokens_cached,
        "prompt_eval_count": prompt_eval_count,
        "eval_count": completion_tokens,
        "cache_hit": compute_deterministic_cache_hit(tokens_cached, prompt_eval_count),
        "http_status": 200,
        "finish_reason": "stop",
        "quality_score": quality_score,
        "proc_instructions": NA,
        "proc_cycles": 45_000_000,
        "proc_peak_phys_mb": 12.4,
        "system_ram_used_end_mb": 8200.0,
        "throttle_delta_events": 0,
        "energy_gpu_j": NA,
        "energy_total_j": NA,
        "energy_net_above_idle_j": NA,
    }


def test_isolation_guard_allows_only_intel_graphics_namespace():
    from adapters.windows_intel_graphics.runner import IntelPaths

    paths = IntelPaths(REPO_DIR, suffix="_session1")
    ok_path = os.path.join(paths.raw, "raw_trials.jsonl")
    assert paths.guard(ok_path) == ok_path

    forbidden_targets = [
        os.path.join(REPO_DIR, "data", "windows_x86_64", "raw", "raw_trials.jsonl"),
        os.path.join(REPO_DIR, "results", "publication_campaign", "raw_trials.jsonl"),
        os.path.join(REPO_DIR, "results", "publication_campaign_linux_x86_64", "summary.json"),
        os.path.join(REPO_DIR, "data", "darwin_aarch64", "raw", "raw_trials.jsonl"),
        os.path.join(REPO_DIR, "data", "manifest_sha256.json"),
        os.path.join(REPO_DIR, "reproducibility", "clean_run_windows_session_1", "data"),
    ]
    for target in forbidden_targets:
        with pytest.raises(PermissionError):
            paths.guard(target)


def test_validator_accepts_valid_w2_and_w5_records():
    rec_w2 = _valid_record()
    ok, reason = validate_trial_extraction(rec_w2, "B_warm", "picoclaw", "W2")
    assert ok, reason

    rec_w5 = _valid_record(
        agent_key="python_native",
        workload="W5",
        prompt_tokens=620,
        tokens_cached=618,
        prompt_eval_count=2,
        completion_tokens=120,
        quality_score=5,
    )
    ok5, reason5 = validate_trial_extraction(rec_w5, "B_warm", "python_native", "W5")
    assert ok5, reason5


def test_validator_rejects_anomalies_and_incoherent_tokens():
    # NaN latency
    bad = _valid_record()
    bad["t_orch_ms"] = float("nan")
    ok, _ = validate_trial_extraction(bad, "B_warm", "picoclaw", "W2")
    assert not ok

    # Negative latency
    bad = _valid_record()
    bad["t_orch_ms"] = -1.2
    ok, _ = validate_trial_extraction(bad, "B_warm", "picoclaw", "W2")
    assert not ok

    # tokens_cached > prompt_tokens
    bad = _valid_record(tokens_cached=3000, prompt_tokens=2000)
    ok, _ = validate_trial_extraction(bad, "B_warm", "picoclaw", "W2")
    assert not ok

    # Cold regime marked cache_hit=True
    bad = _valid_record(regime="A_cold", cache_prompt=False, tokens_cached=2000, prompt_eval_count=1)
    ok, _ = validate_trial_extraction(bad, "A_cold", "picoclaw", "W2")
    assert not ok

    # Simulated fallback or HTTP != 200
    bad = _valid_record()
    bad["http_status"] = 503
    ok, _ = validate_trial_extraction(bad, "B_warm", "picoclaw", "W2")
    assert not ok

    # NVML leak
    bad = _valid_record()
    bad["nvml_used"] = True
    ok, _ = validate_trial_extraction(bad, "B_warm", "picoclaw", "W2")
    assert not ok

    # W5 missing/invalid quality_score
    bad = _valid_record(agent_key="python_native", workload="W5", quality_score=0)
    ok, _ = validate_trial_extraction(bad, "B_warm", "python_native", "W5")
    assert not ok


def test_per_trial_retry_retries_only_failed_trial_up_to_limit():
    calls = {"n": 0}

    def flaky_trial():
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient socket timeout")
        if calls["n"] == 2:
            r = _valid_record()
            r["t_orch_ms"] = float("nan")
            return r
        return _valid_record()

    rec, passed, reasons = execute_trial_with_retry(
        flaky_trial, regime="B_warm", agent_key="picoclaw", workload="W2", max_retries=3, retry_delay_s=0.01
    )
    assert passed is True
    assert calls["n"] == 3
    assert rec is not None and rec["retry_attempts"] == 3
    assert len(reasons) == 2

    # Persistent failure returns caveat after 3 retries without raising
    always_bad_calls = {"n": 0}

    def always_bad():
        always_bad_calls["n"] += 1
        r = _valid_record()
        r["http_status"] = 500
        return r

    rec2, passed2, reasons2 = execute_trial_with_retry(
        always_bad, regime="B_warm", agent_key="picoclaw", workload="W2", max_retries=3, retry_delay_s=0.01
    )
    assert passed2 is False
    assert always_bad_calls["n"] == 3
    assert rec2 is not None and rec2["extraction_validated"] is False
    assert len(reasons2) == 3


def test_delta_telemetry_non_cumulative_and_explicit_na(monkeypatch):
    mon = IntelGraphicsThermalAndLoadMonitor()
    snaps = [
        {
            "timestamp_monotonic": 100.0,
            "system_ram_total_mb": 16264.0,
            "system_ram_used_mb": 7000.0,
            "system_ram_available_mb": 9264.0,
            "system_ram_pct": 43.0,
            "server_rss_mb": 2100.0,
            "cpu_utilization_pct": 12.0,
            "cpu_freq_mhz": 4000,
            "cpu_pct_max_freq": 100,
            "igpu_shared_mem_mb": 180.0,
            "igpu_dedicated_mem_mb": 1.0,
            "igpu_utilization_pct": 3.0,
            "acpi_tz00_c": 27.9,
            "acpi_tz01_c": 29.9,
            "cpu_pkg_temp_c": NA,
            "thermal_sensor_source": "ACPI_ThermalZoneInformation_motherboard_only",
            "acpi_throttle_reasons_bitmask": 0,
            "fan_rpm": NA,
            "cpu_pkg_power_w": NA,
        },
        {
            "timestamp_monotonic": 102.0,
            "system_ram_total_mb": 16264.0,
            "system_ram_used_mb": 7150.5,
            "system_ram_available_mb": 9113.5,
            "system_ram_pct": 44.0,
            "server_rss_mb": 2105.0,
            "cpu_utilization_pct": 55.0,
            "cpu_freq_mhz": 3980,
            "cpu_pct_max_freq": 99,
            "igpu_shared_mem_mb": 184.25,
            "igpu_dedicated_mem_mb": 1.0,
            "igpu_utilization_pct": 4.5,
            "acpi_tz00_c": 27.9,
            "acpi_tz01_c": 29.9,
            "cpu_pkg_temp_c": NA,
            "thermal_sensor_source": "ACPI_ThermalZoneInformation_motherboard_only",
            "acpi_throttle_reasons_bitmask": 0,
            "fan_rpm": NA,
            "cpu_pkg_power_w": NA,
        },
    ]
    it = iter(snaps)
    monkeypatch.setattr(mon, "snapshot", lambda: next(it))
    mon.start_trial()
    delta = mon.stop_trial()

    assert delta["system_ram_delta_mb"] == pytest.approx(150.5, abs=0.01)
    assert delta["igpu_shared_mem_delta_mb"] == pytest.approx(4.25, abs=0.01)
    assert delta["throttle_delta_events"] == 0
    assert delta["energy_gpu_j"] == NA
    assert delta["energy_total_j"] == NA
    assert delta["energy_net_above_idle_j"] == NA
    assert delta["pcie_bandwidth_mb_s"] == NA
    assert delta["nvml_used"] is False


def test_tost_equivalence_contrasts_and_autocorrelation():
    # Equivalent Session 1 vs Session 2 samples
    s1 = [100.0, 101.2, 99.5, 100.8, 99.9, 100.4, 101.0, 99.7, 100.3, 100.1]
    s2 = [100.4, 99.8, 100.9, 100.1, 99.6, 100.7, 100.2, 101.1, 99.9, 100.5]
    res_eq = run_tost_equivalence(s1, s2, low=-5.0, upp=5.0)
    assert res_eq["equivalent_at_alpha"] is True
    assert res_eq["tost_p_value"] < 0.05

    # Clearly shifted samples should NOT be equivalent within +/-5 ms
    s3 = [125.0, 126.1, 124.8, 125.5, 125.9, 124.9, 125.2, 126.0, 125.4, 125.1]
    res_neq = run_tost_equivalence(s1, s3, low=-5.0, upp=5.0)
    assert res_neq["equivalent_at_alpha"] is False

    # Session records contrast & inter-session replication
    recs_s1 = []
    recs_s2 = []
    for rep in range(1, 11):
        r_pico = _valid_record(agent_key="picoclaw", workload="W2")
        r_pico["rep"] = rep
        r_pico["t_orch_ms"] = 8.0 + (rep % 3) * 0.2
        r_pico["t_task_ms"] = 3500.0 + r_pico["t_orch_ms"]
        recs_s1.append(dict(r_pico))
        r_pico2 = dict(r_pico)
        r_pico2["t_orch_ms"] = 8.1 + (rep % 3) * 0.2
        r_pico2["t_task_ms"] = 3505.0 + r_pico2["t_orch_ms"]
        recs_s2.append(r_pico2)

        r_oc = _valid_record(agent_key="openclaw_minimal", workload="W2")
        r_oc["rep"] = rep
        r_oc["t_orch_ms"] = 28.0 + (rep % 3) * 0.4
        r_oc["t_task_ms"] = 3500.0 + r_oc["t_orch_ms"]
        recs_s1.append(dict(r_oc))
        r_oc2 = dict(r_oc)
        r_oc2["t_orch_ms"] = 28.2 + (rep % 3) * 0.4
        r_oc2["t_task_ms"] = 3505.0 + r_oc2["t_orch_ms"]
        recs_s2.append(r_oc2)

    ana = analyze_session_records(recs_s1)
    c = ana["runtime_contrasts"]["openclaw_minimal_minus_picoclaw"]["W2"]
    assert c["delta_t_orch_median_ms"] > 15.0
    assert c["p_value_orch_holm_bonferroni"] < 0.01

    rep_ana = analyze_inter_session_replication(recs_s1, recs_s2, "B_warm")
    assert rep_ana["total_cells_compared"] == 2
    assert rep_ana["t_task_equivalent_cells"] == 2
    assert rep_ana["t_orch_equivalent_cells"] == 2

    # Monotonic drift detection
    drift = compute_autocorrelation_and_trend([100.0 + i * 5.0 for i in range(12)])
    assert drift["significant_drift_p05"] is True
    assert drift["trend_spearman_rho"] == pytest.approx(1.0, abs=0.01)
