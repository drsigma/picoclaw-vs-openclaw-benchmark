# PROTOCOL V2: Quad-Platform Empirical Systems Benchmark Protocol

**Protocol Version:** 2.0.0  
**Frozen Status:** Frozen (Immutable)  
**Protocol Hash (SHA-256):** `faae1495c811125a945ade49e6026b160b211ca67168a42d27a0b15a0350210f`  
**Author:** Rafael Paniccia Cassetta (UFABC)  
**Repository:** `https://github.com/drsigma/picoclaw-vs-openclaw-benchmark`  

---

## 1. Overview and Scope

This protocol establishes the immutable methodological specification for confirmatory and diagnostic execution of the quad-platform edge AI agent orchestrator benchmark across four heterogeneous operating systems and microarchitectures:
1. **Apple Silicon M4 macOS ARM64** (Unified Memory Architecture, 120 GB/s bus, physical Apple SMC shunts at 50 ms);
2. **Ubuntu 26.04 x86_64 Core i9-14900HX** (Linux RAPL energy_uj, POSIX rusage, Linux CFS scheduler);
3. **Microsoft Windows 11 Pro x86_64 Core i9 + NVIDIA RTX 4090** (Dedicated GPU baseline, NVML board power telemetry);
4. **Microsoft Windows 10/11 x86_64 Intel HD Graphics 4600 UMA** (Constrained legacy desktop, Win32 PSAPI rusage).

---

## 2. Statistical Unit & Analysis Foundations (Item 0.3)

### Primary Statistical Unit
The primary statistical unit is the **experimental condition cell**:
$$\text{Cell} = \langle \text{Platform}, \text{Workload}, \text{Regime}, \text{Runtime Arm}, \text{Session} \rangle$$

All inferential claims are evaluated on cell medians and inter-quartile ranges (IQR) across physical repetitions.

### Elimination of Spurious Repetition Pairing
In block-randomized designs, physical trial repetition index ($k \in \{1, \dots, n\}$) **does not represent temporal alignment**. Different orchestrators run at distinct wall-clock moments. Consequently:
- **No element-wise paired t-test or paired Wilcoxon test across randomized repetition indices is permitted.**
- Inter-runtime contrasts must be evaluated using two-sample independent tests adapted for serial dependence (**Moving Block Bootstrap, MBB**) or cell-level paired contrasts across matched conditions.
- Inter-session comparisons are evaluated between paired session medians ($S_1$ vs. $S_2$).

---

## 3. Confirmatory Hypotheses vs. Exploratory Analyses (Item 0.2)

To avoid data-dredging and post-hoc hypothesis generation, this protocol strictly enforces the boundary between prior confirmatory hypotheses and exploratory diagnostics:

### A. Confirmatory Hypotheses (Pre-registered)
1. **$H_{\text{conf}, 1}$ (Orchestrator Overhead in Warm Cache):**
   Under warm KV-cache prefix retention (Regime B), the Compiled Native architecture (Go) exhibits lower orchestration latency ($T_{\text{orch}}$) than the Managed Event-Driven runtime (Node.js/V8) with a smallest effect size of interest (SESOI) of $\Delta = \pm 5\text{ ms}$. Evaluated via Two One-Sided Tests (TOST, $\alpha=0.05$, $90\%$ CI) and Moving Block Bootstrap ($B=10{,}000$).
2. **$H_{\text{conf}, 2}$ (Inter-Session Replication Equivalence):**
   Condition cell medians between Session 1 ($S_1$) and Session 2 ($S_2$) are statistically equivalent within an equivalence margin of $\pm 10\%$, confirming system stability across platform re-initialization.
3. **$H_{\text{conf}, 3}$ (Tool-RAG Prefix Amortization):**
   Dynamic semantic tool pruning (Tool-RAG) reduces total task latency by $\ge 10\times$ compared to an un-pruned 54-tool catalog in single-slot KV-cache engines by eliminating prefix thrashing.
4. **$H_{\text{conf}, 4}$ (Prefill Masking in Cold Cache):**
   Under cold attention prefill (Regime A), neural computation accounts for $>75\%$ of total wall-clock latency ($\Phi_{\text{orch}} < 25\%$), resulting in practical equivalence among all tested orchestrator runtimes.

### B. Exploratory and Diagnostic Analyses (Not Promoted to Hypotheses)
1. **$A_{\text{expl}, 1}$ (Microarchitectural Instruction Counts):**
   Retired instruction counters (`proc_instructions` via `perf` and `QueryProcessCycleTime`) serve as runtime activity indicators, not direct proxies for end-to-end efficiency.
2. **$A_{\text{expl}, 2}$ (Electrical Energy Dissipation):**
   Energy metrics derived from heterogeneous physical sensors (Apple SMC vs. Linux RAPL vs. NVIDIA NVML) are compared within platform boundaries and interpreted with sensor accuracy qualifications.
3. **$A_{\text{expl}, 3}$ (OS Scheduler Affinity & Directional Drift):**
   Session-level drift and Linux CFS core migration effects are analyzed to characterize platform warming.
4. **$A_{\text{expl}, 4}$ (Hardware Thermal Throttling Diagnostics):**
   Thermal throttle events (`cpu_pkg_throttle_events`) are tracked to empirically test whether thermal saturation degrades latency over extended runs.

---

## 4. Workload Contracts (W1 to W5)

| Workload | Domain | Canonical Prompt Tokens | Completion Tokens | Tools in Catalog | Expected Tool Calls |
|:---|:---|:---:|:---:|:---:|:---:|
| **W1** | Single-Tool Arithmetic | 1,084 | 28 | 15 | 1 (`calculate_hypotenuse`) |
| **W2 (Minimal)** | Multi-Tool Selection | 1,092 | 32 | 15 | 2 (`fetch_log`, `hash_sha256`) |
| **W2 (Bloated)** | Catalog Bloat Ablation | 7,091 | 32 | 54 | 2 (`fetch_log`, `hash_sha256`) |
| **W3** | Vector RAG (Cosine) | 1,287 | 42 | 15 | 2 (`vector_search`, `read_chunk`) |
| **W4** | Multi-Turn Memory | 2,150 | 35 | 15 | 1 per turn (10 turns) |
| **W5** | Enterprise Synthesis | 2,259 | 38 | 2 | 2 (`query_analytics_db`, `read_governance_policy`) |

---

## 5. Execution Modes and Counterbalancing (Item 1.4, 3.1, 3.2)

- **`--smoke-test`**: 1 trial per cell, 0 warmups. Fast end-to-end integration test.
- **`--quick`**: 5 trials per cell, 1 warmup. Fast sensitivity and regression checking.
- **`--full`**: 30 trials per cell, 3 warmups. Confirmatory publication evidence.
- **`--invert-blocks`**: Reverses execution sequence in Session 2 to decouple block position from thermal drift.
- **`--resume`**: Safely skips previously completed trials recorded in raw JSONL logs without re-executing.
- **`--dry-run`**: Outputs execution plan and pre-flight validation without making network or LLM calls.

---

## 6. Pre-defined Exclusion Criteria (Item 5.5)

A trial or cell is excluded from confirmatory analysis **only** under the following objective, pre-registered conditions:
1. HTTP response status is not 200 (unless part of a dedicated fault-injection ablation);
2. Prompt token count diverges by $>5\%$ from canonical workload contract in equalized arms;
3. `finish_reason` is not in `{"stop", "tool_calls", "length"}`;
4. Trial wall-clock timeout is exceeded;
5. Mandatory provenance fields (`session_id`, `timestamp_iso`, `git_commit`) are missing or empty;
6. Physical sensor read returns `NaN` or `Inf`.
