# Cover Letter for Submission to SoftwareX (Elsevier)

**To:**  
The Editor-in-Chief  
*SoftwareX*, Elsevier  

**Subject:** Submission of Original Software Article:  
*"PicoClaw vs. OpenClaw: An Extensible, Multi-Platform Benchmark Suite for Autonomous AI Agent Orchestration Architectures on Apple Silicon"*

**Author:**  
Rafael Paniccia Cassetta  
Centro de Engenharia, Modelagem e Ciências Sociais Aplicadas (CECS)  
Universidade Federal do ABC (UFABC), Santo André, SP, Brazil  
Email: `rafael.paniccia@aluno.ufabc.edu.br`  

---

Dear Editor-in-Chief and Editorial Board of *SoftwareX*,

I am pleased to submit our original software manuscript titled **"PicoClaw vs. OpenClaw: An Extensible, Multi-Platform Benchmark Suite for Autonomous AI Agent Orchestration Architectures on Apple Silicon"** for consideration as an original research software article in *SoftwareX*.

### Originality and Scientific Contribution
With the rapid migration of autonomous AI agents from remote cloud endpoints to local client devices, execution runtime bottlenecks have become a defining constraint. On unified memory architectures such as Apple Silicon (UMA @ 120 GB/s), agent orchestrators compete directly with quantized neural weights (`llama.cpp`) for memory bus bandwidth and compute cycles.

Our software, `picoclaw-vs-openclaw-benchmark`, addresses this fundamental challenge by providing:
1. **Mathematical Isolation of Orchestrator Overhead ($T_{\text{orch}}$):** A modular framework decoupling neural inference latency from agent execution delay across four standardized workload tiers (W1–W4).
2. **Hardware-Level Telemetry and Security Model:** Dual physical instrumentation combining Apple SMC electrical current sampling (`powermetrics` in mW) with unprivileged Darwin XNU `libproc` performance counters (retired instructions and CPU cycles). Crucially, the software implements automatic privilege detection and graceful degradation: orchestrators and neural servers always run strictly in unprivileged user space, while root is strictly quarantined to reading physical SMC current shunts.
3. **Rigorous Non-Parametric Statistics:** Full automated computation of Energy-Delay Product ($\text{EDP} = E \times T$), exact Garwood (1936) Poisson fiducial limits, Mann-Whitney $U$ significance tests, Cliff's Delta ($d = -1.0$), and Vargha-Delaney effect sizes ($\hat{A}_{12} = 0.0$).
4. **Controlled Ablation Matrix:** Empirical quantification of the cost of 54 enterprise tools and TypeBox validation in Node.js/V8 compared to native compiled Go Mach-O binaries.

### Multi-OS Reviewer Reproducibility
Recognizing that journal reviewers operate across diverse environments (including Linux x86_64 machines without Apple Metal GPUs or superuser access), our framework incorporates a **reviewer-friendly portable simulation pipeline (`make simulate-campaign`)**. This command dispatches a self-contained mock loopback server, executes the complete factorial matrix, runs non-parametric hypothesis tests, and renders high-resolution figures in under **10 seconds**, backed by continuous integration testing on both `ubuntu-latest` and `macos-latest` GitHub Actions runners.

The complete code, datasets, telemetry logs, and documentation are available under open licenses (MIT License for software and Creative Commons CC-BY 4.0 for data) at:  
👉 `https://github.com/drsigma/picoclaw-vs-openclaw-benchmark`  
Permanent Zenodo archive DOI: `10.5281/zenodo.placeholder` (prepared for Release `v1.0.0`).

This manuscript has not been published elsewhere and is not currently under consideration by any other journal. All authors have approved the submission.

Thank you very much for your time and consideration.

Sincerely,

**Rafael Paniccia Cassetta**  
Federal University of ABC (UFABC), Brazil  
`rafael.paniccia@aluno.ufabc.edu.br`
