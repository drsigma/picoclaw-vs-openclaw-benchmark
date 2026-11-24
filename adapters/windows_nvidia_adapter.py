#!/usr/bin/env python3
"""
adapters/windows_nvidia_adapter.py - Dedicated Windows 11 + NVIDIA GPU Telemetry & Guard Adapter.

Strictly isolated from Windows-Intel (`adapters/windows_intel_graphics/`), Linux, and macOS adapters.
Collects real NVIDIA GPU telemetry via `nvidia-smi` and NVML DLL (`temperature.gpu`, `utilization.gpu`,
`memory.used`, `memory.total`, `power.draw`, `clocks_event_reasons.active`), handling WDDM `[N/A]`
fields transparently as `None` (never substituting 0 or crashing).
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import time
from typing import Any

from benchmark.windows_x86_64_telemetry_adapter import (
    Nvml,
    ThermalController,
    WindowsHardwarePowerMonitor,
    assert_pmu_available,
    decompose_nvml_throttle_reasons,
    detect_windows_host_provenance,
)

NA_TOKENS = {"", "[n/a]", "n/a", "[not supported]", "not supported", "none", "unknown"}

NVIDIA_SMI_QUERY_FIELDS = (
    "index",
    "uuid",
    "name",
    "memory.total",
    "driver_version",
    "temperature.gpu",
    "utilization.gpu",
    "memory.used",
    "power.limit",
    "power.draw",
    "persistence_mode",
    "clocks_event_reasons.active",
)

NVIDIA_SMI_QUERY_FIELDS_LEGACY = (
    "index",
    "uuid",
    "name",
    "memory.total",
    "driver_version",
    "temperature.gpu",
    "utilization.gpu",
    "memory.used",
    "power.limit",
    "power.draw",
    "persistence_mode",
    "clocks_throttle_reasons.active",
)


def parse_nvidia_float(raw: str | None) -> float | None:
    """Parse a numeric nvidia-smi field, converting WDDM [N/A] tokens cleanly to None."""
    if raw is None:
        return None
    s = raw.strip()
    if s.lower() in NA_TOKENS:
        return None
    cleaned = s.replace("MiB", "").replace("W", "").replace("%", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_nvidia_str(raw: str | None) -> str | None:
    """Parse a string nvidia-smi field, converting WDDM [N/A] tokens cleanly to None."""
    if raw is None:
        return None
    s = raw.strip()
    if s.lower() in NA_TOKENS:
        return None
    return s


def parse_nvidia_bitmask(raw: str | None) -> int | None:
    """Parse hexadecimal/integer clocks_event_reasons.active bitmask, returning None if [N/A]."""
    s = parse_nvidia_str(raw)
    if s is None:
        return None
    try:
        return int(s, 0)
    except ValueError:
        return None


def _run_nvidia_smi_query(gpu_index: int = 0, timeout_s: float = 10.0) -> list[str]:
    smi_bin = shutil.which("nvidia-smi")
    if not smi_bin:
        raise RuntimeError("FAIL-FAST: nvidia-smi not found in PATH; physical NVIDIA GPU required.")

    last_err: Exception | None = None
    for fields in (NVIDIA_SMI_QUERY_FIELDS, NVIDIA_SMI_QUERY_FIELDS_LEGACY):
        cmd = [
            smi_bin,
            f"--id={gpu_index}",
            f"--query-gpu={','.join(fields)}",
            "--format=csv,noheader,nounits",
        ]
        try:
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE, timeout=timeout_s).strip()
            lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
            if not lines:
                raise RuntimeError("nvidia-smi returned empty output")
            parts = [p.strip() for p in lines[0].split(",")]
            if len(parts) < len(fields):
                raise RuntimeError(f"nvidia-smi returned {len(parts)} columns, expected {len(fields)}: {lines[0]!r}")
            return parts
        except Exception as exc:
            last_err = exc
            continue
    raise RuntimeError(f"FAIL-FAST: nvidia-smi query failed for GPU index {gpu_index}: {last_err}")


def query_nvidia_smi_snapshot(gpu_index: int = 0, timeout_s: float = 10.0) -> dict[str, Any]:
    """
    Query live NVIDIA GPU telemetry via nvidia-smi.
    Explicitly handles WDDM `[N/A]` fields (`power.limit`, `persistence_mode`, etc.) as `None`.
    """
    parts = _run_nvidia_smi_query(gpu_index=gpu_index, timeout_s=timeout_s)
    idx_f = parse_nvidia_float(parts[0])
    bitmask = parse_nvidia_bitmask(parts[11])
    dec = decompose_nvml_throttle_reasons(bitmask)

    return {
        "gpu_index": int(idx_f) if idx_f is not None else gpu_index,
        "gpu_uuid": parse_nvidia_str(parts[1]),
        "gpu_name": parse_nvidia_str(parts[2]),
        "gpu_vram_total_mb": parse_nvidia_float(parts[3]),
        "driver_version": parse_nvidia_str(parts[4]),
        "gpu_temp_c": parse_nvidia_float(parts[5]),
        "gpu_utilization_pct": parse_nvidia_float(parts[6]),
        "gpu_vram_used_mb": parse_nvidia_float(parts[7]),
        "gpu_power_limit_w": parse_nvidia_float(parts[8]),
        "gpu_power_draw_w": parse_nvidia_float(parts[9]),
        "gpu_persistence_mode": parse_nvidia_str(parts[10]),
        "clocks_event_reasons_active": parse_nvidia_str(parts[11]),
        **dec,
        "telemetry_source": "nvidia_smi_nvml_wddm",
    }


def verify_windows_nvidia_platform(gpu_index: int = 0) -> dict[str, Any]:
    """
    Platform + GPU guard for Windows-NVIDIA confirmatory campaigns.
    Verifies native Windows host AND physical NVIDIA GPU accessibility via nvidia-smi.
    """
    if platform.system() != "Windows":
        raise RuntimeError(
            f"FAIL-FAST: Native platform mismatch! Windows-NVIDIA runner requires Windows x86_64. "
            f"Detected: {platform.system()} {platform.machine()}"
        )
    if os.environ.get("WSL_DISTRO_NAME"):
        raise RuntimeError("FAIL-FAST: WSL environment detected; native Windows required.")

    snap = query_nvidia_smi_snapshot(gpu_index=gpu_index)
    if not snap.get("gpu_name") or not snap.get("gpu_uuid"):
        raise RuntimeError(f"FAIL-FAST: Physical NVIDIA GPU not detected or incomplete metadata: {snap}")
    return snap


class WindowsNvidiaTelemetryAdapter:
    """
    Unified Windows-NVIDIA telemetry orchestrator combining:
      - NVML DLL high-frequency energy/power integration (PowerMonitor)
      - nvidia-smi snapshot with WDDM [N/A] resilience
      - Active thermal gating and cooldown enforcement
    """

    def __init__(self, gpu_index: int = 0) -> None:
        self.gpu_index = gpu_index
        self.gpu_info = verify_windows_nvidia_platform(gpu_index=gpu_index)
        assert_pmu_available()
        self.thermal = ThermalController()
        self.power = WindowsHardwarePowerMonitor()

    def nvidia_smi_snapshot(self) -> dict[str, Any]:
        return query_nvidia_smi_snapshot(gpu_index=self.gpu_index)

    def check_and_cooldown(
        self,
        gpu_ceiling_c: float = 82.0,
        cpu_ceiling_c: float = 88.0,
        gpu_target_c: float = 72.0,
        cpu_target_c: float = 75.0,
        min_cooldown_s: float = 90.0,
        max_wait_s: float = 600.0,
    ) -> dict[str, Any]:
        """
        Active thermal safety guard (Phase 0.4):
        If GPU >= 82 C, CPU >= 88 C, or severe thermal throttle active, pauses execution
        until GPU <= 72 C and CPU <= 75 C (for at least min_cooldown_s seconds).
        """
        snap = self.thermal.snapshot()
        smi = self.nvidia_smi_snapshot()
        gpu_c = smi.get("gpu_temp_c")
        if gpu_c is None:
            gpu_c = snap.get("gpu_temp_c")
        cpu_c = snap.get("cpu_pkg_temp_c")
        severe_throttle = bool(smi.get("gpu_thermal_throttle_active_end"))

        triggered = (
            (gpu_c is not None and gpu_c >= gpu_ceiling_c)
            or (cpu_c is not None and cpu_c >= cpu_ceiling_c)
            or severe_throttle
        )
        if not triggered:
            return {
                "cooldown_triggered": False,
                "waited_s": 0.0,
                "gpu_temp_c": gpu_c,
                "cpu_temp_c": cpu_c,
                "severe_throttle": severe_throttle,
            }

        t0 = time.monotonic()
        print(
            f"[THERMAL COOLDOWN] Triggered: gpu={gpu_c}C (limit {gpu_ceiling_c}C), "
            f"cpu={cpu_c}C (limit {cpu_ceiling_c}C), throttle={severe_throttle}. "
            f"Waiting >= {min_cooldown_s:.0f}s until <= {gpu_target_c}C/{cpu_target_c}C...",
            flush=True,
        )
        while True:
            time.sleep(2.0)
            elapsed = time.monotonic() - t0
            snap = self.thermal.snapshot()
            smi = self.nvidia_smi_snapshot()
            gpu_c = smi.get("gpu_temp_c") if smi.get("gpu_temp_c") is not None else snap.get("gpu_temp_c")
            cpu_c = snap.get("cpu_pkg_temp_c")
            gpu_ok = gpu_c is None or gpu_c <= gpu_target_c
            cpu_ok = cpu_c is None or cpu_c <= cpu_target_c
            if elapsed >= min_cooldown_s and gpu_ok and cpu_ok:
                break
            if elapsed >= max_wait_s:
                print(
                    f"[THERMAL COOLDOWN WARNING] Max cooldown wait ({max_wait_s}s) reached: "
                    f"gpu={gpu_c}C cpu={cpu_c}C",
                    flush=True,
                )
                break
        waited = round(time.monotonic() - t0, 2)
        print(f"[THERMAL COOLDOWN] Resumed after {waited:.1f}s: gpu={gpu_c}C cpu={cpu_c}C", flush=True)
        return {
            "cooldown_triggered": True,
            "waited_s": waited,
            "gpu_temp_c": gpu_c,
            "cpu_temp_c": cpu_c,
            "severe_throttle": bool(smi.get("gpu_thermal_throttle_active_end")),
        }


__all__ = [
    "NVIDIA_SMI_QUERY_FIELDS",
    "Nvml",
    "ThermalController",
    "WindowsHardwarePowerMonitor",
    "WindowsNvidiaTelemetryAdapter",
    "assert_pmu_available",
    "decompose_nvml_throttle_reasons",
    "detect_windows_host_provenance",
    "parse_nvidia_bitmask",
    "parse_nvidia_float",
    "parse_nvidia_str",
    "query_nvidia_smi_snapshot",
    "verify_windows_nvidia_platform",
]
