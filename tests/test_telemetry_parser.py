"""
Unit Tests for Hardware Telemetry & Powermetrics Parsing
Testes Unitários para Telemetria de Hardware e Parser do Powermetrics

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

import pytest


def parse_powermetrics_sample(sample_text: str):
    """
    Parse a single powermetrics text block and extract power metrics in milliwatts.
    """
    metrics = {
        "cpu_mw": 0.0,
        "gpu_mw": 0.0,
        "ane_mw": 0.0,
        "package_mw": 0.0
    }
    for line in sample_text.splitlines():
        line = line.strip()
        if "CPU Power:" in line:
            parts = line.split(":")
            val = float(parts[1].replace("mW", "").strip())
            metrics["cpu_mw"] = val
        elif "GPU Power:" in line:
            parts = line.split(":")
            val = float(parts[1].replace("mW", "").strip())
            metrics["gpu_mw"] = val
        elif "ANE Power:" in line:
            parts = line.split(":")
            val = float(parts[1].replace("mW", "").strip())
            metrics["ane_mw"] = val
        elif "Combined Power (CPU + GPU + ANE):" in line:
            parts = line.split(":")
            val = float(parts[1].replace("mW", "").strip())
            metrics["package_mw"] = val

    if metrics["package_mw"] == 0.0:
        metrics["package_mw"] = metrics["cpu_mw"] + metrics["gpu_mw"] + metrics["ane_mw"]

    return metrics


def test_parse_sample_block():
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


def test_energy_numerical_integration():
    """Verify numerical integration across three 100ms samples."""
    samples = [
        {"package_mw": 10000.0}, # 10 W
        {"package_mw": 12000.0}, # 12 W
        {"package_mw": 14000.0}, # 14 W
    ]
    dt_seconds = 0.1 # 100ms
    energy_joules = sum((s["package_mw"] / 1000.0) * dt_seconds for s in samples)
    # Expected: (10*0.1) + (12*0.1) + (14*0.1) = 1.0 + 1.2 + 1.4 = 3.6 Joules
    assert pytest.approx(energy_joules, 0.001) == 3.6
