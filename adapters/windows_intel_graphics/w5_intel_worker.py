#!/usr/bin/env python3
"""
adapters/windows_intel_graphics/w5_intel_worker.py

Isolated W5 Real-World RAG worker (LangChain + SQLite + Governance Policy + LLM-as-a-Judge)
for the Windows Intel Graphics adapter. Reuses the repository's canonical W5_langchain_real_world
tools, SQLite database (analytics.db), governance_policy.txt, and evaluator.py, with:
  - Extended HTTP timeout (300s) suited for Intel HD Graphics / Haswell CPU inference
  - Strict Explicit-NA fail-fast on HTTP != 200 (never falls back to simulated 503 responses)
  - Deterministic cache_hit, tokens_cached, prompt_eval_count, eval_count, and quality_score (1-5)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from typing import Any

import psutil

REPO_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from W5_langchain_real_world.agent import (  # noqa: E402
    build_w5_langchain_tools,
    tool_query_sqlite,
    tool_read_policy,
)
from W5_langchain_real_world.evaluator import evaluate_quality  # noqa: E402

API_URL = os.environ.get("LLAMA_API_URL", "http://127.0.0.1:8080/v1/chat/completions")


def _rss_mb() -> float:
    try:
        return round(psutil.Process().memory_info().rss / (1024.0 * 1024.0), 3)
    except Exception:
        return 0.0


def run_w5_intel_trial(warmth: str = "Warm", max_tokens: int = 256, timeout_s: float = 300.0) -> dict[str, Any]:
    rss_idle = _rss_mb()
    t_start = time.perf_counter()

    t0_dispatch = time.perf_counter()
    db_res = tool_query_sqlite(
        "SELECT p.name, p.tier, p.allocated_budget_usd, p.current_spend_usd, "
        "t.p99_latency_ms, t.error_rate_pct, c.compliance_status, c.violations_count "
        "FROM projects p "
        "JOIN service_telemetry t ON p.id = t.project_id "
        "JOIN compliance_audit c ON p.id = c.project_id"
    )
    policy_res = tool_read_policy("SLAS AND LATENCY LIMITS")
    tools_catalog = build_w5_langchain_tools()
    t_dispatch_ms = (time.perf_counter() - t0_dispatch) * 1000.0
    tool_calls_count = 2

    user_prompt = (
        f"Cross-Domain Operational Audit Request:\n"
        f"Policy Document Guidelines:\n{policy_res}\n\n"
        f"Telemetry and Financial Database Records:\n{db_res}\n\n"
        f"Identify all projects violating latency SLAs or budget limits (>5% spend overrun) "
        f"and provide an executive compliance summary."
    )
    messages = [
        {
            "role": "system",
            "content": "You are a senior enterprise infrastructure auditor. Be concise, factual, and identify specific SLA/budget breaches.",
        },
        {"role": "user", "content": user_prompt},
    ]

    cache_prompt = os.environ.get(
        "BENCH_CACHE_PROMPT", "true" if warmth.lower() == "warm" else "false"
    ).lower() == "true"

    payload = {
        "model": "local-llama",
        "messages": messages,
        "tools": tools_catalog,
        "tool_choice": "none",
        "temperature": 0.0,
        "seed": 42,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
        "cache_prompt": cache_prompt,
    }

    t0_neural = time.perf_counter()
    prompt_ms = 0.0
    predicted_ms = 0.0
    ttft_ms = 0.0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_cached_tokens = 0
    total_uncached_tokens = 0
    http_status = 0
    finish_reason = ""
    out_chunks: list[str] = []
    has_server_timings = False
    first_chunk = True

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        http_status = resp.status
        if http_status != 200:
            raise RuntimeError(f"W5 llama-server returned HTTP {http_status}")
        for raw_line in resp:
            line = raw_line.decode("utf-8").strip()
            if not line or not line.startswith("data: "):
                continue
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break
            chunk = json.loads(data_str)
            tm = chunk.get("timings")
            if isinstance(tm, dict):
                prompt_ms = float(tm.get("prompt_ms", prompt_ms))
                predicted_ms = float(tm.get("predicted_ms", predicted_ms))
                total_uncached_tokens = int(tm.get("prompt_n", total_uncached_tokens))
                total_completion_tokens = int(tm.get("predicted_n", total_completion_tokens))
                total_cached_tokens = int(tm.get("cache_n", total_cached_tokens))
                has_server_timings = True
            us = chunk.get("usage")
            if isinstance(us, dict):
                if int(us.get("prompt_tokens", 0)) > 0:
                    total_prompt_tokens = int(us["prompt_tokens"])
                if int(us.get("completion_tokens", 0)) > 0:
                    total_completion_tokens = int(us["completion_tokens"])
                det = us.get("prompt_tokens_details") or {}
                if "cached_tokens" in det:
                    total_cached_tokens = int(det["cached_tokens"])
            choices = chunk.get("choices") or []
            if choices:
                c0 = choices[0]
                if c0.get("finish_reason"):
                    finish_reason = str(c0["finish_reason"])
                delta = c0.get("delta") or {}
                content = delta.get("content")
                tc = delta.get("tool_calls")
                if content:
                    out_chunks.append(content)
                if (content or tc) and first_chunk:
                    ttft_ms = (time.perf_counter() - t0_neural) * 1000.0
                    first_chunk = False

    t_neural_wall_ms = (time.perf_counter() - t0_neural) * 1000.0
    t_neural_ms = (prompt_ms + predicted_ms) if has_server_timings else t_neural_wall_ms
    if total_prompt_tokens <= 0:
        total_prompt_tokens = total_cached_tokens + total_uncached_tokens
    if not finish_reason:
        finish_reason = "stop"
    if ttft_ms <= 0.0:
        ttft_ms = prompt_ms if prompt_ms > 0.0 else t_neural_wall_ms
    itl_ms = (
        max(0.01, (t_neural_ms - ttft_ms) / float(total_completion_tokens - 1))
        if total_completion_tokens > 1
        else max(0.01, t_neural_ms / max(1, total_completion_tokens))
    )

    # Measure task completion BEFORE judge call so judge latency does not pollute agent T_orch/T_task
    t_task_ms = (time.perf_counter() - t_start) * 1000.0
    t_orch_ms = max(0.0, t_task_ms - t_neural_ms)
    phi_orch = (t_orch_ms / t_task_ms * 100.0) if t_task_ms > 0 else 0.0
    t_http_ms = max(0.0, t_orch_ms - t_dispatch_ms)

    agent_output = "".join(out_chunks)
    t_eval0 = time.perf_counter()
    eval_res = evaluate_quality(agent_output, timeout_s=min(120.0, timeout_s))
    eval_ms = (time.perf_counter() - t_eval0) * 1000.0
    quality_score = int(eval_res.get("quality_score", 1))
    quality_score = max(1, min(5, quality_score))

    rss_peak = max(rss_idle, _rss_mb())
    cache_hit = bool(total_cached_tokens > 0 and total_uncached_tokens <= 4)
    cache_hit_pct = round((total_cached_tokens / total_prompt_tokens * 100.0) if total_prompt_tokens > 0 else 0.0, 2)

    return {
        "architecture": "LangChain Real-World Agent (W5)",
        "workload": "W5",
        "warmth": warmth,
        "t_task_ms": round(t_task_ms, 3),
        "t_neural_ms": round(t_neural_ms, 3),
        "prompt_ms": round(prompt_ms, 3),
        "predicted_ms": round(predicted_ms, 3),
        "t_orch_ms": round(t_orch_ms, 3),
        "phi_orch_pct": round(phi_orch, 3),
        "ttft_ms": round(ttft_ms, 3),
        "itl_ms": round(itl_ms, 3),
        "t_dispatch_ms": round(t_dispatch_ms, 3),
        "t_prune_ms": 0.0,
        "t_http_ms": round(t_http_ms, 3),
        "t_judge_eval_ms": round(eval_ms, 3),
        "rss_idle_mb": rss_idle,
        "rss_peak_mb": rss_peak,
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "output_tokens": total_completion_tokens,
        "cached_tokens": total_cached_tokens,
        "tokens_cached": total_cached_tokens,
        "prompt_eval_count": total_uncached_tokens,
        "eval_count": total_completion_tokens,
        "cache_hit": cache_hit,
        "uncached_prompt_tokens": total_uncached_tokens,
        "cache_hit_pct": cache_hit_pct,
        "tool_calls": tool_calls_count,
        "http_status": http_status,
        "finish_reason": finish_reason,
        "quality_score": quality_score,
        "evaluation_reasoning": str(eval_res.get("reasoning", "")),
        "output_preview": agent_output[:300],
    }


if __name__ == "__main__":
    warmth_arg = sys.argv[1] if len(sys.argv) > 1 else "Warm"
    result = run_w5_intel_trial(warmth=warmth_arg)
    print(json.dumps(result))
