# Research Highlights

* Quad-platform benchmark and Tool-RAG pruner for local LLM agents across macOS ARM64, Linux x86_64, Windows 11 NVIDIA, and Windows Intel iGPU.
* Zero-Copy Tool-RAG (54->Top-5, -87.1% prompt tokens) achieves W2 cold prefill speedups of 7.28x (macOS), 5.16x (Linux), 4.64x (Windows NVIDIA), and 9.96x (Windows Intel iGPU).
* Direct hardware telemetry (Apple SMC, Intel RAPL/NVML, Win32 QueryProcessCycleTime, PSAPI) isolates client orchestration delay across four physical nodes.
* Native Go yields 4.44x (macOS), 5.31x (Linux), 3.70x (Windows NVIDIA), and 4.91x (Windows Intel iGPU) orchestration speedup over Node.js in W2.
* Empirical reproducibility protocol: Moving Block Bootstrap CIs, dual-session TOST contrast tests, clean from-scratch runs, and segregated PMU instruction/cycle telemetry.
