# Table 1: Quad-Platform Master Systems & Microarchitectural Conformance (W2 Tool Chain)

| Architecture & Runtime | Platform OS | $T_{\text{task}}$ Median (ms) | $T_{\text{orch}}$ Median (ms) [95% CI] | $\Phi_{\text{orch}}$ (%) | Peak RSS (MB) | Net Energy (J) | EDP ($J \cdot s$) | Instructions (M) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| PicoClaw (Native Go) | macOS ARM64 (M4) | 5272.68 | 5.53 [5.16, 6.50] | 0.10% | 5.09 | 88.28 | 464.63 | 62.27M |
| PicoClaw (Native Go) | Linux x86_64 | 2725.00 | 6.66 [6.05, 7.29] | 0.24% | 9.70 | 204.61 | 555.93 | 32.65M |
| PicoClaw (Native Go) | Windows 11 NVIDIA | 2928.29 | 13.11 [11.49, 14.04] | 0.45% | 10.20 | 136.97 | 402.65 | N/A* |
| PicoClaw (Native Go) | Windows Intel iGPU | 53505.80 | 14.03 [13.77, 14.68] | 0.03% | 8.19 | N/A** | N/A** | N/A* |
| OpenClaw (Node.js Minimal 15) | macOS ARM64 (M4) | 5284.81 | 20.60 [20.43, 21.02] | 0.39% | 37.55 | 89.34 | 474.17 | 789.72M |
| OpenClaw (Node.js Minimal 15) | Linux x86_64 | 2760.46 | 31.45 [31.04, 32.14] | 1.14% | 86.42 | 203.81 | 560.20 | 768.09M |
| OpenClaw (Node.js Minimal 15) | Windows 11 NVIDIA | 2906.76 | 40.68 [40.50, 41.01] | 1.40% | 72.89 | 136.74 | 400.27 | N/A* |
| OpenClaw (Node.js Minimal 15) | Windows Intel iGPU | 53505.92 | 57.86 [56.87, 58.39] | 0.11% | 54.71 | N/A** | N/A** | N/A* |
| OpenClaw (Node.js Full 54) | macOS ARM64 (M4) | 18406.88 | 24.55 [24.38, 24.82] | 0.13% | 37.71 | 305.82 | 5628.88 | 791.65M |
| OpenClaw (Node.js Full 54) | Linux x86_64 | 7891.12 | 35.99 [35.60, 37.42] | 0.46% | 86.67 | 553.76 | 4364.61 | 771.51M |
| OpenClaw (Node.js Full 54) | Windows 11 NVIDIA | 7896.41 | 48.55 [48.15, 48.82] | 0.61% | 72.93 | 467.43 | 3694.01 | N/A* |
| OpenClaw (Node.js Full 54) | Windows Intel iGPU | 226696.86 | 68.89 [68.08, 69.65] | 0.03% | 54.76 | N/A** | N/A** | N/A* |
| PythonNative (CPython VM) | macOS ARM64 (M4) | 5286.33 | 11.63 [11.35, 11.81] | 0.22% | 24.13 | 88.89 | 468.11 | 649.57M |
| PythonNative (CPython VM) | Linux x86_64 | 2747.65 | 17.13 [16.87, 18.23] | 0.62% | 40.15 | 205.49 | 567.20 | 2544.43M |
| PythonNative (CPython VM) | Windows 11 NVIDIA | 2859.50 | 26.99 [25.81, 30.29] | 0.94% | N/A† | 137.81 | 394.05 | N/A* |
| PythonNative (CPython VM) | Windows Intel iGPU | 53578.00 | 45.63 [41.24, 49.75] | 0.09% | N/A† | N/A** | N/A** | N/A* |
| Bun JSC Minimal 15 | Linux x86_64 | 2773.73 | 7.28 [7.13, 7.36] | 0.26% | 23.93 | 206.67 | 572.71 | 54.47M |
| Bun JSC Minimal 15 | Windows 11 NVIDIA | 2856.44 | 16.48 [16.27, 17.85] | 0.58% | 24.64 | 136.16 | 387.46 | N/A* |
| Bun JSC Minimal 15 | Windows Intel iGPU | 53564.68 | 23.70 [23.43, 24.09] | 0.04% | 23.65 | N/A** | N/A** | N/A* |
| Neural Baseline (Direct Server) | macOS ARM64 (M4) | 5279.45 | 0.00 [0.00, 0.00] | 0.00% | N/A‡ | 88.17 | 463.17 | N/A‡ |
| Neural Baseline (Direct Server) | Linux x86_64 | 2735.55 | 0.00 [0.00, 0.00] | 0.00% | N/A‡ | 204.41 | 558.57 | N/A‡ |
| Neural Baseline (Direct Server) | Windows 11 NVIDIA | 2773.49 | 0.00 [0.00, 0.00] | 0.00% | N/A‡ | 131.06 | 363.54 | N/A‡ |
| Neural Baseline (Direct Server) | Windows Intel iGPU | 51817.81 | 0.00 [0.00, 0.00] | 0.00% | N/A‡ | N/A** | N/A** | N/A‡ |

> **Table 1 Methodological Notes and Microarchitectural References:**  
> `*` **N/A\*** (*PMU Instruction Counters on Windows 11*): In Windows 11 user-mode, CPU PMU architectural instruction counters are restricted by the NT kernel without elevated driver tracing (kernel ETW/WPR profiling introduces unviable asynchronous latency for isolated process measurement). Win32 user-mode API exposes thread cycles via `QueryProcessCycleTime` (`realtimeapiset.h`), precluding access to `IA32_FIXED_CTR0` (`INST_RETIRED.ANY`). Under strict empirical methodology, synthetic IPC extrapolations are avoided; CPU cycles are reported directly (43.0M cycles in PicoClaw vs. 507.9M cycles in OpenClaw Full, an 11.82x ratio). *Refs:* Microsoft Learn (`QueryProcessCycleTime`); Intel® 64 and IA-32 SDM Vol. 3B Ch. 20; Weaver, V. M. (IEEE ISPASS 2013).  
> `†` **N/A†** (*Peak RSS of PythonNative on Windows 11*): The Windows invocation via `py.exe` (PEP 397) functions as a lightweight launcher wrapper stub dispatching an independent worker child process (`python.exe`). PSAPI telemetry (`GetProcessMemoryInfo`) monitored the immediate parent wrapper PID (~4.91 MB) rather than the CPython worker child heap. Factual `N/A` is reported in lieu of the wrapper stub memory. *Refs:* Python PEP 397; Microsoft Learn (Win32 PSAPI).  
> `‡` **N/A‡** (*Direct Neural Baseline*): The neural baseline issues direct HTTP requests from the telemetry harness to the resident `llama-server` without intermediary agent runtimes ($T_{\text{orch}} \equiv 0$); no client agent process exists for RSS or instruction attribution. *Refs:* Experimental decomposition protocol $T_{\text{task}} = T_{\text{orch}} + T_{\text{neural}}$.  
> `||` **N/A for Bun on macOS**: Bun (JSC) was evaluated as a secondary JavaScript engine ablation on x86_64 nodes (Linux and Windows 11) following the freeze of the Darwin ARM64 reference campaign.  
> `**` **N/A\*\*** (*Host Package Energy on Windows Intel Graphics*): Intel HD Graphics 4600 operates on unified host memory aperture (UMA); without kernel RAPL MSR driver or discrete NVML, host package energy and EDP are not instrumented in user-mode.  
> `§` **Cross-ISA Hardware Counter Segregation:** Direct numerical comparisons of retired hardware instruction counts between Apple Silicon (ARM64 RISC) and Intel Core i5 (x86_64 CISC) are physically and microarchitecturally incommensurable due to divergent instruction set densities, macro-op fusion, and RISC micro-operation expansion. Hardware instructions are segregated by ISA (reported under respective architecture columns) and must be evaluated via relative expansion ratios (e.g. OpenClaw Full vs. PicoClaw) rather than cross-ISA raw scalar counts.  
> `¶` **Clean Physical Executions:** All consolidated datasets originate from unbroken, from-scratch executions without partial or reused trials.
