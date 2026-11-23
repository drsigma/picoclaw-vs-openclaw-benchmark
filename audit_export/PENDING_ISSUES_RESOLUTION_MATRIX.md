# PENDING_ISSUES_RESOLUTION_MATRIX.md
## Audit & Methodological Issue Resolution Matrix: [NR] vs. [RR] Classification
**Repository:** `picoclaw-vs-openclaw-benchmark` (branch `main`)  
**Commit Baseline:** Post-reconciliation V2 readiness  
**Date:** 2026-11-23  
**Audit Protocol:** Quad-Platform Systems Benchmarking Guidelines (Zero-Mock, Empirically Grounded, Venue-Neutral)

---

### Executive Classification Taxonomy
- **`[NR]` — Resolved without New Experimental Run:** Issue fully resolved in software engineering, mathematical formalization, contract definition, test coverage, gatekeeper automation, table/figure generation, or documentation from existing verified data.
- **`[RR]` — Requires Targeted Experimental Run / External Action:** Physical action required outside the local development turn (e.g., executing nightly `--full` confirmatory campaigns across the four testbeds, minting final Zenodo DOI upon release, or independent third-party execution in an external facility).

---

### Master Traceability Table

| # | Priority / Domain | Item & Requirement Description | Classification | Implemented Component / File | Verification Command & Evidence |
|---|---|---|:---:|---|---|
| **1.1** | **Priority 1: Reconciled Counts** | Eliminate all dataset count contradictions. Exactly 35 raw datasets, 18,616 total lines (records), 16,995 measured trials, and 1,621 warmups across quad-platform testbeds. | `[NR]` | `scripts/reproduce_quad_platform_analysis.py`, `paper/macros_quad_platform.tex`, `results/quad_platform_tables/macros_quad_platform.tex` | `pytest tests/test_no_hardcoded_metrics_or_mocks.py -k test_reconciled_35_datasets_counts` (Exit 0) |
| **1.2** | **Priority 1: Macro Generation** | Single source of truth dynamically generated from raw datasets without hardcoded 19,141 / 17,460 fallbacks. | `[NR]` | `scripts/reproduce_quad_platform_analysis.py:generate_quad_platform_macros_tex` | `pytest tests/test_artifact_consistency.py -k test_quad_platform_macros_consistency` (Exit 0) |
| **1.3** | **Priority 1: Manifest Count** | Synchronize cryptographic manifest tracking all 302 tracked files with 0 hash mismatches and 0 missing files. | `[NR]` | `data/manifest_sha256.json`, `scripts/verify_manifest.py` | `python3 scripts/verify_manifest.py --pre-flight` (302/302 valid, Exit 0) |
| **2.1** | **Priority 2: W2 Tokens Definition** | Formally define and standardize official W2 tokens: minimal (15 tools) = 2,177 prompt tokens; bloated (54 tools) = 7,091 prompt tokens; Tool-RAG (top-5) = 917 prompt tokens; completion = 30 tokens ($\pm 5\%$). | `[NR]` | `benchmark/workload_contracts.py:WORKLOAD_CONTRACTS`, `protocol/protocol_v2.0.json` | `pytest tests/test_no_hardcoded_metrics_or_mocks.py -k test_w2_token_variants_exact_definitions` (Exit 0) |
| **2.2** | **Priority 2: W2 Contract Enforcement** | Enforce exact token validation per arm and tool mode, rejecting deviations or truncated schemas. | `[NR]` | `benchmark/workload_contracts.py:audit_cell_trial` | `pytest tests/test_protocol_v2_and_contracts.py` (Exit 0) |
| **3.1** | **Priority 3: Remove Permissive Defaults** | Eliminate hardcoded multipliers (`* 0.85` in energy calculation) and permissive silent exceptions (`except Exception: pass`). | `[NR]` | `src/telemetry_backend.py:slice_energy`, `read_cpu_energy_uj`, `read_nvidia_power_w` | `pytest tests/test_no_hardcoded_metrics_or_mocks.py -k test_no_hardcoded_energy_fraction_or_permissive_defaults` (Exit 0) |
| **3.2** | **Priority 3: Fail-Fast Telemetry** | Replace silent zeros with explicit `None` / `"N/A"` when hardware sensors are uninstrumented or fail. | `[NR]` | `src/telemetry_backend.py`, telemetry adapters | Tested in multiplatform telemetry tests (Exit 0) |
| **4.1** | **Priority 4: 35-Dataset Gatekeeper** | Expand automated gatekeeper to scan and audit all 35 historical `.jsonl` files (18,616 records) rather than only 7 Darwin files. | `[NR]` | `scripts/audit_submission_gatekeeper.py:run_gatekeeper_suite` | `python3 scripts/audit_submission_gatekeeper.py` (35/35 datasets compliant, 18,616 records, Exit 0) |
| **4.2** | **Priority 4: Gatekeeper Certificate** | Emit consolidated cryptographic audit certificate for all 35 datasets and mirror to audit export. | `[NR]` | `data/gatekeeper_audit_certificate.json`, `audit_export/gatekeeper_35_jsonl_audit.json` | `pytest tests/test_artifact_consistency.py -k test_gatekeeper_audit_certificate_verified` (Exit 0) |
| **5.1** | **Priority 5: Independent Protocol** | Provide deterministic, step-by-step instructions for independent third-party reproduction in `docs/REPRODUCIBILITY_INDEPENDENT.md` and `REPRODUCIBILITY.md`. | `[NR]` | `docs/REPRODUCIBILITY_INDEPENDENT.md`, `REPRODUCIBILITY.md` | Verified clean documentation without personal paths |
| **5.2** | **Priority 5: Independent Evaluation** | External execution by independent third-party team in external laboratory without author intervention. | `[RR]` | External research facilities / third-party reviewers | `[ ] PENDENTE EXECUÇÃO POR TERCEIRO INDEPENDENTE` |
| **6.1** | **Priority 6: Tables & Figures Regeneration** | Regenerate publication Tables 1–8 in Markdown and LaTeX, high-resolution Figures 1–6 in 300 DPI, and replication reports. | `[NR]` | `scripts/reproduce_quad_platform_analysis.py`, `scripts/generate_audit_txt_chunks.py` | `python3 scripts/reproduce_quad_platform_analysis.py --quick` (Exit 0) |
| **6.2** | **Priority 6: Diagnostic CSVs** | Regenerate stationarity, TOST power, MBB coverage, Linux throttling stratification, and drift CSVs. | `[NR]` | `audit_export/mbb_coverage_and_tost_power.csv`, `inter_session_drift_test.csv`, `linux_throttling_stratification.csv`, `w5_token_and_schema_audit.csv` | Verified on disk and matched against LaTeX tables |
| **7.1** | **Priority 7: DOI Standardization** | Centralize permanent release identifier as `10.5281/zenodo.PENDING_RELEASE` across CITATION.cff, README.md, and manuscript without fabricated DOIs. | `[NR]` | `CITATION.cff`, `README.md`, `paper/manuscript.tex` | Checked via text search: zero invented DOIs |
| **7.2** | **Priority 7: Zenodo Release Minting** | Create official GitHub Release tag and mint permanent Zenodo DOI upon publication acceptance. | `[RR]` | Author GitHub release & Zenodo deposit | `[ ] PENDENTE AÇÃO EXTERNA DO AUTOR (Aguardando publicação)` |
| **8.1** | **Workload Contracts & Schemas** | Standardize token bounds and expected tool call sequences across all workloads W1–W5. | `[NR]` | `benchmark/workload_contracts.py:WORKLOAD_CONTRACTS` | `pytest tests/test_protocol_v2_and_contracts.py` (Exit 0) |
| **8.2** | **Tool Order & Prompt Hash Traceability** | Contract specifies canonical prompt SHA-256 hashes and expected tool dispatch sequences. Existing historical JSONL validated for tool count/call presence; per-trial prompt hash and ordered call arrays logged for all new collections. | `[NR]` / `[RR]` | `benchmark/workload_contracts.py`, `scripts/audit_submission_gatekeeper.py` | Contracts define hashes; gatekeeper verifies compliance |
| **8.3** | **Thermal & Energy Disparities** | Document sensor boundaries: full-package UMA shunt (SMC) on M4; CPU RAPL + dGPU NVML on Linux/Windows x86_64; user-mode explicit N/A on Windows Intel iGPU. Linux thermal stratification confirmed: $0.0^\circ\text{C}$ median package temp delta, $-0.17\%$ median latency elongation. | `[NR]` | `docs/TELEMETRY_ARCHITECTURE.md`, `audit_export/linux_throttling_stratification.csv` | Documented in Systems Replication Report and manuscript |
| **8.4** | **W5 LangChain Segregation** | Segregate confounded `python_native` W5 (prompt truncation / schema failure) to Table 8 Part B footnote ($\P$); exclude from Tables 2 and 7 latency/energy contrasts. | `[NR]` | `scripts/reproduce_quad_platform_analysis.py`, Table 8 | `pytest tests/test_statistical_engine.py -k test_w5_python_native_segregation` (Exit 0) |
| **8.5** | **W5 Python Native Re-Collection** | Optional targeted re-execution of corrected `W5_langchain_real_world/agent.py` under full 30-rep confirmatory regime. | `[RR]` | `scripts/run_linux_x86_64_master_campaign.py`, `scripts/run_darwin_campaign.sh` | To be executed during overnight confirmatory run |
| **8.6** | **Quad-Platform Confirmatory Campaign** | Full 30-rep confirmatory dual-session execution with counterbalanced block inversion (`--invert-blocks`) on all 4 physical machines. | `[RR]` | Master runners across platforms | Planned overnight run (`--full`) writing to `data/campaign_v2/` |

---

### Detailed Analysis of Priority Items

#### 1. Reconciliation of Counts & Invariants
- **Historical Raw Datasets:** Exactly **35 `.jsonl` files** across the four platforms:
  * Apple Silicon M4 (Node 1): 7 campaign files in `results/publication_campaign/` + 2 cross-platform files in `data/` (`mcp_live_transport_trials.jsonl`, `external_framework_langchain_trials.jsonl`) = **9 datasets**.
  * Linux x86_64 Ubuntu (Node 2): 5 datasets in Session 1 + 5 datasets in Session 2 = **10 datasets**.
  * Windows 11 NVIDIA (Node 3): 5 datasets in Session 1 + 5 datasets in Session 2 = **10 datasets**.
  * Windows 10 Intel HD Graphics 4600 (Node 4): 3 datasets in Session 1 + 3 datasets in Session 2 = **6 datasets**.
  * **Grand Total:** $9 + 10 + 10 + 6 = \mathbf{35\text{ datasets}}$.
- **Total Records & Trials:**
  * Total JSONL rows (records): **18,616**.
  * Total measured (non-warmup) evaluations: **16,995**.
  * Total discarded warmup evaluations: **1,621**.
  * Verification: $16{,}995 + 1{,}621 = 18{,}616$.
- **Manifest:** All 302 tracked files match their cryptographic SHA-256 signatures in `data/manifest_sha256.json`.

#### 2. W2 Token Parity & Tool-RAG Standardization
- Standardized across `benchmark/workload_contracts.py` and `protocol/protocol_v2.0.json`:
  * **Minimal Schema (15 tools):** 2,177 prompt tokens, 30 completion tokens ($\pm 5\%$).
  * **Bloated Schema (54 tools):** 7,091 prompt tokens, 30 completion tokens ($\pm 5\%$).
  * **Tool-RAG Schema (Top-5 tools):** 917 prompt tokens, 30 completion tokens ($\pm 5\%$).
- Protocol V2 SHA-256 hash recalculated and frozen: `717e550e7c976a35c9d7af4c5ce85cb967ebf0f7f15f4bfd8c6f81dcb3250358`.

#### 3. Telemetry Backend Hardening
- Eliminated artificial scaling factor `tot_j * 0.85` in `src/telemetry_backend.py`.
- Replaced permissive zero returns with explicit `None` when RAPL or NVML sensors are inaccessible.
- Automated regression test `test_no_hardcoded_energy_fraction_or_permissive_defaults` guards against permissive fallbacks.

#### 4. Gatekeeper Expansion over 35 Datasets
- `scripts/audit_submission_gatekeeper.py` now scans all 35 datasets dynamically via `audit_raw_datasets()`.
- Micro-benchmark transport ablations (MCP live IPC) properly recognized without spurious LLM token requirements.
- Full certificate issued: `data/gatekeeper_audit_certificate.json` (35 datasets, 18,616 records, 0 violations).

---

### Conclusion & Overnight Execution Readiness
All `[NR]` items have been programmatically resolved, mathematically aligned, and verified via automated tests. The repository is fully shielded and ready for scheduled overnight physical runs (`[RR]`), which will deposit clean confirmatory data into `data/campaign_v2/` without touching historical records.
