# PicoClaw vs. OpenClaw: Performance Evaluation of Go and TypeScript AI Agent Architectures on Apple Silicon M4
[![UFABC](https://img.shields.io/badge/Institution-UFABC-blue.svg)](http://www.ufabc.edu.br/)
[![Course](https://img.shields.io/badge/Course-CCM313--EEI203-darkgreen.svg)](https://propg.ufabc.edu.br/)
[![Platform](https://img.shields.io/badge/Platform-Apple%20Silicon%20M4-purple.svg)](https://www.apple.com/)
[![Statistical Rigor](https://img.shields.io/badge/Poisson%20Assertiveness-%E2%89%A5%2090.3%25%20--%2093.8%25-brightgreen.svg)](docs/03_METODOLOGIA_ESTATISTICA_POISSON.md)
[![License](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

**Author:** Rafael Paniccia Cassetta (Student ID: 21202520618)  
**Program:** Graduate Program in Information Engineering / Computer Science  
**Course:** CCM313-EEI203 — Performance Analysis of Networks and Systems (2026.3)  
**Instructor:** Federal University of ABC (UFABC)  

---

## 📌 Executive Summary / Resumo Executivo

This repository contains the complete experimental campaign, reproducible toolchain, hardware telemetry logs, Poisson statistical validation engine, and final submission artifacts comparing two contrasting AI agent architectures on the **Apple Silicon M4** platform (10-core CPU, 10-core Metal GPU, 24 GB Unified Memory):
1. **PicoClaw v0.3.1 (Sipeed):** Native, statically compiled Go 1.23.2 binary leveraging concurrent goroutines and lightweight tri-color mark-sweep garbage collection.
2. **OpenClaw v2026.10.7:** Enterprise-grade modular TypeScript agent orchestrator executing atop the Google V8 engine (Node.js v26.12.1) with dynamic TypeBox schema validation and native SQLite state management.

Both agent orchestrators were benchmarked against an identical local neural serving layer powered by **llama.cpp (b11887 Metal GPU)** serving **Meta Llama-3.2-3B-Instruct (GGUF Q4_K_M)** under greedy decoding (`temperature = 0.0`, `seed = 42`), strictly eliminating neural stochasticity across comparative runs.

---

## 📊 Key Findings at a Glance

| Evaluated Dimension | PicoClaw (Go 1.23.2) | OpenClaw (Node.js 26.12.1) | Comparative Ratio / Advantage | Statistical Significance |
| :--- | :---: | :---: | :---: | :---: |
| **Cold-Start Launch ($T_{\text{cold}}$)** | **$9.63 \pm 0.22\text{ ms}$** | $225.55 \pm 16.06\text{ ms}$ | **$23.42\times$ faster** | $t = 30.12, \; p < 10^{-23}$ |
| **Steady-State Idle RSS** | **$14.02 \pm 0.13\text{ MB}$** | $166.10 \pm 0.50\text{ MB}$ | **$11.85\times$ less RAM** | $t = 59.44, \; p < 10^{-35}$ |
| **Peak Resident RAM (W4 10-Turn)** | **$33.83 \pm 0.34\text{ MB}$** | $448.33 \pm 3.95\text{ MB}$ | **$13.25\times$ less RAM** | $t = 61.20, \; p < 10^{-47}$ |
| **Hardware Instructions Retired (PMC)** | **$155.84\text{ M}$** | $4,650.08\text{ M}$ | **$29.84\times$ fewer instructions** | $t = 82.15, \; p < 10^{-40}$ |
| **Tool Dispatch Throughput ($R_{\text{tool}}$)** | **$326.39\text{ ops/s}$** | $64.30\text{ ops/s}$ | **$5.08\times$ higher throughput** | $z = 19.92, \; p < 10^{-15}$ |
| **Energy-Delay Product (EDP - W1)** | **$31.62\text{ J}\cdot\text{s}$** | $41.48\text{ J}\cdot\text{s}$ | **$24.4\%\text{ EDP reduction}$** | $t = 11.45, \; p < 10^{-13}$ |
| **Default Prompt Footprint (Factory CLI)** | **$4,657\text{ tokens}$** | $16,369\text{ tokens}$ | **$3.51\times$ smaller prompt** | Exceeds 4,096-tok limit |

---

## 🎯 Poisson Sampling & High Assertiveness ($\ge 90\%$ to $100\%$)

Following academic peer-review feedback, the experimental sampling was rigorously evaluated under a **Poisson Point Process model** for tool dispatch events. To guarantee a statistical assertiveness level of **$\ge 90\%$ (relative error $d \le 10\%$)** with Garwood (1936) exact $\chi^2$ confidence intervals:

* **Tier W2 (3 Tools/Run):** Evaluated over $K = 300$ tool dispatches ($n = 100$ runs), achieving **$90.33\%$ statistical assertiveness** ($\text{IC}_{90\%}: [296.03, 359.13]\text{ ops/s}$).
* **Tier W4 (10 Tools/Run):** Evaluated over $K = 1,000$ tool dispatches ($n = 100$ runs), achieving **$93.75\%$ statistical assertiveness** ($\text{IC}_{95\%}: [209.70, 237.61]\text{ ops/s}$).
* **Overdispersion Test:** Cameron & Trivedi (1990) test statistic $|z| < 1.96$, confirming pure equidispersed Poisson behavior without overdispersion.

![Poisson Assertiveness](figures/fig7_poisson_assertiveness.png)

---

## 📂 Repository Directory Structure

```text
picoclaw-vs-openclaw-benchmark/
├── README.md                                  <- Executive overview and reproduction entry point
├── docs/                                      <- Comprehensive academic documentation (100% Bilingual)
│   ├── 00_GUIA_PRATICO_INTRODUTORIO_PT.md     <- Practical introductory guide (PT)
│   ├── 00_PRACTICAL_INTRODUCTORY_GUIDE_EN.md  <- Practical introductory guide (EN)
│   ├── 01_GLOSSARIO_PT.md                     <- Detailed Technical Glossary (Portuguese)
│   ├── 02_GLOSSARY_EN.md                      <- Formal Technical Glossary (English)
│   ├── 03_METODOLOGIA_ESTATISTICA_POISSON.md  <- Poisson statistical proofs & sample sizing (PT)
│   ├── 03_POISSON_STATISTICAL_METHODOLOGY_EN.md <- Poisson statistical proofs & sample sizing (EN)
│   ├── 04_HARDWARE_TELEMETRY_TERMINAL_OUTPUTS.md <- Step-by-step terminal sessions & telemetry (PT)
│   ├── 04_HARDWARE_TELEMETRY_TERMINAL_OUTPUTS_EN.md <- Step-by-step terminal sessions & telemetry (EN)
│   ├── 05_GUIA_REPRODUCAO_PASSO_A_PASSO.md    <- One-click reproduction guide for reviewers (PT)
│   ├── 05_STEP_BY_STEP_REPRODUCTION_GUIDE_EN.md <- One-click reproduction guide for reviewers (EN)
│   ├── 06_ACADEMIC_DEFENSE_FAQ.md             <- Q&A for journal reviewer and defense committee (PT)
│   ├── 06_ACADEMIC_DEFENSE_FAQ_EN.md          <- Q&A for journal reviewer and defense committee (EN)
│   ├── 07_PRINTS_PASSO_A_PASSO.md             <- Visual terminal screenshots walkthrough (PT)
│   ├── 07_STEP_BY_STEP_SCREENSHOTS_EN.md      <- Visual terminal screenshots walkthrough (EN)
│   ├── 08_REGISTRO_DE_AJUSTES_E_DESVIOS.md    <- Formal log of 9 methodological adjustments (PT)
│   ├── 08_ADJUSTMENTS_AND_CORRECTIVE_ACTIONS_EN.md <- Formal log of 9 methodological adjustments (EN)
│   ├── 09_EQUALIZED_TEST_CONDITIONS_GUARANTEE_PT.md <- Proof of strictly equalized conditions (PT)
│   └── 09_EQUALIZED_TEST_CONDITIONS_GUARANTEE_EN.md <- Proof of strictly equalized conditions (EN)
├── screenshots/                               <- Actual terminal screens of tools on Apple Silicon M4
│   ├── print_screen_01_llama_server.png       <- llama-server Metal GPU start and health check
│   ├── print_screen_02_hyperfine.png          <- Cold-start benchmarking (23.4x PicoClaw advantage)
│   ├── print_screen_03_powermetrics.png       <- Real Apple M4 SMC power rail telemetry
│   ├── print_screen_04_live_execution.png     <- Real-time physical execution of W1-W4 workloads
│   ├── print_screen_05_poisson_engine.png     <- Poisson analytical engine & Garwood CIs
│   └── print_screen_06_caffeinate_quiescence.png <- Host OS quiescence & sleep suppression
├── campaign_run_1/                            <- Campaign 1: Baseline 480 factorial trials + SMC telemetry
├── campaign_run_2/                            <- Campaign 2: Second live physical trial run on Metal GPU
├── campaign_run_3/                            <- Campaign 3: Third live physical trial run on Metal GPU
├── campaign_run_4/                            <- Campaign 4: Fourth live physical trial run on Metal GPU
├── campaign_run_5/                            <- Campaign 5: Fifth live physical trial run on Metal GPU
├── campaign_comparison/                       <- Cross-campaign ANOVA, CV%, and reproducibility
│   ├── CAMPAIGN_COMPARISON.md                 <- Cross-campaign comparison report (Portuguese)
│   ├── CAMPAIGN_COMPARISON_EN.md              <- Cross-campaign comparison report (English)
│   └── multi_campaigns_comparison.json        <- Consolidated statistical JSON payload
├── benchmark/                                 <- Executable benchmark harnesses & orchestrators
│   ├── run_all_experiments.py                 <- 480-run factorial experiment driver
│   ├── run_live_campaign.py                   <- Live physical campaign executor
│   ├── compare_campaigns.py                   <- Cross-campaign ANOVA & CV% comparison engine
│   ├── poisson_sampling_validation.py         <- Poisson engine for >=90% assertiveness validation
│   ├── picoclaw_orch.go                       <- Go equalized orchestrator source
│   ├── picoclaw_orch                          <- Compiled native Mach-O ARM64 orchestrator
│   ├── openclaw_orch.mjs                      <- Node.js equalized orchestrator module
│   ├── generate_datasets.py                   <- Deterministic W1-W4 workload generator
│   ├── generate_charts.py                     <- Matplotlib 300-DPI publication chart renderer
│   ├── build_reports.py                       <- Word (.docx) & PDF academic report generator
│   └── build_layperson_guide.py               <- Layperson guide generator
├── data/                                      <- Raw benchmark telemetry and run metadata
│   ├── results_all.json                       <- Consolidated 480 factorial run observations
│   ├── poisson_results.json                   <- Poisson rates, Garwood CIs, and dispersion test
│   ├── powermetrics_idle.txt                  <- Raw Apple M4 SMC idle telemetry (100 ms)
│   ├── powermetrics_picoclaw.txt              <- Raw Apple M4 SMC PicoClaw telemetry (100 ms)
│   ├── powermetrics_openclaw.txt              <- Raw Apple M4 SMC OpenClaw telemetry (100 ms)
│   ├── powermetrics_parsed.json               <- Parsed power time-series (CPU, GPU, ANE)
│   ├── privileged_quiescence.log              <- Spotlight & sleep quiescence verification log
│   └── manifest_sha256.json                   <- SHA-256 cryptographic checksums of all artifacts
├── figures/                                   <- High-resolution 300-DPI publication charts
│   ├── fig1_architecture_topology.png         <- Integrated system loopback topology
│   ├── fig2_exp1_cold_start_rss.png           <- Cold-start latency and RSS scaling
│   ├── fig3_exp2_latency_overhead.png         <- Isolated orchestration latency & overhead ratio
│   ├── fig4_exp3_energy_edp.png               <- Real powermetrics trace, energy & EDP
│   ├── fig5_exp4_tools_and_bloat.png          <- Tool dispatch throughput & prompt bloat
│   ├── fig6_pmc_hardware_counters.png         <- Apple M4 instructions, cycles & phys footprint
│   ├── fig7_poisson_assertiveness.png         <- Poisson assertiveness convergence & Garwood CIs
│   └── fig8_three_campaigns_reproducibility.png <- Multi-campaign reproducibility (CV < 2.5%)
└── reports/                                   <- Formal submitted reports (.docx and .pdf)
    ├── CCM313-EEI203-system-testing-Rafael-Paniccia-Cassetta.docx
    ├── CCM313-EEI203-system-testing-Rafael-Paniccia-Cassetta.pdf
    ├── CCM313-EEI203-project-workplan-Rafael-Paniccia-Cassetta-revised.docx
    ├── CCM313-EEI203-project-workplan-Rafael-Paniccia-Cassetta-revised.pdf
    ├── Guia-Explicativo-e-Defesa-Rafael-Paniccia-Cassetta.docx
    └── Guia-Explicativo-e-Defesa-Rafael-Paniccia-Cassetta.pdf
```

---

## 🚀 Quickstart: Reproducing All Results

### 1. Verify Cryptographic Integrity
```bash
python3 -c '
import json, hashlib, os
manifest = json.load(open("data/manifest_sha256.json"))
ok = sum(1 for p, m in manifest.items() if os.path.exists(p) and hashlib.sha256(open(p, "rb").read()).hexdigest() == m["sha256"])
print(f"Verified {ok}/{len(manifest)} files matching cryptographic SHA-256 signatures.")
'
```

### 2. Run the High-Assertiveness Poisson Engine
```bash
python3 benchmark/poisson_sampling_validation.py
```

### 3. Regenerate All Figures and Reports
```bash
python3 benchmark/generate_charts.py
python3 benchmark/build_reports.py
python3 benchmark/build_layperson_guide.py
```

For comprehensive instructions, see the [Step-by-Step Reproduction Guide](docs/05_GUIA_REPRODUCAO_PASSO_A_PASSO.md).

---

## 📜 Academic Integrity and AI Tools Disclosure

In accordance with UFABC academic regulations and CCM313-EEI203 course policies:
* **AI Tool Utilized:** Google Antigravity coding assistant (powered by Gemini).
* **Scope of AI Assistance:** Assisting in packaging standalone binaries, writing ctypes bindings for Darwin's `libproc.dylib`, formatting LaTeX mathematical expressions, and styling report documents.
* **Supervision & Verification:** 100% of physical hardware executions on the Apple Mac mini M4, empirical telemetry sampling, raw log validation, statistical hypothesis testing, and conclusions were independently conducted, verified, and supervised by the student **Rafael Paniccia Cassetta (RA: 21202520618)**.

---

## 📚 References

1. **Jain, R. (1991).** *The Art of Computer Systems Performance Analysis: Techniques for Experimental Design, Measurement, Simulation, and Modeling.* John Wiley & Sons.
2. **Lilja, D. J. (2000).** *Measuring Computer Performance: A Practitioner's Guide.* Cambridge University Press.
3. **Garwood, F. (1936).** *Fiducial Limits for the Poisson Distribution.* Biometrika, 28(3/4), 437–442.
4. **Cameron, A. C., & Trivedi, P. K. (1990).** *Regression-based tests for overdispersion in the Poisson model.* Journal of Econometrics, 46(3), 347–364.
5. **Sipeed. (2026).** *PicoClaw: Ultra-lightweight Edge AI Agent Framework (v0.3.1).* Mach-O ARM64 release.
6. **Steinberger, P., & OpenClaw Foundation. (2026).** *OpenClaw Autonomous Personal Assistant (v2026.10.7).* NPM package distribution.
