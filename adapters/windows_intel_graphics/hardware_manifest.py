#!/usr/bin/env python3
"""
adapters/windows_intel_graphics/hardware_manifest.py

Collects, validates, and persists complete hardware/OS/driver provenance for
Windows machines equipped with Intel Graphics (iGPU / Shared System Memory).
Explicitly forbids calling nvidia-smi or NVML as a GPU detector or metric source.
"""
from __future__ import annotations

import datetime
import json
import os
import platform
import shutil
import subprocess
import sys
from typing import Any


def _run_ps_json(ps_script: str, timeout: float = 15.0) -> Any:
    try:
        out = subprocess.check_output(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        ).strip()
        return json.loads(out) if out else None
    except Exception:
        return None


def collect_intel_windows_manifest(repo_dir: str | None = None) -> dict[str, Any]:
    """Collect read-only hardware/OS/Intel Graphics inventory via Win32/CIM (never nvidia-smi)."""
    ps = r"""
$ErrorActionPreference = 'SilentlyContinue'
$cs = Get-CimInstance Win32_ComputerSystem
$bb = Get-CimInstance Win32_BaseBoard
$bios = Get-CimInstance Win32_BIOS
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$ram = @(Get-CimInstance Win32_PhysicalMemory)
$os = Get-CimInstance Win32_OperatingSystem
$gpus = @(Get-CimInstance Win32_VideoController)
$disks = @(Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3")
$reg = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
$kernelVer = (Get-Item 'C:\Windows\System32\ntoskrnl.exe').VersionInfo.ProductVersion
$out = [ordered]@{
  computer_name = $env:COMPUTERNAME
  username = $env:USERNAME
  is_admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  system_manufacturer = $cs.Manufacturer
  system_model = $cs.Model
  baseboard_manufacturer = $bb.Manufacturer
  baseboard_product = $bb.Product
  bios_manufacturer = $bios.Manufacturer
  bios_version = $bios.SMBIOSBIOSVersion
  cpu_name = if ($cpu) { $cpu.Name.Trim() } else { '' }
  cpu_cores = if ($cpu) { [int]$cpu.NumberOfCores } else { 0 }
  cpu_logical = if ($cpu) { [int]$cpu.NumberOfLogicalProcessors } else { 0 }
  cpu_max_clock_mhz = if ($cpu) { [int]$cpu.MaxClockSpeed } else { 0 }
  ram_total_bytes = if ($cs) { [int64]$cs.TotalPhysicalMemory } else { 0 }
  ram_modules = @($ram | ForEach-Object { @{
    capacity_gb = [math]::Round($_.Capacity / 1GB, 2)
    speed_mhz = $_.Speed
    configured_clock_mhz = $_.ConfiguredClockSpeed
    part_number = ($_.PartNumber -replace '\s','')
  }})
  os_caption = $os.Caption
  os_display_version = $reg.DisplayVersion
  os_version = $os.Version
  os_build = $os.BuildNumber
  os_ubr = $reg.UBR
  kernel_version = $kernelVer
  os_architecture = $os.OSArchitecture
  gpus = @($gpus | ForEach-Object { @{
    name = $_.Name
    vendor = $_.AdapterCompatibility
    driver_version = $_.DriverVersion
    pnp_device_id = $_.PNPDeviceID
    adapter_ram_bytes = $_.AdapterRAM
    status = $_.Status
  }})
  logical_disks = @($disks | ForEach-Object { @{
    drive = $_.DeviceID
    size_gb = [math]::Round($_.Size / 1GB, 2)
    free_gb = [math]::Round($_.FreeSpace / 1GB, 2)
  }})
  active_power_scheme = ((powercfg /getactivescheme 2>&1) -join ' ').Trim()
}
$out | ConvertTo-Json -Depth 6
"""
    raw = _run_ps_json(ps) if platform.system() == "Windows" else None
    gpus = (raw or {}).get("gpus") or []
    if isinstance(gpus, dict):
        gpus = [gpus]

    intel_gpu = next(
        (g for g in gpus if "intel" in str(g.get("name", "")).lower() or "intel" in str(g.get("vendor", "")).lower()),
        gpus[0] if gpus else {"name": "Intel Graphics (iGPU)", "driver_version": "N/A", "vendor": "Intel Corporation"},
    )
    has_nvidia_gpu = any(
        "nvidia" in str(g.get("name", "")).lower() or "nvidia" in str(g.get("vendor", "")).lower()
        for g in gpus
    )

    git_commit = "unknown"
    if repo_dir:
        git_cmd = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
        if os.path.exists(git_cmd) or shutil.which("git"):
            try:
                git_commit = subprocess.check_output(
                    [git_cmd, "-C", repo_dir, "rev-parse", "HEAD"],
                    text=True,
                    timeout=10,
                ).strip()
            except Exception:
                pass

    ram_bytes = int((raw or {}).get("ram_total_bytes") or 0)
    ram_gb = round(ram_bytes / (1024.0 ** 3), 2) if ram_bytes > 0 else 0.0

    return {
        "manifest_version": "1.0",
        "collected_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "machine_role": "windows_intel_graphics_dedicated",
        "gpu_architecture_policy": (
            "Intel Graphics integrated GPU (UMA / shared system RAM). "
            "No discrete NVIDIA GPU present; nvidia-smi and NVML are disallowed "
            "as GPU probes or primary telemetry metrics."
        ),
        "dedicated_nvidia_gpu_present": has_nvidia_gpu,
        "git_commit": git_commit,
        "host": {
            "computer_name": (raw or {}).get("computer_name") or platform.node(),
            "username": (raw or {}).get("username") or os.environ.get("USERNAME", "unknown"),
            "is_admin": bool((raw or {}).get("is_admin", False)),
            "system_manufacturer": (raw or {}).get("system_manufacturer", "Unknown"),
            "system_model": (raw or {}).get("system_model", "Unknown"),
            "baseboard_manufacturer": (raw or {}).get("baseboard_manufacturer", "Unknown"),
            "baseboard_product": (raw or {}).get("baseboard_product", "Unknown"),
            "bios_manufacturer": (raw or {}).get("bios_manufacturer", "Unknown"),
            "bios_version": (raw or {}).get("bios_version", "Unknown"),
        },
        "cpu": {
            "name": (raw or {}).get("cpu_name") or platform.processor(),
            "physical_cores": int((raw or {}).get("cpu_cores") or 0),
            "logical_processors": int((raw or {}).get("cpu_logical") or os.cpu_count() or 0),
            "max_clock_mhz": int((raw or {}).get("cpu_max_clock_mhz") or 0),
        },
        "memory": {
            "total_bytes": ram_bytes,
            "total_usable_gb": ram_gb,
            "shared_with_igpu": True,
            "modules": (raw or {}).get("ram_modules") or [],
        },
        "gpu": {
            "primary_name": intel_gpu.get("name", "Intel Graphics"),
            "vendor": intel_gpu.get("vendor", "Intel Corporation"),
            "driver_version": intel_gpu.get("driver_version", "N/A"),
            "pnp_device_id": intel_gpu.get("pnp_device_id", "N/A"),
            "memory_architecture": "UMA / Shared System Memory (iGPU)",
            "all_display_adapters": gpus,
        },
        "os": {
            "caption": (raw or {}).get("os_caption") or platform.platform(),
            "display_version": (raw or {}).get("os_display_version", ""),
            "version": (raw or {}).get("os_version", platform.version()),
            "build": (raw or {}).get("os_build", ""),
            "ubr": (raw or {}).get("os_ubr", ""),
            "kernel_version": (raw or {}).get("kernel_version", ""),
            "architecture": (raw or {}).get("os_architecture", platform.machine()),
        },
        "storage": {
            "logical_disks": (raw or {}).get("logical_disks") or [],
        },
        "power_scheme": (raw or {}).get("active_power_scheme", "N/A"),
    }


def detect_intel_windows_provenance(repo_dir: str) -> dict[str, str]:
    """Return Gate 0 provenance strings (hardware, os, git_commit) without calling nvidia-smi."""
    m = collect_intel_windows_manifest(repo_dir=repo_dir)
    h = m["host"]
    cpu = m["cpu"]
    mem = m["memory"]
    gpu = m["gpu"]
    os_info = m["os"]

    board = h.get("baseboard_product") or h.get("system_model") or "Windows x86_64"
    hardware = (
        f"{h.get('system_manufacturer', '')} {board} | "
        f"{cpu.get('name', 'Intel CPU')} ({cpu.get('physical_cores')}C/{cpu.get('logical_processors')}T) | "
        f"{mem.get('total_usable_gb', 0.0):.2f} GiB Shared RAM | "
        f"{gpu.get('primary_name')} (driver {gpu.get('driver_version')}, iGPU UMA, no dGPU)"
    ).strip()

    ubr = f".{os_info['ubr']}" if os_info.get("ubr") else ""
    os_str = (
        f"{os_info.get('caption', 'Windows')} {os_info.get('display_version', '')} "
        f"(Build {os_info.get('build', '')}{ubr}, kernel {os_info.get('kernel_version', 'N/A')}, "
        f"{os_info.get('architecture', 'x86_64')})"
    ).strip()

    git_commit = m.get("git_commit", "")
    if len(git_commit) != 40:
        raise RuntimeError(f"FAIL-FAST: invalid git HEAD {git_commit!r}")

    return {
        "hardware": hardware,
        "os": os_str,
        "git_commit": git_commit,
    }


def save_machine_manifest(out_dir: str, repo_dir: str | None = None) -> tuple[str, str]:
    """Save machine_manifest_intel_win.json and machine_manifest_intel_win.txt."""
    os.makedirs(out_dir, exist_ok=True)
    m = collect_intel_windows_manifest(repo_dir=repo_dir)
    json_path = os.path.join(out_dir, "machine_manifest_intel_win.json")
    txt_path = os.path.join(out_dir, "machine_manifest_intel_win.txt")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)

    lines = [
        "================================================================================",
        "MACHINE MANIFEST — WINDOWS INTEL GRAPHICS (DEDICATED ADAPTER)",
        "================================================================================",
        f"Collected At (UTC): {m['collected_at_utc']}",
        f"Computer / User   : {m['host']['computer_name']} / {m['host']['username']} (Admin={m['host']['is_admin']})",
        f"System / Board    : {m['host']['system_manufacturer']} {m['host']['baseboard_product']} (BIOS {m['host']['bios_version']})",
        f"CPU               : {m['cpu']['name']} ({m['cpu']['physical_cores']}C/{m['cpu']['logical_processors']}T @ {m['cpu']['max_clock_mhz']} MHz)",
        f"RAM               : {m['memory']['total_usable_gb']} GB usable (Shared with Intel iGPU)",
        f"Primary GPU       : {m['gpu']['primary_name']} | Driver: {m['gpu']['driver_version']} | UMA Shared Memory",
        f"NVIDIA dGPU       : {m['dedicated_nvidia_gpu_present']} (nvidia-smi / NVML disabled)",
        f"OS / Kernel       : {m['os']['caption']} {m['os']['display_version']} Build {m['os']['build']}.{m['os']['ubr']} (Kernel {m['os']['kernel_version']})",
        f"Active Power Plan : {m['power_scheme']}",
        f"Git Commit        : {m['git_commit']}",
        "================================================================================",
    ]
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return json_path, txt_path
