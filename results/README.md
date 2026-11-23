# Results Directory: Campaign Outputs & Analytical Artifacts

This directory serves as the output destination for analysis summaries, statistical tables, publication figures, and cross-platform comparisons generated during and after benchmark campaigns.

---

## 1. Pre-Run Status (Pre-Campaign)

In a pre-run repository package:
- Experimental results and derived statistical outputs have not yet been generated.
- Pre-flight validation (`--pre-run` and `--dry-run`) does **not** require post-run results to exist.
- Directory structures are verified or automatically initialized by the benchmark runners before executing workloads.

---

## 2. Post-Run Generated Artifacts (Produced Post-Campaign)

Following campaign execution on native target platforms, the analytical pipeline produces:
- `results/publication_campaign/`: Primary publication campaign trial records (`*.jsonl`), power measurements, and statistical summaries (`*.json`).
- `results/publication_campaign/tables/`: Generated LaTeX (`.tex`) and Markdown (`.md`) summary tables.
- `results/publication_campaign_*_session*/`: Platform-specific replication session trial outputs and metadata.
- `results/quad_platform_tables/`: Consolidated cross-platform LaTeX tables (`table1_master_summary.tex`, `macros_quad_platform.tex`, etc.).

---

## 3. Post-Run Analysis & Audit Pipeline

After physical campaigns complete on native hardware, run:
```bash
# 1. Generate consolidated tables, figures, and statistical tests
python3 scripts/reproduce_quad_platform_analysis.py

# 2. Execute automated submission gatekeeper to verify invariants and Roofline bounds
python3 scripts/audit_submission_gatekeeper.py --post-run

# 3. Verify cryptographic integrity of all produced artifacts
python3 scripts/verify_manifest.py --post-run
```
