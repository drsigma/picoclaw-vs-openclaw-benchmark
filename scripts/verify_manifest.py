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


def verify_manifest() -> int:
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

    for rel_path, expected_hash in manifest.items():
        abs_path = os.path.join(REPO_DIR, rel_path)
        if not os.path.exists(abs_path):
            missing.append(rel_path)
            continue

        actual_hash = compute_sha256(abs_path)
        if actual_hash != expected_hash:
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
