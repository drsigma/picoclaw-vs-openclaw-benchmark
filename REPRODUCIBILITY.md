# Reproducibility Guide: Quad-Platform Empirical Systems Evaluation

This document provides complete, deterministic instructions for independently reproducing, auditing, and validating all experimental results, statistical tests, and publication artifacts for the **PicoClaw vs. OpenClaw** benchmark suite across **four distinct physical hardware platforms**.

---

## 1. Hardware Testbed Specifications

| Profile | Platform / OS | CPU & Memory | GPU & Telemetry Domain | Baseline Idle Power ($P_{\text{idle}}$) |
| :--- | :--- | :--- | :--- | :--- |
| **Node 1** | **macOS 26.6.2** (Darwin ARM64) | Apple M4 (4P + 6E), 24 GB Unified LPDDR5X (120 GB/s) | 10-Core Metal 3 (UMA, on-die), Apple SMC `powermetrics` | $1.20\text{ W}$ |
| **Node 2** | **Ubuntu 26.04 LTS** (Linux 7.0 x86_64) | Intel Core i5-12500H (16T), 30.5 GiB DDR5-4800 | NVIDIA RTX 3050 Laptop (4 GB GDDR6), Intel RAPL + NVML | $19.71\text{ W}$ / $20.08\text{ W}$ |
| **Node 3** | **Windows 11 Pro** (Build 26200 x86_64) | Intel Core i5-12500H (16T), 31.7 GiB DDR5-4800 | NVIDIA RTX 3050 Laptop (4 GB GDDR6), Intel MSR RAPL + NVML DLL | $24.13\text{ W}$ / $21.96\text{ W}$ |
| **Node 4** | **Windows 10 Pro** (Build 19045 x86_64) | Intel Core i7-4790K @ 4.0 GHz (4C/8T), 16 GB DDR3 | Intel HD Graphics 4600 (UMA Shared RAM), Win32 PSAPI (user-mode) | $28.50\text{ W}$ (Host-only) |

> **Technical Note on Sensor Domains and User-Mode Constraints:**  
> - On Apple M4, electrical shunts instrument the full SoC package (CPU + GPU + DRAM).  
> - On Linux and Windows NVIDIA, sensors capture CPU Package (RAPL/MSR) and discrete GPU board (NVML), excluding motherboard VRMs.  
> - On Windows Intel Graphics, host package energy and discrete VRAM are marked `N/A**` because execution operates in unprivileged user-mode without kernel MSR RAPL or NVML drivers. Never substitute `0` for uninstrumented sensors.

---

## 2. Reviewer Fast Verification (< 10 seconds, No GPU/Sudo Required)

For peer reviewers or systems without local LLM weights or GPU hardware, the test suite and simulated execution dry-run validate all protocol invariants, schema parsing, and statistical calculation pipelines:

```bash
# 1. Activate isolated Python environment
python3 -m venv .venv_repro
source .venv_repro/bin/activate
pip install -r requirements.txt

# 2. Execute automated test suite (51 tests)
pytest -q

# 3. Execute portable simulation dry-run
make dry-run
```

---

## 3. Native Execution Across the Four Physical Nodes

### Node 1: Apple Silicon M4 (macOS Darwin ARM64)
```bash
# Setup dependencies and environment
make setup

# User-space physical execution (graceful degradation)
make benchmark

# Full physical electrical telemetry via Apple SMC (requires sudo)
make benchmark-full-smc

# Regenerate figures
make reproduce-figures
```

### Node 2: Linux x86_64 (Ubuntu 26.04 with NVIDIA dGPU)
```bash
# Automated gold campaign with Intel RAPL MSR and NVIDIA NVML telemetry
sudo bash reproduce_linux_gold.sh

# Or direct invocation via master campaign script
python scripts/run_linux_x86_64_master_campaign.py --ngl 16 --reps 30
```

### Node 3: Windows 11 x86_64 (NVIDIA dGPU)
```powershell
# Open PowerShell 7+ as Administrator
.\windows_gold.ps1 -Reps 30 -Ngl 16

# Or direct invocation via master script
python scripts\run_windows_x86_64_master_campaign.py --ngl 16 --reps 30
```

### Node 4: Windows 10/11 x86_64 (Intel HD Graphics 4600 iGPU UMA)
```powershell
# Launch automated campaign with sentinel monitor and Win32 PSAPI telemetry
powershell -ExecutionPolicy Bypass -File .\launch_sentinel_intel_win.ps1
```

### Enterprise Workload W5 (LangChain + SQLite + LLM-as-a-Judge)
```bash
# Run a standalone W5 trial (Warm or Cold regime) against local llama-server
python -m W5_langchain_real_world.agent Warm
python -m W5_langchain_real_world.agent Cold
```
*(Multi-trial W5 blocks across all runtimes are orchestrated automatically by `scripts/run_linux_x86_64_master_campaign.py`, `scripts/run_windows_x86_64_master_campaign.py`, and `adapters/windows_intel_graphics/w5_intel_worker.py`.)*

---

## 4. Master Quad-Platform Consolidation Pipeline

All 35 raw empirical `.jsonl` datasets on disk reside under the exact paths listed in Section 3 of `AUDIT_REPORT_FINAL.md`:
- `results/publication_campaign/` (7 files) and `data/` (2 files) — macOS ARM64 M4 Sessions 1 & 2: `results/publication_campaign/{raw_trials,warm_cache_trials,inter_session_trials,kv_cache_thrashing_trials,tool_rag_mitigation_trials,prefill_ablation,uma_energy_bandwidth_trials}.jsonl` plus `data/mcp_live_transport_trials.jsonl` and `data/external_framework_langchain_trials.jsonl`
- `data/linux_x86_64_session1/raw/` and `data/linux_x86_64_session2/raw/` (10 files: `raw_trials.jsonl`, `warm_cache_trials.jsonl`, `kv_cache_thrashing_trials.jsonl`, `mcp_live_transport_trials.jsonl`, `tool_rag_mitigation_trials.jsonl` per session)
- `data/windows_x86_64_session1/raw/` and `data/windows_x86_64_session2/raw/` (10 files: same 5-file campaign structure per session)
- `data/windows_intel_graphics_session1/raw/` and `data/windows_intel_graphics_session2/raw/` (6 files: `raw_trials.jsonl`, `warm_cache_trials.jsonl`, `tool_rag_mitigation_trials.jsonl` per session)

To recalculate 100% of empirical metrics from these 35 raw `.jsonl` datasets, execute hypothesis testing, compute Moving Block Bootstrap confidence intervals, regenerate Tables 1–8 and all 6 figures at 300 DPI, export plain-text chunks, and verify tests and SHA-256 hashes:

```bash
python scripts/reproduce_quad_platform_analysis.py
python scripts/generate_audit_txt_chunks.py
pytest -q
python scripts/verify_manifest.py
```

The master pipeline (`scripts/reproduce_quad_platform_analysis.py`) executes four phases:
1. **Phase 1: Commit & Dataset Auditing:** Scans all **35 raw `.jsonl` files** on disk and computes line counts, measured vs. warmup trial counts, workloads, and SHA-256 checksums.
2. **Phase 2: Telemetry & Drift Diagnostics:** Evaluates lag-1 serial autocorrelation ($r_1$), effective sample size ($n_{\text{eff}}$), OLS linear regression drift with Holm-Bonferroni FWER control, and NVML/MSR thermal throttle registers across **190 experimental cells**.
3. **Phase 3: Statistical Consolidation:** Computes empirical medians, IQRs, Moving Block Bootstrap 95% CIs ($b=3$), Kruskal-Wallis omnibus tests, Mann-Whitney $U$, Cliff's $\delta$, Vargha-Delaney $A_{12}$, and dual-session TOST equivalence tests (`ttost_ind`).
4. **Phase 4: Dynamic Artifact Generation:**
   - Tables 1–8 in Markdown and LaTeX format in `audit_export/tables/` and `results/quad_platform_tables/`.
   - Figures 1–6 in 300 DPI PNG (100% English) in `figures/` and `audit_export/figures/`.
   - Dynamic systems replication report (`audit_export/Systems_Replication_Report.md`) and synchronized audit report (`AUDIT_REPORT_FINAL.md`).
   - Consolidated audit archive `audit_export_quad_platform.zip`.

---

## 5. Methodological Design Rationale & Core Script Architecture

### Why Each Methodological Choice Was Made
- **KV-Cache Slot Isolation (`T1`, `T2`, `T3`):** Uncontrolled concurrent requests evict prefix KV blocks (`T2`), causing quadratic prompt re-prefill. Comparing `T2` against block-isolated slot allocation (`T3`) quantifies attention eviction penalties separately from client runtime overhead (Kwon et al., 2023).
- **Moving Block Bootstrap ($b=3$) & Effective Sample Size ($n_{\text{eff}}$):** Under Regime B (warm cache), OS standby page caching and loopback TCP cadence can induce lag-1 serial dependence ($|r_1| > 2/\sqrt{n}$). Computing $n_{\text{eff}}$ and applying Moving Block Bootstrap (Künsch, 1989) preserves short-range temporal correlation when estimating 95% confidence intervals for medians.
- **Dual-Session Block-Bootstrap TOST of Contrasts ($\Delta T_{\text{orch}}$):** Conventional null-hypothesis tests cannot prove cross-session replicability. Moving Block Bootstrap ($b=3$, $B=5{,}000$) Two One-Sided Tests (Schuirmann, 1987; Lakens, 2017) formally test whether inter-session differences in $\Delta T_{\text{orch}} = T_{\text{orch}}(\text{Runtime}) - T_{\text{orch}}(\text{PicoClaw})$ fall inside a fixed, pre-specified data-independent SESOI ($\Delta_{\text{SESOI}} = \pm 5.0\text{ ms}$), with exact order-statistic 90% CIs mathematically aligned to $\alpha = 0.05$ under the standardized 3-state rule (`Equivalent`, `Different`, `Inconclusive`).
- **Cross-ISA Hardware Counter Segregation:** Raw retired instruction counts are not commensurable between ARM64 (RISC) and x86_64 (CISC) due to instruction density and micro-op expansion (Weaver et al., 2013). Counters are segregated by ISA and compared via within-node ratios; on Windows, where `CR4.PCE` restricts user-mode PMU instructions, Win32 `QueryProcessCycleTime` records process CPU cycles directly without synthetic IPC extrapolation.

### Architecture of Core Scripts
- **`scripts/reproduce_quad_platform_analysis.py`:** Master zero-hardcode consolidation pipeline covering raw JSONL ingestion, stationarity/drift diagnostics, non-parametric hypothesis tests, Markdown/LaTeX table generation, 300 DPI plotting, dynamic report generation, and ZIP packaging.
- **`scripts/verify_manifest.py`:** Streaming 64 KB SHA-256 verifier checking every tracked raw dataset, script, figure, and table against `data/manifest_sha256.json` (`--update` refreshes hashes after verified runs).
- **`benchmark/adapters/` & `adapters/windows_intel_graphics/`:** Strategy/Adapter layer (`AgentOrchestratorAdapter`) isolating runtime engines (Go, Node.js, CPython, Bun, LangChain) and OS-native telemetry hooks (Apple SMC/`libproc`, Linux RAPL/NVML/`perf_event_open`, Windows MSR/NVML/Win32 PSAPI) from the benchmark harness.
- **`scripts/generate_audit_txt_chunks.py`:** Slices consolidated reports, Tables 1–8, and CSV diagnostics into portable plain-text chunks ($\le 150\text{ KB}$ each) under `audit_txt_chunks/` with explicit source headers.

---

## 6. Cryptographic Manifest Verification

To cryptographically audit that all active raw datasets, configuration manifests, and scripts match their expected SHA-256 signatures:

```bash
python scripts/verify_manifest.py
```

To update the cryptographic manifest following new verified physical runs:

```bash
python scripts/verify_manifest.py --update
```
