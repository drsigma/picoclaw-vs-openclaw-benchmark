# Data Directory: Pre-Run Workload Staging & Runtime Output Specification

This directory houses static synthetic workload inputs required to execute the benchmark, as well as the staging directories for runtime execution artifacts.

---

## 1. Pre-Run Static Assets (Included Pre-Campaign)

The `data/workload_data/` directory contains pre-generated static assets required for workload evaluation:
- `data/workload_data/b_proj.bin`: Projection matrix for embedding projections (W4).
- `data/workload_data/doc_embeddings.bin`: Vector chunk store for retrieval evaluation (W3).
- `data/workload_data/embedding_head_100k.npz`: Projection weights for neural baseline evaluations.
- `data/workload_data/mock_files/`: Mock directory tree and files for tool exploration (W1).
- `data/workload_data/system_logs.jsonl`: Mock input log file for log-analysis workloads (W2, 750 lines).

These input files are immutable workload contracts verified cryptographically before running any benchmark.

---

## 2. Post-Run Runtime Artifacts (Produced Post-Campaign)

All experimental trial dataset files (`*.jsonl`) and raw execution logs are **runtime artifacts produced during and after campaign execution**.
In accordance with reproducibility guidelines:
- **They are not required in the pre-run package.**
- They are generated dynamically on target native hardware (Darwin M4, Linux x86_64, Windows NVIDIA, Windows Intel HD Graphics 4600).
- The runners automatically initialize target session subdirectories:
  * `data/linux_x86_64_session1/raw/*.jsonl`
  * `data/linux_x86_64_session2/raw/*.jsonl`
  * `data/windows_x86_64_session1/raw/*.jsonl`
  * `data/windows_x86_64_session2/raw/*.jsonl`
  * `data/windows_intel_graphics_session1/raw/*.jsonl`
  * `data/windows_intel_graphics_session2/raw/*.jsonl`
  * `data/external_framework_langchain_trials.jsonl`
  * `data/mcp_live_transport_trials.jsonl`
- Following execution, `scripts/audit_submission_gatekeeper.py --post-run` audits the resulting datasets and generates `data/gatekeeper_audit_certificate.json`.

---

## 3. Verification Commands

- **Pre-Run Verification (Safe, No Trials Required)**:
  ```bash
  python3 scripts/verify_manifest.py --pre-run
  python3 scripts/audit_submission_gatekeeper.py --pre-run
  ```
- **Post-Run Verification (Full Campaign Audit)**:
  ```bash
  python3 scripts/verify_manifest.py --post-run
  python3 scripts/audit_submission_gatekeeper.py --post-run
  ```
