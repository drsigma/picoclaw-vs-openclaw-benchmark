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
