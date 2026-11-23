#!/usr/bin/env python3
"""
benchmark/protocol_freeze.py - Immutable Experimental Protocol Freeze Validator
Validador de Imutabilidade do Protocolo Experimental (Fase 0 - Itens 0.1, 0.2, 0.3)

Calculates, checks, and validates the SHA-256 cryptographic signature of protocol_v2.0.json.
Enforces strict fail-fast validation: any tampering, missing mandatory field, or schema
drift raises an immediate error and returns non-zero exit code.

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from typing import Any, Dict

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTOCOL_PATH = os.path.join(REPO_DIR, "protocol", "protocol_v2.0.json")

MANDATORY_PROTOCOL_KEYS = (
    "protocol_version",
    "protocol_name",
    "frozen_at_utc",
    "provenance",
    "experimental_conditions",
    "platforms",
    "workload_matrix",
    "execution_modes",
    "session_and_block_design",
    "hypotheses_classification",
    "pre_defined_exclusion_criteria",
    "statistical_methods",
)


def compute_protocol_hash(filepath: str = PROTOCOL_PATH) -> str:
    """Computes SHA-256 hash of the canonical serialized JSON protocol."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Protocol file not found: {filepath}")
    with open(filepath, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest()


def load_and_validate_protocol(filepath: str = PROTOCOL_PATH) -> Dict[str, Any]:
    """Loads and strictly validates protocol structure and invariants."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Protocol file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        try:
            proto = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON syntax in protocol file {filepath}: {exc}") from exc

    # Invariant 1: Check mandatory top-level keys
    missing_keys = [k for k in MANDATORY_PROTOCOL_KEYS if k not in proto]
    if missing_keys:
        raise ValueError(f"Protocol violation: Missing mandatory keys in {filepath}: {missing_keys}")

    # Invariant 2: Version format
    ver = proto.get("protocol_version")
    if not ver or not isinstance(ver, str) or not ver.startswith("2."):
        raise ValueError(f"Protocol violation: Invalid protocol_version: {ver!r}")

    # Invariant 3: Model and server invariants
    exp_cond = proto.get("experimental_conditions", {})
    if exp_cond.get("model") != "Meta-Llama-3.2-3B-Instruct":
        raise ValueError(f"Protocol violation: Unexpected model: {exp_cond.get('model')}")
    if exp_cond.get("quantization") != "Q4_K_M":
        raise ValueError(f"Protocol violation: Unexpected quantization: {exp_cond.get('quantization')}")

    # Invariant 4: Hypotheses separation (confirmatory vs exploratory)
    hypo = proto.get("hypotheses_classification", {})
    conf = hypo.get("confirmatory", [])
    expl = hypo.get("exploratory_and_diagnostic", [])
    if not conf or not expl:
        raise ValueError("Protocol violation: Both confirmatory and exploratory hypotheses must be defined.")

    # Invariant 5: Workloads W1 to W5 present
    wl = proto.get("workload_matrix", {})
    for w in ("W1", "W2", "W3", "W4", "W5"):
        if w not in wl:
            raise ValueError(f"Protocol violation: Workload {w} missing from workload_matrix.")

    # Invariant 6: Statistical unit definition
    design = proto.get("session_and_block_design", {})
    if "statistical_unit" not in design or not design["statistical_unit"]:
        raise ValueError("Protocol violation: Statistical unit must be explicitly defined.")

    return proto


def verify_protocol_cli() -> int:
    parser = argparse.ArgumentParser(description="Experimental Protocol Freeze Validator")
    parser.add_argument("--protocol", default=PROTOCOL_PATH, help="Path to protocol JSON")
    parser.add_argument("--check-hash", default=None, help="Expected SHA-256 hash to verify against")
    args = parser.parse_args()

    print("=" * 78)
    print("📋 [PROTOCOL FREEZE VALIDATOR] Checking Protocol V2 Immutability")
    print("=" * 78)

    try:
        proto = load_and_validate_protocol(args.protocol)
        sha = compute_protocol_hash(args.protocol)
        print(f"✅ Protocol Version: {proto.get('protocol_version')}")
        print(f"✅ Protocol Name:    {proto.get('protocol_name')}")
        print(f"✅ SHA-256 Digest:   {sha}")
        print(f"✅ Confirmatory Hypotheses: {len(proto['hypotheses_classification']['confirmatory'])}")
        print(f"✅ Exploratory Analyses:    {len(proto['hypotheses_classification']['exploratory_and_diagnostic'])}")
        print(f"✅ Workloads Configured:    {list(proto['workload_matrix'].keys())}")

        if args.check_hash:
            if sha.lower() != args.check_hash.lower():
                print(f"❌ [HASH MISMATCH] Expected {args.check_hash}, got {sha}")
                return 1
            print(f"✅ [HASH VERIFIED] Matches expected hash: {args.check_hash}")

        print("=" * 78)
        print("🎉 Protocol V2 validation passed successfully. Invariants enforced.")
        print("=" * 78)
        return 0
    except Exception as exc:
        print(f"\n❌ [PROTOCOL FAILURE] {exc}", file=sys.stderr)
        print("=" * 78)
        return 1


if __name__ == "__main__":
    sys.exit(verify_protocol_cli())
