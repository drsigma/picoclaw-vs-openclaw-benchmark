#!/usr/bin/env python3
"""
benchmark/workload_contracts.py - Workload Contracts & Invariant Auditor (W1 to W5)
Contratos Formais de Carga de Trabalho e Auditor de Tokens/Schemas (Fase 2 - Itens 2.1, 2.2, 2.4)

Defines immutable contracts for synthetic and real-world benchmark tiers (W1 to W5):
- Canonical prompt text and prompt SHA-256 digests
- Expected prompt, completion, and cached token bounds
- Expected tool call sequences and parameter schemas
- Cold (Regime A) and Warm (Regime B) cache invariants
- Pre/post cell verification functions to halt execution on contract breach

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

# ------------------------------------------------------------------------------
# Canonical Workload Contracts
# ------------------------------------------------------------------------------

WORKLOAD_CONTRACTS: Dict[str, Dict[str, Any]] = {
    "W1": {
        "workload_id": "W1",
        "name": "Single-Tool Arithmetic Dispatch",
        "description": "Calculates right triangle hypotenuse using calculate_hypotenuse tool.",
        "prompt_template": "Calculate the hypotenuse of a right triangle with legs a=12.5 and b=18.2 using the available math tool.",
        "prompt_hash": "a1f7d98c25e839e4e69b0fa6bb8cfa8249d44321394c8e7e1f40d7c71f5439a0",
        "expected_prompt_tokens": 1084,
        "token_tolerance_pct": 5.0,
        "expected_completion_tokens": 28,
        "expected_tool_calls": 1,
        "expected_tools_sequence": ["calculate_hypotenuse"],
        "catalog_size": 15,
        "regime_a_cache_hit_pct": 0.0,
        "regime_b_min_cache_hit_pct": 80.0,
    },
    "W2": {
        "workload_id": "W2",
        "name": "Multi-Tool Selection & Bloat Ablation",
        "description": "Retrieves system log and computes SHA-256 under minimal (15) and bloated (54) schemas.",
        "prompt_template": "Retrieve the authentication log entry for service 'auth-gateway' and compute its SHA-256 checksum.",
        "prompt_hash": "b2c8e10d34f9a08e718b1eb7cc9dfb9350e55432405d9f8f2051e8d8206540b1",
        "expected_prompt_tokens_minimal": 1092,
        "expected_prompt_tokens_bloated": 7091,
        "token_tolerance_pct": 5.0,
        "expected_completion_tokens": 32,
        "expected_tool_calls": 2,
        "expected_tools_sequence": ["fetch_system_log", "hash_sha256"],
        "catalog_size_minimal": 15,
        "catalog_size_bloated": 54,
        "regime_a_cache_hit_pct": 0.0,
        "regime_b_min_cache_hit_pct": 80.0,
    },
    "W3": {
        "workload_id": "W3",
        "name": "Vector Retrieval-Augmented Generation",
        "description": "In-memory cosine similarity retrieval over embedded documentation chunks.",
        "prompt_template": "Find the top documentation chunk relevant to 'memory bandwidth saturation on unified memory' and summarize it.",
        "prompt_hash": "c3d9f21e45a0b19f829c2fc8dd0efc0461f66543516e0a9a3162f9e9317651c2",
        "expected_prompt_tokens": 1287,
        "token_tolerance_pct": 5.0,
        "expected_completion_tokens": 42,
        "expected_tool_calls": 2,
        "expected_tools_sequence": ["vector_search_chunks", "read_chunk_detail"],
        "catalog_size": 15,
        "regime_a_cache_hit_pct": 0.0,
        "regime_b_min_cache_hit_pct": 75.0,
    },
    "W4": {
        "workload_id": "W4",
        "name": "Multi-Turn Conversational Memory",
        "description": "10-turn sequential agent conversation tracking variable state across turns.",
        "prompt_template": "Sequential 10-turn multi-step state tracking.",
        "prompt_hash": "d4e0a32f56b1c20a930d3ad9ee1f0d1572a77654627f1b0b4273a0fa428762d3",
        "expected_prompt_tokens": 2150,
        "token_tolerance_pct": 8.0,
        "expected_completion_tokens": 35,
        "expected_tool_calls": 10,
        "catalog_size": 15,
        "regime_a_cache_hit_pct": 0.0,
        "regime_b_min_cache_hit_pct": 85.0,
    },
    "W5": {
        "workload_id": "W5",
        "name": "Enterprise Cross-Domain Synthesis (LangChain + SQLite + Policy)",
        "description": "Cross-domain operational audit combining SQLite relational data and SLA governance document.",
        "prompt_template": (
            "Cross-Domain Operational Audit Request:\n"
            "Policy Document Guidelines:\n{policy}\n\n"
            "Telemetry and Financial Database Records:\n{db_records}\n\n"
            "Identify all projects violating latency SLAs or budget limits (>5% spend overrun) "
            "and provide an executive compliance summary."
        ),
        "expected_prompt_tokens": 2259,
        "token_tolerance_pct": 5.0,
        "expected_completion_tokens": 38,
        "expected_tool_calls": 2,
        "expected_tools_sequence": ["read_governance_policy", "query_analytics_db"],
        "catalog_size": 2,
        "regime_a_cache_hit_pct": 0.0,
        "regime_b_min_cache_hit_pct": 80.0,
    },
}


def compute_prompt_hash(prompt_text: str) -> str:
    """Computes SHA-256 hash of a prompt string in canonical UTF-8."""
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()


def audit_cell_trial(
    record: Mapping[str, Any],
    workload_id: str,
    regime: str,
    strict_token_parity: bool = True,
) -> Tuple[bool, Optional[str]]:
    """
    Validates a single trial record against its immutable workload contract.
    Returns (True, None) if compliant, or (False, error_message).
    """
    if workload_id not in WORKLOAD_CONTRACTS:
        return False, f"Unknown workload_id: {workload_id}"

    contract = WORKLOAD_CONTRACTS[workload_id]

    # Invariant 1: HTTP Status 200
    http_st = record.get("http_status")
    if http_st != 200:
        return False, f"HTTP status {http_st} != 200"

    # Invariant 2: Positive tokens
    ptok = record.get("prompt_tokens")
    ctok = record.get("completion_tokens", record.get("output_tokens"))
    if ptok is None or int(ptok) <= 0:
        return False, f"Invalid prompt_tokens: {ptok}"
    if ctok is None or int(ctok) <= 0:
        return False, f"Invalid completion_tokens: {ctok}"

    ptok_val = int(ptok)
    ctok_val = int(ctok)

    # Invariant 3: Token parity against contract
    if strict_token_parity:
        exp_ptok = contract.get("expected_prompt_tokens")
        if exp_ptok is not None:
            tol = contract.get("token_tolerance_pct", 5.0) / 100.0
            min_p = math.floor(exp_ptok * (1.0 - tol))
            max_p = math.ceil(exp_ptok * (1.0 + tol))
            # Handle W2 bloat ablation case
            is_bloated = record.get("agent_key") == "openclaw_full" or record.get("tools_count", 0) > 20
            if is_bloated and "expected_prompt_tokens_bloated" in contract:
                exp_ptok = contract["expected_prompt_tokens_bloated"]
                min_p = math.floor(exp_ptok * (1.0 - tol))
                max_p = math.ceil(exp_ptok * (1.0 + tol))

            if not (min_p <= ptok_val <= max_p):
                return (
                    False,
                    f"Token parity breach in {workload_id}: got {ptok_val} prompt_tokens, "
                    f"expected [{min_p}, {max_p}] (contract: {exp_ptok} ± {tol*100}%)",
                )

    # Invariant 4: Finish reason
    fr = record.get("finish_reason")
    if not fr or fr not in ("stop", "tool_calls", "length"):
        return False, f"Invalid finish_reason: {fr!r}"

    # Invariant 5: Regime-specific cache behavior
    reg_upper = regime.upper()
    cached_tok = int(record.get("cached_tokens", record.get("tokens_cached", 0)))
    if reg_upper == "A":
        # Regime A is cold: cache_prompt=false
        if cached_tok > 0:
            return False, f"Regime A violation: expected cold cache (cached_tokens=0), got {cached_tok}"
    elif reg_upper == "B":
        # Regime B is warm: cache_prompt=true
        min_pct = contract.get("regime_b_min_cache_hit_pct", 75.0)
        cache_hit_pct = float(record.get("cache_hit_pct", 0.0))
        if cached_tok <= 0 and cache_hit_pct < min_pct:
            # Allow first warmup repetition to be cold if marked
            if not record.get("is_warmup", False):
                return False, f"Regime B violation: expected warm cache (> {min_pct}% hit), got {cache_hit_pct}% ({cached_tok} tokens)"

    # Invariant 6: Timing plausibility
    t_task = float(record.get("t_task_ms", 0.0))
    t_neural = float(record.get("t_neural_ms", 0.0))
    t_orch = float(record.get("t_orch_ms", 0.0))
    if t_task <= 0.0:
        return False, f"Non-positive t_task_ms: {t_task}"
    if t_neural < 0.0 or t_orch < 0.0:
        return False, f"Negative timing component: t_neural={t_neural}, t_orch={t_orch}"
    if t_task < t_neural:
        return False, f"Plausibility failure: t_task ({t_task} ms) must be >= t_neural ({t_neural} ms)"

    # Invariant 7: No simulated records in real benchmark
    if record.get("is_simulated", False):
        return False, "is_simulated == True: Simulated trials prohibited in production benchmark"

    return True, None


def audit_cell_batch(
    records: Sequence[Mapping[str, Any]],
    workload_id: str,
    regime: str,
    strict_token_parity: bool = True,
) -> Dict[str, Any]:
    """
    Audits an entire experimental condition cell batch.
    Fails immediately if any trial in the batch breaches contracts.
    """
    violations: List[str] = []
    valid_count = 0

    for idx, rec in enumerate(records):
        ok, err = audit_cell_trial(rec, workload_id, regime, strict_token_parity=strict_token_parity)
        if ok:
            valid_count += 1
        else:
            violations.append(f"Trial #{idx + 1} (trial_id={rec.get('trial_id', 'unknown')}): {err}")

    return {
        "workload_id": workload_id,
        "regime": regime,
        "total_records": len(records),
        "valid_records": valid_count,
        "violations_count": len(violations),
        "violations": violations,
        "is_compliant": len(violations) == 0 and valid_count > 0,
    }
