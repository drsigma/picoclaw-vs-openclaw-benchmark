# Table 1: Tri-Platform Master Systems & Microarchitectural Conformance (W2 Tool Chain)

| Architecture & Runtime | Platform OS | $T_{\text{task}}$ Median (ms) | $T_{\text{orch}}$ Median (ms) [95% CI] | $\Phi_{\text{orch}}$ (%) | Peak RSS (MB) | Net Energy (J) | EDP ($J \cdot s$) | Instructions (M) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| PicoClaw (Native Go) | macOS ARM64 (M4) | 5265.14 | 7.11 [6.70, 7.35] | 0.14% | 5.03 | 83.88 | 442.18 | 62.56M |
| PicoClaw (Native Go) | Linux x86_64 | 2725.00 | 6.66 [6.05, 7.29] | 0.24% | 9.70 | 204.61 | 555.93 | 32.65M |
| PicoClaw (Native Go) | Windows 11 x86_64 | 2746.68 | 10.94 [10.72, 11.11] | 0.40% | 10.15 | 128.17 | 351.97 | N/A* |
| OpenClaw (Node.js Minimal 15) | macOS ARM64 (M4) | 5269.28 | 21.69 [21.48, 21.78] | 0.41% | 37.62 | 84.69 | 445.75 | 789.34M |
| OpenClaw (Node.js Minimal 15) | Linux x86_64 | 2760.46 | 31.45 [31.04, 32.14] | 1.14% | 86.42 | 203.81 | 560.20 | 768.09M |
| OpenClaw (Node.js Minimal 15) | Windows 11 x86_64 | 2767.66 | 38.80 [38.51, 39.23] | 1.40% | 72.82 | 130.25 | 360.87 | N/A* |
| OpenClaw (Node.js Full 54) | macOS ARM64 (M4) | 18335.53 | 25.68 [25.38, 25.78] | 0.14% | 37.83 | 291.28 | 5342.60 | 791.35M |
| OpenClaw (Node.js Full 54) | Linux x86_64 | 7891.12 | 35.99 [35.60, 37.42] | 0.46% | 86.67 | 553.76 | 4364.61 | 771.51M |
| OpenClaw (Node.js Full 54) | Windows 11 x86_64 | 7663.76 | 45.70 [45.49, 46.20] | 0.59% | 72.82 | 461.66 | 3529.62 | N/A* |
| PythonNative (CPython VM) | macOS ARM64 (M4) | 5263.19 | 11.00 [10.76, 11.32] | 0.21% | 24.00 | 84.48 | 444.58 | 651.89M |
| PythonNative (CPython VM) | Linux x86_64 | 2747.65 | 17.13 [16.87, 18.23] | 0.62% | 40.15 | 205.49 | 567.20 | 2544.43M |
| PythonNative (CPython VM) | Windows 11 x86_64 | 2750.00 | 34.49 [28.54, 36.30] | 1.26% | N/A† | 130.79 | 361.76 | N/A* |
| Bun JSC Minimal 15 | Linux x86_64 | 2773.73 | 7.28 [7.13, 7.36] | 0.26% | 23.93 | 206.67 | 572.71 | 54.47M |
| Bun JSC Minimal 15 | Windows 11 x86_64 | 2745.86 | 15.16 [15.01, 15.67] | 0.56% | 24.62 | 131.48 | 361.91 | N/A* |
| Neural Baseline (Direct Server) | macOS ARM64 (M4) | 5261.41 | 0.00 [0.00, 0.00] | 0.00% | N/A‡ | 83.69 | 439.82 | N/A‡ |
| Neural Baseline (Direct Server) | Linux x86_64 | 2735.55 | 0.00 [0.00, 0.00] | 0.00% | N/A‡ | 204.41 | 558.57 | N/A‡ |
| Neural Baseline (Direct Server) | Windows 11 x86_64 | 2733.74 | 0.00 [0.00, 0.00] | 0.00% | N/A‡ | 126.34 | 345.64 | N/A‡ |

> **Table 1 Methodological Notes and Microarchitectural References:**  
> `*` **N/A\*** (*PMU Instruction Counters on Windows 11*): In Windows 11 user-mode, CPU PMU architectural instruction counters are restricted by the NT kernel without elevated driver tracing (kernel ETW/WPR profiling introduces unviable asynchronous latency for isolated process measurement). Win32 user-mode API exposes thread cycles via `QueryProcessCycleTime` (`realtimeapiset.h`), precluding access to `IA32_FIXED_CTR0` (`INST_RETIRED.ANY`). Under strict empirical methodology, synthetic IPC extrapolations are avoided; CPU cycles are reported directly (43.0M cycles in PicoClaw vs. 507.9M cycles in OpenClaw Full, an 11.82x ratio). *Refs:* Microsoft Learn (`QueryProcessCycleTime`); Intel® 64 and IA-32 SDM Vol. 3B Ch. 20; Weaver, V. M. (IEEE ISPASS 2013).  
> `†` **N/A†** (*Peak RSS of PythonNative on Windows 11*): The Windows invocation via `py.exe` (PEP 397) functions as a lightweight launcher wrapper stub dispatching an independent worker child process (`python.exe`). PSAPI telemetry (`GetProcessMemoryInfo`) monitored the immediate parent wrapper PID (~4.91 MB) rather than the CPython worker child heap. Factual `N/A` is reported in lieu of the wrapper stub memory. *Refs:* Python PEP 397; Microsoft Learn (Win32 PSAPI).  
> `‡` **N/A‡** (*Direct Neural Baseline*): The neural baseline issues direct HTTP requests from the telemetry harness to the resident `llama-server` without intermediary agent runtimes ($T_{\text{orch}} \equiv 0$); no client agent process exists for RSS or instruction attribution. *Refs:* Experimental decomposition protocol $T_{\text{task}} = T_{\text{orch}} + T_{\text{neural}}$.  
> `||` **N/A for Bun on macOS**: Bun (JSC) was evaluated as a secondary JavaScript engine ablation on x86_64 nodes (Linux and Windows 11) following the freeze of the Darwin ARM64 reference campaign.  
> `§` **Clean Physical Executions:** All consolidated datasets originate from unbroken, from-scratch executions without partial or reused trials.
