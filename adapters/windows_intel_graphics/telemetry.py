#!/usr/bin/env python3
"""
adapters/windows_intel_graphics/telemetry.py

Dedicated Windows Intel Graphics (iGPU / UMA Shared Memory) telemetry module.
Zero mocks, zero NVML / nvidia-smi calls, strict 'N/A' for metrics unavailable in
Windows user-mode, and strictly per-trial deltas (never cumulative OS counters).
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import datetime
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import threading
import time
from typing import Any

import psutil

# Explicit Zero-Mock constant for hardware counters unavailable in Windows user-mode on Intel iGPU
NA = "N/A"

# Win32 ExecutionState flags for anti-sleep protection
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


def assert_windows_process_counters_available() -> None:
    """Verify Win32 QueryProcessCycleTime and GetProcessMemoryInfo are available."""
    if platform.system() != "Windows":
        raise RuntimeError("Windows Intel Graphics telemetry requires Windows OS.")
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
    if not hasattr(kernel32, "QueryProcessCycleTime"):
        raise RuntimeError("FAIL-FAST: QueryProcessCycleTime unavailable.")
    if not hasattr(psapi, "GetProcessMemoryInfo"):
        raise RuntimeError("FAIL-FAST: GetProcessMemoryInfo unavailable.")


def set_system_awake(keep_display: bool = True) -> bool:
    """Assert Win32 SetThreadExecutionState so Windows does not suspend or turn off display."""
    if platform.system() != "Windows":
        return False
    try:
        flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | (ES_DISPLAY_REQUIRED if keep_display else 0)
        res = ctypes.windll.kernel32.SetThreadExecutionState(flags)
        return res != 0
    except Exception:
        return False


def cleanup_orphan_processes(
    target_names: tuple[str, ...] = ("llama-server.exe", "picoclaw_orch_windows.exe"),
    port_to_check: int = 8080,
) -> dict[str, Any]:
    """
    Terminate orphan benchmark processes and verify loopback port availability
    before starting a new block to avoid exhausting shared RAM or freezing.
    """
    killed: list[dict[str, Any]] = []
    lower_targets = {t.lower() for t in target_names}
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            pname = (proc.info.get("name") or "").lower()
            if pname in lower_targets:
                pid = proc.info["pid"]
                proc.terminate()
                try:
                    proc.wait(timeout=3.0)
                except psutil.TimeoutExpired:
                    proc.kill()
                killed.append({"pid": pid, "name": pname})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Check if any process still holds the target port
    port_free = True
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", port_to_check)) == 0:
            port_free = False

    return {
        "killed_processes": killed,
        "port_checked": port_to_check,
        "port_free": port_free,
    }


def run_subprocess_with_intel_win_counters(
    cmd: list[str],
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    timeout: float | None = None,
) -> tuple[str, str, int, dict[str, Any]]:
    """
    Run a worker subprocess encapsulated in a Win32 Job Object and extract empirical
    QueryProcessCycleTime, GetProcessMemoryInfo (PeakWorkingSetSize), and PageFaultCount.
    Hardware retired instructions (PMU) are explicitly declared 'N/A' in user-mode (Zero-Mock).
    """
    cmd = list(cmd)
    if cmd and os.path.basename(cmd[0]).lower() in ("py.exe", "py"):
        real_py = sys.executable
        if os.path.basename(real_py).lower() in ("py.exe", "py"):
            real_py = shutil.which("python.exe") or shutil.which("python") or real_py
        cmd[0] = real_py

    windll = getattr(ctypes, "windll", None)
    if windll is None:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate(timeout=timeout)
        return stdout, stderr, proc.returncode, {
            "proc_instructions": NA,
            "proc_cycles": NA,
            "proc_billed_energy": NA,
            "proc_peak_phys_mb": NA,
            "proc_rss_mb": NA,
            "page_faults": NA,
        }

    kernel32 = windll.kernel32
    psapi = windll.psapi

    hJob = None
    try:
        hJob = kernel32.CreateJobObjectW(None, None)
    except Exception:
        hJob = None

    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    hProcess = None
    try:
        hProcess = kernel32.OpenProcess(0x1000 | 0x0400, False, proc.pid)
        if hJob and hProcess:
            kernel32.AssignProcessToJobObject(hJob, hProcess)
    except Exception:
        pass

    child_peak_rss_bytes = 0
    stop_event = threading.Event()

    def _child_watcher() -> None:
        nonlocal child_peak_rss_bytes
        try:
            parent_proc = psutil.Process(proc.pid)
        except Exception:
            return
        while not stop_event.is_set():
            try:
                if not parent_proc.is_running():
                    break
                for ch in parent_proc.children(recursive=True):
                    try:
                        mem = ch.memory_info()
                        wset = getattr(mem, "peak_wset", None) or getattr(mem, "rss", 0)
                        if wset > child_peak_rss_bytes:
                            child_peak_rss_bytes = wset
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            time.sleep(0.005)

    watcher = threading.Thread(target=_child_watcher, daemon=True)
    watcher.start()

    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        raise
    finally:
        stop_event.set()
        watcher.join(timeout=0.15)

    cycles = ctypes.c_uint64()
    pmc = PROCESS_MEMORY_COUNTERS_EX()
    pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)

    proc_cycles: int | str = NA
    proc_peak_mb = 0.0
    proc_rss_mb = 0.0
    page_faults: int | str = NA

    if hProcess:
        if kernel32.QueryProcessCycleTime(hProcess, ctypes.byref(cycles)):
            proc_cycles = int(cycles.value)
        if psapi.GetProcessMemoryInfo(hProcess, ctypes.byref(pmc), pmc.cb):
            proc_peak_mb = round(pmc.PeakWorkingSetSize / (1024.0 * 1024.0), 4)
            proc_rss_mb = round(pmc.WorkingSetSize / (1024.0 * 1024.0), 4)
            page_faults = int(pmc.PageFaultCount)
        kernel32.CloseHandle(hProcess)

    job_peak_mb = 0.0
    if hJob:
        try:
            ext_info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            ret_len = wintypes.DWORD()
            if kernel32.QueryInformationJobObject(
                hJob, 9, ctypes.byref(ext_info), ctypes.sizeof(ext_info), ctypes.byref(ret_len)
            ):
                job_peak_bytes = max(ext_info.PeakJobMemoryUsed, ext_info.PeakProcessMemoryUsed)
                if job_peak_bytes > 0:
                    job_peak_mb = round(job_peak_bytes / (1024.0 * 1024.0), 4)
        except Exception:
            pass
        finally:
            try:
                kernel32.CloseHandle(hJob)
            except Exception:
                pass

    if child_peak_rss_bytes > 0:
        child_mb = round(child_peak_rss_bytes / (1024.0 * 1024.0), 4)
        proc_peak_mb = max(proc_peak_mb, child_mb)
        if proc_rss_mb <= 5.0:
            proc_rss_mb = max(proc_rss_mb, child_mb)

    if job_peak_mb > 0:
        proc_peak_mb = max(proc_peak_mb, job_peak_mb)
        if proc_rss_mb <= 5.0:
            proc_rss_mb = max(proc_rss_mb, job_peak_mb)

    hw_stats = {
        "proc_instructions": NA,  # PMU retired instruction counter restricted in Windows user-mode
        "proc_cycles": proc_cycles,
        "proc_billed_energy": NA,  # Darwin XNU SMC metric, not applicable on Windows
        "proc_peak_phys_mb": proc_peak_mb if proc_peak_mb > 0 else NA,
        "proc_rss_mb": proc_rss_mb if proc_rss_mb > 0 else NA,
        "page_faults": page_faults,
    }
    return stdout, stderr, proc.returncode, hw_stats


def _query_windows_intel_sensors_raw() -> dict[str, Any]:
    """
    Query real Windows CIM / WDDM performance counters for CPU clock, ACPI thermal zones,
    Intel HD Graphics WDDM shared/dedicated memory, GPU engine utilization, and optional
    LibreHardwareMonitor WMI sensors. Never invokes nvidia-smi or NVML.
    """
    ps = r"""
$ErrorActionPreference = 'SilentlyContinue'
$procInfo = Get-CimInstance Win32_PerfFormattedData_Counters_ProcessorInformation | Where-Object { $_.Name -eq '_Total' } | Select-Object -First 1
$tz = @(Get-CimInstance Win32_PerfFormattedData_Counters_ThermalZoneInformation | ForEach-Object {
    @{
        name = $_.Name
        temp_c = if ($_.HighPrecisionTemperature) { [math]::Round(($_.HighPrecisionTemperature / 10.0) - 273.15, 2) } elseif ($_.Temperature) { [math]::Round($_.Temperature - 273.15, 2) } else { $null }
        throttle_reasons = [int64]$_.ThrottleReasons
    }
})
$gpuShared = (Get-Counter '\GPU Adapter Memory(*)\Shared Usage' -ErrorAction SilentlyContinue).CounterSamples
$gpuDed = (Get-Counter '\GPU Adapter Memory(*)\Dedicated Usage' -ErrorAction SilentlyContinue).CounterSamples
$gpuEng = (Get-Counter '\GPU Engine(*)\Utilization Percentage' -ErrorAction SilentlyContinue).CounterSamples

$sharedBytes = 0
if ($gpuShared) { $sharedBytes = ($gpuShared | Measure-Object -Property CookedValue -Maximum).Maximum }
$dedBytes = 0
if ($gpuDed) { $dedBytes = ($gpuDed | Measure-Object -Property CookedValue -Maximum).Maximum }
$engSum = $null
if ($gpuEng) { $engSum = [math]::Min(100.0, [math]::Round(($gpuEng | Measure-Object -Property CookedValue -Sum).Sum, 2)) }

# Optional LibreHardwareMonitor / OpenHardwareMonitor live CPU package diode temp if installed & running
$lhmCpuTemp = $null
$lhmPkgPowerW = $null
$lhmFanRpm = $null
foreach ($ns in @('root/LibreHardwareMonitor', 'root/OpenHardwareMonitor')) {
    $sensors = Get-CimInstance -Namespace $ns -ClassName Sensor -ErrorAction SilentlyContinue
    if ($sensors) {
        $ct = $sensors | Where-Object { $_.SensorType -eq 'Temperature' -and $_.Name -match 'CPU Package|Core Max' } | Select-Object -First 1
        if ($ct) { $lhmCpuTemp = [math]::Round([double]$ct.Value, 2) }
        $pw = $sensors | Where-Object { $_.SensorType -eq 'Power' -and $_.Name -match 'CPU Package' } | Select-Object -First 1
        if ($pw) { $lhmPkgPowerW = [math]::Round([double]$pw.Value, 3) }
        $fn = $sensors | Where-Object { $_.SensorType -eq 'Fan' -and $_.Value -gt 0 } | Select-Object -First 1
        if ($fn) { $lhmFanRpm = [int]$fn.Value }
        break
    }
}

$out = [ordered]@{
    cpu_freq_mhz = if ($procInfo) { [int]$procInfo.ProcessorFrequency } else { $null }
    cpu_pct_max_freq = if ($procInfo) { [int]$procInfo.PercentofMaximumFrequency } else { $null }
    cpu_pct_utility = if ($procInfo) { [int]$procInfo.PercentProcessorUtility } else { $null }
    thermal_zones = $tz
    igpu_shared_mem_mb = if ($gpuShared) { [math]::Round($sharedBytes / 1MB, 2) } else { $null }
    igpu_dedicated_mem_mb = if ($gpuDed) { [math]::Round($dedBytes / 1MB, 2) } else { $null }
    igpu_utilization_pct = $engSum
    lhm_cpu_pkg_temp_c = $lhmCpuTemp
    lhm_cpu_pkg_power_w = $lhmPkgPowerW
    lhm_fan_rpm = $lhmFanRpm
}
$out | ConvertTo-Json -Depth 4
"""
    if platform.system() != "Windows":
        return {}
    try:
        out = subprocess.check_output(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10.0,
        ).strip()
        return json.loads(out) if out else {}
    except Exception:
        return {}


class IntelGraphicsThermalAndLoadMonitor:
    """
    Per-trial delta telemetry & thermal/RAM safeguard monitor for Windows Intel Graphics.

    - Computes strictly per-trial deltas (end vs start) for throttle counts, shared RAM,
      and WDDM iGPU memory (never summing cumulative OS counters).
    - Periodically samples CPU utilization, frequency, and iGPU load during each trial.
    - Applies controlled cooldown pauses if temperature exceeds threshold, sustained
      thermal frequency throttling occurs, or available shared RAM drops dangerously low.
    - Reports explicit 'N/A' for metrics genuinely unavailable in Windows user-mode.
    """

    def __init__(
        self,
        cpu_temp_threshold_c: float = 82.0,
        min_clock_under_load_mhz: int = 3100,
        min_free_ram_mb: float = 1800.0,
        cooldown_duration_s: float = 20.0,
        cooldown_log_path: str | None = None,
    ) -> None:
        self.telemetry_backend = "windows_intel_graphics_wddm_pdh_and_win32_user_mode"
        self.cpu_temp_threshold_c = cpu_temp_threshold_c
        self.min_clock_under_load_mhz = min_clock_under_load_mhz
        self.min_free_ram_mb = min_free_ram_mb
        self.cooldown_duration_s = cooldown_duration_s
        self.cooldown_log_path = cooldown_log_path

        self._t0: float = 0.0
        self._s0: dict[str, Any] = {}
        self._cpu_samples: list[float] = []
        self._ram_used_samples: list[float] = []
        self._stop_evt = threading.Event()
        self._thread: threading.Thread | None = None
        self._server_pid: int | None = None

    def set_server_pid(self, pid: int | None) -> None:
        self._server_pid = pid

    def _server_rss_mb(self) -> float | str:
        if not self._server_pid:
            return NA
        try:
            return round(psutil.Process(self._server_pid).memory_info().rss / (1024.0 * 1024.0), 2)
        except Exception:
            return NA

    def snapshot(self) -> dict[str, Any]:
        vm = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=None)
        raw = _query_windows_intel_sensors_raw()

        tz_list = raw.get("thermal_zones") or []
        if isinstance(tz_list, dict):
            tz_list = [tz_list]
        tz_map: dict[str, float] = {}
        throttle_reasons_mask = 0
        for item in tz_list:
            name = str(item.get("name", ""))
            if item.get("temp_c") is not None:
                tz_map[name] = float(item["temp_c"])
            tr = item.get("throttle_reasons")
            if isinstance(tr, (int, float)):
                throttle_reasons_mask |= int(tr)

        lhm_temp = raw.get("lhm_cpu_pkg_temp_c")
        if lhm_temp is not None:
            cpu_pkg_temp_c: float | str = float(lhm_temp)
            thermal_source = "LibreHardwareMonitor_WMI_CPU_Package"
        else:
            # ACPI TZ00/TZ01 on desktop Z97 boards are motherboard zones, NOT CPU package diode.
            # Report ACPI zones transparently and keep cpu_pkg_temp_c as 'N/A' (Zero-Mock).
            cpu_pkg_temp_c = NA
            thermal_source = "ACPI_ThermalZoneInformation_motherboard_only"

        return {
            "timestamp_monotonic": time.monotonic(),
            "system_ram_total_mb": round(vm.total / (1024.0 * 1024.0), 2),
            "system_ram_used_mb": round(vm.used / (1024.0 * 1024.0), 2),
            "system_ram_available_mb": round(vm.available / (1024.0 * 1024.0), 2),
            "system_ram_pct": round(vm.percent, 2),
            "server_rss_mb": self._server_rss_mb(),
            "cpu_utilization_pct": round(float(cpu_pct), 2),
            "cpu_freq_mhz": raw.get("cpu_freq_mhz") if raw.get("cpu_freq_mhz") is not None else NA,
            "cpu_pct_max_freq": raw.get("cpu_pct_max_freq") if raw.get("cpu_pct_max_freq") is not None else NA,
            "igpu_shared_mem_mb": raw.get("igpu_shared_mem_mb") if raw.get("igpu_shared_mem_mb") is not None else NA,
            "igpu_dedicated_mem_mb": raw.get("igpu_dedicated_mem_mb") if raw.get("igpu_dedicated_mem_mb") is not None else NA,
            "igpu_utilization_pct": raw.get("igpu_utilization_pct") if raw.get("igpu_utilization_pct") is not None else NA,
            "acpi_tz00_c": tz_map.get(r"\_TZ.TZ00", NA),
            "acpi_tz01_c": tz_map.get(r"\_TZ.TZ01", NA),
            "cpu_pkg_temp_c": cpu_pkg_temp_c,
            "thermal_sensor_source": thermal_source,
            "acpi_throttle_reasons_bitmask": throttle_reasons_mask,
            "fan_rpm": raw.get("lhm_fan_rpm") if raw.get("lhm_fan_rpm") is not None else NA,
            "cpu_pkg_power_w": raw.get("lhm_cpu_pkg_power_w") if raw.get("lhm_cpu_pkg_power_w") is not None else NA,
        }

    def start_trial(self) -> dict[str, Any]:
        psutil.cpu_percent(interval=None)
        self._cpu_samples.clear()
        self._ram_used_samples.clear()
        self._stop_evt.clear()
        self._s0 = self.snapshot()
        self._t0 = time.perf_counter()

        def _sampler() -> None:
            while not self._stop_evt.is_set():
                try:
                    self._cpu_samples.append(psutil.cpu_percent(interval=None))
                    self._ram_used_samples.append(psutil.virtual_memory().used / (1024.0 * 1024.0))
                except Exception:
                    pass
                self._stop_evt.wait(0.25)

        self._thread = threading.Thread(target=_sampler, daemon=True)
        self._thread.start()
        return self._s0

    def stop_trial(self) -> dict[str, Any]:
        t1 = time.perf_counter()
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        s1 = self.snapshot()
        s0 = self._s0
        duration_s = max(0.0001, t1 - self._t0)

        # Strictly per-trial DELTAS (end - start), never cumulative OS totals
        def _delta(k: str) -> float | str:
            v0, v1 = s0.get(k), s1.get(k)
            if isinstance(v0, (int, float)) and isinstance(v1, (int, float)):
                return round(float(v1) - float(v0), 3)
            return NA

        # Throttle delta: detect transition into active throttle or active ACPI throttle during trial
        tr0 = int(s0.get("acpi_throttle_reasons_bitmask", 0))
        tr1 = int(s1.get("acpi_throttle_reasons_bitmask", 0))
        # Count newly asserted throttle bits or active throttle during the trial window (delta, not cumulative)
        newly_asserted_bits = bin(tr1 & (~tr0)).count("1")
        active_throttle_delta = newly_asserted_bits + (1 if (tr1 != 0 and newly_asserted_bits == 0) else 0)

        # Frequency-drop throttling signal when CPU was heavily loaded (>60%)
        avg_cpu = round(sum(self._cpu_samples) / len(self._cpu_samples), 2) if self._cpu_samples else s1["cpu_utilization_pct"]
        max_cpu = round(max(self._cpu_samples), 2) if self._cpu_samples else s1["cpu_utilization_pct"]
        peak_sys_ram = round(max(self._ram_used_samples), 2) if self._ram_used_samples else s1["system_ram_used_mb"]

        freq_end = s1.get("cpu_freq_mhz")
        clock_throttled = bool(
            isinstance(freq_end, (int, float))
            and avg_cpu >= 60.0
            and 0 < freq_end < self.min_clock_under_load_mhz
        )
        temp_end = s1.get("cpu_pkg_temp_c")
        temp_throttled = bool(isinstance(temp_end, (int, float)) and temp_end >= self.cpu_temp_threshold_c)
        thermal_throttled = bool(active_throttle_delta > 0 or clock_throttled or temp_throttled)

        # Energy: strictly 'N/A' unless real hardware sensor (e.g. LibreHardwareMonitor RAPL) reported Watts
        p0, p1 = s0.get("cpu_pkg_power_w"), s1.get("cpu_pkg_power_w")
        if isinstance(p0, (int, float)) and isinstance(p1, (int, float)) and p0 > 0 and p1 > 0:
            avg_p = 0.5 * (p0 + p1)
            energy_cpu_pkg_j: float | str = round(avg_p * duration_s, 4)
        else:
            energy_cpu_pkg_j = NA

        return {
            "trial_wall_s": round(duration_s, 6),
            "cpu_utilization_avg_pct": avg_cpu,
            "cpu_utilization_max_pct": max_cpu,
            "cpu_freq_start_mhz": s0.get("cpu_freq_mhz", NA),
            "cpu_freq_end_mhz": freq_end,
            "cpu_pct_max_freq_end": s1.get("cpu_pct_max_freq", NA),
            "system_ram_total_mb": s1["system_ram_total_mb"],
            "system_ram_used_start_mb": s0["system_ram_used_mb"],
            "system_ram_used_end_mb": s1["system_ram_used_mb"],
            "system_ram_peak_mb": peak_sys_ram,
            "system_ram_delta_mb": _delta("system_ram_used_mb"),
            "system_ram_available_end_mb": s1["system_ram_available_mb"],
            "server_rss_mb": s1["server_rss_mb"],
            "igpu_shared_mem_start_mb": s0.get("igpu_shared_mem_mb", NA),
            "igpu_shared_mem_end_mb": s1.get("igpu_shared_mem_mb", NA),
            "igpu_shared_mem_delta_mb": _delta("igpu_shared_mem_mb"),
            "igpu_dedicated_mem_end_mb": s1.get("igpu_dedicated_mem_mb", NA),
            "igpu_utilization_end_pct": s1.get("igpu_utilization_pct", NA),
            "acpi_tz00_start_c": s0.get("acpi_tz00_c", NA),
            "acpi_tz00_end_c": s1.get("acpi_tz00_c", NA),
            "acpi_tz01_start_c": s0.get("acpi_tz01_c", NA),
            "acpi_tz01_end_c": s1.get("acpi_tz01_c", NA),
            "cpu_pkg_temp_start_c": s0.get("cpu_pkg_temp_c", NA),
            "cpu_pkg_temp_end_c": temp_end,
            "gpu_temp_start_c": NA,  # Intel HD Graphics 4600 die temp shares package / not exposed via WMI user-mode
            "gpu_temp_end_c": NA,
            "thermal_sensor_source": s1.get("thermal_sensor_source", NA),
            "fan_rpm_end": s1.get("fan_rpm", NA),
            "throttle_reasons_start": tr0,
            "throttle_reasons_end": tr1,
            "throttle_delta_events": active_throttle_delta,
            "clock_throttle_detected": clock_throttled,
            "thermal_throttled": thermal_throttled,
            # Zero-Mock explicit 'N/A' fields for metrics unavailable on Intel HD Graphics user-mode
            "energy_cpu_pkg_j": energy_cpu_pkg_j,
            "energy_gpu_j": NA,
            "energy_total_j": NA,
            "energy_net_above_idle_j": NA,
            "pcie_bandwidth_mb_s": NA,
            "nvml_used": False,
        }

    def check_and_cooldown(self, context_label: str = "") -> dict[str, Any]:
        """
        Inspect thermal, throttling, and shared RAM state before a trial/block.
        If any safety threshold is exceeded, execute a controlled cooldown pause
        and log the event to cooldown_events.jsonl.
        """
        snap = self.snapshot()
        reasons: list[str] = []

        cpu_temp = snap.get("cpu_pkg_temp_c")
        if isinstance(cpu_temp, (int, float)) and cpu_temp >= self.cpu_temp_threshold_c:
            reasons.append(f"cpu_pkg_temp_c={cpu_temp:.1f}C >= {self.cpu_temp_threshold_c:.1f}C")

        for tz_key in ("acpi_tz00_c", "acpi_tz01_c"):
            tz_val = snap.get(tz_key)
            if isinstance(tz_val, (int, float)) and tz_val >= self.cpu_temp_threshold_c:
                reasons.append(f"{tz_key}={tz_val:.1f}C >= {self.cpu_temp_threshold_c:.1f}C")

        if int(snap.get("acpi_throttle_reasons_bitmask", 0)) != 0:
            reasons.append(f"acpi_throttle_reasons_bitmask={snap['acpi_throttle_reasons_bitmask']}")

        avail_mb = snap.get("system_ram_available_mb", 99999.0)
        if isinstance(avail_mb, (int, float)) and avail_mb < self.min_free_ram_mb:
            reasons.append(f"low_shared_ram_available_mb={avail_mb:.1f} < {self.min_free_ram_mb:.1f}")

        if not reasons:
            return {"cooldown_triggered": False, "cooldown_s": 0.0, "reasons": []}

        t0 = time.monotonic()
        time.sleep(self.cooldown_duration_s)
        waited = round(time.monotonic() - t0, 2)
        after = self.snapshot()

        event = {
            "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "context": context_label,
            "reasons": reasons,
            "cooldown_s": waited,
            "before": {
                "cpu_pkg_temp_c": snap.get("cpu_pkg_temp_c"),
                "acpi_tz00_c": snap.get("acpi_tz00_c"),
                "acpi_tz01_c": snap.get("acpi_tz01_c"),
                "system_ram_available_mb": snap.get("system_ram_available_mb"),
                "cpu_freq_mhz": snap.get("cpu_freq_mhz"),
            },
            "after": {
                "cpu_pkg_temp_c": after.get("cpu_pkg_temp_c"),
                "acpi_tz00_c": after.get("acpi_tz00_c"),
                "acpi_tz01_c": after.get("acpi_tz01_c"),
                "system_ram_available_mb": after.get("system_ram_available_mb"),
                "cpu_freq_mhz": after.get("cpu_freq_mhz"),
            },
        }
        if self.cooldown_log_path:
            os.makedirs(os.path.dirname(self.cooldown_log_path), exist_ok=True)
            with open(self.cooldown_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")

        return {"cooldown_triggered": True, "cooldown_s": waited, "reasons": reasons}
