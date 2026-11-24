#!/usr/bin/env python3
"""
tests/test_windows_nvidia_campaign.py - Unit tests for dedicated Windows-NVIDIA
Protocol V2 stack (adapter, runner CLI, --invert-blocks, --output-dir, --session-id,
--ngl 16 default, side-effect-free --dry-run, and W5 non-truncation).
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

from adapters.windows_nvidia_adapter import (
    parse_nvidia_bitmask,
    parse_nvidia_float,
    parse_nvidia_str,
    query_nvidia_smi_snapshot,
    verify_windows_nvidia_platform,
)
from scripts import run_windows_nvidia_master_campaign as nv_runner

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER_PATH = os.path.join(REPO_DIR, "scripts", "run_windows_nvidia_master_campaign.py")


def test_windows_nvidia_adapter_handles_wddm_na_fields(monkeypatch):
    """WDDM [N/A] tokens for power.limit / persistence_mode must parse to None, never 0 or crash."""
    assert parse_nvidia_float("[N/A]") is None
    assert parse_nvidia_float("N/A") is None
    assert parse_nvidia_float("[Not Supported]") is None
    assert parse_nvidia_float("46") == 46.0
    assert parse_nvidia_float("3.77 W") == 3.77
    assert parse_nvidia_str("[N/A]") is None
    assert parse_nvidia_str("GPU-abc-123") == "GPU-abc-123"
    assert parse_nvidia_bitmask("0x0000000000000001") == 1
    assert parse_nvidia_bitmask("[N/A]") is None

    fake_row = [
        "0",
        "GPU-a17dd36a-a4e0-a443-dc0e-b0ecdca79432",
        "NVIDIA GeForce RTX 3050 Laptop GPU",
        "4096",
        "581.95",
        "52",
        "12",
        "320",
        "[N/A]",
        "14.25",
        "[N/A]",
        "0x0000000000000004",
    ]
    monkeypatch.setattr("adapters.windows_nvidia_adapter._run_nvidia_smi_query", lambda gpu_index=0, timeout_s=10.0: fake_row)
    snap = query_nvidia_smi_snapshot(gpu_index=0)
    assert snap["gpu_index"] == 0
    assert snap["gpu_name"] == "NVIDIA GeForce RTX 3050 Laptop GPU"
    assert snap["gpu_temp_c"] == 52.0
    assert snap["gpu_utilization_pct"] == 12.0
    assert snap["gpu_vram_used_mb"] == 320.0
    assert snap["gpu_vram_total_mb"] == 4096.0
    assert snap["gpu_power_draw_w"] == 14.25
    assert snap["gpu_power_limit_w"] is None
    assert snap["gpu_persistence_mode"] is None
    assert snap["gpu_sw_power_cap"] is True
    assert snap["gpu_thermal_throttle_active_end"] is False


def test_windows_nvidia_platform_guard_rejects_non_windows(monkeypatch):
    monkeypatch.setattr("adapters.windows_nvidia_adapter.platform.system", lambda: "Linux")
    with pytest.raises(RuntimeError, match="Native platform mismatch"):
        verify_windows_nvidia_platform()


def test_windows_nvidia_runner_defaults_and_invert_blocks(tmp_path):
    ap = nv_runner.build_arg_parser()

    out_s1 = str(tmp_path / "windows_x86_64_nvidia_test_S1")
    args_s1 = ap.parse_args(["--full", "--session-id", "run1_S1", "--output-dir", out_s1])
    assert args_s1.ngl == 16
    assert args_s1.session_id == "run1_S1"
    assert args_s1.output_dir == out_s1
    assert args_s1.invert_blocks is False

    plan_s1 = nv_runner.resolve_execution_plan(args_s1)
    assert plan_s1["ngl"] == 16
    assert plan_s1["session_id"] == "run1_S1"
    assert plan_s1["exec_stages"][:2] == ["A", "B"]
    assert plan_s1["workload_seq"] == ["W1", "W2", "W3", "W4", "W5"]
    assert plan_s1["arms_seq"] == nv_runner.MAIN_ARMS
    assert plan_s1["tool_rag_regimes"][0][0] == "regime_b_warm"
    assert os.path.abspath(plan_s1["output_dir"]) == os.path.abspath(out_s1)

    out_s2 = str(tmp_path / "windows_x86_64_nvidia_test_S2")
    args_s2 = ap.parse_args(["--full", "--invert-blocks", "--session-id", "run1_S2", "--output-dir", out_s2])
    plan_s2 = nv_runner.resolve_execution_plan(args_s2)
    assert plan_s2["invert_blocks"] is True
    assert plan_s2["session_id"] == "run1_S2"
    assert plan_s2["exec_stages"][:2] == ["B", "A"]
    assert plan_s2["workload_seq"] == ["W5", "W4", "W3", "W2", "W1"]
    assert plan_s2["arms_seq"] == list(reversed(nv_runner.MAIN_ARMS))
    assert plan_s2["tool_rag_regimes"][0][0] == "regime_a_cold"


def test_windows_nvidia_runner_help_and_dry_run_side_effect_free(tmp_path):
    r_help = subprocess.run([sys.executable, RUNNER_PATH, "--help"], capture_output=True, text=True, check=False)
    assert r_help.returncode == 0
    assert "--session-id" in r_help.stdout
    assert "--output-dir" in r_help.stdout
    assert "--invert-blocks" in r_help.stdout
    assert "--ngl" in r_help.stdout

    dry_out = tmp_path / "dry_isolated_s2"
    r_dry = subprocess.run(
        [
            sys.executable,
            RUNNER_PATH,
            "--dry-run",
            "--full",
            "--invert-blocks",
            "--session-id",
            "test_s2_dry",
            "--output-dir",
            str(dry_out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r_dry.returncode == 0, r_dry.stderr
    assert "NGL:          16" in r_dry.stdout
    assert "Session ID:   test_s2_dry" in r_dry.stdout
    assert "Invert Order: True" in r_dry.stdout
    assert "['B', 'A'" in r_dry.stdout
    assert not dry_out.exists(), "--dry-run must not create directories or dirty the working tree"


def test_w5_workers_have_no_1000_char_policy_truncation():
    for rel in (
        os.path.join("benchmark", "openclaw_orch.mjs"),
        os.path.join("benchmark", "bun_jsc_agent.mjs"),
        os.path.join("benchmark", "picoclaw_orch_windows.go"),
    ):
        with open(os.path.join(REPO_DIR, rel), "r", encoding="utf-8") as f:
            src = f.read()
        assert ".slice(0, 1000)" not in src, f"Found W5 1000-char truncation in {rel}"
        assert "polStr[:1000]" not in src, f"Found W5 1000-char truncation in {rel}"
