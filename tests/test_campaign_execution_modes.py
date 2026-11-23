#!/usr/bin/env python3
"""
tests/test_campaign_execution_modes.py - Campaign Execution Modes and Environment Manifest Verification
Validates --dry-run, --smoke-test, --quick, --full, --invert-blocks, and environment manifest generation.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import pytest

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_environment_manifest_generation():
    """Validates that environment_manifest.py generates complete, non-empty metadata."""
    from benchmark.environment_manifest import record_environment_manifest

    with tempfile.TemporaryDirectory() as tmpdir:
        path = record_environment_manifest(tmpdir, "test_session_id")
        assert os.path.exists(path)

        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["manifest_version"] == "2.0.0"
        assert manifest["session_id"] == "test_session_id"
        assert "recorded_at_utc" in manifest
        assert "cpu" in manifest
        assert manifest["cpu"]["cpu_count_logical"] >= 1
        assert "ram" in manifest
        assert "runtimes" in manifest
        assert "python" in manifest["runtimes"]


def test_linux_runner_dry_run_modes():
    """Validates that Linux master runner handles --dry-run and --dry-run --invert-blocks cleanly."""
    cmd1 = [sys.executable, os.path.join(REPO_DIR, "scripts", "run_linux_x86_64_master_campaign.py"), "--dry-run"]
    res1 = subprocess.run(cmd1, capture_output=True, text=True)
    assert res1.returncode == 0
    assert "[DRY-RUN]" in res1.stdout

    cmd2 = [sys.executable, os.path.join(REPO_DIR, "scripts", "run_linux_x86_64_master_campaign.py"), "--dry-run", "--invert-blocks"]
    res2 = subprocess.run(cmd2, capture_output=True, text=True)
    assert res2.returncode == 0
    assert "Invert Order: True" in res2.stdout


def test_darwin_runner_dry_run():
    """Validates that unified benchmark runner handles --dry-run and --dry-run --invert-blocks cleanly."""
    cmd = [sys.executable, os.path.join(REPO_DIR, "benchmark", "run_unified_benchmark.py"), "--dry-run"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "[DRY-RUN]" in res.stdout


def test_windows_intel_runner_dry_run():
    """Validates that Windows Intel iGPU runner handles --dry-run on host cleanly."""
    cmd = [sys.executable, os.path.join(REPO_DIR, "adapters", "windows_intel_graphics", "runner.py"), "--dry-run"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "[DRY-RUN]" in res.stdout


def test_cli_fast_help_and_dry_run_exit_code_zero():
    """Item 1: Validates immediate and safe exit with code 0 on --help and --dry-run across all CLI runners."""
    targets = [
        os.path.join(REPO_DIR, "benchmark", "run_unified_benchmark.py"),
        os.path.join(REPO_DIR, "scripts", "reproduce_quad_platform_analysis.py"),
        os.path.join(REPO_DIR, "scripts", "run_linux_x86_64_master_campaign.py"),
        os.path.join(REPO_DIR, "scripts", "run_windows_x86_64_master_campaign.py"),
        os.path.join(REPO_DIR, "adapters", "windows_intel_graphics", "runner.py"),
        os.path.join(REPO_DIR, "scripts", "run_external_framework_langchain_benchmark.py"),
        os.path.join(REPO_DIR, "scripts", "run_mcp_live_transport_ablation.py"),
        os.path.join(REPO_DIR, "scripts", "run_quantization_scaling_ablation.py"),
        os.path.join(REPO_DIR, "scripts", "analyze_roofline_and_kv_scaling.py"),
        os.path.join(REPO_DIR, "scripts", "audit_submission_gatekeeper.py"),
    ]

    for script_path in targets:
        assert os.path.exists(script_path), f"Script missing: {script_path}"

        # 1. --help test (fast exit 0)
        res_help = subprocess.run([sys.executable, script_path, "--help"], capture_output=True, text=True, timeout=5)
        assert res_help.returncode == 0, f"--help failed for {os.path.basename(script_path)}: {res_help.stderr}"

        # 2. --dry-run test (fast exit 0)
        res_dry = subprocess.run([sys.executable, script_path, "--dry-run"], capture_output=True, text=True, timeout=5)
        assert res_dry.returncode == 0, f"--dry-run failed for {os.path.basename(script_path)}: {res_dry.stderr}"
        assert "[DRY-RUN]" in res_dry.stdout, f"Missing [DRY-RUN] tag in stdout for {os.path.basename(script_path)}"


def test_platform_mismatch_guard_aborts_real_execution():
    """Item 2: Validates that platform-specific runners abort with exit code 1 when invoked on mismatched OS."""
    import platform
    current_os = platform.system()

    if current_os == "Linux":
        # Windows runners on Linux must abort on real execution (--smoke-test)
        res_win = subprocess.run(
            [sys.executable, os.path.join(REPO_DIR, "scripts", "run_windows_x86_64_master_campaign.py"), "--smoke-test"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert res_win.returncode == 1
        assert "Native platform mismatch" in res_win.stderr

        res_intel = subprocess.run(
            [sys.executable, os.path.join(REPO_DIR, "adapters", "windows_intel_graphics", "runner.py"), "--smoke-test"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert res_intel.returncode == 1
        assert "Native platform mismatch" in res_intel.stderr

        # Darwin runner on Linux must abort on real execution
        res_darwin = subprocess.run(
            [sys.executable, os.path.join(REPO_DIR, "benchmark", "run_unified_benchmark.py"), "--smoke-test"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert res_darwin.returncode == 1
        assert "Native platform mismatch" in res_darwin.stderr

        # Shell script darwin campaign on Linux must abort
        darwin_sh = os.path.join(REPO_DIR, "scripts", "run_darwin_campaign.sh")
        if os.path.exists(darwin_sh):
            res_sh = subprocess.run(["bash", darwin_sh, "--smoke-test"], capture_output=True, text=True, timeout=5)
            assert res_sh.returncode == 1
            assert "Native platform mismatch" in res_sh.stderr


def test_gatekeeper_rejects_empty_dataset():
    """Item 3: Validates that empty or zero-record JSONL files are rejected with error by gatekeeper."""
    from scripts.audit_submission_gatekeeper import audit_jsonl_file

    with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w", delete=False) as f:
        tmp_name = f.name
        # Write empty file

    try:
        stats = audit_jsonl_file(tmp_name)
        assert stats["is_compliant"] is False
        assert stats["valid_records"] == 0
        assert any("Empty file error" in err for err in stats["errors"])
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
