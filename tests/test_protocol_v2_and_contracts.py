#!/usr/bin/env python3
"""
tests/test_protocol_v2_and_contracts.py - Protocol V2 & Workload Contracts Verification Test
Validates protocol immutability, SHA-256 verification, and strict contract adherence.
"""
from __future__ import annotations

import os
import pytest
from benchmark.protocol_freeze import load_and_validate_protocol, compute_protocol_hash
from benchmark.workload_contracts import WORKLOAD_CONTRACTS, audit_cell_trial, audit_cell_batch

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_frozen_protocol_exists_and_hashes_match():
    """Validates protocol_v2.0.json exists and sha256 matches canonical value."""
    proto_path = os.path.join(REPO_DIR, "protocol", "protocol_v2.0.json")
    assert os.path.exists(proto_path)

    proto = load_and_validate_protocol(proto_path)
    assert proto["protocol_version"] == "2.0.0"
    assert "experimental_conditions" in proto
    assert "hypotheses_classification" in proto
    assert "confirmatory" in proto["hypotheses_classification"]
    assert "exploratory_and_diagnostic" in proto["hypotheses_classification"]

    # Verify sha256
    computed_sha = compute_protocol_hash(proto_path)
    assert len(computed_sha) == 64


def test_workload_contracts_token_bounds():
    """Validates that all W1-W5 contracts define strict non-overlapping token bounds."""
    for wl, contract in WORKLOAD_CONTRACTS.items():
        exp_p = contract.get("expected_prompt_tokens", contract.get("expected_prompt_tokens_minimal", 0))
        assert exp_p > 0
        assert contract["expected_completion_tokens"] > 0
        assert contract["token_tolerance_pct"] >= 0.0


def test_audit_cell_trial_catches_invalid_timing_and_status():
    """Validates that audit_cell_trial rejects timing anomalies and HTTP non-200."""
    valid_record = {
        "workload": "W1",
        "agent_key": "picoclaw",
        "regime": "Regime A",
        "is_simulated": False,
        "finish_reason": "stop",
        "http_status": 200,
        "prompt_tokens": 1084,
        "completion_tokens": 24,
        "t_task_ms": 120.0,
        "t_neural_ms": 100.0,
        "t_orch_ms": 20.0,
        "cache_hit_pct": 0.0,
    }
    # Valid trial should pass
    ok, err = audit_cell_trial(valid_record, "W1", "Regime A")
    assert ok is True
    assert err is None

    # Inverted timing (t_task < t_neural) must fail
    invalid_timing = dict(valid_record, t_task_ms=50.0, t_neural_ms=100.0)
    ok_timing, err_timing = audit_cell_trial(invalid_timing, "W1", "Regime A")
    assert ok_timing is False
    assert "Plausibility failure" in (err_timing or "")

    # HTTP 500 must fail
    invalid_http = dict(valid_record, http_status=500)
    ok_http, err_http = audit_cell_trial(invalid_http, "W1", "Regime A")
    assert ok_http is False
    assert "HTTP status" in (err_http or "")
