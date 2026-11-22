# Research Highlights (SoftwareX Editorial Submission)

* Quad-platform benchmark and Tool-RAG pruner for local LLM agents across macOS ARM64, Linux x86_64, Windows 11 NVIDIA, and Windows Intel iGPU.
* Zero-Copy Tool-RAG (54->Top-5) cuts cold prefill latency by up to 9.96x across four distinct physical hardware environments.
* Direct hardware telemetry (Apple SMC, Intel RAPL/NVML, Win32 CycleTime, PSAPI) isolates client orchestration delay.
* Native Go yields 4.44x (macOS), 5.40x (Linux), 3.70x (Windows NVIDIA), and 4.91x (Windows Intel) orchestration speedup over Node.js.
* Zero-Mock forensic compliance: moving-block bootstrap CIs, TOST equivalence tests, clean-from-scratch runs, and empirical instruction/cycle telemetry.
