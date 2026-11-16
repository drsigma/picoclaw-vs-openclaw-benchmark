# Research Highlights (SoftwareX Editorial Submission)

* Tri-platform benchmark and Tool-RAG pruner for local LLM agents across macOS ARM64, Linux x86_64, and Windows 11.
* Zero-Copy Tool-RAG (54->Top-5) cuts cold prefill latency/energy by >85% across all 3 operating systems.
* Direct hardware telemetry (Apple SMC, Intel RAPL/NVML, Win32 CycleTime) isolates client orchestration delay.
* Native Go yields 3.61x (macOS), 5.40x (Linux), and 4.18x (Windows 11) orchestration speedup over Node.js.
* Zero-Mock forensic compliance: median bootstrap CIs, clean-from-scratch runs, and empirical instruction/cycle telemetry.
