#!/usr/bin/env python3
"""
benchmark/environment_manifest.py - Automated Environment Manifest Recorder
Registrador Automático do Manifesto de Ambiente (Fase 4 - Itens 4.1, 4.2)

Captures comprehensive system hardware, operating system, runtime versions,
governor, power source, and quiescent state at the beginning of each benchmark session.

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""
from __future__ import annotations

import datetime
import json
import os
import platform
import shutil
import subprocess
import sys
from typing import Any, Dict, Optional


def _read_win_registry_str(subkey: str, value_name: str) -> Optional[str]:
    """Read a string value directly from HKLM Windows Registry (no hardcodes)."""
    if sys.platform != "win32":
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey) as key:
            val, _ = winreg.QueryValueEx(key, value_name)
            if isinstance(val, str) and val.strip():
                return val.strip()
    except Exception:
        return None
    return None


def _query_wmi_cpu_name() -> Optional[str]:
    """Fallback real hardware query via WMI Win32_Processor (never estimated)."""
    if sys.platform != "win32":
        return None
    try:
        out = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)",
            ],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        ).strip()
        return out if out else None
    except Exception:
        return None


def _query_win_installed_ram_kb() -> tuple[Optional[int], Optional[str]]:
    """
    Query physically installed system memory directly from SMBIOS via Win32
    GetPhysicallyInstalledSystemMemory (primary) or WMI Win32_PhysicalMemory (secondary).
    Never estimates, rounds up, or hardcodes memory capacity.
    """
    if sys.platform != "win32":
        return None, None
    try:
        import ctypes
        kb = ctypes.c_ulonglong(0)
        if ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(kb)) and kb.value > 0:
            return int(kb.value), "win32_GetPhysicallyInstalledSystemMemory"
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum",
            ],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        ).strip()
        if out.isdigit() and int(out) > 0:
            return int(out) // 1024, "wmi_Win32_PhysicalMemory"
    except Exception:
        pass
    return None, None


def get_system_product_info() -> Dict[str, Optional[str]]:
    """Collect real hardware vendor/product identity from firmware/BIOS tables."""
    if sys.platform == "win32":
        return {
            "manufacturer": _read_win_registry_str(r"HARDWARE\DESCRIPTION\System\BIOS", "SystemManufacturer"),
            "product_name": _read_win_registry_str(r"HARDWARE\DESCRIPTION\System\BIOS", "SystemProductName"),
        }
    return {"manufacturer": None, "product_name": None}


def get_cpu_info() -> Dict[str, Any]:
    phys_cores: Optional[int] = None
    try:
        import psutil
        phys_cores = psutil.cpu_count(logical=False)
    except Exception:
        phys_cores = None

    info: Dict[str, Any] = {
        "architecture": platform.machine() or None,
        "processor": platform.processor() or None,
        "cpu_count_physical": phys_cores,
        "cpu_count_logical": os.cpu_count(),
        "model_name": None,
        "detection_source": None,
    }
    if sys.platform == "linux":
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                for line in f:
                    if "model name" in line:
                        info["model_name"] = line.split(":", 1)[1].strip()
                        info["detection_source"] = "proc_cpuinfo"
                        break
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            out = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
            if out:
                info["model_name"] = out
                info["detection_source"] = "darwin_sysctl"
        except Exception:
            pass
    elif sys.platform == "win32":
        reg_name = _read_win_registry_str(r"HARDWARE\DESCRIPTION\System\CentralProcessor\0", "ProcessorNameString")
        if reg_name:
            info["model_name"] = reg_name
            info["detection_source"] = "winreg_ProcessorNameString"
        else:
            wmi_name = _query_wmi_cpu_name()
            if wmi_name:
                info["model_name"] = wmi_name
                info["detection_source"] = "wmi_Win32_Processor"
        info["cpuid_identifier"] = os.environ.get("PROCESSOR_IDENTIFIER") or None
    return info


def get_ram_info() -> Dict[str, Any]:
    os_usable_gb: Optional[float] = None
    available_gb: Optional[float] = None
    percent_used: Optional[float] = None
    try:
        import psutil
        vm = psutil.virtual_memory()
        os_usable_gb = round(vm.total / (1024.0 ** 3), 2)
        available_gb = round(vm.available / (1024.0 ** 3), 2)
        percent_used = vm.percent
    except Exception:
        pass

    installed_kb, installed_src = _query_win_installed_ram_kb()
    installed_gb = round(installed_kb / (1024.0 ** 2), 2) if installed_kb is not None else None
    total_gb = installed_gb if installed_gb is not None else os_usable_gb

    return {
        "total_gb": total_gb,
        "installed_physical_gb": installed_gb,
        "installed_physical_kb": installed_kb,
        "installed_detection_source": installed_src,
        "os_usable_gb": os_usable_gb,
        "available_gb": available_gb,
        "percent_used": percent_used,
    }


def get_power_source() -> str:
    try:
        import psutil
        bat = psutil.sensors_battery()
        if bat is None:
            return "AC_MAINS_OR_DESKTOP"
        return "AC_MAINS" if bat.power_plugged else "BATTERY"
    except Exception:
        return "UNKNOWN"


def get_cpu_governor() -> str:
    if sys.platform == "linux":
        try:
            p = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception:
            pass
    return "default_or_managed"


def get_runtime_versions() -> Dict[str, str]:
    versions = {
        "python": sys.version.split()[0],
        "go": "unavailable_in_environment (binary not in PATH)",
        "node": "unavailable_in_environment (binary not in PATH)",
        "bun": "unavailable_in_environment (binary not in PATH)",
        "llama_server": "unavailable_in_environment (binary not in PATH)",
        "powershell": "unavailable_in_environment (binary not in PATH)",
    }
    tool_commands = [
        ("go", "go", ["go", "version"]),
        ("node", "node", ["node", "--version"]),
        ("bun", "bun", ["bun", "--version"]),
        ("llama_server", "llama-server", ["llama-server", "--version"]),
        ("powershell", "pwsh", ["pwsh", "--version"]),
        ("powershell", "powershell", ["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]),
    ]
    for key, binary, cmd in tool_commands:
        resolved = shutil.which(binary)
        if resolved and versions[key].startswith("unavailable"):
            try:
                out_raw = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=10).strip()
                lines = [ln.strip() for ln in out_raw.splitlines() if ln.strip()]
                versions[key] = lines[0] if lines else f"installed_at_{resolved}_empty_output"
            except Exception:
                versions[key] = f"installed_at_{resolved}_probe_failed"
    return versions


def get_pmu_and_security_status() -> Dict[str, Any]:
    status: Dict[str, Any] = {
        "perf_event_paranoid": None,
        "pmu_status": "unavailable_in_environment",
        "rapl_status": "unavailable_in_environment",
        "restriction_reason": None,
    }
    if sys.platform == "linux":
        paranoid_file = "/proc/sys/kernel/perf_event_paranoid"
        if os.path.exists(paranoid_file):
            try:
                with open(paranoid_file, "r", encoding="utf-8") as f:
                    val = int(f.read().strip())
                status["perf_event_paranoid"] = val
                if val <= 0:
                    status["pmu_status"] = "available_unrestricted"
                elif val == 1:
                    status["pmu_status"] = "restricted_system_wide"
                    status["restriction_reason"] = "kernel.perf_event_paranoid=1 (kernel-level profiling restricted to root)"
                else:
                    status["pmu_status"] = "restricted_high_paranoid"
                    status["restriction_reason"] = f"kernel.perf_event_paranoid={val} >= 2 restricts unprivileged user PMU access"
            except PermissionError:
                status["pmu_status"] = "permission_denied"
                status["restriction_reason"] = "Permission denied reading /proc/sys/kernel/perf_event_paranoid"
            except Exception as e:
                status["restriction_reason"] = str(e)
        else:
            status["restriction_reason"] = "File /proc/sys/kernel/perf_event_paranoid not found"

        rapl_dir = "/sys/class/powercap/intel-rapl"
        if os.path.exists(rapl_dir):
            try:
                energy_file = os.path.join(rapl_dir, "intel-rapl:0", "energy_uj")
                if os.path.exists(energy_file) and os.access(energy_file, os.R_OK):
                    status["rapl_status"] = "available_readable"
                else:
                    status["rapl_status"] = "restricted_permission_denied"
                    status["restriction_reason"] = "RAPL sysfs exists but energy_uj is not readable without root/sudo"
            except Exception as e:
                status["rapl_status"] = f"error: {e}"
        else:
            status["rapl_status"] = "unavailable_in_environment (no intel-rapl sysfs)"
    elif sys.platform == "darwin":
        status["pmu_status"] = "apple_smc_powermetrics_supported"
        status["rapl_status"] = "not_applicable (Apple Silicon UMA)"
    elif sys.platform == "win32":
        status["pmu_status"] = "win32_psapi_cycles_supported"
        status["rapl_status"] = "not_applicable (Windows RAPL via driver/fallback)"
    return status


def record_environment_manifest(
    output_dir: str,
    session_id: str,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Captures complete environment state and writes atomic environment_manifest.json.
    Returns the absolute path of the generated manifest.
    """
    os.makedirs(output_dir, exist_ok=True)
    manifest_path = os.path.join(output_dir, "environment_manifest.json")

    manifest = {
        "manifest_version": "2.0.0",
        "session_id": session_id,
        "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "platform_machine": platform.machine(),
        "system_product": get_system_product_info(),
        "cpu": get_cpu_info(),
        "ram": get_ram_info(),
        "power_source": get_power_source(),
        "cpu_governor": get_cpu_governor(),
        "pmu_and_security": get_pmu_and_security_status(),
        "runtimes": get_runtime_versions(),
        "extra_metadata": extra_metadata or {},
    }

    tmp_path = manifest_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, manifest_path)
    return manifest_path


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    sid = sys.argv[2] if len(sys.argv) > 2 else "SESSION_TEST"
    p = record_environment_manifest(out_dir, sid)
    print(f"Recorded environment manifest: {p}")
