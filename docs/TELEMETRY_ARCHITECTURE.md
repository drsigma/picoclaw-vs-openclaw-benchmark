# Telemetry Architecture and Hardware Sensor Boundaries across Quad-Platform Matrix

This document provides formal technical documentation for the hardware telemetry subsystems, sensor interfaces, and physical observation boundaries utilized across the four physical benchmark platforms in accordance with empirical systems benchmarking standards.

---

## 1. Physical Hardware & Sensor Architecture

| Platform | Primary Telemetry Interface | Measurable Domains | Unobservable / Restricted Domains | Sampling & Attribution Model |
| :--- | :--- | :--- | :--- | :--- |
| **macOS ARM64 (Apple Silicon M4)** | Apple SMC via `powermetrics` / `task_info` | Unified Package Power (CPU clusters, Metal GPU, ANE, DRAM controller) | Per-thread hardware PMC counters in standard unprivileged space | Continuous root daemon sampling at 50 ms intervals with trapezoidal energy integration |
| **Linux x86_64 (Ubuntu 26.04)** | Intel RAPL (`/sys/class/powercap`) + NVIDIA NVML (`pynvml`) | CPU package (`intel-rapl:0`), DRAM domain (`intel-rapl:0:0`), discrete RTX 3050 power shunts | Per-process fine-grained GPU thread energy decomposition | Microsecond MSR hardware energy counter deltas + NVML power polling at 10 ms |
| **Windows 11 x86_64 (NVIDIA)** | NVIDIA NVML (`pynvml`) + Win32 `QueryProcessCycleTime` | Discrete RTX 3050 GPU power/temperature, process user/kernel cycles via PSAPI | Direct kernel MSR RAPL without ring-0 driver; DRAM domain unobservable | Delta measurement of process execution cycles and NVML board power integration |
| **Windows 10/11 x86_64 (Intel HD Graphics 4600)** | Win32 PSAPI / `QueryProcessCycleTime` | Process CPU cycles, CPU package thermal register (WMI/ACPI), physical RSS | Direct GPU hardware counter without Intel GPA; DRAM energy unobservable | Process cycle attribution; energy fields set explicitly to `null` / `N/A` |

---

## 2. Sensor Boundaries and Attribution Principles

### 2.1 Apple Silicon M4 (Unified Memory Architecture)
- **Sensor:** Apple System Management Controller (SMC) sampled via root `powermetrics`.
- **Physical Granularity:** Total system-on-chip (SoC) package power decomposed into CPU (Efficiency vs. Performance clusters), Integrated Metal GPU, and Apple Neural Engine (ANE).
- **Attribution Policy:** Quiescent idle package baseline ($P_{\text{idle}} \approx 1.20\text{ W}$) is subtracted from active integration window to compute net execution energy $E_{\text{net}} = \int (P(t) - P_{\text{idle}}) \, dt$.
- **Bandwidth Approximation:** Unified Memory Architecture (UMA) memory throughput is modeled analytically as $BW_{\text{UMA}} = N_{\text{tokens}} \times \text{Model\_Size} / T_{\text{gen}}$ and documented as an upper-bound order-of-magnitude analytical estimate rather than a bus hardware counter.

### 2.2 Linux x86_64 (Intel i5-12500H + NVIDIA RTX 3050 Laptop)
- **Sensors:** Running Average Power Limit (RAPL) sysfs interface (`/sys/class/powercap/intel-rapl:0`) and NVIDIA Management Library (`libnvidia-ml.so`).
- **Energy Accounting:** Combined system energy under load:
  $$E_{\text{total}} = \Delta E_{\text{RAPL, CPU}} + \Delta E_{\text{RAPL, DRAM}} + \int_{t_{\text{start}}}^{t_{\text{end}}} P_{\text{NVML, GPU}}(t) \, dt$$
- **Telemetry Backend Label:** Labeled as `rapl_nvml_hardware`.
- **Throttling Verification:** Hardware register `cpu_pkg_throttle_events` and NVML throttle masks (`gpu_throttle_reasons`) are sampled before and after each trial to guarantee thermal quiescence.

### 2.3 Windows 11 x86_64 (NVIDIA RTX 3050 Laptop)
- **Sensors:** NVIDIA NVML via `pynvml` and Win32 PSAPI process cycle accounting (`QueryProcessCycleTime`).
- **Telemetry Backend Label:** Labeled as `win32_cycles_nvml_real`.
- **Explicit-Null Policy:** Because direct kernel MSR RAPL access is restricted without third-party ring-0 kernel drivers, CPU package energy is not fabricated. GPU energy is measured directly from NVML, and CPU computational effort is captured through exact hardware thread cycle counters.

### 2.4 Windows 10/11 x86_64 (Intel Core i7-4790K / HD Graphics 4600 iGPU)
- **Sensors:** Win32 `QueryProcessCycleTime`, `K32GetProcessMemoryInfo`, and WMI/ACPI thermal probes.
- **Telemetry Backend Label:** Labeled as `win32_cycles_psapi`.
- **Explicit-Null Policy:** DRAM and package energy counters are physically unavailable through user-mode APIs on legacy Haswell iGPU architectures. All energy fields (`energy_total_j`, `energy_gpu_j`, `energy_net_above_idle_j`) are recorded explicitly as `null` / `"N/A"`, with execution cost represented faithfully by elapsed latency and hardware process cycles.

---

## 3. Telemetry Verification in Quality Gatekeeper

Every collected JSONL record must contain:
1. `telemetry_backend`: Explicit non-empty string declaring the active sensor subsystem.
2. `is_simulated`: Boolean set to `false`.
3. Sensor fields matching the declared backend (no synthetic numerical values in restricted domains).
4. Physical plausibility checks: $T_{\text{task}} \ge T_{\text{neural}} \ge 0$, and when energy is measured, $E \ge 0$.
