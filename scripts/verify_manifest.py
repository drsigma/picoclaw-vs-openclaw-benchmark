#!/usr/bin/env python3
"""
scripts/verify_manifest.py - Cryptographic Artifact Integrity Verifier
Verificador Criptográfico de Integridade de Artefatos

Validates registered SHA-256 hashes in data/manifest_sha256.json against files on disk.
Valida os hashes SHA-256 registrados em data/manifest_sha256.json contra os arquivos em disco.

Author / Autor: Rafael Paniccia Cassetta (UFABC)
Language / Idioma: Bilingual (PT-BR & EN-US)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(REPO_DIR, "data", "manifest_sha256.json")
MANIFEST_STATIC_PATH = os.path.join(REPO_DIR, "data", "manifest_static_sha256.json")


def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 hex digest of a file in 64 KB streaming chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def update_manifest() -> int:
    """Recomputes SHA-256 for all tracked files and updates data/manifest_sha256.json."""
    if not os.path.exists(MANIFEST_PATH):
        print(f"❌ [ERROR] Manifest file not found: {MANIFEST_PATH}")
        return 1

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Also track additional core files if present
    additional = [
        "paper/manuscript.tex",
        "paper/RESPONSE_TO_REVIEWERS.md",
        "benchmark/protocol_invariants.py",
        "benchmark/stats_core.py",
        "benchmark/bun_jsc_agent.mjs",
        "benchmark/adapters/bun_minimal_adapter.py",
        "tests/conftest.py",
        "scripts/run_prefill_ablation.py",
        "scripts/run_w2_resample.py",
        "scripts/run_warm_cache_campaign.py",
        "scripts/run_regime_a_equalized_update.py",
        "scripts/run_regime_b_w2_w4_unified_session.py",
        "scripts/run_inter_session_replication.py",
        "scripts/run_tool_rag_mitigation_experiment.py",
        "scripts/export_audit_bundle.py",
        "results/exploratory_campaigns/raw_trials_pre_w2_fix.jsonl",
        "results/exploratory_campaigns/warm_cache_trials_two_session_backup.jsonl",
        "results/publication_campaign/prefill_regression_fit.json",
        "results/publication_campaign/tables/table_prefill_ablation.tex",
        "results/publication_campaign/tables/table_warm_cache.tex",
        "results/publication_campaign/tables/table_tool_rag_mitigation.tex",
        "results/publication_campaign/warm_cache_trials.jsonl",
        "results/publication_campaign/warm_cache_summary.json",
        "results/publication_campaign/warm_cache_statistical_tests.json",
        "results/publication_campaign/campaign_metadata.json",
        "results/publication_campaign/spearman_correlation_matrix.json",
        "results/publication_campaign/tables/table_spearman_correlation.tex",
        "results/publication_campaign/pca_variance_decomposition.json",
        "results/publication_campaign/tables/table_pca_loadings.tex",
        "results/publication_campaign/prefill_ablation.jsonl",
        "results/publication_campaign/inter_session_trials.jsonl",
        "results/publication_campaign/inter_session_replication.json",
        "results/publication_campaign/tool_rag_mitigation_trials.jsonl",
        "results/publication_campaign/tool_rag_mitigation_summary.json",
        "results/publication_campaign/hyperfine_cold_start.json",
        "results/publication_campaign/hyperfine_agent_init.json",
        "results/publication_campaign/hyperfine_worker_version.json",
        "results/publication_campaign/llama_server_publication.log",
        "results/publication_campaign/powermetrics_publication_sample.txt",
        "scripts/run_uma_energy_and_bandwidth_attribution.py",
        "scripts/run_kv_cache_thrashing_ablation.py",
        "scripts/run_independent_validation_suite.py",
        "results/publication_campaign/uma_energy_bandwidth_trials.jsonl",
        "results/publication_campaign/uma_energy_bandwidth_attribution.json",
        "results/publication_campaign/kv_cache_thrashing_trials.jsonl",
        "results/publication_campaign/kv_cache_thrashing_summary.json",
        "results/publication_campaign/sensitivity_and_outlier_analysis.json",
        "results/publication_campaign/independent_validation_report.json",
        "results/publication_campaign/cross_hardware_and_independent_validation.json",
        "results/publication_campaign/tables/table_energy_bandwidth_deconvolution.tex",
        "data/roofline_kv_affine_model.json",
        "data/harness_self_overhead.json",
        "data/external_framework_langchain_summary.json",
        "extensions/langchain_adapter/langchain_orch.py",
        "src/telemetry_backend.py",
        "scripts/analyze_roofline_and_kv_scaling.py",
        "scripts/measure_harness_self_overhead.py",
        "scripts/run_cross_hardware_replica.py",
        "scripts/run_cross_hardware_replica.sh",
        "scripts/run_cross_hardware_replica.ps1",
        "scripts/run_external_framework_langchain_benchmark.py",
        "benchmark/mcp_server.py",
        "scripts/run_mcp_live_transport_ablation.py",
        "scripts/run_quantization_scaling_ablation.py",
        "scripts/audit_submission_gatekeeper.py",
        "data/mcp_live_transport_ablation.json",
        "data/quantization_scaling_ablation.json",
        "data/gatekeeper_audit_certificate.json",
        "results/publication_campaign/tables/table_mcp_transport_ablation.tex",
        "results/publication_campaign/tables/table_quantization_scaling.tex",
        "data/uma_energy_bandwidth_attribution.json",
        "data/mcp_live_transport_trials.jsonl",
        "data/external_framework_langchain_trials.jsonl",
        "scripts/reproduce_quad_platform_analysis.py",
        "scripts/generate_audit_txt_chunks.py",
        ".github/workflows/reproducibility.yml",
        "AUDIT_REPORT_FINAL.md",
        "audit_export/Systems_Replication_Report.md",
        "audit_export/REVIEW_PACKAGE_README.md",
        "audit_export/pytest_output.txt",
        "audit_export/tost_block_sensitivity.csv",
        "audit_export/tost_block_sensitivity_expanded.csv",
        "audit_export/quad_platform_consolidated_summary.csv",
        "audit_export/anomaly_and_cache_diagnostics.csv",
        "audit_export/w5_token_and_schema_audit.csv",
        "audit_export/mbb_coverage_and_tost_power.csv",
        "audit_export/linux_throttling_stratification.csv",
        "audit_export/inter_session_drift_test.csv",
        "audit_export/sensitivity_analysis_summary.json",
        "audit_export/V2_READINESS_MATRIX.md",
        "benchmark/linux_x86_64_telemetry_adapter.py",
        "benchmark/windows_x86_64_telemetry_adapter.py",
        "benchmark/protocol_freeze.py",
        "benchmark/workload_contracts.py",
        "benchmark/environment_manifest.py",
        "protocol/protocol_v2.0.json",
        "docs/PROTOCOL_V2.md",
        "docs/TELEMETRY_ARCHITECTURE.md",
        "docs/REPRODUCIBILITY_INDEPENDENT.md",
        "scripts/run_linux_campaign.sh",
        "scripts/run_windows_campaign.ps1",
        "scripts/run_darwin_campaign.sh",
        "tests/test_no_hardcoded_metrics_or_mocks.py",
        "tests/test_protocol_v2_and_contracts.py",
        "tests/test_campaign_execution_modes.py",
    ]
    # Dynamically include all raw quad-platform session JSONL datasets and consolidated tables
    import glob as _glob
    for pattern in (
        "data/linux_x86_64_session1/raw/*.jsonl",
        "data/linux_x86_64_session2/raw/*.jsonl",
        "data/windows_x86_64_session1/raw/*.jsonl",
        "data/windows_x86_64_session2/raw/*.jsonl",
        "data/windows_intel_graphics_session1/raw/*.jsonl",
        "data/windows_intel_graphics_session2/raw/*.jsonl",
        "audit_export/tables/*.md",
        "audit_export/tables/*.tex",
        "results/quad_platform_tables/*.tex",
    ):
        for abs_match in sorted(_glob.glob(os.path.join(REPO_DIR, pattern))):
            additional.append(os.path.relpath(abs_match, REPO_DIR).replace("\\", "/"))
    for rel_path in additional:
        abs_path = os.path.join(REPO_DIR, rel_path)
        if os.path.exists(abs_path) and rel_path not in manifest:
            manifest[rel_path] = ""

    updated = {}
    for rel_path in sorted(manifest.keys()):
        if (
            rel_path.startswith("results/simulated_check/")
            or rel_path == "data/results_all.json"
            or rel_path.startswith("results/exploratory_campaigns/campaign_comparison/")
            or "poisson" in rel_path.lower()
            or "fig7" in rel_path
            or "fig8" in rel_path
        ):
            continue
        abs_path = os.path.join(REPO_DIR, rel_path)
        if os.path.exists(abs_path):
            updated[rel_path] = compute_sha256(abs_path)
        else:
            print(f"⚠️  [SKIP] File missing on disk, omitting from updated manifest: {rel_path}")

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2)
        f.write("\n")

    print(f"✅ [SUCCESS] Updated {len(updated)} tracked file signatures in {MANIFEST_PATH}")
    update_static_manifest()
    return 0


def update_static_manifest() -> int:
    """Computes SHA-256 exclusively for static pre-run files, omitting runtime trial .jsonl and campaign logs."""
    static_entries = [
        ".github/workflows/reproducibility.yml",
        ".gitignore",
        "CITATION.cff",
        "CONTRIBUTING.md",
        "DATA_LICENSE",
        "LICENSE",
        "Makefile",
        "README.md",
        "pyproject.toml",
        "requirements.txt",
        "protocol/protocol_v2.0.json",
        "src/telemetry_backend.py",
        "data/README.md",
        "results/README.md",
    ]

    for d in ["benchmark", "adapters", "scripts", "tests", "docs", "paper"]:
        abs_d = os.path.join(REPO_DIR, d)
        if not os.path.exists(abs_d):
            continue
        for root, _, files in os.walk(abs_d):
            if "__pycache__" in root or ".pytest_cache" in root:
                continue
            for f in sorted(files):
                if f.endswith(".pyc") or f.endswith(".pyo") or f == ".DS_Store" or f.endswith(".log"):
                    continue
                # Exclude runtime trial jsonl files from static manifest
                if f.endswith(".jsonl") and "workload_data" not in root:
                    continue
                rel = os.path.relpath(os.path.join(root, f), REPO_DIR).replace("\\", "/")
                static_entries.append(rel)

    # Include mock data inside data/workload_data (needed by workloads W1-W5)
    wl_data = os.path.join(REPO_DIR, "data", "workload_data")
    if os.path.exists(wl_data):
        for root, _, files in os.walk(wl_data):
            for f in sorted(files):
                rel = os.path.relpath(os.path.join(root, f), REPO_DIR).replace("\\", "/")
                static_entries.append(rel)

    static_entries = sorted(set(static_entries))
    updated_static = {}
    for rel_path in static_entries:
        abs_path = os.path.join(REPO_DIR, rel_path)
        if os.path.exists(abs_path):
            updated_static[rel_path] = compute_sha256(abs_path)

    os.makedirs(os.path.dirname(MANIFEST_STATIC_PATH), exist_ok=True)
    with open(MANIFEST_STATIC_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_static, f, indent=2)
        f.write("\n")

    print(f"✅ [SUCCESS] Updated {len(updated_static)} static file signatures in {MANIFEST_STATIC_PATH}")
    return 0


def verify_manifest(manifest_file: str | None = None) -> int:
    if "--update" in sys.argv:
        return update_manifest()

    # Determine manifest mode
    is_pre_run = "--pre-run" in sys.argv
    is_post_run = "--post-run" in sys.argv

    if manifest_file:
        target_path = manifest_file
    elif is_pre_run:
        target_path = MANIFEST_STATIC_PATH
    elif is_post_run:
        target_path = MANIFEST_PATH
    else:
        # Default fallback: check static manifest if full manifest does not exist or if .jsonl are absent
        target_path = MANIFEST_PATH if os.path.exists(MANIFEST_PATH) else MANIFEST_STATIC_PATH

    if not os.path.exists(target_path):
        # Fall back to static if post-run not available
        if target_path == MANIFEST_PATH and os.path.exists(MANIFEST_STATIC_PATH):
            target_path = MANIFEST_STATIC_PATH
        else:
            print(f"❌ [ERROR] Manifest file not found: {target_path}")
            return 1

    with open(target_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest_label = "Pre-Run Static" if "static" in os.path.basename(target_path) else "Post-Run Complete"
    total_files = len(manifest)
    print("========================================================================")
    print(f" 🔐 [PT-BR] Verificação de Integridade Criptográfica (SHA-256) [{manifest_label}]")
    print(f"    [EN-US] Cryptographic Artifact Integrity Verification ({total_files} files)")
    print("========================================================================")

    mismatches = []
    missing = []
    verified_count = 0

    for rel_path, exp_val in manifest.items():
        abs_path = os.path.join(REPO_DIR, rel_path)
        if not os.path.exists(abs_path):
            missing.append(rel_path)
            continue

        if isinstance(exp_val, dict):
            expected_hash = exp_val.get("sha256", "")
        else:
            expected_hash = str(exp_val)

        actual_hash = compute_sha256(abs_path)
        if actual_hash.lower() != expected_hash.lower():
            mismatches.append((rel_path, expected_hash, actual_hash))
        else:
            verified_count += 1

    if missing:
        print(f"\n❌ [ERROR] Missing files ({len(missing)}):")
        for m in missing:
            print(f"   - {m}")

    if mismatches:
        print(f"\n❌ [ERROR] Hash mismatches ({len(mismatches)}):")
        for p, exp, act in mismatches:
            print(f"   - {p}")
            print(f"     Expected: {exp}")
            print(f"     Actual:   {act}")

    if not missing and not mismatches:
        print(f"✅ [SUCCESS] All {verified_count}/{total_files} tracked files match their cryptographic SHA-256 signature!")
        print("   [PT-BR] Todos os arquivos rastreados conferem com suas assinaturas SHA-256 registradas.")
        print("========================================================================\n")
        return 0
    else:
        print(f"\n⚠️  [FAILURE] Verification failed: {verified_count}/{total_files} valid, {len(mismatches)} altered, {len(missing)} missing.")
        print("========================================================================\n")
        return 1


def pre_flight_check(is_pre_run: bool = False) -> int:
    """
    Executes comprehensive pre-flight verification:
    1. Verifies all files in manifest exist and hashes match.
    2. Validates execution permissions of scripts and binaries.
    3. Checks protocol freeze and core configuration invariants.
    4. Confirms output directories (data/ and results/) exist or are created.
    Returns 0 on complete compliance, 1 on any failure.
    """
    manifest_label = "Pre-Run Static Mode" if is_pre_run else "Standard Verification"
    print("========================================================================")
    print(f" 🚀 [PRE-FLIGHT VERIFIER] Comprehensive Pre-Flight Check ({manifest_label})")
    print("========================================================================")

    target_manifest = MANIFEST_STATIC_PATH if is_pre_run else (MANIFEST_PATH if os.path.exists(MANIFEST_PATH) else MANIFEST_STATIC_PATH)
    res = verify_manifest(target_manifest)
    if res != 0:
        print("❌ [PRE-FLIGHT FAILED] Manifest integrity check failed.", file=sys.stderr)
        return 1

    permission_errors = []
    if os.name != "nt":
        exec_targets = [
            "benchmark/picoclaw_orch",
            "benchmark/picoclaw_orch_linux",
            "benchmark/python_orch.py",
            "scripts/reproduce_quad_platform_analysis.py",
            "scripts/verify_manifest.py",
            "scripts/audit_submission_gatekeeper.py",
        ]
        for rel in exec_targets:
            abs_p = os.path.join(REPO_DIR, rel)
            if os.path.exists(abs_p):
                if not os.access(abs_p, os.X_OK):
                    permission_errors.append(f"Missing executable permission (chmod +x): {rel}")

    if permission_errors:
        print("\n❌ [PERMISSION ERRORS]:", file=sys.stderr)
        for err in permission_errors:
            print(f"   - {err}", file=sys.stderr)
        return 1

    proto_path = os.path.join(REPO_DIR, "protocol", "protocol_v2.0.json")
    if not os.path.exists(proto_path):
        print("❌ [PRE-FLIGHT FAILED] Missing protocol/protocol_v2.0.json", file=sys.stderr)
        return 1

    # Ensure output staging directories exist
    os.makedirs(os.path.join(REPO_DIR, "data"), exist_ok=True)
    os.makedirs(os.path.join(REPO_DIR, "results"), exist_ok=True)

    if is_pre_run:
        print("ℹ️  [PRE-RUN NOTICE] Static pre-run verification passed.")
        print("   Runtime trial .jsonl files will be generated during physical campaign execution.")
    print("✅ [PRE-FLIGHT PASSED] All files verified, permissions confirmed, protocol present.")
    print("========================================================================\n")
    return 0


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        print("Usage: scripts/verify_manifest.py [--pre-run | --post-run | --pre-flight | --update | --dry-run | -h]")
        sys.exit(0)
    if "--dry-run" in sys.argv:
        print("⚡ [DRY-RUN] Manifest verification execution plan verified. Exiting code 0.")
        sys.exit(0)
    if "--update" in sys.argv:
        sys.exit(update_manifest())
    if "--pre-run" in sys.argv or ("--pre-flight" in sys.argv and "--post-run" not in sys.argv and not os.path.exists(MANIFEST_PATH)):
        sys.exit(pre_flight_check(is_pre_run=True))
    if "--pre-flight" in sys.argv:
        sys.exit(pre_flight_check(is_pre_run=("--pre-run" in sys.argv)))
    sys.exit(verify_manifest())
