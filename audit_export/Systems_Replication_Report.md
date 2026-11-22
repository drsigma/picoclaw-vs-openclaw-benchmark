# QUAD-PLATFORM MICROARCHITECTURAL SYSTEMS REPLICATION REPORT
## Empirical Systems Evaluation: macOS ARM64 (Apple M4) vs. Linux x86_64 vs. Windows 11 x86_64 (NVIDIA) vs. Windows 10/11 x86_64 (Intel Graphics)

**Document Classification:** Systems Replication Report  
**Date of Consolidation:** 2026-11-22  
**Repository Branch:** `main`  
**Evaluation Scope:** Empirical measurement and quad-platform consolidation across 4 distinct physical hardware/OS profiles (35 raw JSONL datasets, 190 experimental cells).  

---

## 1. EXECUTIVE SUMMARY & CONSOLIDATED METRICS

This report documents the physical execution, microarchitectural instrumentation, and statistical consolidation of the **PicoClaw vs. OpenClaw** benchmark suite across **four distinct physical hardware platforms**:
1. **Platform 1 (Reference Architecture):** Apple Silicon Mac Mini M4 (Darwin 26.6.2, ARM64, 10-core SoC [4 Performance + 6 Efficiency], 24 GB Unified LPDDR5X Memory at 120 GB/s on-die bandwidth, Metal 3, Apple SMC `powermetrics` telemetry).
2. **Platform 2:** Dell G15 5520 under Ubuntu 26.04 LTS (Kernel Linux 7.0.0-43-generic x86_64, Intel Core i5-12500H [16 logical threads], 30.5 GiB DDR5-4800, discrete NVIDIA GeForce RTX 3050 Laptop GPU 4 GB VRAM, Intel RAPL MSR + NVIDIA NVML + `perf_event_open`).
3. **Platform 3:** Dell G15 5520 under Microsoft Windows 11 64-bit (Build 26200 x86_64, Intel Core i5-12500H [16 logical threads], 31.7 GiB DDR5-4800, discrete NVIDIA GeForce RTX 3050 Laptop GPU 4 GB VRAM, Intel MSR RAPL + NVML DLL + Win32 PSAPI + WDDM).
4. **Platform 4:** MSI Z97 XPOWER AC under Microsoft Windows 10 Pro 64-bit (Build 19045 x86_64, Intel Core i7-4790K @ 4.00 GHz [4 cores / 8 threads], 15.88 GiB Shared DDR3-1600 System RAM, integrated Intel HD Graphics 4600 iGPU UMA, Win32 PSAPI process telemetry in unprivileged user-mode).

> **Methodological Note on Offload Regimes and Regime B Commensurability (Dell G15 Linux/Windows & Intel iGPU):**  
> Neural inference on the Dell G15 nodes (Linux and Windows 11) operated under a hybrid offload regime (`-ngl 16`, allocating approximately 3.0 GiB within the 4 GB GDDR6 VRAM ceiling and retaining remaining layers in host DDR5 memory), inducing continuous PCIe 4.0 host-to-GPU streaming (~5.2 GB/s). On the Intel HD Graphics 4600 node, inference executed over a shared DDR3 host memory aperture (UMA). Consequently, absolute warm-cache (Regime B) latency gains on the x86_64 nodes are constrained by PCIe/RAM bandwidth saturation and are not directly commensurable with the Apple M4 unified memory architecture.

> **Authorship and Execution Node Declaration:** Git author `drsgima` (author of the Windows testbed commits) operated the dedicated Windows physical testbed nodes.

### Key Empirical Findings (Workload W2 -- Standard 15-Tool Chain):
- **Client Middleware Dispatch Latency ($T_{\text{orch}}$):**
  * **macOS ARM64 (M4):** PicoClaw Go achieved a median latency of **5.53 ms** vs. OpenClaw Full at **24.55 ms** (**4.44x speedup**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
  * **Linux x86_64:** PicoClaw Go achieved a median latency of **6.68 ms** vs. OpenClaw Full at **35.53 ms** (**5.31x speedup**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
  * **Windows 11 NVIDIA:** PicoClaw Go achieved a median latency of **13.11 ms** vs. OpenClaw Full at **48.55 ms** (**3.70x speedup**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
  * **Windows Intel iGPU:** PicoClaw Go achieved a median latency of **14.03 ms** vs. OpenClaw Full at **68.89 ms** (**4.91x speedup**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
- **Resident Physical Memory Footprint (Peak RSS):**
  * **macOS ARM64 (M4):** PicoClaw Go stabilized at **5.09 MB** vs. OpenClaw Full at **37.71 MB** (**7.41x memory reduction**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
  * **Linux x86_64:** PicoClaw Go stabilized at **9.69 MB** vs. OpenClaw Full at **86.64 MB** (**8.94x memory reduction**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
  * **Windows 11 NVIDIA:** PicoClaw Go stabilized at **10.20 MB** vs. OpenClaw Full at **72.93 MB** (**7.15x memory reduction**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
  * **Windows Intel iGPU:** PicoClaw Go stabilized at **8.19 MB** vs. OpenClaw Full at **54.76 MB** (**6.69x memory reduction**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
- **Instruction Bloat and Hardware PMC / CPU Cycle Telemetry:**
  * **macOS ARM64 (Apple PMU):** OpenClaw Full executed **791.7M instructions**, compared to **62.3M** in PicoClaw (**12.71x ratio**).
  * **Linux x86_64 (`perf_event_open`):** OpenClaw Full executed **772.1M instructions**, compared to **32.4M** in PicoClaw (**23.87x ratio**).
  * **Windows 11 NVIDIA (`QueryProcessCycleTime`):** Hardware instruction counters are restricted in user-mode (`N/A*`); empirical CPU cycles confirm **528.1M cycles** in OpenClaw Full vs. **45.8M** in PicoClaw (**11.54x cycle ratio**).
  * **Windows Intel iGPU (`QueryProcessCycleTime`):** Hardware instruction counters are restricted in user-mode (`N/A*`); empirical CPU cycles confirm **1446.1M cycles** in OpenClaw Full vs. **87.8M** in PicoClaw (**16.47x cycle ratio**).

---

## 2. HARDWARE THROTTLING & IDLE POWER DECOMPOSITION

### 2.1. NVML Register Inspection and Per-Trial Thermal/Power Throttling Deltas (M8)
Detailed per-trial inspection of raw JSONL hardware telemetry records (exported in `audit_export/anomaly_and_cache_diagnostics.csv`) establishes exact intra-trial throttling behavior without synthetic proxies:
- **Linux x86_64 CPU Package Intra-Trial Deltas (`cpu_pkg_throttle_events`):** In `scripts/run_linux_x86_64_master_campaign.py`, `cpu_pkg_throttle_events` records the genuine **intra-trial delta** (`end - start` summed across 16 logical threads from Linux sysfs `package_throttle_count`). Non-zero intra-trial increments occurred in **884/900 (98.2%)** Regime A trials (max single-trial delta **120,948 events**, **445** consecutive-trial increases, CPU package peak **100.0°C**) and **768/900 (85.3%)** Regime B trials (max delta **14,576**, CPU peak **95.0°C**). This documents active Intel Alder Lake mobile PL1/PL2 thermal-power throttling under `-ngl 16` AVX2 hybrid CPU+GPU offload, explaining Linux's elevated positive lag-1 autocorrelation ($r_1$) addressed via $r_1$-corrected Mann-Whitney variance in Table 2. Meanwhile, the discrete NVIDIA RTX 3050 GPU on Linux recorded **0 thermal-throttle events** and **0 SW power-cap events** (`nvml_throttle_reasons_bitmask = 0x0`, GPU peak **71.0°C**).
- **Windows 11 NVIDIA Discrete GPU & CPU Telemetry:** Across all **1,800** measured Regime A & B trials on Windows 11 NVIDIA, NVML hardware registers recorded **0 GPU thermal-throttle events** (`0x20`/`0x40`) and **0 GPU SW power-cap events** (`0x04`; GPU peak **74.0°C**, CPU peak **78.0°C**). The only non-zero NVML bitmask observed at trial completion was `0x01` (`nvmlClocksThrottleReasonGpuIdle`, **902/1800** trials). Windows user-mode telemetry does not expose Linux sysfs `package_throttle_count` (`cpu_pkg_throttle_events = 0`).
- **Zero Discrete GPU Thermal Slowdown:** Across all Linux and Windows discrete-GPU trials combined, `gpu_thermal_throttle_active_end` recorded **0 thermal throttling events** and `gpu_sw_power_cap` recorded **0 power-cap events**.

### 2.2. Explicit Idle Power ($P_{\text{idle}}$) Telemetry and Duration Integration
Idle power baselines were empirically characterized during dedicated quiescence intervals prior to benchmark execution:
- **macOS ARM64 (Apple M4):** $P_{\text{idle}} = 1.20\text{ W}$ (Apple SMC SoC Package, quiescent range 1.00 W--1.46 W).
- **Linux x86_64 (Ubuntu 26.04):**
  * Session 1: $P_{\text{idle}} = 19.71\text{ W}$ (Intel CPU Package RAPL: 14.74 W, discrete NVIDIA GPU NVML: 4.98 W).
  * Session 2: $P_{\text{idle}} = 20.08\text{ W}$ (Intel CPU Package RAPL: 15.10 W, discrete NVIDIA GPU NVML: 4.98 W).
- **Windows 11 x86_64 (NVIDIA):**
  * Session 1: $P_{\text{idle}} = 24.13\text{ W}$ (Intel CPU Package RAPL MSR: 15.20 W, discrete NVIDIA GPU NVML: 8.93 W).
  * Session 2: $P_{\text{idle}} = 21.96\text{ W}$ (Intel CPU Package RAPL MSR: 15.20 W, discrete NVIDIA GPU NVML: 6.76 W).
- **Windows 10/11 x86_64 (Intel Graphics):**
  * Sessions 1 & 2: $P_{\text{idle}} = 28.50\text{ W}$ (Intel Core i7-4790K host package baseline). Dynamic host package energy is marked `N/A**` due to unprivileged user-mode execution without a kernel MSR RAPL driver.

> **Explanation of Apparent $P_{\text{idle}}$ Duration Scaling in Linux:**
> The telemetry harness computes net dynamic energy by subtracting $P_{\text{idle}} \times \text{trial\_wall\_s}$ from gross energy across the complete trial lifecycle (including subprocess initialization, loopback socket binding, and process teardown). In short-duration workloads (W1--W2), $\text{trial\_wall\_s} > T_{\text{task}}$ due to fixed subprocess overhead. Dividing $(E_{\text{total}} - E_{\text{net}})$ by $T_{\text{task}}$ yields an apparent variation from ~24.9 W (W1) to ~20.1 W (W4), which is a lifecycle duration-ratio artifact rather than sensor drift.

---

## 3. STATISTICAL SERIAL DEPENDENCE & DRIFT ANALYSIS

Following established systems benchmarking methodology (Kalibera & Jones 2013; Hoefler & Belli 2015; Maricq et al. 2018; Künsch 1989), serial dependence and temporal drift were evaluated across all experimental cells:

### 3.1. Autocorrelation ($r_1$) Across Both Regimes, $r_1$-Adjusted Mann-Whitney $U$, and Moving Block Bootstrap (M4)
- **Presence of Serial Dependence in Both Regimes:** Applying the white-noise 95% boundary at $n=30$ ($|r_1| > 2/\sqrt{30} \approx 0.365$), statistically detectable lag-1 autocorrelation occurs in **both** execution regimes: **20/95 (21.1%)** cells in **Regime A (Cold Prefill)** and **27/95 (28.4%)** cells in **Regime B (Warm Cache)** (**47/190**, 24.7% overall).
  * **Regime A (Cold Prefill) $r_1$ ranges:** macOS ARM64 $r_1 \in [-0.310, +0.433]$; Linux x86_64 $r_1 \in [-0.340, +0.778]$; Windows 11 NVIDIA $r_1 \in [-0.313, +0.219]$; Windows Intel iGPU $r_1 \in [-0.463, +0.193]$.
  * **Regime B (Warm Cache) $r_1$ ranges:** macOS ARM64 $r_1 \in [-0.895, +0.434]$; Linux x86_64 $r_1 \in [-0.430, +0.685]$; Windows 11 NVIDIA $r_1 \in [-0.386, +0.450]$; Windows Intel iGPU $r_1 \in [-0.284, +0.387]$.
  * For every cell exceeding $|r_1| > 2/\sqrt{n}$, the effective sample size $n_{\text{eff}} = \min(n, n(1 - r_1)/(1 + r_1))$ is computed and 95% confidence intervals are obtained via **Moving Block Bootstrap (MBB, block size $b=3$; Künsch 1989)**.
- **Table 2 $r_1$-Adjusted Mann-Whitney $U$ Variance Correction:** For pairwise comparisons in Table 2 (excluding confounded W5 `python_native` per M1), cells with positive autocorrelation ($r_1 > 0$) inflate the asymptotic variance of $U$ using $n_{\text{eff}} = n(1-r_1)/(1+r_1)$ (retaining $n_{\text{eff}} = n$ conservatively when $r_1 \le 0$). Across **146 pairwise contrasts**, **99** are significant under standard Holm-Bonferroni and **91** remain significant under $r_1$-corrected Holm-Bonferroni; **8 contrast(s)** lose statistical significance under $r_1$ correction (flagged `(NS*)` in Table 2, all on Linux x86_64 where active CPU thermal/PL throttling induced positive serial correlation).

### 3.2. Linear Regression Drift Test with Holm-Bonferroni Family-Wise Error Control (M7)
Ordinary least-squares regression of task latency against repetition index ($1 \dots 30$) was evaluated across all experimental cells with Holm-Bonferroni FWER adjustment (Holm 1979):
- Across all **190 experimental cells**, **188/190 (98.9%)** exhibited no statistically significant temporal drift ($p_{\text{adj}} \ge 0.05$); **2/190** reached Holm-Bonferroni significance: Windows 11 Regime B (Warm Cache) `neural_baseline` W1 (+3.611 ms/rep, 0.174%/rep, $p_{\text{adj}}=0.04731$); macOS (M4) Regime A (Cold Prefill) `openclaw_full` W4 (+13.012 ms/rep, 0.007%/rep, $p_{\text{adj}}=4.4e-05$).
- **Worst-Case Slope Magnitudes (%/rep):** Across all **valid (non-segregated)** cells, the largest observed absolute slope magnitude was **0.599%/rep** (`Windows Intel iGPU`, `Regime B (Warm Cache)`, `neural_baseline`, `W5`, $p_{\text{adj}} = 1$, non-significant). Including the segregated W5 `python_native` arm (excluded per M1), the overall maximum raw slope was **1.376%/rep** in `Windows 11` `Regime B (Warm Cache)` `python_native` `W5` ($p_{\text{adj}} = 1$).

---

## 4. CONSOLIDATED EMPIRICAL TABLES SUMMARY

### 4.1. Table 5: Tool-RAG Schema Pruning Analysis (M6)
- **Token Reduction:** Dynamic Tool-RAG pruning reduces active prompt tokens from 7,091 (static 54-tool catalog) to **917 tokens** (retrieved Top-5 schema), a **$-87.1\%$ token reduction**.
- **Regime A (Cold Prefill) Speedups vs. 54-Tool Full (`OpenClaw Tool-RAG`):** **7.28x** on macOS M4, **5.16x** on Linux x86_64, **4.64x** on Windows 11 NVIDIA, and **9.96x** on Windows Intel iGPU.
- **Speedups vs. 15-Tool Minimal (`OpenClaw Tool-RAG`, M6):** Cold Prefill achieves **2.10x** (macOS M4), **1.79x** (Linux x86_64), **1.71x** (Windows 11 NVIDIA), and **2.35x** (Windows Intel iGPU); Warm Cache achieves **1.07x**, **1.31x**, **1.26x**, and **1.22x**, respectively.
- **Baseline Normalization Transparency:** On macOS ARM64, both 54-Tool Full and 15-Tool Minimal ratios reference internal unmitigated baselines measured in the identical session (`tool_rag_mitigation_trials.jsonl`). On Linux x86_64, Windows 11 NVIDIA, and Windows Intel iGPU, pruned arms reference each node's primary unmitigated `openclaw_full` and `openclaw_minimal` baselines (`raw_trials.jsonl` for Regime A; `warm_cache_trials.jsonl` for Regime B).

### 4.2. Table 4: KV-Cache Thrashing & Slot Isolation
- Cache eviction penalties quantified as the latency ratio of uncontrolled thrashing to block-isolated slot retention ($T_2/T_3$):
  * **macOS ARM64 (M4):** Minimal catalog penalty $= 6.85\text{x}$; Full catalog penalty $= 19.46\text{x}$.
  * **Linux x86_64:** Minimal catalog penalty $= 1.48\text{x}$; Full catalog penalty $= 2.63\text{x}$.
  * **Windows 11 NVIDIA:** Minimal catalog penalty $= 2.01\text{x}$; Full catalog penalty $= 2.30\text{x}$.
  * **Platform Scope:** Evaluated on the 3 primary nodes (macOS M4, Linux x86_64, Windows 11 NVIDIA); Windows Intel iGPU was scoped to W2 and W5 workloads.

### 4.3. Table 3: Cache Invariance Clarification
- Empirical measurements confirm that **cache invariance applies only to absolute orchestrator latency $T_{\text{orch}}$ (ms)** ($|\Delta T_{\text{orch}}| < 2.0\text{ ms}$, with a maximum observed difference of $1.95\text{ ms}$ for PicoClaw (Go) on Windows 11 NVIDIA).
- The relative overhead fraction $\Phi_{\text{orch}} = T_{\text{orch}} / T_{\text{task}}$ increases under warm cache because neural inference latency $T_{\text{neural}}$ drops substantially under KV prefix reuse.

### 4.4. Table 7: Multi-Platform Dual-Session Replication (Fixed-SESOI Block-Bootstrap TOST; M2--M5)
- Dual-session contrast analysis ($\Delta T_{\text{orch}} = T_{\text{orch}}(\text{Runtime}) - T_{\text{orch}}(\text{PicoClaw})$) across **95 valid platform/regime/workload pairs** (**7 confounded W5 `python_native` pairs excluded per M1**) using Moving Block Bootstrap ($b=3$, $B=5{,}000$; Künsch 1989) with a **fixed, pre-specified data-independent SESOI of $\pm 5.0\text{ ms}$** ($<0.2\%$ of Regime A task duration) and exact order-statistic **90% MBB CIs** aligned with $\alpha = 0.05$ TOST under the standardized 3-state rule (Schuirmann 1987; Lakens 2017):
  * **`Equivalent` (90% CI wholly inside $[-5.0, +5.0]\text{ ms}$, $p_{\text{TOST}} < 0.05$):** **76/95 (80.0%)**
  * **`Different` (90% CI wholly outside $[-5.0, +5.0]\text{ ms}$):** **0/95 (0.0%)**
  * **`Inconclusive` (90% CI straddles SESOI boundary):** **19/95 (20.0%)** (concentrated in 10-turn W4 loops and Windows `python_native` startup variance)

### 4.5. Table 8: Enterprise LangChain + SQLite Workload (W5), Token Audit (M1) & Prototype Judge De-Scoping (E3 / C5)
- Table 8 consolidates W5 across **all 4 physical platforms** (macOS M4, Linux x86_64, Windows 11 NVIDIA, and Windows Intel iGPU) in both Cold and Warm regimes, adding exact `Prompt / Comp. Tokens` audited from the raw JSONLs (`audit_export/w5_token_and_schema_audit.csv`).
- **Token Audit & Segregation of `python_native` (M1, Option A):** Comparable client orchestrators (`picoclaw`, `openclaw_minimal`, `openclaw_full`, `bun_minimal`, `neural_baseline`) processed `2,007--6,921` prompt tokens and `33--38` completion tokens with `finish_reason=tool_calls` across all four platforms. In contrast, `python_native` (LangChain Core) on macOS M4, Windows 11 NVIDIA, and Windows Intel iGPU executed a confounded/truncated prompt (`1,287` prompt / `26` completion tokens; TTFT `50.0 ms` vs. `4,939.5 ms` in macOS Regime A; `finish_reason=stop` on Intel iGPU), while Linux x86_64 Regime B exhibited a `1,416.3 ms` LangChain initialization anomaly. Accordingly, `python_native` in W5 is **excluded from all latency, energy, and TOST contrasts (Tables 2 and 7)** and explicitly **segregated into Part B of Table 8**; any lower latency or energy in Part B is a schema-failure/truncation artifact rather than runtime efficiency.
- **Prototype LLM-as-a-Judge Documentation & De-Scoping (E3 / C5):** **No comparative output-quality evaluation was conducted across runtimes.** The `Quality Score (1-5)` column has been removed from comparative Table 8 (Parts A and B) so that non-comparable prototype telemetry does not appear as a mostly-empty column; instead, prototype diagnostics from `W5_langchain_real_world/evaluator.py` (instrumented solely on the segregated `python_native` W5 arm and uninstrumented on all comparable arms) are isolated in Table 8's dedicated **Schema & Prototype Judge Audit** sub-table:
  * **Judge Model & Inference Configuration:** Local `llama-server` endpoint (`http://127.0.0.1:8080/v1/chat/completions`, `model="local-llm"`) serving **`Meta-Llama-3.2-3B-Instruct` (`Q4_K_M`)** at `temperature = 0.0`, `max_tokens = 150`, `cache_prompt = False`, with deterministic keyword fallback (`heuristic_evaluate()`) if HTTP/JSON parsing fails.
  * **Prompt & 5-Point Rubric (`RUBRIC`, `evaluator.py` lines 17--32):** Scores a cross-domain infrastructure and compliance audit summary on an integer 1--5 scale against three seeded database/policy checks — (1) financial budget overrun (`Alpha-Neural-Gateway > 5%`), (2) SLA latency breach (`Beta-Vector-Search > 120 ms`), and (3) compliance quarantine (`Gamma-Tool-Router`) — requesting JSON output `{"quality_score": <1..5>, "reasoning": "<concise explanation>"}` (`5` = all 3 issues accurately cross-referenced; `4` = at least 2 accurate; `3` = 1--2 issues with imprecise values or missing cross-reference; `2` = factual errors/hallucinations or single-domain failure; `1` = irrelevant, empty, or completely wrong output).
  * **Scored Output Counts ($N=30$ per Regime) & Recorded Diagnostics:** On macOS ARM64 (`N=30` measured outputs in Regime A Cold and `N=30` in Regime B Warm), all `30/30` Cold and `30/30` Warm trials recorded `quality_score = 1.0/5.0` with `evaluation_reasoning = "Empty output"`, triggered immediately by the empty-string guard (`evaluator.py` lines 75--76) because strict LangChain schema validation failed to emit a synthesized text response. Thus, **`1.0/5.0` directly reflects strict schema-validation failure / empty output rather than comparative runtime quality**. On Windows Intel iGPU (`N=30` outputs per regime in Session 1 Cold/Warm and Session 2 Cold/Warm), all `30/30` trials per cell scored `3.0/5.0` (identifying 1 database issue without policy-document cross-referencing).
  * **Same-Family / Self-Evaluation Bias Risk:** Because the prototype judge queries the exact same local `Llama-3.2-3B-Instruct` model used by the agent, it carries explicit **same-family / self-evaluation bias** (Zheng et al. 2023) and 3B-model judging limitations. Consequently, `quality_score` is retained only as diagnostic telemetry explaining the segregated `python_native` W5 failure mode and supports no claims of comparative output quality across runtimes.

---

## 5. FORMAL LITERATURE REFERENCES

1. **Kalibera, T. & Jones, R. (2013):** *Rigorous Benchmarking in Reasonable Time*, ACM ISMM '13, pp. 63--74. DOI: `10.1145/2464157.2464160`
2. **Hoefler, T. & Belli, R. (2015):** *Scientific Benchmarking of Parallel Computing Systems*, ACM/IEEE SC '15, Article 73, pp. 73:1--73:12. DOI: `10.1145/2807591.2807644`
3. **Maricq, A., Duplyakin, D., Jimenez, I., Maltzahn, C., Stutsman, R., & Ricci, R. (2018):** *Taming Performance Variability*, USENIX OSDI '18, pp. 409--425. ISBN: `978-1-939133-08-3`
4. **Künsch, H. R. (1989):** *The Jackknife and the Bootstrap for General Stationary Observations*, The Annals of Statistics, 17(3):1217--1241. DOI: `10.1214/aos/1176347265`
5. **Schuirmann, D. J. (1987):** *A Comparison of the Two One-Sided Tests Procedure and the Power Approach for Assessing the Equivalence of Average Bioavailability*, Journal of Pharmacokinetics and Biopharmaceutics, 15(6):657--680. DOI: `10.1007/BF01068419`
6. **Lakens, D. (2017):** *Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses*, Social Psychological and Personality Science, 8(4):355--362. DOI: `10.1177/1948550617697177`
7. **Mann, H. B. & Whitney, D. R. (1947):** *On a Test of Whether One of Two Random Variables is Stochastically Larger than the Other*, The Annals of Mathematical Statistics, 18(1):50--60. DOI: `10.1214/aoms/1177730491`
8. **Kruskal, W. H. & Wallis, W. A. (1952):** *Use of Ranks in One-Criterion Variance Analysis*, Journal of the American Statistical Association, 47(260):583--621. DOI: `10.1080/01621459.1952.10483441`
9. **Holm, S. (1979):** *A Simple Sequentially Rejective Multiple Test Procedure*, Scandinavian Journal of Statistics, 6(2):65--70. DOI: `10.2307/4615733`
10. **Cliff, N. (1993):** *Dominance Statistics: Ordinal Analyses to Answer Ordinal Questions*, Psychological Bulletin, 114(3):494--509. DOI: `10.1037/0033-2909.114.3.494`
11. **Vargha, A. & Delaney, H. D. (2000):** *A Critique and Improvement of the "CL" Common Language Effect Size Statistics of McGraw and Wong*, Journal of Educational and Behavioral Statistics, 25(2):101--132. DOI: `10.3102/10769986025002101`
12. **Weaver, V. M., Terpstra, D., & Moore, S. (2013):** *Non-Determinism and Overcount on Modern Hardware Performance Counter Implementations*, IEEE ISPASS 2013, pp. 215--224. DOI: `10.1109/ISPASS.2013.6557172`
13. **Kwon, W. et al. (2023):** *Efficient Memory Management for Large Language Model Serving with PagedAttention*, ACM SOSP '23, pp. 611--626. DOI: `10.1145/3600006.3613165`
14. **Yao, S. et al. (2023):** *ReAct: Synergizing Reasoning and Acting in Language Models*, ICLR 2023 (`arXiv:2210.03629`).
15. **Zheng, L. et al. (2023):** *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*, NeurIPS 2023 (`arXiv:2306.05685`).
16. **Reddi, V. J. et al. (2020):** *MLPerf Inference Benchmark*, ACM/IEEE ISCA 2020, pp. 446--459. DOI: `10.1109/ISCA45697.2020.00045`
17. **You, J., Chung, J.-W., & Chowdhury, M. (2023):** *Zeus: Understanding and Optimizing GPU Energy Consumption of DNN Training*, USENIX NSDI '23, pp. 119--139. ISBN: `978-1-939133-33-5`
18. **Barroso, L. A. & Hölzle, U. (2007):** *The Case for Energy-Proportional Computing*, IEEE Computer, 40(12):33--37. DOI: `10.1109/MC.2007.443`
19. **Fahad, M., Shahid, A., Manumachu, R. R., & Lastovetsky, A. (2019):** *A Comparative Study of Methods for Measurement of Energy of Computing*, Energies, 12(11):2204. DOI: `10.3390/en12112204`
20. **Williams, S., Waterman, A., & Patterson, D. (2009):** *Roofline: An Insightful Visual Performance Model for Multicore Architectures*, Communications of the ACM, 52(4):65--76. DOI: `10.1145/1498765.1498785`
21. **Smith, A. M., Katz, D. S., Niemeyer, K. E., & FORCE11 Software Citation Working Group (2016):** *Software Citation Principles*, PeerJ Computer Science, 2:e86. DOI: `10.7717/peerj-cs.86`
22. **Bayley, G. V. & Hammersley, J. M. (1946):** *The ``Effective'' Number of Independent Observations in an Autocorrelated Time Series*, Supplement to the Journal of the Royal Statistical Society, 8(2):184--197. DOI: `10.2307/2983560`
23. **Zimmerman, D. W. & Zumbo, B. D. (1993):** *Rank Transformations and the Power of the Student t Test and Welch t' Test for Non-Normal Populations with Unequal Variances*, Canadian Journal of Experimental Psychology, 47(3):523--539. DOI: `10.1037/h0078850`
24. **Yue, S. & Wang, C. (2004):** *The Mann-Kendall Test Modified by Effective Sample Size to Detect Trend in Serially Correlated Hydrological Series*, Water Resources Management, 18(3):201--218. DOI: `10.1023/B:WARM.0000043140.61082.60`
25. **Fagerland, M. W. & Sandvik, L. (2009):** *The Wilcoxon-Mann-Whitney Test under Scrutiny*, Statistics in Medicine, 28(10):1487--1497. DOI: `10.1002/sim.3561`

---

## 6. FILE INVENTORY AND SHA-256 DIGESTS

Every empirical `.jsonl` file on disk is listed below with its exact relative path, total record count, measured trial count, warmup count, workloads, and computed SHA-256 digest:

| Relative Path | Platform | Session Identifier | Role | Workloads | Total Lines | Measured Trials | Warmup Trials | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | :--- |
| `results/publication_campaign/raw_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `raw` | W1, W2, W3, W4, W5 | 825 | 750 | 75 | `9f624bd429c810fbbaa2c952b18ea718b17d42b7b8667d6419c561ec7f60ed01` |
| `results/publication_campaign/warm_cache_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `warm` | W1, W2, W3, W4, W5 | 825 | 750 | 75 | `bd2854fd866a1d1b963ef7cfe8e659e6c68b59794c1cf6c3ac4f38952f79dea6` |
| `results/publication_campaign/kv_cache_thrashing_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `kv` | W2 | 90 | 90 | 0 | `48532324bcb7ad5c0d072c80571480e308dfdf48029312cded4677f47bbd3081` |
| `data/mcp_live_transport_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `mcp` | W2 | 135 | 135 | 0 | `03e8d3bd247e29c498e87a727daaa41d47e4d3b6005713d25a0a33301d3232c4` |
| `results/publication_campaign/tool_rag_mitigation_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `rag` | W1, W2, W3, W4 | 1056 | 960 | 96 | `3631f7843cef17e9a6c53fd2fc0970164c10ec090433d1f034e4d3238e35dc22` |
| `results/publication_campaign/prefill_ablation.jsonl` | macOS (M4) | `darwin_m4_session1` | `prefill` | 8 conditions | 528 | 480 | 48 | `ce1a12908ef22c0c40b1ff42c3a17a0914779234d9e81e003c7cf2d1b2ee9f5f` |
| `results/publication_campaign/uma_energy_bandwidth_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `uma` | W2, W3 | 120 | 120 | 0 | `960dbbe9c568134175a5c049a3e5f936bcebeb69c93777c4dc7037c6a58a31e3` |
| `data/external_framework_langchain_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `langchain` | W1, W2, W3, W4 | 144 | 120 | 24 | `2fe416fbf8b74ca4dcd18bfb7bb58f69044fa31b8c5fb60a9f3f3658ea458365` |
| `results/publication_campaign/inter_session_trials.jsonl` | macOS (M4) | `darwin_m4_session2` | `warm` | W1, W2, W3, W4, W5 | 825 | 750 | 75 | `ca99fe1748f8e4c171f4a180e258c183797aae3291f7e0d3e44433c77e106ba0` |
| `data/linux_x86_64_session1/raw/raw_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `65f27603213370acfc317357c2c8a01f2abb664858c443b1ae27941d9d9d54a5` |
| `data/linux_x86_64_session1/raw/warm_cache_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `c7388d9d64c9b765ff29e4c91d7e5406b02764cc7cac48d6c7a06d0fd0962d67` |
| `data/linux_x86_64_session1/raw/kv_cache_thrashing_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `kv` | W2 | 184 | 180 | 4 | `b5217cdfae6f7ef23ee994b2555e5050150da3ba6303fa250550d1534b6ec559` |
| `data/linux_x86_64_session1/raw/mcp_live_transport_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `mcp` | W2 | 297 | 270 | 27 | `e8ba4fcbc7403346fb946e524571fe6bf69722eee7d58a560eaceccd1dd7c5f8` |
| `data/linux_x86_64_session1/raw/tool_rag_mitigation_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `ac3c0f22fba876213b9ebe3f6e49edaa5e0c71446827ad6a9139bddf14650b32` |
| `data/linux_x86_64_session2/raw/raw_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `43df3c3249528937871d9728bb4437107696117be1ec3af8f171f457a810957b` |
| `data/linux_x86_64_session2/raw/warm_cache_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `3767a65018317e9e3e93efb0b595e6bc64150b2a454cce7d7baba473f9d379da` |
| `data/linux_x86_64_session2/raw/kv_cache_thrashing_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `kv` | W2 | 184 | 180 | 4 | `c67bfcd561c8ef224a44221a37494c4886d3598eaff1a18f4788977fcf20a328` |
| `data/linux_x86_64_session2/raw/mcp_live_transport_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `mcp` | W2 | 297 | 270 | 27 | `907a8e21bc41eedc92f3fec78b2e9dc46fd2fd31e80a9e6073426570b5c655e9` |
| `data/linux_x86_64_session2/raw/tool_rag_mitigation_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `65434ed3546fbb07f6fcabadeafe64762f4a774c7faab56ee7c3c552dd2d4598` |
| `data/windows_x86_64_session1/raw/raw_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `264db96648f43c8301a936cd9e8a26895a8c79d284b5a78dd62021a1b4006cf9` |
| `data/windows_x86_64_session1/raw/warm_cache_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `3091e23b550627a6b34b692f50566cf99f12ab3ac3fda820dbd2e66a953de019` |
| `data/windows_x86_64_session1/raw/kv_cache_thrashing_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `kv` | W2 | 184 | 180 | 4 | `5ab229460ef19505cd721cf795d7569337212a81fdd3652aa3275a4fb0f8de79` |
| `data/windows_x86_64_session1/raw/mcp_live_transport_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `mcp` | W2 | 297 | 270 | 27 | `9888d6edfabe937e2b0e85845314479b361013ba0fed24220ce58bf206abffab` |
| `data/windows_x86_64_session1/raw/tool_rag_mitigation_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `449bc5204c6f1cd222002eeebd95a3ebbdc45915002a188eb4fa4a7a3b1848f9` |
| `data/windows_x86_64_session2/raw/raw_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `f42f751681083f82787947c10244fecdd24c21ba6e123abd3752870d30568297` |
| `data/windows_x86_64_session2/raw/warm_cache_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `d2df5802ed7c48e3064da8d5eabd27e9f494756bffdb4ad1429560c5286eb891` |
| `data/windows_x86_64_session2/raw/kv_cache_thrashing_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `kv` | W2 | 184 | 180 | 4 | `f4ac5017ceae16ff4c28b936b988d5f76f96f225e81de1d627970ccb5ce28786` |
| `data/windows_x86_64_session2/raw/mcp_live_transport_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `mcp` | W2 | 297 | 270 | 27 | `d9b1e3500af1b210405a7c87de1c6d442ccba36a41e355a99bba68ab16d12e36` |
| `data/windows_x86_64_session2/raw/tool_rag_mitigation_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `ad45f15cb9bea1c483692b6e4dcf39062c709b4f2f2fad1267316692ac616e62` |
| `data/windows_intel_graphics_session1/raw/raw_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session1` | `raw` | W2, W5 | 330 | 300 | 30 | `e6993e9edeb9964f2109972da4444e6bca4d9952260961eebf1a3286d2a71d80` |
| `data/windows_intel_graphics_session1/raw/warm_cache_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session1` | `warm` | W2, W5 | 330 | 300 | 30 | `081809a8c7b44808fb0cfe41d4bdf7a08d77e68f8e16dfcf1f678ecfe5b4f7ab` |
| `data/windows_intel_graphics_session1/raw/tool_rag_mitigation_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session1` | `rag` | W2 | 132 | 120 | 12 | `b4501867f7a7642c18f31130f0f35e926e9aeb3e19d8a028ce32acf28afff669` |
| `data/windows_intel_graphics_session2/raw/raw_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session2` | `raw` | W2, W5 | 330 | 300 | 30 | `920d68b0197e3039021a1ca327b41807c2cd7b60ed1b606371f6d30e65854a33` |
| `data/windows_intel_graphics_session2/raw/warm_cache_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session2` | `warm` | W2, W5 | 330 | 300 | 30 | `d922a01b5dd42bd5ce8b4b9248bf6a4cb636a45384c025d9bffcb010f021e22c` |
| `data/windows_intel_graphics_session2/raw/tool_rag_mitigation_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session2` | `rag` | W2 | 132 | 120 | 12 | `34736fbad16b3fb5d499c14805a4e4700d21337ed7a57090bad8b98811a04157` |
| **TOTAL (35 files)** | **4 Platforms** | **All Sessions** | **All** | **W1--W5 + Ablations** | **18,616** | **16,995** | **1,621** | **SHA-256 Computed** |

---

## 7. METHODOLOGICAL LIMITATIONS & THREATS TO VALIDITY

1. **Offload & Memory Topology Asymmetry (UMA vs. Hybrid PCIe vs. Shared DDR3):** Apple M4 executes full on-die GPU offload (`-ngl 99`, 120 GB/s unified LPDDR5X). Both Dell G15 nodes (Linux x86_64 and Windows 11 NVIDIA) operate under hybrid offload (`-ngl 16`) bounded by 4 GB GDDR6 VRAM with continuous PCIe 4.0 host-to-GPU streaming (~5.2 GB/s). Intel HD Graphics 4600 executes over a shared DDR3-1600 host memory aperture. Consequently, absolute Regime B neural latency and package energy comparisons are confined to within-node contrasts.
2. **Unequal Workload Scope on Windows Intel iGPU (Restricted to W2, W5, and Tool-RAG — E8):** On shared DDR3-1600 memory, measured Regime A (Cold Prefill) trial durations on the Intel HD Graphics 4600 node spanned **53.5 s** (`picoclaw` / 15-tool `openclaw_minimal` W2) to **226.7 s** (54-tool `openclaw_full` W2), with comparable W5 arms requiring **50.1 s--56.9 s** per trial. Executing the complete W1--W4 workload matrix (especially 10-turn multi-step W4 dialogues exceeding 8--15 minutes per cold trial), KV-thrashing ablations (Table 4), and MCP transport ablations (Table 6) across two 30-repetition sessions would require multi-day continuous runtime and expose measurements to severe thermal and OS background drift. Scoping the Intel iGPU node to W2 (standard 3-tool chain), W5 (enterprise workflow), and W2 Tool-RAG captures cross-architecture middleware overhead ($T_{\text{orch}}$, Peak RSS, Win32 CPU cycles) and cold-prefill schema pruning within tractable, stationary dual-session windows.
3. **Unequal Runtime Scope for Bun JSC (Evaluated on x86_64 Only in Consolidated Matrix — E8):** Bun (`bun_minimal`, JavaScriptCore engine) is marked `N/A||` in the macOS ARM64 consolidated Cold/Warm matrix (Tables 1, 2, and 8) because Bun was introduced as a secondary JavaScript-engine ablation (isolating V8 runtime overhead from JavaScript semantics) after the Apple Silicon M4 primary Cold/Warm campaign (`raw_trials.jsonl`, `warm_cache_trials.jsonl`) was frozen. Bun was subsequently evaluated across both Cold and Warm regimes on all three x86_64 nodes (Linux x86_64, Windows 11 NVIDIA, and Windows Intel iGPU); standalone macOS ARM64 Warm Session 2 Bun JSC measurements remain preserved in `results/publication_campaign/inter_session_trials.jsonl` without synthesizing unmeasured macOS Regime A baselines.
4. **Windows User-Mode Telemetry Boundaries (`N/A*`, `N/A§`, `N/A**`):** Unprivileged Windows user-mode restricts PMU retired instruction counters (`CR4.PCE`, reported via empirical Win32 `QueryProcessCycleTime` cycles instead), excludes `py.exe` PEP 397 wrapper stub PID metrics (`N/A§`), and lacks kernel MSR RAPL access on Intel HD Graphics 4600 (`N/A**`).
5. **Segregation of W5 `python_native` & Prototype Judge Bias (M1, E3, C5):** `python_native` (LangChain Core) in W5 experienced schema-validation failure and prompt truncation (`1,287/26` tokens) and is excluded from Tables 2 and 7. The `Quality Score` column was removed from comparative Table 8; prototype evaluator diagnostics (`W5_langchain_real_world/evaluator.py`, querying the same local `Llama-3.2-3B-Instruct` model solely on `python_native` W5, $N=30$/regime, subject to same-family bias) are isolated in a separate Schema & Prototype Judge Audit sub-table. No comparative output-quality evaluation was performed across runtimes.
6. **Linux Mobile CPU Thermal/PL Throttling (M8):** Under `-ngl 16` AVX2 hybrid offload on Linux x86_64, positive intra-trial deltas in `cpu_pkg_throttle_events` elevated positive lag-1 autocorrelation ($r_1$), mitigated via $n_{\text{eff}}$-adjusted Mann-Whitney $U$ variance (Table 2; Bayley & Hammersley 1946; Yue & Wang 2004; Zimmerman & Zumbo 1993; Fagerland & Sandvik 2009) and Moving Block Bootstrap ($b=3$, Table 7).
7. **External Validity Boundaries & Licensing (C9):** Empirical findings are bounded by (i) a single 3B quantized model (`Meta-Llama-3.2-3B-Instruct Q4_K_M`, governed by the Meta Llama 3.2 Community License), (ii) a single inference server backend (`llama-server` / `llama.cpp`, MIT License), (iii) deterministic synthetic workloads (W1--W5), and (iv) heterogeneous platform sensor domains. All reference agents under the `PicoClaw` and `OpenClaw` names are clean-room academic benchmark implementations.

---

## 8. EMPIRICAL SUMMARY & CONCLUDING OBSERVATIONS

The quad-platform measurement campaign shows that:
1. **Workload-Dependent Middleware Overhead & W3 Ranking Inversion (C3):** Compiled Go (`PicoClaw`) exhibits lower client dispatch latency ($T_{\text{orch}}$) than Node.js V8 (`OpenClaw`) in I/O- and schema-bound workloads (**W1, W2, W4, and W5**) and lower Peak RSS across all four hardware and operating system profiles. **Explicitly, a ranking inversion occurs in compute-bound Vector RAG (W3):** scalar dot-product loops in Go (`PicoClaw` Cold $T_{\text{orch}} = 36.83$ ms on macOS, $45.09$ ms on Linux, $49.68$ ms on Windows 11) are outperformed by vectorized SIMD/BLAS routines in `PythonNative` ($21.52$ ms on macOS, $35.20$ ms on Linux) and `Bun` JSC ($28.32$ ms on Linux, $39.99$ ms on Windows 11, and $18.09$ ms Warm Session 2 on macOS).
2. **Inter-Session Contrast Equivalence (Three-State TOST Outcomes — C8):** Moving Block Bootstrap ($b=3$, $B=5{,}000$) TOST against a fixed $\pm 5.0\text{ ms}$ SESOI across 95 valid dual-session pairs yielded **76 `Equivalent` (80.0%)**, **19 `Inconclusive` (20.0%)** (concentrated in 10-turn W4 loops and Windows `python_native` startup variance), and **0 `Different` (0.0%)**, while excluding 7 schema-failed W5 `python_native` pairs.
3. **Segregated Microarchitectural Grounding:** Retired hardware instruction ratios are evaluated within-ISA on ARM64 and x86_64 Linux, complemented by empirical Win32 CPU cycle ratios on both Windows platforms.
4. **Artifact Inventory and Traceability:** Raw JSONL datasets, analysis scripts, manuscript source, regenerated tables, figures, saved test outputs, and SHA-256 manifests are synchronized in `main` for independent reproduction.
