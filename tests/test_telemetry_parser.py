"""
Unit Tests for Hardware Telemetry & Powermetrics Parsing
Testes Unitários para Telemetria de Hardware e Parser do Powermetrics

Author / Autor: Rafael Paniccia Cassetta (UFABC)
Language / Idioma: Bilingual (PT-BR & EN-US comments, English code)
"""

import sys

import pytest

from benchmark.telemetry import (
    LinuxRAPLMonitor,
    SMCPowerMonitor,
    get_process_rusage_v4,
    integrate_energy_trapezoidal,
    parse_powermetrics_sample,
)


def test_parse_sample_block():
    """Verify powermetrics sample parsing into CPU, GPU, ANE and package power."""
    sample_raw = """
    *** Sampled system activity (Mon Nov 10 20:00:00 2026 -0300) (100.12ms elapsed) ***

    CPU Power: 1250 mW
    GPU Power: 11400 mW
    ANE Power: 0 mW
    Combined Power (CPU + GPU + ANE): 12650 mW
    """
    parsed = parse_powermetrics_sample(sample_raw)
    assert parsed["cpu_mw"] == 1250.0
    assert parsed["gpu_mw"] == 11400.0
    assert parsed["ane_mw"] == 0.0
    assert parsed["package_mw"] == 12650.0


def test_parse_sample_fallback_combined():
    """Verify fallback summation if Combined Power header is absent."""
    sample_raw = """
    CPU Power: 2000 mW
    GPU Power: 3000 mW
    """
    parsed = parse_powermetrics_sample(sample_raw)
    assert parsed["cpu_mw"] == 2000.0
    assert parsed["gpu_mw"] == 3000.0
    assert parsed["package_mw"] == 5000.0


def test_integrate_energy_trapezoidal():
    """Verify trapezoidal numerical integration of power samples over monotonic timestamps."""
    # 0.0s: 10 W (10000 mW)
    # 1.0s: 20 W (20000 mW) -> trapezoid area = 1.0 * (10 + 20) / 2 = 15 J
    # 2.0s: 20 W (20000 mW) -> rectangle area = 1.0 * (20 + 20) / 2 = 20 J
    # Total expected: 35.0 J
    samples = [
        {"timestamp_ns": 0, "package_mw": 10000.0, "cpu_mw": 6000.0, "gpu_mw": 4000.0, "ane_mw": 0.0},
        {"timestamp_ns": 1_000_000_000, "package_mw": 20000.0, "cpu_mw": 12000.0, "gpu_mw": 8000.0, "ane_mw": 0.0},
        {"timestamp_ns": 2_000_000_000, "package_mw": 20000.0, "cpu_mw": 12000.0, "gpu_mw": 8000.0, "ane_mw": 0.0},
    ]
    summary = integrate_energy_trapezoidal(samples)
    assert pytest.approx(summary["energy_total_j"], 0.001) == 35.0
    assert summary["duration_s"] == 2.0


def test_integrate_energy_empty_or_single():
    """Verify empty sample list yields 0.0 Joules."""
    res_empty = integrate_energy_trapezoidal([])
    assert res_empty["energy_total_j"] == 0.0

    res_single = integrate_energy_trapezoidal([{
        "timestamp_ns": 0,
        "elapsed_ms": 100.0,
        "package_mw": 5000.0,
        "cpu_mw": 2000.0,
        "gpu_mw": 3000.0,
        "ane_mw": 0.0
    }])
    assert res_single["energy_total_j"] > 0.0


def test_get_process_rusage_v4():
    """Verify Darwin libproc hardware counters on macOS, or None fallback on Linux."""
    res = get_process_rusage_v4()
    if sys.platform == "darwin":
        assert res is not None
        assert "proc_instructions" in res
        assert "proc_cycles" in res
        assert "proc_rss_mb" in res
        assert isinstance(res["proc_instructions"], int)
        assert isinstance(res["proc_cycles"], int)
    else:
        # On Linux without libproc, either returns psutil dict or None
        assert res is None or "proc_rss_mb" in res


def test_smc_monitor_no_sudo_degradation():
    """Verify SMCPowerMonitor non-root graceful degradation without crashing."""
    monitor = SMCPowerMonitor()
    monitor.start()
    res = monitor.stop()
    assert res is None or isinstance(res, dict)


def test_rapl_monitor_graceful_handling():
    """Verify LinuxRAPLMonitor graceful fallback when sysfs nodes are unavailable."""
    monitor = LinuxRAPLMonitor()
    monitor.start()
    res = monitor.stop()
    assert res is None or isinstance(res, dict)


def test_multiplatform_telemetry_backend():
    """Gate E2/E3: Verifies multiplatform telemetry abstraction layer (src/telemetry_backend.py)."""
    from src.telemetry_backend import UnifiedTelemetryBackend
    backend = UnifiedTelemetryBackend(sample_interval_ms=100)
    assert backend is not None
    assert hasattr(backend, "start_campaign")
    assert hasattr(backend, "stop_campaign")
    assert hasattr(backend, "slice_energy")
    assert hasattr(backend, "run_process_with_telemetry")

    if sys.platform == "darwin":
        assert backend.is_darwin_arm64 is True
        assert backend.backend_name == "apple_smc_powermetrics"
    else:
        assert backend.is_darwin_arm64 is False


