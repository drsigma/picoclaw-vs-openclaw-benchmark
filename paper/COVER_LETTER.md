# Manuscript Submission Cover Letter (Template)

**To:**  
The Editorial Board  

**Subject:** Submission of Original Research Software Manuscript:  
*"A Reproducible Benchmark Suite for Isolating Orchestration Overhead, Schema Prefill Scaling, and KV-Cache Dynamics in Local LLM Agents (Quad-Platform Empirical Validation: macOS, Linux, and Windows)"*

**Author:**  
Rafael Paniccia Cassetta  
Centro de Engenharia, Modelagem e Ciências Sociais Aplicadas (CECS)  
Universidade Federal do ABC (UFABC), Santo André, SP, Brazil  
Email: `rafael.paniccia@aluno.ufabc.edu.br`  

---

Dear Editorial Board,

I am pleased to submit our original software manuscript titled **"A Reproducible Benchmark Suite for Isolating Orchestration Overhead, Schema Prefill Scaling, and KV-Cache Dynamics in Local LLM Agents"** for consideration.

### Originality and Scientific Contribution
With the rapid migration of autonomous AI agents from remote cloud endpoints to local client devices, execution runtime bottlenecks have become a defining constraint. On modern computing platforms—ranging from unified memory architectures such as Apple Silicon (UMA @ 120 GB/s) to discrete GPU x86_64 nodes and integrated Intel graphics systems—agent orchestrators compete directly with quantized neural weights (`llama.cpp`) for memory bus bandwidth and compute cycles.

Our software, `picoclaw-vs-openclaw-benchmark`, addresses this challenge by providing an extensible, quad-platform systems benchmarking harness and an active schema-pruning module:
1. **Mathematical Isolation of Orchestrator Overhead ($T_{\text{orch}}$) and Active Zero-Copy Tool-RAG Schema Pruner:** A modular framework decoupling neural inference latency from agent execution delay across standardized workload tiers (W1–W5) and language runtimes (Go native, Node.js V8, native Bun/JavaScriptCore, and CPython 3.12/3.14). Empirical W2 $T_{\text{orch}}$ speedups for native Go over Node.js reach **$4.44\times$ on macOS ARM64 (Apple M4)** ($5.53\text{ ms}$ vs. $24.55\text{ ms}$), **$5.31\times$ on Linux x86_64 (Ubuntu 26.04)** ($6.68\text{ ms}$ vs. $35.53\text{ ms}$), **$3.70\times$ on Windows 11 NVIDIA** ($13.11\text{ ms}$ vs. $48.55\text{ ms}$), and **$4.91\times$ on Windows Intel Graphics** ($14.03\text{ ms}$ vs. $68.89\text{ ms}$). Furthermore, the built-in **Zero-Copy Dynamic Tool-RAG Schema Pruner** ($54 \rightarrow \text{Top-}5$, $-87.1\%$ prompt tokens) achieves W2 cold prompt-prefill speedups of **$7.28\times$ on macOS** (same-session baseline), **$5.16\times$ on Linux**, **$4.64\times$ on Windows NVIDIA**, and **$9.96\times$ on Windows Intel Graphics** (with x86_64 pruned arms normalized to each node's primary unmitigated campaign baseline).
2. **Quad-Platform Hardware Microarchitectural Telemetry and Strict Empirical Protocol:** Physical instrumentation leverages native operating system facilities across four physical nodes:
   - *Darwin ARM64:* Direct Apple SMC power rail sampling with GPU idle and Darwin XNU per-process microarchitectural counters (`libproc` / `ri_instructions` reducing instruction bloat by $12.71\times$ in PicoClaw vs. OpenClaw Full).
   - *Linux x86_64:* Intel RAPL MSR energy integration, NVIDIA NVML GPU telemetry, and hardware PMU instruction counters via `perf_event_open(2)` ($23.87\times$ instruction bloat reduction: $32.4\text{M}$ vs. $772.1\text{M}$).
   - *Windows 11 x86_64 (NVIDIA):* High-resolution Win32 cycle tracking via `QueryProcessCycleTime` ($11.54\times$ cycle ratio: $45.8\text{M}$ cycles in PicoClaw vs. $528.1\text{M}$ cycles in OpenClaw Full), PSAPI process memory monitoring, and NVML DLL telemetry.
   - *Windows 10/11 x86_64 (Intel Graphics):* Win32 PSAPI process telemetry and `QueryProcessCycleTime` ($16.47\times$ cycle ratio: $87.8\text{M}$ vs. $1446.1\text{M}$ cycles) on shared host memory aperture (UMA); dynamic host package energy and discrete VRAM documented transparently as `N/A**` due to unprivileged user-mode execution.
3. **Non-Parametric Statistics and Moving Block Bootstrap CIs:** Automated computation of Energy-Delay Product ($\text{EDP} = E \times T$), Medians and Interquartile Ranges ($\text{IQR}$), two-sided Mann-Whitney $U$ tests adjusted via step-down Holm-Bonferroni, Cliff's Delta ($d$), Vargha-Delaney effect sizes ($\hat{A}_{12}$), Two One-Sided Equivalence Tests (TOST), and Moving Block Bootstrap confidence intervals preserving short-range serial dependence structure.
4. **Clean-Room Runs and Provenance:** 100% of consolidated datasets originate from clean from-scratch runs with cryptographic SHA-256 verification.

### Multi-OS Reproducibility
Recognizing that reviewers operate across diverse environments (including Linux x86_64 and Windows machines without Apple Metal GPUs or superuser access), our framework incorporates a **portable dry-run pipeline (`make dry-run` / `pytest`)**, automated shell scripts (`reproduce_linux_gold.sh`), PowerShell scripts (`windows_gold.ps1`), and master reproduction scripts (`scripts/reproduce_quad_platform_analysis.py`).

The complete code, datasets, telemetry logs, and documentation are available under open licenses (MIT License for software and Creative Commons CC-BY 4.0 for data) at:  
`https://github.com/drsigma/picoclaw-vs-openclaw-benchmark`  
Permanent Zenodo archive DOI: `10.5281/zenodo.14187265`.

This manuscript has not been published elsewhere and is not currently under consideration by any other venue. All authors have approved the submission.

Thank you very much for your time and consideration.

Sincerely,

**Rafael Paniccia Cassetta**  
Federal University of ABC (UFABC), Brazil  
`rafael.paniccia@aluno.ufabc.edu.br`
