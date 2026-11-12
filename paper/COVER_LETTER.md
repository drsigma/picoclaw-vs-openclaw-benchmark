# Cover Letter for Submission to SoftwareX (Elsevier)

**To:**  
The Editor-in-Chief  
*SoftwareX*, Elsevier  

**Subject:** Submission of Original Software Article:  
*"A Reproducible Benchmark Suite for Isolating Orchestration Overhead and Schema Prefill Costs in Local LLM Agents on Apple Silicon"*

**Author:**  
Rafael Paniccia Cassetta  
Centro de Engenharia, Modelagem e Ciências Sociais Aplicadas (CECS)  
Universidade Federal do ABC (UFABC), Santo André, SP, Brazil  
Email: `rafael.paniccia@aluno.ufabc.edu.br`  

---

Dear Editor-in-Chief and Editorial Board of *SoftwareX*,

I am pleased to submit our original software manuscript titled **"A Reproducible Benchmark Suite for Isolating Orchestration Overhead and Schema Prefill Costs in Local LLM Agents on Apple Silicon"** for consideration as an original research software article in *SoftwareX*.

### Originality and Scientific Contribution
With the rapid migration of autonomous AI agents from remote cloud endpoints to local client devices, execution runtime bottlenecks have become a defining constraint. On unified memory architectures such as Apple Silicon (UMA @ 120 GB/s), agent orchestrators compete directly with quantized neural weights (`llama.cpp`) for memory bus bandwidth and compute cycles.

Our software, `picoclaw-vs-openclaw-benchmark`, addresses this fundamental challenge by providing:
1. **Mathematical Isolation of Orchestrator Overhead ($T_{\text{orch}}$):** A modular framework decoupling neural inference latency from agent execution delay across four standardized workload tiers (W1–W4).
2. **Two-Layer Hardware Telemetry and Privilege Model:** Dual-layer physical instrumentation combining (i) system-wide package electrical power sampling via Apple SMC (`powermetrics` at 50 ms resolution, numerically integrated via the composite trapezoidal rule) with (ii) per-process microarchitectural attribution (`ri_instructions`, `ri_cycles`, `ri_billed_energy`, and `ri_lifetime_max_phys_footprint`) polled from the Darwin XNU kernel via `libproc` (`proc_pid_rusage` with `RUSAGE_INFO_V4`). Crucially, privilege isolation is strictly enforced: all agent runtimes, orchestrator child processes, and the `llama-server` daemon execute exclusively in unprivileged user space, with graceful non-root degradation marking electrical fields as `N/A` without synthetic proxies.
3. **Rigorous Non-Parametric Statistics and Factor Analysis:** Automated computation of Energy-Delay Product ($\text{EDP} = E \times T$), Medians and Interquartile Ranges ($\text{IQR}$), two-sided Mann-Whitney $U$ tests adjusted via step-down Holm-Bonferroni, Cliff's Delta ($d$), Vargha-Delaney effect sizes ($\hat{A}_{12}$ with 95% bootstrap CIs), pairwise Spearman correlation matrices, and Principal Component Analysis (PCA) variance decomposition.
4. **Controlled Ablation Matrix and Empirical Findings:** Physical evaluation across 1,320 trials ($n=30$ per condition across cold-prefill Regime A and warm-cache Regime B) demonstrates that compiled Go (PicoClaw) achieves $23.4\times$ faster cold-start invocation ($9.63\text{ ms}$ vs. $225.55\text{ ms}$ for Node.js V8), $2.82\times$ lower physical memory footprint on global average, $3.84\times$ fewer retired instructions, and $4.72\times$ fewer CPU cycles. In 10-turn autonomous ReAct loops (W4) under Regime A, avoiding 54-tool catalog prompt bloat delivers a **$92.53\%$ lower Energy-Delay Product** ($d = -1.0$, $\hat{A}_{12} = 0.0$, $p < 10^{-5}$). In Regime B with amortized KV-cache prefix retention, block isolation delivers a **$21.6\times$ latency reduction** for the 54-tool catalog, revealing that orchestrator overhead ($\Phi_{\text{orch}} \in [0.37\%, 4.65\%]$) becomes directly measurable in I/O and vector-intensive workloads.

### Multi-OS Reviewer Reproducibility
Recognizing that journal reviewers operate across diverse environments (including Linux x86_64 machines without Apple Metal GPUs or superuser access), our framework incorporates a **reviewer-friendly portable dry-run pipeline (`make dry-run`)**. This command dispatches a self-contained loopback mock server, executes the complete factorial matrix, runs non-parametric hypothesis tests, and renders high-resolution publication figures in under **5 seconds**, backed by continuous integration testing on both `ubuntu-latest` and `macos-latest` GitHub Actions runners.

The complete code, datasets, telemetry logs, and documentation are available under open licenses (MIT License for software and Creative Commons CC-BY 4.0 for data) at:  
👉 `https://github.com/drsigma/picoclaw-vs-openclaw-benchmark`  
Permanent Zenodo archive DOI: `10.5281/zenodo.PENDING_RELEASE` (prepared for Release `v1.0.0`).

This manuscript has not been published elsewhere and is not currently under consideration by any other journal. All authors have approved the submission.

Thank you very much for your time and consideration.

Sincerely,

**Rafael Paniccia Cassetta**  
Federal University of ABC (UFABC), Brazil  
`rafael.paniccia@aluno.ufabc.edu.br`
