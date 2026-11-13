"""
benchmark/protocol_invariants.py - Automated Protocol Invariant Validator
Validador Automático de Invariantes do Protocolo Experimental (Gate 0 & Gate 7)

Enforces strict fail-fast validation across all benchmark campaigns:
  0. Presence of all 9 mandatory Gate 0 provenance fields in every JSONL trial record:
     - session_id, timestamp_iso, git_commit, hardware, os, model_version, quantization, server_flags, workload
  1. prompt_tokens > 0 and completion_tokens > 0 on every evaluated trial;
  2. Strict prompt_tokens parity across all 15-tool arms within each workload (when require_equalized_tokens=True);
  3. Non-empty finish_reason in {"stop", "tool_calls", "length"};
  4. HTTP status strictly equal to 200;
  5. Exact total evaluated trial count (e.g. 600) and balanced per-cell count (e.g. n=30);
  6. Non-empty session_id and git_commit provenance in campaign metadata / trial records;
  7. Positive physical net energy (energy_net_above_idle_j > 0) when require_energy=True;
  8. Explicit separation of prompt_ms (neural prefill) and predicted_ms (autoregressive decode) in trial records.

Author: Rafael Paniccia Cassetta (UFABC)
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

VALID_FINISH_REASONS = frozenset({"stop", "tool_calls", "length"})

GATE_0_REQUIRED_FIELDS: tuple[str, ...] = (
    "session_id",
    "timestamp_iso",
    "git_commit",
    "hardware",
    "os",
    "model_version",
    "quantization",
    "server_flags",
    "workload",
)

EQUALIZED_15_TOOL_ARMS = frozenset(
    {
        "picoclaw",
        "go_orchestrator",
        "openclaw_minimal",
        "node_orchestrator",
        "node_orchestrator_minimal",
        "python_native",
        "python_reference_agent",
        "neural_baseline",
        "local_llm_baseline",
        "bun_minimal",
        "bun_jsc_orchestrator",
    }
)


def validate_gate_0_provenance_fields(
    records: Sequence[Mapping[str, Any]],
    source_name: str = "jsonl",
    require_prompt_predicted_ms: bool = False,
) -> dict[str, Any]:
    """
    Validate that 100% of records in a JSONL file contain all 9 mandatory Gate 0 root fields
    (and optionally prompt_ms / predicted_ms). Raises ValueError immediately on any missing/empty field.
    """
    if not records:
        raise ValueError(f"Gate 0 Invariant violated in {source_name}: empty records sequence.")

    for idx, r in enumerate(records):
        for field in GATE_0_REQUIRED_FIELDS:
            val = r.get(field)
            if not isinstance(val, str) or not val.strip():
                raise ValueError(
                    f"Gate 0 Invariant violated in {source_name} at line #{idx + 1}: "
                    f"missing or empty required provenance field {field!r} (got {val!r})."
                )
        if require_prompt_predicted_ms:
            for timing_field in ("prompt_ms", "predicted_ms"):
                t_val = r.get(timing_field)
                if t_val is None or float(t_val) < 0.0:
                    raise ValueError(
                        f"Gate 4 Invariant violated in {source_name} at line #{idx + 1}: "
                        f"missing or negative {timing_field!r} (got {t_val!r})."
                    )

    return {
        "source_name": source_name,
        "records_checked": len(records),
        "gate_0_fields_verified": list(GATE_0_REQUIRED_FIELDS),
        "status": "PASSED",
    }


def validate_campaign_invariants(
    records: Sequence[Mapping[str, Any]],
    expected_eval_count: int | None = 600,
    require_equalized_tokens: bool = True,
    require_energy: bool = True,
    metadata: Mapping[str, Any] | None = None,
    expected_reps_per_cell: int | None = 30,
    require_gate_0_fields: bool = False,
) -> dict[str, Any]:
    """
    Validate all experimental protocol invariants on campaign records and metadata.
    Raises ValueError immediately on any violation (zero silent fallbacks).
    """
    if not records:
        raise ValueError("Protocol Invariant #5 violated: empty records sequence provided.")

    if require_gate_0_fields:
        validate_gate_0_provenance_fields(records, source_name="campaign_records")

    eval_recs = [r for r in records if not r.get("is_warmup", False)]

    # Invariant 5: Exact sample count and balanced cell repetitions
    if expected_eval_count is not None and len(eval_recs) != expected_eval_count:
        raise ValueError(
            f"Protocol Invariant #5 violated: expected {expected_eval_count} evaluated records, "
            f"got {len(eval_recs)}."
        )

    cell_counts: dict[tuple[str, str], int] = defaultdict(int)
    for r in eval_recs:
        ak = str(r.get("agent_key", ""))
        w = str(r.get("workload", ""))
        cell_counts[(ak, w)] += 1

    if expected_reps_per_cell is not None:
        for (ak, w), cnt in cell_counts.items():
            if cnt != expected_reps_per_cell:
                raise ValueError(
                    f"Protocol Invariant #5 violated: cell ({ak!r}, {w!r}) has {cnt} evaluated records, "
                    f"expected {expected_reps_per_cell}."
                )

    # Invariant 6 (metadata level): session_id and git_commit provenance
    if metadata is not None:
        sid = metadata.get("session_id")
        gcommit = metadata.get("git_commit")
        if not isinstance(sid, str) or not sid.strip():
            raise ValueError("Protocol Invariant #6 violated: missing or empty 'session_id' in campaign metadata.")
        if not isinstance(gcommit, str) or not gcommit.strip():
            raise ValueError("Protocol Invariant #6 violated: missing or empty 'git_commit' in campaign metadata.")

    workload_arm_tokens: dict[str, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))

    for idx, r in enumerate(eval_recs):
        ak = str(r.get("agent_key", "unknown"))
        w = str(r.get("workload", "unknown"))

        # Invariant 1: Positive prompt_tokens and completion_tokens
        pt = r.get("prompt_tokens")
        ct = r.get("completion_tokens", r.get("output_tokens"))
        if pt is None or int(pt) <= 0:
            raise ValueError(
                f"Protocol Invariant #1 violated at record #{idx} ({ak}, {w}): prompt_tokens={pt!r} must be > 0."
            )
        if ct is None or int(ct) <= 0:
            raise ValueError(
                f"Protocol Invariant #1 violated at record #{idx} ({ak}, {w}): completion_tokens={ct!r} must be > 0."
            )

        # Invariant 3: Valid finish_reason
        fr = r.get("finish_reason")
        if not isinstance(fr, str) or fr.strip() not in VALID_FINISH_REASONS:
            raise ValueError(
                f"Protocol Invariant #3 violated at record #{idx} ({ak}, {w}): "
                f"finish_reason={fr!r} not in {sorted(VALID_FINISH_REASONS)}."
            )

        # Invariant 4: HTTP status == 200
        http_st = r.get("http_status")
        if http_st != 200:
            raise ValueError(
                f"Protocol Invariant #4 violated at record #{idx} ({ak}, {w}): http_status={http_st!r} != 200."
            )

        # Invariant 6 (record level): session_id and git_commit provenance
        if metadata is None:
            r_sid = r.get("session_id")
            r_gc = r.get("git_commit")
            if not isinstance(r_sid, str) or not r_sid.strip():
                raise ValueError(
                    f"Protocol Invariant #6 violated at record #{idx} ({ak}, {w}): missing or empty 'session_id'."
                )
            if not isinstance(r_gc, str) or not r_gc.strip():
                raise ValueError(
                    f"Protocol Invariant #6 violated at record #{idx} ({ak}, {w}): missing or empty 'git_commit'."
                )
        else:
            if "session_id" in r and (not isinstance(r["session_id"], str) or not r["session_id"].strip()):
                raise ValueError(
                    f"Protocol Invariant #6 violated at record #{idx} ({ak}, {w}): empty 'session_id' in record."
                )
            if "git_commit" in r and (not isinstance(r["git_commit"], str) or not r["git_commit"].strip()):
                raise ValueError(
                    f"Protocol Invariant #6 violated at record #{idx} ({ak}, {w}): empty 'git_commit' in record."
                )

        # Invariant 7: Physical energy > 0 when require_energy=True
        if require_energy:
            en = r.get("energy_net_above_idle_j")
            if en is None or float(en) <= 0.0:
                raise ValueError(
                    f"Protocol Invariant #7 violated at record #{idx} ({ak}, {w}): "
                    f"energy_net_above_idle_j={en!r} must be > 0 when require_energy=True."
                )

        if ak in EQUALIZED_15_TOOL_ARMS:
            workload_arm_tokens[w][ak].add(int(pt))

    # Invariant 2: Equalized prompt_tokens across all 15-tool arms per workload
    if require_equalized_tokens:
        for w, arm_map in workload_arm_tokens.items():
            all_pts: set[int] = set()
            for pts_set in arm_map.values():
                all_pts.update(pts_set)
            if len(all_pts) > 1:
                formatted = {k: sorted(v) for k, v in arm_map.items()}
                raise ValueError(
                    f"Protocol Invariant #2 violated in workload {w}: 15-tool arms diverged in prompt_tokens: {formatted}"
                )

    return {
        "validated_records": len(eval_recs),
        "cells_validated": len(cell_counts),
        "require_equalized_tokens": require_equalized_tokens,
        "require_energy": require_energy,
        "status": "PASSED",
    }
