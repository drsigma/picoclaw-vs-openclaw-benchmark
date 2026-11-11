# Technologies, Libraries, and Tools Used
## Methodological Rationale, Software Architecture, and Engineering Decisions
**Project:** Performance Evaluation of PicoClaw (Go) vs. OpenClaw (Node.js) on Apple Silicon M4  
**Author:** Rafael Paniccia Cassetta (Student ID: 21202520618) — UFABC  
**Course:** CCM313-EEI203 — Performance Evaluation of Networks and Computer Systems (2026.3)  

---

## 1. Why Python for the Benchmark Suite and Test Automation?

A fundamental question in computer systems performance evaluation is: **given that the evaluated agents are written in Go and Node.js/TypeScript, why was the entire test orchestration, telemetry capture, statistical validation, and reporting pipeline implemented in Python?**

The methodological and architectural rationales are definitive:

1. **Strict Separation Between Object under Test and Measurement Harness:**
   * In systems performance evaluation methodology (Raj Jain, 1991), the test instrument (*Test Harness*) must not interfere with the runtime or memory space of the system under test.
   * If Node.js were used to measure OpenClaw, the test harness would compete for the same Google V8 engine, heap garbage collector, and `libuv` event loop, corrupting latency measurements and RSS memory curves.
   * If Go were used to measure PicoClaw, internal instrumentation bias would be introduced.
   * Python functions as a **neutral, external supervisor**, launching agent runtimes as isolated operating system child processes, monitoring PIDs, sampling RSS memory, and querying hardware sensors without sharing memory space or execution threads.

2. **Scientific Maturity and Academic Statistical Rigor:**
   * The Python scientific ecosystem features **SciPy** and **NumPy**, the gold-standard, peer-reviewed computational libraries in academic literature.
   * Computing exact Garwood (1936) Poisson fiducial limits, Cameron & Trivedi (1990) overdispersion regression tests, and One-Way ANOVA tests requires analytical quantiles of the Chi-Square ($\chi^2$) and $F$ distributions, implemented with 64-bit IEEE 754 floating-point stability in SciPy. Pure Bash or stock JavaScript lacks native support for these statistical operations without fragile third-party modules.

3. **Multiprocess Orchestration and Daemon Management:**
   * Python's standard `subprocess` library allows starting background Metal GPU daemons (`llama-server`), verifying HTTP health status via `urllib`, triggering system anti-sleep utilities (`caffeinate`), running agent processes with deterministic timeouts, and handling exit signals reliably across POSIX environments.

4. **Integrated Scientific Publishing Pipeline (Figures and Reports):**
   * Using unified JSONL raw telemetry traces, Python simultaneously generates publication-ready 300-DPI vector/raster figures (`matplotlib`) and formal academic `.docx` reports formatted according to Brazilian ABNT/UFABC university standards (`python-docx`), establishing an unbroken cryptographic chain of custody from raw trial telemetry to published findings.

---

## 2. Python Libraries: Specific Names, Versions, and Rationale

All Python libraries are pinned and provisioned inside the isolated virtual environment at [`tools/.venv`](../tools/).

| Library | Version | Primary Project Function | Rationale for Selection |
| :--- | :---: | :--- | :--- |
| **`scipy`** | `1.15.2` | Statistical inference engine, Chi-Square quantiles, Garwood Poisson intervals, and ANOVA. | **Strict Mathematical Rigor:** Provides analytical functions `scipy.stats.chi2.ppf` and `scipy.stats.poisson` necessary to compute exact Garwood (1936) fiducial limits for Poisson event counts, the Cameron & Trivedi dispersion diagnostic, and One-Way ANOVA (`scipy.stats.f_oneway`) across all 5 physical campaigns, avoiding empirical approximations. |
| **`numpy`** | `2.2.3` | High-performance linear algebra, dense tensor storage, and vector similarity search. | **Vectorized Processing in Workload W3 (RAG):** Manages the 98,688-parameter projection head (`embedding_head_100k.npz`), executing L2 normalization and dot-product cosine similarity operations across 10,000 document text chunks via Apple Silicon M4 vectorized SIMD instructions. |
| **`matplotlib`** | `3.10.1` | 300-DPI vector and raster rendering of scientific figures (Figures 1 through 8). | **Publication-Ready Graphics:** Supports complete LaTeX mathematical typography via mathtext, asymmetric empirical error bars, high-resolution 300-DPI rasterization, and colorblind-safe color palettes conforming to IEEE/ACM formatting standards. |
| **`python-docx`** | `1.1.2` | Programmatic compilation of formal Academic System Testing Reports (`reports/*.docx`). | **ABNT & Institutional Compliance:** Automatically builds formatted academic reports with formal pagination, structured comparison tables, figure captions, and institutional headers directly from empirical trial logs, without requiring Microsoft Word installed on the host. |
| **`dulwich`** | `0.22.8` | Pure-Python Git protocol implementation for repository staging, commits, and SSH pushes. | **Bypassing macOS Xcode CLT Stubs:** On macOS, `/usr/bin/git` is an Apple shim that invokes an intrusive GUI prompt requesting a 15 GB Xcode download. `dulwich` operates entirely in user-space Python, manages Git packfiles directly, and authenticates via Ed25519 SSH keys with zero OS developer tool dependencies. |

### Standard Library Native Modules (Zero External Overhead)
* **`subprocess`:** Low-level process lifecycle management, stdout/stderr stream piping, and synchronous command execution.
* **`urllib.request` & `urllib.error`:** HTTP client communication targeting local loopback (`127.0.0.1:8080`) for server healthchecks and OpenAI ChatCompletions schema submissions.
* **`hashlib`:** Cryptographic SHA-256 digest calculation for all 215 tracked files registered in [`data/manifest_sha256.json`](../data/manifest_sha256.json).
* **`json` & `csv`:** Structured parsing and emission of JSON Lines logs (`consolidated_trials.jsonl`) and benchmark summary tables.
* **`time` (`time.perf_counter_ns`):** Nanosecond-resolution monotonic clock sampling mapped directly to the hardware cycle counter on macOS.
* **`pathlib` & `os.path`:** Cross-platform portable relative path resolution ensuring reproducible execution from any working directory.

---

## 3. System Tools, Compilers, and Runtime Engines

| Tool | Version / Build | What is it? | Rationale for Selection |
| :--- | :---: | :--- | :--- |
| **Go (Golang)** | `1.23.2` | Static compiler for native ARM64 machine code (PicoClaw). | **Bare-Metal Native Minimalism:** Compiles directly into ~57 MB Mach-O ARM64 binaries without intermediate virtual machines or bytecode interpreters. Go's $M:N$ scheduler (~2 KB per goroutine stack) and concurrent tri-color mark-sweep GC eliminate major stop-the-world pauses ($< 1\text{ ms}$), achieving $9.63\text{ ms}$ cold start and a tiny $14\text{ to }34\text{ MB}$ RAM footprint. |
| **Node.js / TypeScript** | `v26.12.1` | JavaScript/TypeScript runtime engine powered by Google V8 (OpenClaw). | **Industry-Standard Enterprise Contender:** Represents the dominant architecture used for commercial AI agents. Google V8 provides tiered JIT compilation (Sparkplug, Maglev, Turbofan), TypeBox dynamic schema validation, and native `node:sqlite` persistence, allowing realistic quantification of enterprise memory overhead ($166\text{ to }448\text{ MB}$) and launch delays ($225\text{ ms}$). |
| **llama.cpp** | `build b11887 (Metal)` | Local C++ neural inference server with Apple Metal GPU acceleration. | **Zero-Overhead Bare-Metal Serving:** Runs language models directly on Apple Silicon M4's 10-core Metal GPU using custom Metal Shading Language compute kernels, bypassing Python/PyTorch and CUDA wrappers. Enforces deterministic greedy decoding (`temperature = 0.0`, `seed = 42`), ensuring token-identical model outputs across both agents. |
| **hyperfine** | `1.19.0` | High-precision statistical CLI benchmarking tool written in Rust. | **Objective Cold-Start Timing:** Implements automated warmup cycles (`--warmup 5`), disk cache clearing, and 30 consecutive iterations to calculate mean, standard deviation, min, and max timings, eliminating human bias and launch jitter. |
| **powermetrics** | Native Apple macOS | Hardware diagnostic utility sampling Apple Silicon on-die power sensors. | **Direct Hardware Power Telemetry via SMC:** The only authorized macOS utility capable of querying analog/digital sensors in the Apple System Management Controller (SMC), reporting real physical power dissipation in milliwatts (mW) for CPU, GPU, and unified DRAM at 100 ms intervals. |
| **caffeinate** | Native Apple macOS | Command-line utility controlling macOS power management assertions. | **System Quiescence & Anti-Throttling:** Executed with `-dims` (Display, Idle, Machine, System) assertions to prevent the Mac mini M4 from entering sleep states, disabling displays, or throttling clock frequencies during multi-hour test runs. |
| **mdutil** | Native Apple macOS | Spotlight indexing control utility for macOS. | **Disk I/O Quiescence:** Temporarily pauses background indexing by `mds` and `mdworker` processes, ensuring disk I/O in Workload W2 reflects solely experimental file operations rather than background system activity. |
| **Astral uv** | `v0.5.x` | High-speed Python package and environment manager written in Rust. | **Instantaneous Isolated Provisioning:** Resolves, downloads, and builds virtual environment packages in under 3 seconds, isolating all Python dependencies strictly within `tools/.venv`. |

---

## 4. Workload Architecture and Dataset Interactivity

1. **Workload W1 (Simple Reflection):**
   * Operates purely in memory. Standard library `urllib` submits an architectural reflection query and measures time-to-first-token and orchestrator scheduling delay.
2. **Workload W2 (3-Step Tool Chain):**
   * Consumes `data/workload_data/mock_files/` via `list_dir`, filters `data/workload_data/system_logs.jsonl` via `grep_logs`, and calculates descriptive metrics via `calc_stats`.
3. **Workload W3 (In-Memory Vector RAG):**
   * Uses **`numpy`** to load pre-calculated projection weights from `data/workload_data/embedding_head_100k.npz`, computing dot-product cosine similarities across 10,000 document chunks stored in `data/workload_data/rag_chunks_10k.json`.
4. **Workload W4 (10-Turn Autonomous ReAct Loop):**
   * Executes a continuous autonomous loop alternating between W2 and W3 tools across 10 sequential turns, tracking gradual RSS heap growth.

---

## 5. Methodological Conclusion

Every technology selection adheres strictly to **reproducibility**, **statistical validity**, and **non-intrusiveness**. Pairing compiled native binaries (Go, C++ Metal, Rust) with a dedicated Python test and analysis harness ensures any independent researcher can verify and replicate these findings with zero ambiguity.
