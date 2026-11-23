# picoclaw-vs-openclaw-benchmark: A Quad-Platform Benchmark Suite for Autonomous LLM Agent Middleware

[![CI](https://github.com/drsigma/picoclaw-vs-openclaw-benchmark/actions/workflows/reproducibility.yml/badge.svg)](https://github.com/drsigma/picoclaw-vs-openclaw-benchmark/actions)
[![Code License: MIT](https://img.shields.io/badge/Code%20License-MIT-yellow.svg)](LICENSE)
[![Data License: CC BY 4.0](https://img.shields.io/badge/Data%20License-CC%20BY%204.0-lightgrey.svg)](DATA_LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.PENDING_RELEASE.svg)](https://doi.org/10.5281/zenodo.PENDING_RELEASE)

## Software Description

`picoclaw-vs-openclaw-benchmark` is an open-source experimental benchmark suite designed to isolate, measure, and analyze client-side agent orchestration overhead ($T_{\text{orch}} = T_{\text{task}} - T_{\text{neural}}$) independently of neural token generation. The suite compares clean-room reference agent architectures across four physical computing testbeds:
- **macOS ARM64 (Apple M4):** 10-core CPU (4P + 6E), Metal 3 unified GPU, 24 GB LPDDR5X UMA memory, Apple SMC energy telemetry (`powermetrics`) and hardware PMU counters.
- **Linux x86_64 (Ubuntu 26.04 LTS):** Intel Core i5-12500H (16 threads), NVIDIA RTX 3050 Laptop GPU (4 GB VRAM, partial offload `-ngl 16`), Intel RAPL MSR and NVIDIA NVML telemetry.
- **Windows 11 x86_64 (NVIDIA dGPU):** Intel Core i5-12500H, NVIDIA RTX 3050 Laptop GPU, Intel MSR and NVML DLL telemetry, Win32 `QueryProcessCycleTime` CPU cycles.
- **Windows 10/11 x86_64 (Intel HD Graphics 4600 iGPU):** Intel Core i7-4790K (4C/8T), shared DDR3 UMA system memory, user-mode Win32 PSAPI telemetry (dedicated to W2 and W5).

Evaluated runtimes contrast Go and Bun (JavaScriptCore) against Node.js (V8) and CPython. Reference adapters integrate new execution environments with approximately 35--90 lines of code (~90 lines for the native Bun JSC adapter). The underlying neural engine is `llama-server` (`llama.cpp`) hosting Meta Llama-3.2-3B-Instruct (GGUF Q4_K_M) across standardized workloads W1--W5 under deterministic decoding (`temperature = 0.0`, `seed = 42`).

All reference agents evaluated under the `PicoClaw` and `OpenClaw` names are clean-room academic implementations isolated for systems benchmarking. Models are subject to the Meta Llama 3.2 Community License.

## Pre-Run Packaging vs. Post-Run Experimental Artifacts

This repository rigorously distinguishes between **Pre-Run static deliverables** and **Post-Run runtime artifacts**:

### 1. Pre-Run Deliverables (Static Source Package)
The pre-campaign package contains all executable scripts, platform telemetry adapters, frozen workload contracts (W1–W5), deterministic test suites, documentation, and static input data (`data/workload_data/`).
- **Safe Pre-Flight Verification Commands (Zero Workloads Executed)**:
  ```bash
  # Pre-flight static manifest verification
  python3 scripts/verify_manifest.py --pre-run

  # Pre-flight gatekeeper verification (validates schemas, contracts, and directory readiness)
  python3 scripts/audit_submission_gatekeeper.py --pre-run

  # Safe dry-runs across unified and platform runners
  python3 benchmark/run_unified_benchmark.py --dry-run
  python3 scripts/run_linux_x86_64_master_campaign.py --dry-run

  # Unit & contract test execution
  pytest -v
  ```

### 2. Post-Run Runtime Artifacts (Generated Post-Campaign)
Execution trials (`*.jsonl`), power traces, and derived statistical tables/figures are **runtime outputs generated during and after campaign execution**.
- Historical campaign datasets (35 `.jsonl` files comprising 18,616 records across 4 platforms) document prior baseline runs. In a fresh pre-run package, trial datasets are produced when physical campaigns are executed on native testbeds (`--full`).
- **Post-Run Validation & Audit Pipeline**:
  ```bash
  # Post-run campaign reproduction & statistical deconvolution
  python3 scripts/reproduce_quad_platform_analysis.py

  # Post-run automated submission gatekeeper (audits .jsonl datasets & emits certificate)
  python3 scripts/audit_submission_gatekeeper.py --post-run

  # Post-run complete cryptographic manifest verification
  python3 scripts/verify_manifest.py --post-run
  ```

## Illustrative Example

To execute an individual benchmark trial evaluating a specific agent adapter and workload tier against a local `llama-server` instance:

```bash
# 1. Activate isolated Python environment
source .venv_repro/bin/activate

# 2. Run a standalone evaluation trial (e.g., PicoClaw on Workload W2)
python3 -m benchmark.orchestrator --adapter picoclaw --workload W2 --regime warm --trials 30

# 3. Run the offline reproduction script across all 35 raw datasets (~30-60 seconds execution time)
python3 scripts/reproduce_quad_platform_analysis.py
```

The script ingests all 35 raw `.jsonl` files in `data/` and `results/`, evaluates non-parametric statistical tests, generates Tables 1–8 in Markdown and LaTeX, plots Figures 1–6 in 300 DPI, and verifies cryptographic integrity against `data/manifest_sha256.json`. Expected offline reproduction time is approximately 30–60 seconds on a standard x86_64 or ARM64 host (or ~5–10 seconds using `python3 scripts/reproduce_quad_platform_analysis.py --quick`).

## Impact

The empirical findings from this benchmark establish practical bounds on agent orchestration overhead in local LLM deployments:
1. **Decoupled Orchestration Floor:** In cold prefill (Regime A), neural prompt ingestion dominates wall-clock time. In warm KV-cache execution (Regime B), client orchestration fraction $\Phi_{\text{orch}}$ accounts for **0.28% to 4.19%** of total task latency across 15-tool configurations on Apple M4, with task latency remaining within **-2.89% to +4.46%** of zero-middleware neural baselines.
2. **Unified Memory Bandwidth Dynamics:** Under the active-weights Roofline formulation ($S_{\text{active_weights}} = 1.688\text{ GB} + S_{\text{KV}}(N)$ over $\text{ITL}(N)$), observed token generation on Apple Silicon M4 reaches a median memory bandwidth of **102.4 GB/s** (85.3% of theoretical 120 GB/s peak, inter-trial range 99.0–108.5 GB/s), while naive calculation ($2.019\text{ GB} / \text{ITL}$) yields 100.8–117.3 GB/s.
3. **Tool Context Bloat and Dynamic RAG Mitigation:** Static schema loading (54 tools vs. 15 tools) inflates cold prompt evaluation latency by up to 87%. Dynamic Tool-RAG schema pruning ($54 \rightarrow \text{Top-}5$) achieves cold prefill speedups of 4.6x to 10.0x across platforms. In warm KV-cache execution (Regime B), where prefix caching absorbs static prompt tokens, Tool-RAG yields modest latency ratios of **0.93x to 1.09x** relative to the 15-tool minimal baseline on Apple M4 (1.07x in W2), demonstrating that dynamic tool pruning does not universally outperform static minimal schemas when prefix caching is active.
4. **Microarchitectural Counter Disparities:** Hardware PMU counters reveal dramatic disparities in instruction count: Go native executes 32.4M to 62.3M instructions per W2 transaction, whereas Node.js V8 requires 765M to 792M instructions (12.7x to 23.9x ratio) and CPython requires up to 2,654M instructions on Linux. On Windows, CPU cycle measurements via `QueryProcessCycleTime` demonstrate an 11.5x to 16.5x cycle advantage for Go native over enterprise Node.js.

## Limitations

Users and reviewers should interpret these results within documented external validity bounds:
1. **Model Scope:** Measurements use Llama-3.2-3B-Instruct (Q4_K_M). Larger models (8B–70B) exhibit higher neural latency, reducing $\Phi_{\text{orch}}$ further while leaving absolute orchestration overhead invariant.
2. **Hardware and Sensor Boundaries:** Power telemetry uses platform-native hardware interfaces: Apple SMC on-die shunt monitors (entire SoC), Intel RAPL MSR + NVIDIA NVML on Linux/Windows (CPU package + dGPU, excluding motherboard VRMs), and Win32 PSAPI user-mode counters on Intel HD Graphics 4600 (energy marked N/A** due to unprivileged user-mode execution on shared DDR3 memory). Energy and power comparisons are valid only within identical physical nodes.
3. **Thermal and Inter-Session Variance:** Ambient temperature and system state introduce inter-session variance. Detailed intra-trial throttling stratification on Linux is documented in `audit_export/linux_throttling_stratification.csv`, and inter-session directional drift across matched cells is documented in `audit_export/inter_session_drift_test.csv`.
4. **Single-Slot Protocol:** Regime B evaluates deterministic single-slot prefix caching (`-np 1`). Multi-tenant servers with interleaved contexts require RadixAttention or multi-slot allocation to sustain prefix reuse.

## Reproducibility Terminology and Standards

This repository operationalizes ACM/IEEE open-science reproducibility standards:
- **Repeatability (Same Team, Same Experimental Setup):** Verified via dual-session replication across all four hardware/OS platforms ($n=30$ trials per session, matching seeds, zero code modifications, documented in Table 7).
- **Replicability (Different Team, Same Experimental Setup):** Supported by complete self-contained raw trial data (35 `.jsonl` files), deterministic offline reproduction scripts (`scripts/reproduce_quad_platform_analysis.py`), and SHA-256 cryptographic manifests (`data/manifest_sha256.json`).
- **Reproducibility (Different Team, Different Experimental Setup):** Enabled by modular adapter interfaces (`benchmark/adapters/base.py`, ~35--90 lines of code) and cross-platform hardware telemetry backends (Apple SMC, Linux RAPL/NVML, Win32 PSAPI/NVML).

All numbers, tables, figures, and reports are recomputed directly from the 35 raw `.jsonl` files on disk without external network access or hardcoded values. Cryptographic integrity is verified by SHA-256 via `python3 scripts/verify_manifest.py`, and regression consistency is tested via `pytest -q` (recorded in `audit_export/pytest_output.txt`). Expected execution time is ~30-60 seconds.

For extended bilingual documentation (Portuguese / English), see [`docs/README_EXTENDED_BILINGUAL.md`](docs/README_EXTENDED_BILINGUAL.md).
