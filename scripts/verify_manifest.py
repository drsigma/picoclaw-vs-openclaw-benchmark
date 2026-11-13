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
        "paper/RESPONSE_TO_REVIEWERS.md",
        "benchmark/adapters/bun_minimal_adapter.py",
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
        "results/publication_campaign/uma_energy_bandwidth_trials.jsonl",
        "results/publication_campaign/uma_energy_bandwidth_attribution.json",
        "results/publication_campaign/tables/table_energy_bandwidth_deconvolution.tex",
    ]
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
    return 0


def verify_manifest() -> int:
    if "--update" in sys.argv:
        return update_manifest()

    if not os.path.exists(MANIFEST_PATH):
        print(f"❌ [ERROR] Manifest file not found: {MANIFEST_PATH}")
        return 1

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    total_files = len(manifest)
    print("========================================================================")
    print(" 🔐 [PT-BR] Verificação de Integridade Criptográfica (SHA-256)")
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


if __name__ == "__main__":
    sys.exit(verify_manifest())
