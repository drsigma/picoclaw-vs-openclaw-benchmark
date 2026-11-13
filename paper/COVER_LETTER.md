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

Our software, `picoclaw-vs-openclaw-benchmark`, addresses this fundamental challenge by providing both an extensible systems benchmarking harness and an active schema-pruning module:
1. **Mathematical Isolation of Orchestrator Overhead ($T_{\text{orch}}$) and Active Zero-Copy Tool-RAG Schema Pruner:** A modular framework decoupling neural inference latency from agent execution delay across four standardized workload tiers (W1–W4) and four language runtimes (Go Mach-O ARM64, Node.js V8, native Bun/JavaScriptCore, and CPython 3.12). Furthermore, the software includes an active **Zero-Copy Dynamic Tool-RAG Schema Pruner** ($54 \rightarrow \text{Top-}5$ semantically relevant tools via 384-D in-memory cosine similarity in $<0.35\text{ ms}$) that eliminates $>85\%$ of enterprise 54-tool prefill latency and energy under cold execution and outperforms static 15-tool schemas under warm KV-cache retention.
2. **Two-Stage Hardware Telemetry, XNU Counter Negative-Result Validation, and Analytical-Empirical UMA Bandwidth Estimation:** Physical instrumentation combining (i) direct power rail sampling on the Apple SMC `CPU Power` rail with GPU idle and paired baseline subtraction against `neural_baseline` with (ii) per-process microarchitectural counters from Darwin XNU (`ri_instructions`, `ri_cycles`, and `ri_billed_energy`). Crucially, our harness delivers direct physical dispatch energy ($1.252\text{ mJ/op}$ Go vs. $0.196\text{ mJ/op}$ Node Minimal in W2), establishes a formal **Negative Result for Darwin XNU `ri_billed_energy`** ($r = -0.0510, p = 0.580$, centered $\text{OLS } R^2 = -0.676$ vs. the mean, corroborating Fahad et al., 2019 on uncalibrated on-chip energy counters), validates physical CPU energy regressors (`t_exec_ms` $R^2=0.949$, `proc_instructions` $R^2=0.955$, `proc_cycles` $R^2=0.945$), isolates direct SMC `CPU Power` rail orchestrator energy share ($\Phi_{\text{energy, orch}} \in [0.01\%, 1.42\%]$ across W2/W3 in Regime B), and provides an **Analytical & Empirical Memory Bandwidth Estimation ($\text{Model Weights} \div \text{ITL}$)** yielding a global median of $97.0\text{ GB/s}$ ($80.8\%$ of the nominal $120\text{ GB/s}$ LPDDR5X bus) and a mean of $95.9\text{ GB/s}$ ($79.9\%$ in Regime A) to $106.7\text{ GB/s}$ ($88.9\%$ in Regime B; global mean $104.0\text{ GB/s}$ / $86.7\%$), respecting the practical Roofline UMA ceiling ($\approx 86\text{--}88\%$, Imamura, 2026; Benazir & Lin, 2025). Privileges are strictly isolated: agent runtimes and neural daemons execute exclusively in unprivileged user space.
3. **Rigorous Non-Parametric Statistics and Factor Analysis:** Automated computation of Energy-Delay Product ($\text{EDP} = E \times T$), Medians and Interquartile Ranges ($\text{IQR}$), two-sided Mann-Whitney $U$ tests adjusted via step-down Holm-Bonferroni, Cliff's Delta ($d$), Vargha-Delaney effect sizes ($\hat{A}_{12}$ with 95% bootstrap CIs), pairwise Spearman correlation matrices (with Holm-Bonferroni adjusted $p$-values and within-workload stratification), and Principal Component Analysis (PCA) variance decomposition.
4. **Controlled Ablation Matrix, Unified Warm-Cache Session, and Inter-Session Replication ($n=30$):** Physical evaluation across Regime A (cold prefill), Regime B (unified warm KV-cache session), and an independent Inter-Session Replication ($n=30$ per block with native Bun v1.4.4) reveals dual operational regimes: under warm KV-cache amortization (Regime B, prefix hit rate $\ge 97.6\%$), orchestrator execution latency represents only $\Phi_{\text{orch}} \in [0.37\%, 4.65\%]$ of total task duration, with Go, Python, Node.js V8, and Bun achieving intra-session parity within $-1.5\%$ to $+5.8\%$ of the neural baseline (smaller than the $\sim 3\%\text{--}10\%$ cross-session thermal/clock drift in W1, W2, and W4, while W3 vector RAG consistently favors SIMD/BLAS over scalar Go loops by $5.6\%\text{--}5.8\%$). Conversely, compiled Go (PicoClaw) achieves **$3.81\times$ faster mean cold-start invocation** ($9.74\text{ ms}$ vs. $37.15\text{ ms}$ for Node.js V8; median $3.46\times$, $9.67\text{ ms}$ vs. $33.48\text{ ms}$; and $7.29\times$ faster isomorphic worker `--version` startup at $3.04\text{ ms}$ vs. $22.15\text{ ms}$), $2.82\times$ lower physical memory footprint on global average, $3.84\times$ fewer retired instructions, and in 10-turn autonomous ReAct loops (W4) avoiding 54-tool catalog prompt bloat delivers a **$92.53\%$ lower Energy-Delay Product** ($d = -1.0$, $\hat{A}_{12} = 0.0$, $p < 10^{-5}$).

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
