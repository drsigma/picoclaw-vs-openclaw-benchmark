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
2. **Two-Stage Hardware Telemetry and UMA Energy/Bandwidth Deconvolution:** Physical instrumentation combining (i) package and rail power sampling via Apple SMC (`powermetrics` at 50 ms resolution) with (ii) per-process microarchitectural counters from Darwin XNU (`ri_instructions`, `ri_cycles`, and `ri_billed_energy`). Crucially, our harness delivers empirical calibration of kernel billing units ($\hat{\kappa}_{\text{M4}} = 0.0573\text{ mJ / XNU unit}$, $R^2 = 0.0538$), deconvolving client orchestrator energy ($\Phi_{\text{energy, orch}} \in [1.46\%, 2.96\%]$ in W2/W3 under Regime B for native Go and Node.js) and measuring effective LPDDR5X UMA bandwidth ($173.03\text{ GB/s}$ during Metal GPU decoding; up to $2.04\text{ GB/s}$ during host vector RAG). Privileges are strictly isolated: agent runtimes and neural daemons execute exclusively in unprivileged user space.
3. **Rigorous Non-Parametric Statistics and Factor Analysis:** Automated computation of Energy-Delay Product ($\text{EDP} = E \times T$), Medians and Interquartile Ranges ($\text{IQR}$), two-sided Mann-Whitney $U$ tests adjusted via step-down Holm-Bonferroni, Cliff's Delta ($d$), Vargha-Delaney effect sizes ($\hat{A}_{12}$ with 95% bootstrap CIs), pairwise Spearman correlation matrices, and Principal Component Analysis (PCA) variance decomposition.
4. **Controlled Ablation Matrix and Empirical Findings:** Physical evaluation across 1,320 trials ($n=30$ per condition across cold-prefill Regime A and warm-cache Regime B) reveals dual operational regimes: under warm KV-cache amortization (Regime B, prefix hit rate $\ge 97.6\%$), orchestrator execution latency represents only $\Phi_{\text{orch}} \in [0.37\%, 4.65\%]$ of total task duration, with Go, Python, and Node.js Minimal achieving runtime parity within $-1.51\%$ to $+5.83\%$ of the neural baseline, while amortized KV-cache prefix retention delivers a **$21.6\times$ latency reduction** for the 54-tool catalog. Conversely, under cold prefill (Regime A), compiled Go (PicoClaw) achieves $23.4\times$ faster cold-start invocation ($9.63\text{ ms}$ vs. $225.55\text{ ms}$ for Node.js V8), $2.82\times$ lower physical memory footprint on global average, $3.84\times$ fewer retired instructions, and in 10-turn autonomous ReAct loops (W4) avoiding 54-tool catalog prompt bloat delivers a **$92.53\%$ lower Energy-Delay Product** ($d = -1.0$, $\hat{A}_{12} = 0.0$, $p < 10^{-5}$).

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
