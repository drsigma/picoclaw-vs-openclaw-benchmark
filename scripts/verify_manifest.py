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
        "scripts/run_prefill_ablation.py",
        "scripts/run_w2_resample.py",
        "scripts/run_warm_cache_campaign.py",
        "results/publication_campaign/tables/table_prefill_ablation.tex",
        "results/publication_campaign/tables/table_warm_cache.tex",
        "results/publication_campaign/warm_cache_trials.jsonl",
        "results/publication_campaign/warm_cache_summary.json",
        "results/publication_campaign/warm_cache_statistical_tests.json",
        "results/publication_campaign/campaign_metadata.json",
    ]
    for rel_path in additional:
        abs_path = os.path.join(REPO_DIR, rel_path)
        if os.path.exists(abs_path) and rel_path not in manifest:
            manifest[rel_path] = ""

    updated = {}
    for rel_path in sorted(manifest.keys()):
        if rel_path.startswith("results/simulated_check/"):
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
