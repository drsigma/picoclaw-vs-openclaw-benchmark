#!/usr/bin/env python3
"""
scripts/build_review_submission_package.py - Rebuild and verify review_submission_package.zip (<= 100 MB).
Ensures 100% self-contained reproducibility, SHA-256 manifest validity, and test suite passage.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG_DIR = os.path.join(REPO_DIR, "review_submission_package")
ZIP_PATH = os.path.join(REPO_DIR, "review_submission_package.zip")
MANIFEST_PATH = os.path.join(REPO_DIR, "data", "manifest_sha256.json")


def build_package() -> None:
    print(f"Building review submission package in: {PKG_DIR}")
    shutil.rmtree(PKG_DIR, ignore_errors=True)
    os.makedirs(PKG_DIR, exist_ok=True)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    tracked_files = [k for k in manifest.keys() if not k.startswith("_")]
    tracked_files.extend([
        "data/manifest_sha256.json",
        "audit_export_quad_platform.zip",
        "benchmark/picoclaw_orch_linux",
        "benchmark/picoclaw_orch",
    ])

    # Include text chunks and evaluator bundles
    for extra_dir in ("audit_txt_chunks", "evaluator_bundle_txt"):
        full_d = os.path.join(REPO_DIR, extra_dir)
        if os.path.exists(full_d):
            for root, _, files in os.walk(full_d):
                for file in files:
                    tracked_files.append(os.path.relpath(os.path.join(root, file), REPO_DIR).replace("\\", "/"))

    copied = 0
    for rel_path in sorted(set(tracked_files)):
        src = os.path.join(REPO_DIR, rel_path)
        if os.path.exists(src):
            dst = os.path.join(PKG_DIR, rel_path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1

    print(f"Copied {copied} files into {PKG_DIR}")

    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)

    print(f"Compressing into {ZIP_PATH} (compresslevel=9)...")
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, _, files in os.walk(PKG_DIR):
            for file in sorted(files):
                abs_p = os.path.join(root, file)
                arcname = os.path.relpath(abs_p, REPO_DIR).replace("\\", "/")
                zf.write(abs_p, arcname)

    size_bytes = os.path.getsize(ZIP_PATH)
    size_mb = size_bytes / (1024 * 1024)
    print(f"Package created: {ZIP_PATH} ({size_mb:.2f} MB, {size_bytes:,} bytes)")
    assert size_mb <= 100.0, f"Package exceeded 100 MB limit: {size_mb:.2f} MB"


def verify_unpacked() -> None:
    test_dir = "/tmp/audit_zip_check"
    print(f"\nPerforming independent verification in {test_dir}...")
    shutil.rmtree(test_dir, ignore_errors=True)
    os.makedirs(test_dir, exist_ok=True)

    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(test_dir)
        for member in zf.infolist():
            extracted_path = os.path.join(test_dir, member.filename)
            mode = member.external_attr >> 16
            if mode and os.path.exists(extracted_path):
                try:
                    os.chmod(extracted_path, mode)
                except Exception:
                    pass

    pkg_root = os.path.join(test_dir, "review_submission_package")
    assert os.path.exists(pkg_root), f"Missing {pkg_root}"

    # 1. Verify cryptographic manifest
    vm_script = os.path.join(pkg_root, "scripts", "verify_manifest.py")
    res_vm = subprocess.run([sys.executable, vm_script], cwd=pkg_root, capture_output=True, text=True)
    print("verify_manifest output:")
    print(res_vm.stdout)
    assert res_vm.returncode == 0, f"verify_manifest failed in unpacked package:\n{res_vm.stderr}"
    assert "0 missing" in res_vm.stdout or "All" in res_vm.stdout

    # 2. Run pytest inside unpacked package
    res_pt = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=pkg_root, capture_output=True, text=True)
    print("pytest output:")
    print(res_pt.stdout)
    assert res_pt.returncode == 0, f"pytest failed in unpacked package:\n{res_pt.stderr}"

    # 3. Check for forbidden terms
    forbidden = ["softwarex", "elsevier", "elsarticle", "rafalince", "pix_qr_code", "chave pix"]
    violations = []
    for root, _, files in os.walk(pkg_root):
        if ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith((".pyc", ".png", ".bin", ".npz", ".zip", ".exe")):
                continue
            p = os.path.join(root, file)
            try:
                txt = open(p, "r", encoding="utf-8", errors="ignore").read().lower()
                for term in forbidden:
                    if term in txt:
                        violations.append((os.path.relpath(p, pkg_root), term))
            except Exception:
                pass

    if violations:
        print(f"❌ Forbidden terms found: {violations}")
        sys.exit(1)
    else:
        print("✅ Zero forbidden terms found in unpacked submission package!")


if __name__ == "__main__":
    build_package()
    verify_unpacked()
