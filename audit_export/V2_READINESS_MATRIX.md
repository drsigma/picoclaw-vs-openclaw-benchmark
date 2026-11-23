# Master V2 Campaign Readiness & Traceability Matrix (Phases 0 to 8)

This matrix maps all 42 methodological, software engineering, telemetry, and statistical requirements established for the execution of overnight confirmatory benchmark campaigns across the 4 physical platforms.

---

## Complete Traceability Matrix of All 42 Items

| ID | Phase & Requirement | Status | Implemented File / Function / Flag | Verification Evidence & Command |
| :---: | :--- | :---: | :--- | :--- |
| **0.1** | **Immutable Protocol Versioning:** Frozen specification v2.0.0 with SHA-256 validation. | `[x]` | `protocol/protocol_v2.0.json`, `benchmark/protocol_freeze.py` | `python3 benchmark/protocol_freeze.py --check-hash 2aef611c7b...` (Exit 0) |
| **0.2** | **Hypotheses Separation:** Formal separation of confirmatory ($H_1$–$H_4$) from exploratory analyses ($A_1$–$A_4$). | `[x]` | `protocol/protocol_v2.0.json`, `docs/PROTOCOL_V2.md` | `pytest tests/test_protocol_v2_and_contracts.py` (Exit 0) |
| **0.3** | **Statistical Unit Definition:** Fixed cell `platform × workload × regime × runtime × session`, eliminating spurious pairing by random `rep`. | `[x]` | `docs/PROTOCOL_V2.md`, `scripts/reproduce_quad_platform_analysis.py` | `pytest tests/test_statistical_engine.py` (Exit 0) |
| **1.1** | **Repository Completeness:** Integrity of `benchmark/`, `src/`, `tests/`, `scripts/`, `docs/`, `protocol/`. | `[x]` | Repository root tree | `python3 scripts/verify_manifest.py --pre-flight` (All 302 files valid) |
| **1.2** | **Strict Manifest Failure:** Pre-flight validation returning non-zero exit code on missing file or hash divergence. | `[x]` | `scripts/verify_manifest.py --pre-flight` | Verified with exit code 1 on missing permissions; passes on clean repo |
| **1.3** | **Automated Gatekeeper:** Validates JSONL schema, positive tokens, finish reasons, HTTP 200, timing plausibility ($T_{\text{task}} \ge T_{\text{neural}}$). | `[x]` | `scripts/audit_submission_gatekeeper.py` | `python3 scripts/audit_submission_gatekeeper.py` (4,269/4,269 records certified) |
| **1.4** | **Execution Modes:** Standardized `--smoke-test`, `--quick`, `--full`, `--dry-run`, `--resume`, `--invert-blocks` across all runners. | `[x]` | `scripts/run_linux_x86_64_master_campaign.py`, `scripts/run_windows_x86_64_master_campaign.py`, `benchmark/run_unified_benchmark.py`, `adapters/windows_intel_graphics/runner.py` | `pytest tests/test_campaign_execution_modes.py` (All dry-runs pass exit 0) |
| **1.5** | **Real-Time Progress & Flush:** Real-time logging (`flush=True`), atomic checkpointing (`os.fsync()`), fail-fast `sys.exit(1)`. | `[x]` | Master runners across all 4 platforms | Verified in live executions and `--dry-run` |
| **2.1** | **Workload Contracts (W1–W5):** Immutable prompt text, SHA-256 digests, expected tokens, and tool sequences. | `[x]` | `benchmark/workload_contracts.py` | `pytest tests/test_protocol_v2_and_contracts.py` (Exit 0) |
| **2.2** | **Pre/Post Cell Token Audit:** Fail-fast cell validation aborting on token parity or schema breach. | `[x]` | `benchmark/workload_contracts.py:audit_cell_trial`, `audit_cell_batch` | Tested with bad records; rejects violations |
| **2.3** | **W5 Python Native Correction:** Measured $T_{\text{task}}$ prior to LLM-judge; eliminated prompt truncation and simulated fallbacks. | `[x]` | `W5_langchain_real_world/agent.py`, `benchmark/python_orch.py` | `pytest tests/test_no_hardcoded_metrics_or_mocks.py` (Exit 0) |
| **2.4** | **W5 Failure & Version Policy:** Strict segregation between legacy data (M1 exclusion) and new canonical campaigns. | `[x]` | `benchmark/workload_contracts.py`, `scripts/reproduce_quad_platform_analysis.py` | Table 8 segregation verified in pytest |
| **2.5** | **Tool-RAG, MCP & KV-Cache (T1/T2/T3):** End-to-end ablation stages with internal baselines. | `[x]` | Master runners (`stage_tool_rag`, `stage_kv`, `stage_mcp`) | `pytest tests/test_artifact_consistency.py` (Exit 0) |
| **3.1** | **Counterbalanced Session Design:** Session 1 (canonical) vs Session 2 (counterbalanced order) with thermal & load monitoring. | `[x]` | All campaign runners and shell/PowerShell wrappers | Verified via `--invert-blocks` flag |
| **3.2** | **Inverted Block Order:** `--invert-blocks` CLI flag systematically reversing execution blocks. | `[x]` | All 4 master runners | `pytest tests/test_campaign_execution_modes.py` (Exit 0) |
| **3.3** | **Thermal Quiescence & Cooldown:** Pre-trial thermal gate, inter-session cooldown, drop_caches, and governor logging. | `[x]` | `thermal_gate()`, `check_and_cooldown()`, campaign shell wrappers | Verified in Linux, Windows, and Darwin runners |
| **3.4** | **Sample Size Justification:** Formal power calculation and pre-registration of $n=30$, 2 sessions, 5 workloads. | `[x]` | `docs/PROTOCOL_V2.md`, `protocol/protocol_v2.0.json` | Protocol specification verified |
| **3.5** | **Reproducible Block Size ($b$):** Selection rule $b = \text{round}(n^{1/3}) = 3$ with sensitivity across $b \in \{2, 3, 5, 8, 12, \text{adaptive}\}$. | `[x]` | `scripts/reproduce_quad_platform_analysis.py`, `audit_export/tost_block_sensitivity.csv` | Decisions invariant across $b \in \{2, 3, 5\}$ |
| **4.1** | **Session Environment Manifest:** Atomic `environment_manifest.json` recording CPU, RAM, power source, governor, runtimes. | `[x]` | `benchmark/environment_manifest.py` | `pytest tests/test_campaign_execution_modes.py` (Exit 0) |
| **4.2** | **Execution Wrappers (Non-Promotional):** Clean scripts (`run_linux_campaign.sh`, `run_windows_campaign.ps1`, `run_darwin_campaign.sh`). | `[x]` | `scripts/run_linux_campaign.sh`, `scripts/run_windows_campaign.ps1`, `scripts/run_darwin_campaign.sh` | Verified via `./scripts/run_linux_campaign.sh --dry-run` |
| **4.3** | **Hardware Telemetry Documentation:** Explicit boundary documentation for SMC, RAPL, NVML, and Win32 PSAPI. | `[x]` | `docs/TELEMETRY_ARCHITECTURE.md` | Documented and verified in gatekeeper |
| **4.4** | **Hardware Throttling Verification:** Tracking `cpu_pkg_throttle_events` and GPU throttle bitmasks without spurious causal $r_1$ inference. | `[x]` | `thermal_fields()`, `audit_export/linux_throttling_stratification.csv` | Verified in replication report |
| **4.5** | **Explicit-Null Telemetry Integrity:** Restricted counters recorded explicitly as `null` / `"N/A"` without synthetic fabrication. | `[x]` | Telemetry adapters across all platforms | `pytest tests/test_no_hardcoded_metrics_or_mocks.py` (Exit 0) |
| **5.1** | **Additive Latency Model:** Enforcement: $T_{\text{task}} = T_{\text{neural}} + T_{\text{orch}}$ ($T_{\text{orch}} \ge 0$). | `[x]` | Workload contracts, gatekeeper, all adapters | `pytest tests/test_protocol_v2_and_contracts.py` (Exit 0) |
| **5.2** | **Concrete Runtime Analysis:** Analysis focused on Go runtime, Bun JSC, and Node.js V8 rather than generic "compiled vs JIT". | `[x]` | `docs/PROTOCOL_V2.md`, `README.md`, manuscript | Verified in neutral documentation |
| **5.3** | **Instruction Metrics Demarcation:** PMC / cycles treated explicitly as secondary microarchitectural cost, not latency substitute. | `[x]` | Reports and manuscript | Verified across Table 1 and Table 2 |
| **5.4** | **Analytical Roofline UMA Bandwidth:** Declared as active-weight analytical bound rather than physical LPDDR5X bus counter. | `[x]` | `audit_submission_gatekeeper.py`, `README.md` | Verified in gatekeeper certification |
| **5.5** | **Pre-Registered Exclusion Criteria:** Explicit objective criteria: HTTP != 200, length truncation, schema divergence, severe throttle, warmups. | `[x]` | `protocol/protocol_v2.0.json`, `docs/PROTOCOL_V2.md` | Invariant checks in gatekeeper |
| **6.1** | **Unique Trial Identifiers:** `trial_id`, `run_id`, `session_id`, `git_commit`, timestamp, block index, seed in all records. | `[x]` | Master runners across platforms | Schema verified in gatekeeper |
| **6.2** | **Immutable Raw Data & Log Segregation:** Separate raw JSONL, server logs, client stderr, telemetry logs, manifests per session. | `[x]` | Master runners directory layout | Verified in `scripts/run_linux_campaign.sh` |
| **6.3** | **Automatic Post-Block Quality Control:** `audit_cell_batch()` executed after each block before proceeding. | `[x]` | Master runners cell completion | Tested via `workload_contracts.py` |
| **6.4** | **Fail-Fast on Structural Failure:** Halts execution with exit code 1 on non-recoverable error. | `[x]` | All master campaign runners | Verified in unit tests |
| **6.5** | **Independent Reproduction Protocol:** Step-by-step external evaluation guide. | `[x]` | `docs/REPRODUCIBILITY_INDEPENDENT.md` | Comprehensive manual authored |
| **7.1** | **Raw Recomputation with `--data-dir`:** All statistics, tables, and figures computed from raw JSONL with custom path support. | `[x]` | `scripts/reproduce_quad_platform_analysis.py --data-dir` | Tested with `--data-dir . --quick` (Exit 0) |
| **7.2** | **Full TOST Power, $r_1$, $n_{\text{eff}}$, $b$ Reporting:** Explicit power and autocorrelation reporting per cell. | `[x]` | `audit_export/mbb_coverage_and_tost_power.csv`, Table 7 | Low power ($r_1 > 0.4$) marked explicitly |
| **7.3** | **Paired Session Drift & Wilcoxon Tests:** Formal S1 vs S2 non-parametric comparison, sign tests, and Wilcoxon signed-rank tests. | `[x]` | `audit_export/inter_session_drift_test.csv`, Table 7 | Binomial sign tests and drift computed |
| **7.4** | **Comprehensive Sensitivity Audits:** Sensitivity across $b \in \{2, 3, 5, 8, 12, \text{adaptive}\}$, W5 exclusion, telemetry, cache threshold. | `[x]` | `audit_export/sensitivity_analysis_summary.json` | Generated and exported |
| **7.5** | **Automated LaTeX Macros Synchronization:** Single source of truth in `macros_quad_platform.tex` with automated regression tests. | `[x]` | `scripts/reproduce_quad_platform_analysis.py`, `paper/macros_quad_platform.tex` | `pytest tests/test_artifact_consistency.py` (Exit 0) |
| **8.1** | **Artifact Coherence:** 100% numerical consistency between raw JSONL, CSVs, LaTeX tables, figures, and manuscript. | `[x]` | Master audit pipeline | `pytest tests/test_artifact_consistency.py` (Exit 0) |
| **8.2** | **Non-Selective Visualizations:** Explicit labeling of cold (Regime A) vs warm (Regime B) and session in all figures and Table 7. | `[x]` | Publication figures 1–6 and Tables 1–8 | Verified in generated figures |
| **8.3** | **State of the Art Positioning:** Verifiable, accurate bibliographic citations with verified DOIs. | `[x]` | `paper/references.bib` | Clean bibliography without invented DOIs |
| **8.4** | **Explicit Scope Limitations:** Sober discussion of model scale (3B vs larger), sensor scope, single-slot prefix caching. | `[x]` | `README.md`, `paper/manuscript.tex` | Verified neutral text |
| **8.5** | **Unified Release Package:** Consolidated packaging with `PENDING_RELEASE` placeholder awaiting Zenodo minting. | `[ ] PENDENTE AÇÃO EXTERNA (Aguardando cunhagem do DOI pelo autor)` | `scripts/reproduce_quad_platform_analysis.py:package_audit_zip` | `audit_export_quad_platform.zip` created |

---

## Final Readiness Verdict

- **Automated Test Suite:** 69 / 69 tests passing (`pytest -v`, exit code 0).
- **Manifest Pre-Flight Check:** 302 / 302 files verified with matching SHA-256 and executable permissions (`verify_manifest.py --pre-flight`, exit code 0).
- **Quality Gatekeeper Certification:** 4,269 / 4,269 historical records certified valid with zero mock records and zero physical roofline violations (`audit_submission_gatekeeper.py`, exit code 0).
- **Dry-Run Matrix Validation:** 100% passing across Linux x86_64, Windows 11 NVIDIA, Windows Intel HD Graphics iGPU, and macOS ARM64.
- **Overnight Execution Status:** Repository is fully prepared and shielded for overnight confirmatory campaigns.
