#!/usr/bin/env python3
"""
tests/test_no_hardcoded_metrics_or_mocks.py - Automated Codebase & Telemetry Integrity Audit
Ensures zero hardcoded metrics, zero simulation fallbacks in production, zero forbidden publisher terms,
and zero promotional self-certification language in code and configuration.
"""
from __future__ import annotations

import os
import re
import pytest

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_no_simulated_fallbacks_in_workloads():
    """Verifies W5 and workload scripts do not use fallback simulated numbers on exception."""
    w5_path = os.path.join(REPO_DIR, "W5_langchain_real_world", "agent.py")
    with open(w5_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must not contain fallback simulated tokens 512, 110, 450
    assert '"prompt_tokens": 512' not in content
    assert '"completion_tokens": 110' not in content


def test_workload_contracts_immutable():
    """Verifies workload contracts exist and define immutable prompt hashes and token invariants."""
    from benchmark.workload_contracts import WORKLOAD_CONTRACTS, audit_cell_trial

    assert len(WORKLOAD_CONTRACTS) == 5
    for wl in ["W1", "W2", "W3", "W4", "W5"]:
        contract = WORKLOAD_CONTRACTS[wl]
        assert contract["workload_id"] == wl
        exp_p = contract.get("expected_prompt_tokens", contract.get("expected_prompt_tokens_minimal", 0))
        assert exp_p > 0

    # Test audit_cell_trial rejects simulated records
    mock_bad = {
        "workload": "W1",
        "agent_key": "picoclaw",
        "regime": "Regime A",
        "is_simulated": True,
        "finish_reason": "stop",
        "http_status": 200,
        "prompt_tokens": 1084,
        "completion_tokens": 24,
        "t_task_ms": 100.0,
        "t_neural_ms": 80.0,
        "t_orch_ms": 20.0,
    }
    ok, err = audit_cell_trial(mock_bad, "W1", "Regime A")
    assert ok is False
    assert "is_simulated == True" in (err or "")


def test_forbidden_words_in_source_code():
    """Ensures forbidden words (publisher, personal paths, promotional labels) are absent from scripts & benchmark."""
    forbidden = ["softwarex", "elsevier", "elsarticle", "rafalince"]
    promotional = ["padrão ouro", "zero-mock"]

    search_dirs = ["benchmark", "scripts", "adapters"]
    violations = []

    for s_dir in search_dirs:
        full_dir = os.path.join(REPO_DIR, s_dir)
        if not os.path.exists(full_dir):
            continue
        for root, _, files in os.walk(full_dir):
            for file in files:
                if not file.endswith((".py", ".sh", ".ps1")):
                    continue
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, 1):
                        low = line.lower()
                        # Allow self-checking lists that check for forbidden words
                        if "forbidden" in low or "sanitize" in low or "filter" in low:
                            continue
                        for word in forbidden:
                            if word in low:
                                violations.append((path, line_no, word, line.strip()))
                        for promo in promotional:
                            if promo in low:
                                violations.append((path, line_no, promo, line.strip()))

    assert len(violations) == 0, f"Found forbidden terms in source files: {violations}"
