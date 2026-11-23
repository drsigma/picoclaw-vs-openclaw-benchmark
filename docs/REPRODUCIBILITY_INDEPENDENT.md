# Independent Third-Party Reproducibility Protocol

This document provides a comprehensive, step-by-step protocol enabling an independent reviewer, systems researcher, or evaluator to verify, inspect, test, and reproduce all empirical findings, statistical analyses, and software artifacts contained in this repository.

---

## 1. Prerequisites and Environment Setup

### 1.1 Cloning the Repository
```bash
git clone https://github.com/drsigma/picoclaw-vs-openclaw-benchmark.git
cd picoclaw-vs-openclaw-benchmark
```

### 1.2 Python Environment Setup
We recommend Python 3.10+ (tested on Python 3.11, 3.12, 3.13, and 3.14):
```bash
python3 -m venv .venv_repro
source .venv_repro/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.3 Verifying Pre-Flight Manifest & Cryptographic Integrity
Verify that all 302 repository source files, datasets, and scripts match their recorded SHA-256 digests and have correct execution permissions:
```bash
python3 scripts/verify_manifest.py --pre-flight
```
Expected output:
```text
All files validated successfully against manifest.
Exit code: 0
```

---

## 2. Fast Verification (Smoke Tests & Automated Test Suite)

### 2.1 Running Automated Unit & Regression Tests
Run the comprehensive pytest suite covering protocol freeze, workload contracts, adapter interfaces, statistical tests, and gatekeeper integrity:
```bash
pytest -v
```
Expected output:
```text
All tests passed (exit code 0).
```

### 2.2 Dry-Run Matrix Verification
Verify execution matrices, parameter validation, and environment manifest recording without running full hardware inference:

- **Linux x86_64:**
  ```bash
  python3 scripts/run_linux_x86_64_master_campaign.py --dry-run
  python3 scripts/run_linux_x86_64_master_campaign.py --dry-run --invert-blocks
  ```
- **Windows x86_64 (NVIDIA):**
  ```bash
  python3 scripts/run_windows_x86_64_master_campaign.py --dry-run
  ```
- **macOS ARM64 (Apple Silicon):**
  ```bash
  python3 benchmark/run_unified_benchmark.py --dry-run
  ```
- **Windows Intel HD Graphics iGPU:**
  ```bash
  python3 adapters/windows_intel_graphics/runner.py --dry-run
  ```

---

## 3. Full Statistical Re-Execution from Raw Data

Independent reviewers can reproduce 100% of the statistical analyses, tables, figures, hypothesis tests, and LaTeX macros directly from the 35 raw empirical `.jsonl` files (19,141 recorded lines, 17,460 measured trials, 0 synthetic records):

### 3.1 Fast Verification Mode (Reduced Bootstrap Resamples)
```bash
python3 scripts/reproduce_quad_platform_analysis.py --quick
```
This generates:
- Publication Tables 1–8 in Markdown (`audit_export/tables/`) and LaTeX (`results/quad_platform_tables/`)
- Publication Figures 1–6 in 300 DPI PNG (`figures/` and `audit_export/figures/`)
- Statistical report: `audit_export/Systems_Replication_Report.md`
- LaTeX macros: `paper/macros_quad_platform.tex`

### 3.2 Full Bootstrap Mode (2,000 Resamples, B=10,000 TOST)
```bash
python3 scripts/reproduce_quad_platform_analysis.py
```

### 3.3 Re-Analysis on Custom or New Campaigns
Reviewers executing new campaigns in custom directories can point the analysis script to any raw data directory using `--data-dir`:
```bash
python3 scripts/reproduce_quad_platform_analysis.py --data-dir data/campaign_v2 --quick
```

---

## 4. Running a New Confirmatory Campaign Locally

To execute a live hardware benchmark campaign on your own machine:

### 4.1 Launching Local Inference Server (`llama-server`)
Download the standardized model checkpoint (`Meta-Llama-3.2-3B-Instruct-Q4_K_M.gguf`) into `models/` and launch `llama-server`:
```bash
llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 32768 \
  -np 1 \
  --temp 0.0 \
  --seed 42 \
  --port 8080
```

### 4.2 Executing Confirmatory Sessions
Select your target platform script:

- **Linux:**
  ```bash
  ./scripts/run_linux_campaign.sh --smoke-test   # 1 rep fast verification
  ./scripts/run_linux_campaign.sh --quick        # 5 reps quick evaluation
  ./scripts/run_linux_campaign.sh --full         # 30 reps full confirmatory replication
  ```
- **macOS:**
  ```bash
  ./scripts/run_darwin_campaign.sh --smoke-test
  ./scripts/run_darwin_campaign.sh --full
  ```
- **Windows:**
  ```powershell
  .\scripts\run_windows_campaign.ps1 -Mode smoke-test
  .\scripts\run_windows_campaign.ps1 -Mode full
  ```

All raw outputs will be stored in isolated directories under `data/campaign_v2/` without overwriting historical benchmarks.
