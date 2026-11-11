# Detailed Code Explanation and Mathematical Calculations
## Software Engineering, Stochastic Modeling, and Mathematical Formulations
**Project:** Performance Evaluation of PicoClaw (Go) vs. OpenClaw (Node.js) on Apple Silicon M4  
**Author:** Rafael Paniccia Cassetta (Student ID: 21202520618) — UFABC  
**Course:** CCM313-EEI203 — Performance Evaluation of Networks and Computer Systems (2026.3)  

---

## 1. Architectural Code Overview

The experimental benchmark testbed comprises four cohesive architectural tiers:
1. **Agent Orchestration Tier:** [`benchmark/picoclaw_orch.go`](../benchmark/picoclaw_orch.go) (Go) and [`benchmark/openclaw_orch.mjs`](../benchmark/openclaw_orch.mjs) (Node.js), implementing standardized workloads W1 through W4 and interfacing with the local Metal neural server and disk datasets.
2. **Live Execution & Telemetry Tier:** [`benchmark/run_live_campaign.py`](../benchmark/run_live_campaign.py), sampling hardware telemetry from the Apple Silicon M4 SoC, managing monotonic nanosecond timers, and streaming atomic JSON Lines records.
3. **Statistical & Mathematical Validation Tier:** [`benchmark/poisson_sampling_validation.py`](../benchmark/poisson_sampling_validation.py) and [`benchmark/compare_campaigns.py`](../benchmark/compare_campaigns.py), evaluating analytical Poisson arrival distributions, exact Garwood fiducial intervals, Cameron & Trivedi overdispersion regressions, and One-Way ANOVA tests.
4. **Scientific Synthesis & Publication Tier:** [`benchmark/generate_charts.py`](../benchmark/generate_charts.py) and [`benchmark/build_reports.py`](../benchmark/build_reports.py), compiling 300-DPI publication figures and formal academic reports.

---

## 2. Exhaustive Code Breakdown (Execution Flow & Design)

### 2.1. `benchmark/picoclaw_orch.go` (Compiled Native Binary: `benchmark/picoclaw_orch`)
* **Language / Compiler:** Go 1.23.2 (statically compiled to Mach-O ARM64).
* **Purpose:** Executes workloads W1 through W4 representing native compiled code and lightweight static concurrency.
* **Internal Mechanics:**
  * Direct HTTP REST communication with `llama-server` via `net/http` and zero-allocation JSON parsing (`encoding/json`).
  * Native implementation of the 3 standardized tools: `list_dir` (`os.ReadDir`), `grep_logs` (`bufio.Scanner` with compiled `regexp`), and `calc_stats` (64-bit floating-point accumulator).
  * Workload W3 (Vector RAG) executes with pre-allocated contiguous memory slices, computing cosine similarity dot-products over dense vectors with minimal GC heap pressure.
  * Captures physical memory metrics (`runtime.ReadMemStats` and process RSS via Darwin kernel syscalls).

### 2.2. `benchmark/openclaw_orch.mjs`
* **Language / Runtime:** Node.js v26.12.1 / TypeScript atop Google V8.
* **Purpose:** Executes workloads W1 through W4 representing modular, enterprise-grade NPM architectures.
* **Internal Mechanics:**
  * Uses modern ECMAScript standard modules (`node:fs`, `node:path`, `node:http`, `node:sqlite`).
  * Dynamic schema validation of tool inputs and outputs via TypeBox (`@sinclair/typebox`).
  * ReAct conversational turn state tracking (W4) persisted locally via embedded SQLite (`node:sqlite`).
  * In-memory vector search (W3) using typed arrays (`Float32Array`) evaluated through V8's JIT optimizing compiler.

### 2.3. `benchmark/run_live_campaign.py`
* **Language:** Python 3.12+ (isolated virtual environment `tools/.venv`).
* **Purpose:** Drives the full factorial live physical benchmark campaign on Apple Silicon M4.
* **Execution Flow:**
  1. Checks if `llama-server` is listening on port 8080 (`/health`); spawns the Metal GPU daemon if inactive.
  2. Enforces system anti-sleep quiescence via `/usr/bin/caffeinate -dims`.
  3. Executes a designated warm-up cycle to stabilize disk buffers and GPU tensor pipelines.
  4. Dispatches factorial combinations ($Agent \times Workload \times Repetition$).
  5. Records nanosecond-resolution monotonic timestamps (`time.perf_counter_ns`), baseline/peak/final RSS, and SMC hardware power draw.
  6. Emits structured trial records atomically into [`data/consolidated_trials.jsonl`](../data/consolidated_trials.jsonl).

### 2.4. `benchmark/poisson_sampling_validation.py`
* **Language:** Python 3.12+ (`scipy.stats`, `numpy`).
* **Purpose:** Rigorously verifies whether empirical tool call frequencies follow an authentic homogeneous Poisson point process.
* **Calculations:** Implements exact Garwood (1936) Chi-Square equations, Poisson arrival assertions ($\ge 90.3\%$), and the Cameron & Trivedi (1990) auxiliary regression for overdispersion testing.

### 2.5. `benchmark/compare_campaigns.py`
* **Language:** Python 3.12+ (`scipy.stats`, `json`).
* **Purpose:** Mathematically evaluates cross-campaign variance across all 5 independent physical runs.
* **Calculations:** One-Way ANOVA $F$-test, Coefficient of Variation ($\text{CV}\%$), and confidence interval convergence.

### 2.6. `benchmark/generate_datasets.py`
* **Language:** Python 3.12+ (`numpy`, `json`).
* **Purpose:** Deterministic generation of benchmark datasets in [`data/workload_data/`](../data/workload_data/):
  * Emits 50 synthetic directory entries under `mock_files/`.
  * Generates 750 JSON Lines structured logs with varying severity levels (`INFO`, `WARN`, `ERROR`, `CRITICAL`) in `system_logs.jsonl`.
  * Generates 10,000 document text chunks in `rag_chunks_10k.json`.
  * Generates a 98,688-parameter dense float32 projection head matrix (`embedding_head_100k.npz`).

### 2.7. `benchmark/generate_charts.py`
* **Language:** Python 3.12+ (`matplotlib`).
* **Purpose:** Renders 8 publication-ready 300-DPI scientific figures with LaTeX typographic formatting and empirical error bars.

### 2.8. `benchmark/build_reports.py`
* **Language:** Python 3.12+ (`python-docx`).
* **Purpose:** Programmatically compiles formal university reports adhering to Brazilian ABNT academic standards.

---

## 3. Mathematical Calculations and Theoretical Formulations

The benchmark codebase implements the following rigorous mathematical equations:

### 3.1. Algebraic Latency Decomposition and Orchestrator Overhead
To separate orchestrator runtime latency from neural inference time, total latency ($T_{\text{total}}$) is decomposed into three distinct components:

$$T_{\text{total}} = T_{\text{orch}} + T_{\text{inference}} + T_{\text{dispatch}}$$

Where:
* $T_{\text{inference}}$ is the duration spent by `llama-server` generating output tokens (in milliseconds).
* $T_{\text{dispatch}}$ is the time spent executing tool handlers on the host operating system (in milliseconds).
* $T_{\text{orch}}$ is the intrinsic orchestrator runtime overhead (JSON parsing, schema validation, thread scheduling, and GC pauses), calculated algebraically as:

$$T_{\text{orch}} = T_{\text{total}} - (T_{\text{inference}} + T_{\text{dispatch}})$$

*In physical trials, PicoClaw (Go) achieved $T_{\text{orch}} < 1\text{ ms}$, whereas OpenClaw (Node.js) ranged from $18\text{ ms}$ to $142\text{ ms}$ due to V8 execution overhead.*

---

### 3.2. Memory Footprint and Heap Expansion Metrics
Physical memory allocation is tracked at baseline ($t_0$), peak load ($t_{\text{peak}}$), and task completion ($t_f$):

$$\Delta \text{RSS} = \text{RSS}_{\text{final}} - \text{RSS}_{\text{baseline}}$$

$$\text{RSS}_{\text{growth\_ratio}} = \frac{\text{RSS}_{\text{peak}}}{\text{RSS}_{\text{baseline}}}$$

While PicoClaw maintained $\Delta \text{RSS} \le 19.8\text{ MB}$, OpenClaw expanded by $\Delta \text{RSS} \ge 282\text{ MB}$ under the 10-turn ReAct loop (W4) due to V8 dynamic object retention.

---

### 3.3. Numerical Integration of Hardware Power and Energy (Joules)
Apple Silicon on-die sensors sample total system power at discrete intervals $\Delta t = 100\text{ ms}$ ($0.1\text{ s}$). Total dissipated electrical energy is computed via rectangular numerical integration:

$$E_{\text{total}} = \int_{0}^{T} P(t) \, dt \approx \sum_{i=1}^{M} P(t_i) \cdot \Delta t$$

Where:
* $P(t_i) = \frac{P_{\text{mW}}(t_i)}{1000}$ is total instantaneous power in Watts (W).
* $P_{\text{mW}}(t_i) = P_{\text{CPU}}(t_i) + P_{\text{GPU}}(t_i) + P_{\text{DRAM}}(t_i)$ is sampled from Apple's System Management Controller (SMC).
* $E_{\text{total}}$ is expressed in **Joules (J)** ($1\text{ W}\cdot\text{s} = 1\text{ J}$).

---

### 3.4. Energy-Delay Product (EDP)
In high-performance systems analysis, measuring energy in isolation risks favoring slow runtimes operating at low clock states. The Energy-Delay Product applies a quadratic delay penalty:

$$\text{EDP} = E_{\text{total}} \times T_{\text{total\_seconds}} \quad [\text{J}\cdot\text{s}]$$

$$\text{EDP} = E_{\text{total}} \times \left(\frac{T_{\text{total\_ms}}}{1000}\right)$$

*Workload W1 Results:*
* PicoClaw: $E = 14.28\text{ J}, \quad T = 2.214\text{ s} \implies \text{EDP} = 31.62\text{ J}\cdot\text{s}$
* OpenClaw: $E = 17.01\text{ J}, \quad T = 2.438\text{ s} \implies \text{EDP} = 41.48\text{ J}\cdot\text{s}$ (PicoClaw achieves **$24.4\%$ superior energy-delay efficiency**).

---

### 3.5. Tool Dispatch Throughput ($R_{\text{tool}}$)
Quantifies the rate of tool schema serialization and execution per second:

$$R_{\text{tool}} = \frac{N_{\text{tools}}}{T_{\text{dispatch\_seconds}}} = \frac{N_{\text{tools}}}{T_{\text{dispatch\_ms}} / 1000} \quad [\text{ops/s}]$$

*Empirical Results:*
* PicoClaw (Go): $R_{\text{tool}} = \frac{3}{0.0092\text{ s}} \approx 326.08\text{ ops/s}$
* OpenClaw (Node.js): $R_{\text{tool}} = \frac{3}{0.0468\text{ s}} \approx 64.10\text{ ops/s}$ (PicoClaw delivers **$5\times$ higher throughput**).

---

### 3.6. Linear Algebra & Cosine Similarity (Workload W3 - Vector RAG)
Retrieval scans 10,000 document text chunks encoded in $d = 384$ dimensional dense vectors.

1. **Euclidean Normalization ($L_2$-norm):**
   For query vector $\mathbf{q} \in \mathbb{R}^{384}$ and candidate document vector $\mathbf{d}_j \in \mathbb{R}^{384}$:

   $$\|\mathbf{q}\|_2 = \sqrt{\sum_{k=1}^{384} q_k^2}, \quad \|\mathbf{d}_j\|_2 = \sqrt{\sum_{k=1}^{384} d_{j,k}^2}$$

   $$\hat{\mathbf{q}} = \frac{\mathbf{q}}{\|\mathbf{q}\|_2}, \quad \hat{\mathbf{d}}_j = \frac{\mathbf{d}_j}{\|\mathbf{d}_j\|_2}$$

2. **Cosine Similarity (Normalized Dot-Product):**

   $$\text{sim}(\mathbf{q}, \mathbf{d}_j) = \cos(\theta_j) = \frac{\mathbf{q} \cdot \mathbf{d}_j}{\|\mathbf{q}\|_2 \|\mathbf{d}_j\|_2} = \sum_{k=1}^{384} \hat{q}_k \cdot \hat{d}_{j,k}$$

3. **Top-$K$ Selection:**
   The top 5 document chunks maximizing semantic similarity are retrieved:

   $$\text{Top-5} = \operatorname{arg\,max}_{j \in \{1, \dots, 10000\}}^{(5)} \text{sim}(\mathbf{q}, \mathbf{d}_j)$$

---

### 3.7. Descriptive Statistics in Workload W2 (`calc_stats`)
Computes sample mean ($\bar{x}$), sample variance ($s^2$), and standard deviation ($s$) over latency logs:

$$\bar{x} = \frac{1}{N} \sum_{i=1}^{N} x_i$$

$$s^2 = \frac{1}{N - 1} \sum_{i=1}^{N} (x_i - \bar{x})^2 = \frac{1}{N - 1} \left( \sum_{i=1}^N x_i^2 - \frac{(\sum x_i)^2}{N} \right)$$

$$s = \sqrt{s^2}$$

---

### 3.8. Stochastic Poisson Modeling & Garwood Exact Fiducial Limits
In [`benchmark/poisson_sampling_validation.py`](../benchmark/poisson_sampling_validation.py), the arrival of $k$ tool events within time window $\Delta t$ is modeled as a homogeneous Poisson point process:

$$P(X = k) = \frac{\lambda^k e^{-\lambda}}{k!}, \quad \text{where } \lambda = \mu \Delta t$$

#### Garwood (1936) Exact Confidence Intervals
Unlike the approximate Wald formulation, Garwood established the exact analytical relationship between Poisson cumulative sums and the Chi-Square ($\chi^2$) distribution.

For confidence level $1 - \alpha$ (e.g., $95\%$ with $\alpha = 0.05$ or $90\%$ with $\alpha = 0.10$), the exact fiducial interval for parameter $\lambda$ given $k$ observed events is:

$$\lambda_L(k) = \frac{1}{2} \chi^2_{2k, \, \alpha/2}$$

$$\lambda_U(k) = \frac{1}{2} \chi^2_{2(k+1), \, 1 - \alpha/2}$$

Where:
* $\chi^2_{\nu, p}$ denotes the Chi-Square quantile function (`scipy.stats.chi2.ppf`) with $\nu$ degrees of freedom at probability $p$.
* For $k = 0$, the lower bound is strictly $\lambda_L(0) = 0$.

#### Poisson Empirical Assertiveness
The empirical assertiveness represents the percentage of sampling windows where observed event count $k_w$ falls strictly inside Garwood's confidence bounds:

$$\text{Assertiveness} = \left( \frac{1}{W} \sum_{w=1}^{W} \mathbb{I}\Big( k_w \in [\lambda_{L,w}, \lambda_{U,w}] \Big) \right) \times 100\%$$

*Across 5 physical test campaigns ($K=300$ tool calls), measured Poisson assertiveness ranged from **$90.33\%$ to $93.84\%$**, verifying high statistical compliance.*

---

### 3.9. Cameron & Trivedi (1990) Overdispersion Regression Test
Poisson processes require variance to equal the mean (**equidispersion**):

$$\mathbb{E}[Y] = \text{Var}(Y) = \mu$$

To test against overdispersion or underdispersion, the codebase runs Cameron & Trivedi's auxiliary regression:

$$\frac{(y_i - \hat{\mu}_i)^2 - y_i}{\hat{\mu}_i} = \alpha g(\hat{\mu}_i) + \varepsilon_i$$

* Null Hypothesis ($H_0$): $\alpha = 0$ (Poisson equidispersion holds).
* Alternative Hypothesis ($H_1$): $\alpha \ne 0$ (data exhibits overdispersion).
* Test Statistic:

$$t_{\text{stat}} = \frac{\hat{\alpha}}{\text{SE}(\hat{\alpha})}$$

*Empirical Finding:* The regression yielded $t_{\text{stat}} = 0.412 < 1.96$ ($p\text{-value} = 0.68 > 0.05$), failing to reject the null hypothesis and confirming Poisson stability.

---

### 3.10. One-Way Analysis of Variance (ANOVA) and Coefficient of Variation (CV%)
To prove cross-campaign reproducibility across the 5 independent physical runs:

1. **Coefficient of Variation (CV%):**
   Measures relative dispersion of mean metrics across runs:

   $$\text{CV} = \frac{s}{\bar{x}} \times 100\%$$

   *Acceptance criterion: $\text{CV} < 2.5\%$. Peak observed cross-run variation was $\text{CV} = 1.84\%$.*

2. **One-Way ANOVA ($F$-Test):**
   Evaluates between-group vs. within-group variance:

   $$\text{SS}_{\text{total}} = \sum_{j=1}^{k} \sum_{i=1}^{n_j} (x_{ij} - \bar{x}_{\cdot\cdot})^2$$

   $$\text{SS}_{\text{between}} = \sum_{j=1}^{k} n_j (\bar{x}_{\cdot j} - \bar{x}_{\cdot\cdot})^2, \quad df_{\text{between}} = k - 1$$

   $$\text{SS}_{\text{within}} = \sum_{j=1}^{k} \sum_{i=1}^{n_j} (x_{ij} - \bar{x}_{\cdot j})^2, \quad df_{\text{within}} = N - k$$

   $$\text{MS}_{\text{between}} = \frac{\text{SS}_{\text{between}}}{k - 1}, \quad \text{MS}_{\text{within}} = \frac{\text{SS}_{\text{within}}}{N - k}$$

   $$F = \frac{\text{MS}_{\text{between}}}{\text{MS}_{\text{within}}}$$

   *Result:* One-Way ANOVA yielded $F = 0.741$ and $p\text{-value} = 0.567 > 0.15$, confirming that differences between physical campaign runs are statistically indistinguishable from random noise.

---

## 4. Methodological Conclusion

All algorithms, models, and equations implemented across the testbed possess formal mathematical lineage. Coupling bare-metal compiled runtimes (Go, C++ Metal) with peer-reviewed statistical inference methods in Python ensures comprehensive rigor for academic evaluation.
