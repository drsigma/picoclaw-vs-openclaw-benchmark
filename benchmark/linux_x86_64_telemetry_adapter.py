#!/usr/bin/env python3
"""
benchmark/linux_x86_64_telemetry_adapter.py - Native Linux x86_64 telemetry adapter.

Linux counterpart of the Darwin libproc collector (benchmark/telemetry.py). Every value is read
from the running kernel at run time; there are no estimates, no simulated values and no silent
fallbacks. Any unavailable counter raises (FAIL-FAST).

  * PMU (instructions, cycles): perf_event_open(2) attached to the workload PID, enable_on_exec,
    inherit. One event per core PMU (cpu_core / cpu_atom on hybrid Intel; "cpu" otherwise); counts are
    summed because a thread only increments the PMU of the core type it is running on.
  * Peak physical memory (proc_peak_phys_mb), context switches, page faults: wait4(2) rusage of the
    workload process itself (ru_maxrss == VmHWM of the process tree, KiB -> MiB).
    On Linux the primary physical metric is therefore VmHWM / Peak RSS.
  * Energy: Intel RAPL (sysfs powercap, wrap-around aware) + NVIDIA NVML total energy (mJ).
  * Thermal: coretemp package, NVML GPU temperature and throttle reasons, CPU thermal_throttle
    counters, fan RPM (hwmon); fan control through sudo (dell_smm / alienware_wmi).
  * Host provenance (Gate 0): /sys DMI, /proc/cpuinfo, /proc/meminfo, uname, os-release, nvidia-smi, git.
"""

from __future__ import annotations

import ctypes
import glob
import os
import select
import shutil
import struct
import subprocess
import threading
import time
from typing import Any

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def _read_int(path: str) -> int:
    return int(_read(path))


# ==============================================================================
# 1. GATE 0 HOST PROVENANCE
# ==============================================================================

def detect_linux_host_provenance(repo_dir: str = REPO_DIR) -> dict[str, str]:
    sys_vendor = _read("/sys/devices/virtual/dmi/id/sys_vendor")
    product_name = _read("/sys/devices/virtual/dmi/id/product_name")

    cpu_model = None
    with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    if not cpu_model:
        raise RuntimeError("FAIL-FAST: 'model name' not found in /proc/cpuinfo")

    mem_kb = None
    with open("/proc/meminfo", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("MemTotal:"):
                mem_kb = int(line.split()[1])
                break
    if mem_kb is None:
        raise RuntimeError("FAIL-FAST: MemTotal not found in /proc/meminfo")
    ram_str = f"{mem_kb / (1024.0 * 1024.0):.1f} GiB RAM"

    gpu_info = "no NVIDIA GPU (nvidia-smi absent)"
    if shutil.which("nvidia-smi"):
        gpu_info = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            text=True, timeout=10,
        ).strip().splitlines()[0]

    hardware = (
        f"{sys_vendor} {product_name} | {cpu_model} ({os.cpu_count()} logical CPUs) | {ram_str} | {gpu_info}"
    )

    distro = None
    with open("/etc/os-release", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("PRETTY_NAME="):
                distro = line.split("=", 1)[1].strip().strip('"')
    if not distro:
        raise RuntimeError("FAIL-FAST: PRETTY_NAME not found in /etc/os-release")
    uname = subprocess.check_output(["uname", "-srvm"], text=True).strip()

    git_commit = subprocess.check_output(["git", "-C", repo_dir, "rev-parse", "HEAD"], text=True, timeout=10).strip()
    if len(git_commit) != 40:
        raise RuntimeError(f"FAIL-FAST: invalid git HEAD {git_commit!r}")

    return {
        "hardware": hardware,
        "os": f"{distro} ({uname})",
        "git_commit": git_commit,
        "cpu_model": cpu_model,
        "gpu_info": gpu_info,
        "total_ram": ram_str,
        "sys_vendor": sys_vendor,
        "product_name": product_name,
    }


# ==============================================================================
# 2. PMU VIA perf_event_open + RUSAGE VIA wait4
# ==============================================================================

_SYS_PERF_EVENT_OPEN = 298  # x86_64
_PERF_TYPE_HARDWARE = 0
_PERF_COUNT_HW_CPU_CYCLES = 0
_PERF_COUNT_HW_INSTRUCTIONS = 1
_PERF_FLAG_FD_CLOEXEC = 8
# attr.flags bits
_F_DISABLED = 1 << 0
_F_INHERIT = 1 << 1
_F_EXCLUDE_HV = 1 << 6
_F_ENABLE_ON_EXEC = 1 << 12

_libc = ctypes.CDLL(None, use_errno=True)
_libc.syscall.restype = ctypes.c_long


def _core_pmus() -> list[tuple[str, int]]:
    """Core PMUs of this host (hybrid: cpu_core + cpu_atom, otherwise cpu)."""
    pmus = []
    for name in ("cpu_core", "cpu_atom", "cpu"):
        p = f"/sys/bus/event_source/devices/{name}/type"
        if os.path.exists(p):
            pmus.append((name, _read_int(p)))
    if not pmus:
        raise RuntimeError("FAIL-FAST: no core PMU under /sys/bus/event_source/devices")
    if len(pmus) > 1 and pmus[-1][0] == "cpu":
        pmus = [x for x in pmus if x[0] != "cpu"]
    return pmus


def _perf_open(pmu_type: int, hw_config: int, pid: int) -> int:
    attr = bytearray(128)
    struct.pack_into("<IIQ", attr, 0, _PERF_TYPE_HARDWARE, 128, (pmu_type << 32) | hw_config)
    struct.pack_into("<Q", attr, 40, _F_DISABLED | _F_INHERIT | _F_EXCLUDE_HV | _F_ENABLE_ON_EXEC)
    buf = (ctypes.c_char * 128).from_buffer(attr)
    fd = _libc.syscall(_SYS_PERF_EVENT_OPEN, ctypes.byref(buf), pid, -1, -1, _PERF_FLAG_FD_CLOEXEC)
    if fd < 0:
        err = ctypes.get_errno()
        raise RuntimeError(
            f"FAIL-FAST: perf_event_open(pmu_type={pmu_type}, config={hw_config}, pid={pid}) failed: "
            f"errno={err} ({os.strerror(err)}). Required: sysctl kernel.perf_event_paranoid<=0."
        )
    return fd


def assert_pmu_available() -> None:
    paranoid = _read_int("/proc/sys/kernel/perf_event_paranoid")
    if paranoid > 0:
        raise RuntimeError(
            f"FAIL-FAST: kernel.perf_event_paranoid={paranoid} (> 0). "
            "Run: sudo sysctl -w kernel.perf_event_paranoid=-1"
        )


def run_subprocess_with_perf_rusage(
    cmd: list[str],
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    timeout: float | None = None,
) -> tuple[str, str, int, dict[str, Any]]:
    """Run `cmd`, returning (stdout, stderr, returncode, hardware_metrics)."""
    assert_pmu_available()
    pmus = _core_pmus()

    r_pid, w_pid = os.pipe()
    r_go, w_go = os.pipe()

    def _pre_exec() -> None:  # runs in the child between fork and exec; async-signal-safe calls only
        os.write(w_pid, os.getpid().to_bytes(4, "little"))
        os.read(r_go, 1)

    holder: dict[str, Any] = {}

    def _spawn() -> None:
        try:
            holder["proc"] = subprocess.Popen(
                cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=_pre_exec,
            )
        except BaseException as e:  # noqa: BLE001 - re-raised in caller thread
            holder["error"] = e

    th = threading.Thread(target=_spawn, daemon=True)
    th.start()

    fds: dict[str, list[int]] = {"instructions": [], "cycles": []}
    pid = None
    try:
        deadline = time.monotonic() + 30.0
        while pid is None:
            ready, _, _ = select.select([r_pid], [], [], 0.05)
            if ready:
                pid = int.from_bytes(os.read(r_pid, 4), "little")
            elif not th.is_alive() or time.monotonic() > deadline:
                raise holder.get("error") or RuntimeError("FAIL-FAST: workload child did not start")
        for _, ptype in pmus:
            fds["instructions"].append(_perf_open(ptype, _PERF_COUNT_HW_INSTRUCTIONS, pid))
            fds["cycles"].append(_perf_open(ptype, _PERF_COUNT_HW_CPU_CYCLES, pid))
        os.write(w_go, b"1")
    except BaseException:
        try:
            os.write(w_go, b"1")
        except OSError:
            pass
        raise
    finally:
        os.close(r_pid)
        os.close(w_pid)
        os.close(r_go)
        os.close(w_go)

    th.join(timeout=30.0)
    if "error" in holder:
        raise holder["error"]
    proc: subprocess.Popen = holder["proc"]
    assert proc.pid == pid

    sinks: dict[str, bytes] = {}

    def _drain(name: str, stream: Any) -> None:
        sinks[name] = stream.read()

    t_out = threading.Thread(target=_drain, args=("out", proc.stdout), daemon=True)
    t_err = threading.Thread(target=_drain, args=("err", proc.stderr), daemon=True)
    t_out.start()
    t_err.start()

    t_wait0 = time.monotonic()
    while True:
        wpid, status, ru = os.wait4(pid, os.WNOHANG if timeout is not None else 0)
        if wpid == pid:
            break
        if timeout is not None and time.monotonic() - t_wait0 > timeout:
            proc.kill()
            os.wait4(pid, 0)
            raise subprocess.TimeoutExpired(cmd, timeout)
        time.sleep(0.0005)
    t_out.join()
    t_err.join()
    proc.returncode = os.waitstatus_to_exitcode(status)
    proc.stdout.close()
    proc.stderr.close()

    def _sum(kind: str) -> tuple[int, dict[str, int]]:
        per_pmu = {}
        for (pname, _), fd in zip(pmus, fds[kind]):
            per_pmu[pname] = struct.unpack("<Q", os.read(fd, 8))[0]
            os.close(fd)
        return sum(per_pmu.values()), per_pmu

    instructions, ins_pmu = _sum("instructions")
    cycles, cyc_pmu = _sum("cycles")
    if instructions <= 0 or cycles <= 0:
        raise RuntimeError(
            f"FAIL-FAST: PMU returned instructions={instructions}, cycles={cycles} for {cmd[:2]}"
        )

    peak_mb = ru.ru_maxrss / 1024.0  # Linux: KiB
    if peak_mb <= 0.0:
        raise RuntimeError(f"FAIL-FAST: ru_maxrss={ru.ru_maxrss} for {cmd[:2]}")

    hw = {
        "proc_instructions": int(instructions),
        "proc_cycles": int(cycles),
        "proc_billed_energy": 0,  # Darwin-only (ri_billed_energy); no Linux equivalent per process
        "proc_peak_phys_mb": float(peak_mb),
        "proc_rss_mb": float(peak_mb),
        "context_switches": int(ru.ru_nvcsw + ru.ru_nivcsw),
        "context_switches_voluntary": int(ru.ru_nvcsw),
        "page_faults": int(ru.ru_minflt + ru.ru_majflt),
        "page_faults_major": int(ru.ru_majflt),
        "pmu_instructions_by_core_type": ins_pmu,
        "pmu_cycles_by_core_type": cyc_pmu,
    }
    return sinks["out"].decode("utf-8"), sinks["err"].decode("utf-8"), proc.returncode, hw


# ==============================================================================
# 3. THERMAL / FAN CONTROL
# ==============================================================================

def find_hwmon(name: str) -> str:
    for d in sorted(glob.glob("/sys/class/hwmon/hwmon*")):
        if os.path.exists(os.path.join(d, "name")) and _read(os.path.join(d, "name")) == name:
            return d
    raise RuntimeError(f"FAIL-FAST: hwmon '{name}' not found")


def _sudo_write(path: str, value: str) -> None:
    subprocess.run(["sudo", "-n", "tee", path], input=value, text=True, check=True,
                   stdout=subprocess.DEVNULL, timeout=10)


class ThermalController:
    """Pins the Dell G15 fans at maximum and monitors temperatures / throttling."""

    def __init__(self) -> None:
        self.wmi = find_hwmon("alienware_wmi")   # fan*_boost (0-100)
        self.smm = find_hwmon("dell_smm")        # pwm*, fan*_input, fan*_max
        self.core = find_hwmon("coretemp")
        self.pkg_temp = None
        for lbl in sorted(glob.glob(os.path.join(self.core, "temp*_label"))):
            if _read(lbl) == "Package id 0":
                self.pkg_temp = lbl.replace("_label", "_input")
        if self.pkg_temp is None:
            raise RuntimeError("FAIL-FAST: coretemp 'Package id 0' not found")
        self.fans = sorted(glob.glob(os.path.join(self.wmi, "fan*_input")))
        if not self.fans:
            self.fans = sorted(glob.glob(os.path.join(self.smm, "fan*_input")))
        if not self.fans:
            raise RuntimeError("FAIL-FAST: no fan*_input on alienware_wmi or dell_smm")
        self.throttle_files = sorted(glob.glob("/sys/devices/system/cpu/cpu*/thermal_throttle/package_throttle_count"))
        if not self.throttle_files:
            raise RuntimeError("FAIL-FAST: no thermal_throttle counters in sysfs")
        self.nvml = Nvml.instance()

    def force_fans_max(self) -> None:
        for i, _ in enumerate(self.fans, start=1):
            boost = os.path.join(self.wmi, f"fan{i}_boost")
            if os.path.exists(boost):
                _sudo_write(boost, "100")
            en = os.path.join(self.smm, f"pwm{i}_enable")
            pwm = os.path.join(self.smm, f"pwm{i}")
            if os.path.exists(en) and os.path.exists(pwm):
                _sudo_write(en, "1")
                _sudo_write(pwm, "255")

    def fan_rpm(self) -> list[int]:
        return [_read_int(f) for f in self.fans]

    def fan_max_rpm(self) -> list[int]:
        return [_read_int(f.replace("_input", "_max")) for f in self.fans]

    def fans_at_max(self, frac: float = 0.9) -> bool:
        return all(r >= frac * m for r, m in zip(self.fan_rpm(), self.fan_max_rpm()))

    def cpu_temp_c(self) -> float:
        return _read_int(self.pkg_temp) / 1000.0

    def gpu_temp_c(self) -> float:
        return float(self.nvml.temperature())

    def throttle_count(self) -> int:
        return sum(_read_int(p) for p in self.throttle_files)

    def snapshot(self) -> dict[str, Any]:
        return {
            "cpu_pkg_temp_c": self.cpu_temp_c(),
            "gpu_temp_c": self.gpu_temp_c(),
            "fan_rpm": self.fan_rpm(),
            "cpu_pkg_throttle_count": self.throttle_count(),
            "gpu_throttle_reasons": self.nvml.throttle_reasons(),
        }

    def wait_until_cool(self, cpu_max_c: float, gpu_max_c: float, timeout_s: float) -> float:
        t0 = time.monotonic()
        while self.cpu_temp_c() > cpu_max_c or self.gpu_temp_c() > gpu_max_c:
            if time.monotonic() - t0 > timeout_s:
                raise RuntimeError(
                    f"FAIL-FAST: thermal gate not reached in {timeout_s:.0f}s "
                    f"(cpu={self.cpu_temp_c():.1f}C>{cpu_max_c}, gpu={self.gpu_temp_c():.1f}C>{gpu_max_c})"
                )
            time.sleep(1.0)
        return time.monotonic() - t0

    def wait_for_plateau(self, window_s: float = 15.0, tol_c: float = 4.0, timeout_s: float = 300.0) -> dict[str, Any]:
        """Idle plateau: max-min of CPU/GPU temperature over `window_s` below `tol_c`, fans at max."""
        t0 = time.monotonic()
        hist: list[tuple[float, float, float]] = []
        while True:
            now = time.monotonic()
            hist.append((now, self.cpu_temp_c(), self.gpu_temp_c()))
            hist = [h for h in hist if now - h[0] <= window_s]
            if now - hist[0][0] >= window_s - 1.5:
                cpu = [h[1] for h in hist]
                gpu = [h[2] for h in hist]
                if max(cpu) - min(cpu) <= tol_c and max(gpu) - min(gpu) <= tol_c and self.fans_at_max():
                    return {"waited_s": now - t0, "cpu_c": sum(cpu) / len(cpu), "gpu_c": sum(gpu) / len(gpu),
                            "fan_rpm": self.fan_rpm(), "fan_max_rpm": self.fan_max_rpm()}
            if now - t0 > timeout_s:
                raise RuntimeError("FAIL-FAST: thermal plateau not reached")
            time.sleep(1.0)


# ==============================================================================
# 4. NVML (ctypes) AND ENERGY MONITOR
# ==============================================================================

class Nvml:
    _inst: "Nvml | None" = None

    @classmethod
    def instance(cls) -> "Nvml":
        if cls._inst is None:
            cls._inst = Nvml()
        return cls._inst

    def __init__(self) -> None:
        self.lib = ctypes.CDLL("libnvidia-ml.so.1")
        self._chk(self.lib.nvmlInit_v2(), "nvmlInit_v2")
        self.dev = ctypes.c_void_p()
        self._chk(self.lib.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(self.dev)), "GetHandleByIndex")

    @staticmethod
    def _chk(ret: int, what: str) -> None:
        if ret != 0:
            raise RuntimeError(f"FAIL-FAST: NVML {what} returned {ret}")

    def energy_mj(self) -> int:
        e = ctypes.c_uint64()
        self._chk(self.lib.nvmlDeviceGetTotalEnergyConsumption(self.dev, ctypes.byref(e)), "TotalEnergyConsumption")
        return int(e.value)

    def power_mw(self) -> int:
        p = ctypes.c_uint()
        self._chk(self.lib.nvmlDeviceGetPowerUsage(self.dev, ctypes.byref(p)), "PowerUsage")
        return int(p.value)

    def temperature(self) -> int:
        t = ctypes.c_uint()
        self._chk(self.lib.nvmlDeviceGetTemperature(self.dev, 0, ctypes.byref(t)), "Temperature")
        return int(t.value)

    def throttle_reasons(self) -> int:
        r = ctypes.c_ulonglong()
        self._chk(self.lib.nvmlDeviceGetCurrentClocksThrottleReasons(self.dev, ctypes.byref(r)), "ThrottleReasons")
        return int(r.value)


class LinuxHardwarePowerMonitor:
    """Exact energy from hardware counters: Intel RAPL (package, core, uncore) + NVML (GPU)."""

    def __init__(self) -> None:
        base = "/sys/class/powercap"
        self.zones: dict[str, str] = {}
        for z in sorted(glob.glob(f"{base}/intel-rapl:*")):
            if os.path.basename(z).count(":") in (1, 2) and os.path.exists(os.path.join(z, "name")):
                self.zones[_read(os.path.join(z, "name"))] = z
        if "package-0" not in self.zones:
            raise RuntimeError("FAIL-FAST: RAPL package-0 not found under /sys/class/powercap")
        for name, z in self.zones.items():
            p = os.path.join(z, "energy_uj")
            if not os.access(p, os.R_OK):
                raise RuntimeError(
                    f"FAIL-FAST: {p} not readable. Run: sudo chmod -R a+r /sys/class/powercap/intel-rapl*"
                )
        self._range = {n: _read_int(os.path.join(z, "max_energy_range_uj")) for n, z in self.zones.items()}
        self.nvml = Nvml.instance()
        self.telemetry_backend = "linux_intel_rapl_and_nvidia_nvml"
        self.idle_cpu_w = None
        self.idle_gpu_w = None
        self.idle_total_w = None
        self._t0 = 0
        self._snap0: dict[str, int] = {}

    def _snap(self) -> dict[str, int]:
        s = {n: _read_int(os.path.join(z, "energy_uj")) for n, z in self.zones.items()}
        s["gpu_mj"] = self.nvml.energy_mj()
        return s

    def _delta(self, a: dict[str, int], b: dict[str, int]) -> dict[str, float]:
        out = {}
        for n in self.zones:
            d = b[n] - a[n]
            if d < 0:
                d += self._range[n]
            out[n] = d / 1e6
        d = b["gpu_mj"] - a["gpu_mj"]
        if d < 0:
            raise RuntimeError("FAIL-FAST: NVML energy counter decreased")
        out["gpu"] = d / 1e3
        return out

    def measure_idle_baseline(self, duration_s: float) -> dict[str, float]:
        t0 = time.monotonic_ns()
        s0 = self._snap()
        time.sleep(duration_s)
        s1 = self._snap()
        dt = (time.monotonic_ns() - t0) / 1e9
        d = self._delta(s0, s1)
        self.idle_cpu_w = d["package-0"] / dt
        self.idle_gpu_w = d["gpu"] / dt
        self.idle_total_w = self.idle_cpu_w + self.idle_gpu_w
        return {"duration_s": dt, "p_idle_cpu_pkg_w": self.idle_cpu_w, "p_idle_gpu_w": self.idle_gpu_w,
                "p_idle_total_w": self.idle_total_w,
                **{f"p_idle_rapl_{n}_w": d[n] / dt for n in self.zones}}

    def start(self) -> None:
        self._t0 = time.monotonic_ns()
        self._snap0 = self._snap()

    def mark(self) -> dict[str, float]:
        """Energy since start() without stopping (used to split prefill / decode phases)."""
        d = self._delta(self._snap0, self._snap())
        return {"t_s": (time.monotonic_ns() - self._t0) / 1e9, **d}

    def stop(self) -> dict[str, float]:
        if self.idle_total_w is None:
            raise RuntimeError("FAIL-FAST: idle baseline not measured before trials")
        s1 = self._snap()
        dt = (time.monotonic_ns() - self._t0) / 1e9
        d = self._delta(self._snap0, s1)
        total = d["package-0"] + d["gpu"]
        net = total - self.idle_total_w * dt
        return {
            "energy_cpu_pkg_j": d["package-0"],
            "energy_cpu_core_j": d.get("core", float("nan")),
            "energy_cpu_uncore_j": d.get("uncore", float("nan")),
            "energy_gpu_j": d["gpu"],
            "energy_total_j": total,
            "energy_net_above_idle_j": net,
            "p_net_w": net / dt,
            "avg_power_w": total / dt,
            "duration_s": dt,
        }
