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


def get_cpu_info() -> Dict[str, Any]:
    info = {
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "cpu_count_logical": os.cpu_count() or 1,
        "model_name": "Unknown",
    }
    if sys.platform == "linux":
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                for line in f:
                    if "model name" in line:
                        info["model_name"] = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            out = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
            info["model_name"] = out
        except Exception:
            pass
    elif sys.platform == "win32":
        info["model_name"] = os.environ.get("PROCESSOR_IDENTIFIER", "x86_64")
    return info


def get_ram_info() -> Dict[str, Any]:
    try:
        import psutil
        vm = psutil.virtual_memory()
        return {
            "total_gb": round(vm.total / (1024.0 ** 3), 2),
            "available_gb": round(vm.available / (1024.0 ** 3), 2),
            "percent_used": vm.percent,
        }
    except Exception:
        return {"total_gb": None, "available_gb": None, "percent_used": None}


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
        "go": "not_installed",
        "node": "not_installed",
        "bun": "not_installed",
    }
    for tool, cmd in [("go", ["go", "version"]), ("node", ["node", "--version"]), ("bun", ["bun", "--version"])]:
        if shutil.which(tool):
            try:
                out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
                versions[tool] = out
            except Exception:
                versions[tool] = "installed_probe_failed"
    return versions


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
        "cpu": get_cpu_info(),
        "ram": get_ram_info(),
        "power_source": get_power_source(),
        "cpu_governor": get_cpu_governor(),
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
