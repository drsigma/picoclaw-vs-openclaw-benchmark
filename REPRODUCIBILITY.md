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
# Run real-world enterprise multi-step tool workload W5
python -m W5_langchain_real_world.w5_runner --workload W5 --reps 30
```

---

## 4. Master Quad-Platform Consolidation Pipeline

To recalculate 100% of empirical metrics from raw `.jsonl` datasets, execute hypothesis testing, compute moving-block bootstrap confidence intervals, and regenerate all publication tables and 300 DPI figures:

```bash
python scripts/reproduce_quad_platform_analysis.py
```

This single command executes the following phases:
1. **Phase 1: Commit & Dataset Auditing:** Computes SHA-256 for all 31 raw `.jsonl` files.
2. **Phase 2: Telemetry & Drift Diagnostics:** Evaluates serial dependence ($r_1$, $n_{\text{eff}}$), linear regression drift with Holm-Bonferroni control, and thermal slowdown masks across 178 experimental cells.
3. **Phase 3: Statistical Consolidation:** Aggregates medians, IQRs, moving-block bootstrap 95% CIs ($b=3$), Kruskal-Wallis omnibus tests, Mann-Whitney $U$, Cliff's $\delta$, Vargha-Delaney $A_{12}$, and dual-session TOST equivalence tests.
4. **Phase 4: Publication Artifact Generation:**
   - Tables 1–8 in Markdown and LaTeX format in `audit_export/tables/` and `results/tri_platform_tables/`.
   - Figures 1–6 in 300 DPI PNG in `figures/` and `audit_export/figures/`.
   - Comprehensive systems replication report in `audit_export/Systems_Replication_Report.md`.
   - Consolidated audit packages `audit_export_quad_platform.zip` and `audit_export_tri_platform.zip`.

---

## 5. Cryptographic Manifest Verification

To cryptographically audit that all active raw datasets, configuration manifests, and scripts match their expected SHA-256 signatures:

```bash
python scripts/verify_manifest.py
```

To update the cryptographic manifest following new verified physical runs:

```bash
python scripts/verify_manifest.py --update
```
