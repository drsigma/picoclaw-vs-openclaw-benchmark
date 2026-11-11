# Technical and Methodological Glossary (English)
## Performance Evaluation: PicoClaw (Go) vs. OpenClaw (Node.js/TypeScript) on Apple Silicon M4
**Author:** Rafael Paniccia Cassetta (Student ID: 21202520618)  
**Institution:** Federal University of ABC (UFABC)  
**Course:** CCM313-EEI203 — Performance Analysis of Networks and Systems (2026.3)  

---

### 1. Evaluated Performance Metrics

| Symbol | Metric Name | Unit | Type | Formal Definition & Measurement Methodology |
| :--- | :--- | :---: | :---: | :--- |
| $T_{\text{task}}$ | **Task Completion Latency** | ms | Direct | Total wall-clock duration elapsed between prompt dispatch by the orchestrator and complete reception of the final streaming token, measured via monotonic POSIX timers (`CLOCK_MONOTONIC_RAW`). |
| $T_{\text{orch}}$ | **Isolated Orchestration Latency** | ms | Derived | Pure computational latency introduced strictly by the agent runtime (JSON validation, TypeBox schema parsing, IPC socket routing, garbage collection), isolated by subtracting neural execution time: $T_{\text{orch}} = T_{\text{task}} - T_{\text{neural}}$. |
| $\Phi_{\text{orch}}$ | **Orchestration Overhead Ratio** | % | Derived | Percentage share of total task duration consumed exclusively by the orchestration harness: $\Phi_{\text{orch}} = \left(\frac{T_{\text{orch}}}{T_{\text{task}}}\right) \times 100\%$. |
| $\text{TTFT}$ | **Time to First Token** | ms | Direct | Latency elapsed from HTTP request transmission to arrival of the first Server-Sent Events (SSE) content chunk emitted by the neural engine, capturing context prefill latency. |
| $\text{ITL}$ | **Inter-Token Latency** | ms/tok | Direct | Mean temporal interval between consecutive token emissions during the auto-regressive decoding phase: $\text{ITL} = \frac{T_{\text{task}} - \text{TTFT}}{N_{\text{out}} - 1}$. |
| $T_{\text{cold}}$ | **Cold-Start Launch Latency** | ms | Direct | Complete process lifecycle latency measured from `execve()` invocation to process exit or IPC readiness, captured via `hyperfine v2.0.0` across $n = 30$ independent runs. |
| $\text{RSS}$ | **Resident Set Size** | MB | Direct | Number of physical memory pages currently allocated in main DRAM occupied by the process address space, sampled via Darwin XNU's `RUSAGE_INFO_V4` structure (`ri_resident_size`). |
| $\text{PhysFootprint}$ | **Kernel Physical Footprint** | MB | Direct | Authoritative Apple kernel metric (`ri_phys_footprint`) quantifying dirty physical memory retained by the process, excluding clean purgeable memory and file-backed shared mappings. |
| $\alpha_{\text{mem}}$ | **Memory Amplification Factor** | ratio | Derived | Ratio of peak resident memory under workload stress to steady-state idle memory footprint: $\alpha_{\text{mem}} = \frac{\text{RSS}_{\text{peak}}}{\text{RSS}_{\text{idle}}}$. |
| $R_{\text{tool}}$ | **Tool Dispatch Throughput** | ops/s | Derived | Frequency of function/tool call executions and schema validations serialized per second: $R_{\text{tool}} = \frac{N_{\text{tools}}}{T_{\text{dispatch}} / 1000}$. |
| $\text{PMC}$ | **Performance Monitoring Counters** | counts | Direct | Hardware register telemetry from the Apple M4 microarchitecture queried through Darwin's `proc_pid_rusage()` API, reporting retired CPU instructions (`ri_instructions`) and clock cycles (`ri_cycles`). |
| $E_{\text{pkg}}$ | **SoC Package Energy Consumption** | Joules (J) | Direct/Int. | Definite numerical integral of combined power rails (CPU + GPU + ANE) sampled every 100 ms via `/usr/bin/powermetrics`: $E_{\text{pkg}} = \sum P(t) \cdot \Delta t$. |
| $\text{EDP}$ | **Energy-Delay Product** | $\text{J}\cdot\text{s}$ | Derived | Dual-objective efficiency metric penalizing execution configurations that trade excessive latency for marginal power drops: $\text{EDP} = E_{\text{pkg}} \times \left(\frac{T_{\text{task}}}{1000}\right)$. |

---

### 2. Experimental System Components & Runtimes

* **PicoClaw v0.3.1 (Sipeed):** Statically compiled Mach-O ARM64 native binary authored in Go 1.23.2. Features concurrent goroutines with 2 KB starting stack frames, zero dynamic shared libraries (`CGO_ENABLED=0`), and Go's non-generational concurrent tri-color mark-and-sweep garbage collector.
* **OpenClaw v2026.10.7:** Desktop and enterprise autonomous agent orchestrator built on Node.js and TypeScript. Relies on the Google V8 engine, dynamic TypeBox schema validation, NPM plugin dependency trees (497 audited packages), and native SQLite state storage (`node:sqlite`).
* **Node.js v26.12.1 (darwin-arm64):** Server-side JavaScript runtime featuring V8's generational GC (Scavenger / Mark-Compact) and full support for native `node:sqlite` modules required by OpenClaw's session engine.
* **llama.cpp (build b11887 Metal):** High-performance C++20 local inference daemon with full Apple Metal GPU compute shader acceleration, NEON vectorization, and Accelerate framework bindings, exposing OpenAI-compatible endpoints on `127.0.0.1:8080/v1`.
* **Meta Llama-3.2-3B-Instruct (GGUF Q4_K_M):** Quantized 3.21-billion parameter dense autoregressive Transformer (1.92 GiB on disk). Evaluated under greedy decoding (`temperature = 0.0`, `seed = 42`) to guarantee strictly zero neural stochasticity across comparative runs.
* **hyperfine v2.0.0:** Statistical CLI benchmarking harness providing warm-up isolation, high-resolution monotonic timing, statistical outlier rejection, and parametric confidence interval computation.
* **Darwin libproc (`RUSAGE_INFO_V4`):** macOS kernel Application Binary Interface (ABI) invoked via Python `ctypes` to read per-process hardware counters, physical footprints, and kernel-billed energy without requiring superuser escalation.
* **Apple powermetrics:** High-privilege macOS System Management Controller (SMC) profiler polling physical hardware current/voltage shunt sensors at 100 ms cadence across `cpu_power`, `gpu_power`, and `ane_power`.
* **Python Test Harness Scientific Libraries:** For deep architectural justifications and technical breakdowns of each Python library utilized across benchmark orchestration and analysis (`scipy`, `numpy`, `matplotlib`, `python-docx`, `dulwich`, `uv`), consult the formal documentation: [`10_TECHNOLOGIES_LIBRARIES_AND_TOOLS_EN.md`](10_TECHNOLOGIES_LIBRARIES_AND_TOOLS_EN.md).
  * **`scipy` (v1.15.2):** Analytical Chi-Square (`chi2.ppf`), Garwood Poisson fiducial limits, Cameron & Trivedi overdispersion regression, and One-Way ANOVA.
  * **`numpy` (v2.2.3):** 384-dimensional dense projection head management and dot-product cosine similarity in Workload W3 (Vector RAG).
  * **`matplotlib` (v3.10.1):** 300-DPI vector/raster figure rendering with LaTeX mathematical typesetting.
  * **`python-docx` (v1.1.2):** Programmatic compilation of formal ABNT/UFABC academic reports directly from measurement traces.
  * **`dulwich` (v0.22.8):** Pure-Python Git protocol client, avoiding Xcode CLT macOS popup shims.
  * **`uv` (Astral):** Rust-powered package manager provisioning `tools/.venv` in seconds with zero host pollution.

---

### 3. Apple Silicon M4 Architectural Framework

* **Unified Memory Architecture (UMA):** High-bandwidth (120 GB/s) unified physical memory pool (24 GB LPDDR5X) shared identically by the 10-core CPU (4 Performance cores up to 4.4 GHz and 6 Efficiency cores up to 2.8 GHz), the 10-core Metal GPU, and the 16-core Apple Neural Engine (ANE).
* **Zero-Copy Memory Semantics:** Elimination of PCIe interconnect bus copies between host CPU and neural GPU accelerators, allowing the inference server and the agent orchestrator to manipulate adjacent memory spaces without socket overhead.
* **UMA Memory Bus Contention:** Phenomenon whereby heavy GPU matrix-multiplication memory sweeps (prefill and decoding) compete for memory controller arbiters against CPU runtime garbage collection sweeps, magnifying dynamic language latencies.
