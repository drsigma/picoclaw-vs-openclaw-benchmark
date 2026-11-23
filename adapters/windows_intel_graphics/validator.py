#!/usr/bin/env python3
"""
adapters/windows_intel_graphics/validator.py

Strict extraction-time validator and per-trial retry coordinator.
Validates types, absence of NaN/Inf/negative metrics, token field coherence
(tokens_cached, prompt_eval_count, eval_count, deterministic cache_hit),
W5 quality_score bounds, and Explicit-NA / Zero-NVML compliance BEFORE writing
any record to JSONL.
"""
from __future__ import annotations

import math
import time
from typing import Any, Callable


def compute_deterministic_cache_hit(tokens_cached: int, prompt_eval_count: int) -> bool:
    """
    Deterministic boolean definition of KV-cache hit:
    True iff tokens_cached > 0 and uncached prompt_eval_count <= 4.
    """
    return bool(int(tokens_cached) > 0 and int(prompt_eval_count) <= 4)


def _is_valid_number(val: Any) -> bool:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return False
    return not (math.isnan(val) or math.isinf(val))


def validate_trial_extraction(
    rec: dict[str, Any],
    regime: str,
    agent_key: str,
    workload: str,
) -> tuple[bool, str]:
    """
    Validate a single trial record prior to JSONL persistence.
    Returns (is_valid, reason).
    """
    if rec.get("is_simulated") is not False:
        return False, f"is_simulated must be False (got {rec.get('is_simulated')!r})"

    if rec.get("nvml_used") is True:
        return False, "nvml_used must be False on Windows Intel Graphics adapter"

    http_status = rec.get("http_status")
    if http_status != 200:
        return False, f"invalid http_status={http_status!r} (expected 200)"

    # 1. Required non-negative finite latencies
    for field in ("t_task_ms", "t_neural_ms", "t_orch_ms", "prompt_ms", "predicted_ms", "ttft_ms"):
        v = rec.get(field)
        if not _is_valid_number(v) or float(v) < 0.0:
            return False, f"invalid or negative latency {field}={v!r}"

    if float(rec["t_task_ms"]) <= 0.0:
        return False, f"non-positive t_task_ms={rec['t_task_ms']!r}"

    if float(rec["t_neural_ms"]) <= 0.0:
        return False, f"non-positive t_neural_ms={rec['t_neural_ms']!r}"

    # 2. Required token fields & strict coherence
    prompt_tokens = rec.get("prompt_tokens")
    completion_tokens = rec.get("completion_tokens")
    tokens_cached = rec.get("tokens_cached")
    prompt_eval_count = rec.get("prompt_eval_count")
    eval_count = rec.get("eval_count")
    cache_hit = rec.get("cache_hit")

    if not _is_valid_number(prompt_tokens) or int(prompt_tokens) <= 0:
        return False, f"invalid prompt_tokens={prompt_tokens!r}"
    if not _is_valid_number(completion_tokens) or int(completion_tokens) <= 0:
        return False, f"invalid completion_tokens={completion_tokens!r}"
    if not _is_valid_number(tokens_cached) or int(tokens_cached) < 0:
        return False, f"invalid tokens_cached={tokens_cached!r}"
    if not _is_valid_number(prompt_eval_count) or int(prompt_eval_count) < 0:
        return False, f"invalid prompt_eval_count={prompt_eval_count!r}"
    if not _is_valid_number(eval_count) or int(eval_count) <= 0:
        return False, f"invalid eval_count={eval_count!r}"
    if not isinstance(cache_hit, bool):
        return False, f"cache_hit must be bool (got {type(cache_hit).__name__})"

    pt = int(prompt_tokens)
    tc = int(tokens_cached)
    pec = int(prompt_eval_count)
    ec = int(eval_count)
    ct = int(completion_tokens)

    if tc > pt:
        return False, f"tokens_cached ({tc}) > prompt_tokens ({pt})"
    if pec > pt:
        return False, f"prompt_eval_count ({pec}) > prompt_tokens ({pt})"
    if ec != ct:
        return False, f"eval_count ({ec}) != completion_tokens ({ct})"

    expected_hit = compute_deterministic_cache_hit(tc, pec)
    if cache_hit != expected_hit:
        return False, (
            f"cache_hit ({cache_hit}) incoherent with tokens_cached={tc}, "
            f"prompt_eval_count={pec} (expected {expected_hit})"
        )

    if "cold" in regime.lower() and rec.get("cache_prompt") is False and cache_hit is True:
        return False, "cold regime with cache_prompt=False cannot report cache_hit=True"

    # 3. Orchestrator process telemetry (when not neural_baseline)
    if agent_key != "neural_baseline":
        cyc = rec.get("proc_cycles")
        mem = rec.get("proc_peak_phys_mb")
        if not _is_valid_number(cyc) or int(cyc) <= 0:
            return False, f"invalid orchestrator proc_cycles={cyc!r}"
        if not _is_valid_number(mem) or float(mem) <= 0.0:
            return False, f"invalid orchestrator proc_peak_phys_mb={mem!r}"

    # 4. System RAM & delta telemetry sanity
    sys_ram_used = rec.get("system_ram_used_end_mb")
    if not _is_valid_number(sys_ram_used) or float(sys_ram_used) <= 0.0:
        return False, f"invalid system_ram_used_end_mb={sys_ram_used!r}"

    thr_delta = rec.get("throttle_delta_events")
    if not _is_valid_number(thr_delta) or int(thr_delta) < 0:
        return False, f"invalid throttle_delta_events={thr_delta!r}"

    # 5. Offload / backend declaration
    if rec.get("ngl") is None or not isinstance(rec.get("ngl"), int) or rec["ngl"] < 0:
        return False, f"invalid ngl={rec.get('ngl')!r}"
    if not rec.get("execution_backend"):
        return False, "missing execution_backend"

    # 6. W5 quality_score validation
    if workload == "W5" and agent_key == "python_native":
        qs = rec.get("quality_score")
        if not _is_valid_number(qs) or not (1 <= int(qs) <= 5):
            return False, f"W5 python_native requires quality_score in 1..5 (got {qs!r})"
    elif workload == "W5" and rec.get("quality_score") not in (None, "N/A"):
        qs = rec.get("quality_score")
        if not _is_valid_number(qs) or not (1 <= int(qs) <= 5):
            return False, f"W5 quality_score out of bounds 1..5 (got {qs!r})"

    # 7. Tool-RAG pruning check
    if "tool_rag" in agent_key:
        tp = rec.get("t_prune_ms")
        if not _is_valid_number(tp) or float(tp) <= 0.0:
            return False, f"Tool-RAG arm {agent_key} missing positive t_prune_ms={tp!r}"

    # 8. Reject any stray NaN/Inf anywhere in top-level numeric fields
    for k, v in rec.items():
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return False, f"NaN/Inf detected in field {k!r}"

    return True, "OK"


def execute_trial_with_retry(
    run_once_fn: Callable[[], dict[str, Any]],
    regime: str,
    agent_key: str,
    workload: str,
    max_retries: int = 3,
    retry_delay_s: float = 1.5,
) -> tuple[dict[str, Any] | None, bool, list[str]]:
    """
    Execute a single trial and validate its extracted record before returning.
    If execution fails or validation fails, retries ONLY this specific trial up to
    `max_retries` times without aborting the campaign or repeating valid trials.

    Returns (final_record_or_None, passed_validation, failure_reasons).
    """
    reasons: list[str] = []
    last_rec: dict[str, Any] | None = None

    for attempt in range(1, max_retries + 1):
        try:
            rec = run_once_fn()
        except Exception as exc:
            msg = f"attempt {attempt}/{max_retries}: exception={type(exc).__name__}: {exc}"
            reasons.append(msg)
            if attempt < max_retries:
                time.sleep(retry_delay_s)
            continue

        valid, reason = validate_trial_extraction(rec, regime, agent_key, workload)
        rec["retry_attempts"] = attempt
        if valid:
            rec["extraction_validated"] = True
            rec["validation_caveat"] = None
            return rec, True, reasons

        last_rec = rec
        reasons.append(f"attempt {attempt}/{max_retries}: validation_failed={reason}")
        if attempt < max_retries:
            time.sleep(retry_delay_s)

    if last_rec is not None:
        last_rec["extraction_validated"] = False
        last_rec["validation_caveat"] = "; ".join(reasons)
    return last_rec, False, reasons
