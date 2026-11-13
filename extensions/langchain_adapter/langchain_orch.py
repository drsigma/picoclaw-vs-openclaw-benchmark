#!/usr/bin/env python3
"""
extensions/langchain_adapter/langchain_orch.py - External Market Framework Orchestrator (LangChain)
Elsevier SoftwareX: picoclaw-vs-openclaw-benchmark (Gate C1)

Implements the standard benchmark agent contract using langchain-core:
  - Pydantic v2 argument schemas
  - StructuredTool definitions for system tools (list_dir, grep_logs, calc_stats)
  - Tool calling and message state tracking via HumanMessage, AIMessage, ToolMessage
  - Direct HTTP streaming / batch calls to llama-server at http://127.0.0.1:8080/v1/chat/completions

Evaluates the real-world orchestrator overhead (T_orch, peak physical RAM, dispatch delay)
introduced by enterprise Python agent abstraction layers compared to lightweight native runtimes.

Author: Rafael Paniccia Cassetta (UFABC)
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
import time
import urllib.request
from typing import Any, List, Optional

import numpy as np
from pydantic import BaseModel, Field

# Ensure langchain_core is available
try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
    from langchain_core.tools import StructuredTool
except ImportError:
    print("FATAL: langchain-core is not installed in the active environment.", file=sys.stderr)
    sys.exit(1)

REPO_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API_URL = os.environ.get("LLAMA_API_URL", "http://127.0.0.1:8080/v1/chat/completions")
BASE_DIR = os.environ.get("WORKLOAD_DATA_DIR", os.path.join(REPO_DIR, "data", "workload_data"))


def get_rss_mb() -> float:
    try:
        import resource
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        if sys.platform == "darwin":
            return rusage.ru_maxrss / (1024.0 * 1024.0)
        return rusage.ru_maxrss / 1024.0
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Pydantic Schemas and StructuredTools for Workloads W1-W4
# ---------------------------------------------------------------------------

class SystemToolInput(BaseModel):
    action: str = Field(description="Action to execute")
    target: str = Field(description="Target parameter or file path")


class ListDirInput(BaseModel):
    dir_path: str = Field(default="", description="Path of directory to list")


class GrepLogsInput(BaseModel):
    pattern: str = Field(description="Regex pattern to grep in logs")
    file_path: str = Field(default="", description="Log file path")


class CalcStatsInput(BaseModel):
    values: List[float] = Field(description="List of floating-point values")


def tool_list_dir(dir_path: str = "") -> str:
    path = dir_path or os.path.join(BASE_DIR, "mock_files")
    if not os.path.exists(path):
        return json.dumps([])
    files = sorted(os.listdir(path))
    return json.dumps(files)


def tool_grep_logs(pattern: str, file_path: str = "") -> str:
    path = file_path or os.path.join(BASE_DIR, "system_logs.jsonl")
    if not os.path.exists(path):
        return json.dumps({"count": 0, "values": []})
    matched_vals = []
    reg = re.compile(pattern)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                msg = rec.get("message", "")
                if reg.search(msg):
                    if "duration_ms" in rec:
                        matched_vals.append(float(rec["duration_ms"]))
                    elif "val" in rec:
                        matched_vals.append(float(rec["val"]))
            except Exception:
                pass
    return json.dumps({"count": len(matched_vals), "values": matched_vals})


def tool_calc_stats(values: List[float]) -> str:
    if not values:
        return json.dumps({"mean": 0.0, "std": 0.0, "median": 0.0})
    arr = np.array(values, dtype=np.float64)
    res = {
        "mean": round(float(np.mean(arr)), 4),
        "std": round(float(np.std(arr)), 4),
        "median": round(float(np.median(arr)), 4),
    }
    return json.dumps(res)


def build_langchain_tools(count: int = 15) -> list[StructuredTool]:
    """Builds StructuredTools conforming to standard LangChain runtime schemas."""
    tools = [
        StructuredTool.from_function(
            func=tool_list_dir,
            name="system_tool_0",
            description="List mock directory files",
            args_schema=ListDirInput,
        ),
        StructuredTool.from_function(
            func=tool_grep_logs,
            name="system_tool_1",
            description="Grep matching lines from mock system log files",
            args_schema=GrepLogsInput,
        ),
        StructuredTool.from_function(
            func=tool_calc_stats,
            name="system_tool_2",
            description="Calculate summary statistics on extracted log values",
            args_schema=CalcStatsInput,
        ),
    ]
    for i in range(3, count):
        def make_dummy(tool_id):
            return lambda action, target: json.dumps({"status": "ok", "tool": f"system_tool_{tool_id}", "action": action, "target": target})
        t = StructuredTool.from_function(
            func=make_dummy(i),
            name=f"system_tool_{i}",
            description=f"Standard system tool descriptor #{i} for agent runtime evaluation.",
            args_schema=SystemToolInput,
        )
        tools.append(t)
    return tools


def format_openai_tools(lc_tools: list[StructuredTool]) -> list[dict]:
    """Converts LangChain StructuredTools into OpenAI tool calling descriptors."""
    oa_tools = []
    for t in lc_tools:
        oa_tools.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.args_schema.model_json_schema() if t.args_schema else {"type": "object", "properties": {}},
            },
        })
    return oa_tools


def execute_vector_rag(base_dir: str) -> float:
    head_file = os.path.join(base_dir, "mock_files", "head.bin")
    rag_file = os.path.join(base_dir, "rag_chunks.jsonl")
    dim = 384
    n_docs = 100
    if os.path.exists(head_file):
        with open(head_file, "rb") as f:
            mat = np.frombuffer(f.read(), dtype=np.float32).reshape((dim, dim))
    else:
        mat = np.eye(dim, dtype=np.float32)

    vecs = []
    if os.path.exists(rag_file):
        with open(rag_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    d = json.loads(line)
                    vecs.append(d.get("embedding", [0.0] * dim))
    if not vecs:
        vecs = [list(np.ones(dim, dtype=np.float32) * 0.05) for _ in range(n_docs)]
    doc_mat = np.array(vecs, dtype=np.float32)
    q = np.ones(dim, dtype=np.float32) / math.sqrt(dim)
    q_proj = np.dot(mat, q)
    scores = np.dot(doc_mat, q_proj)
    return float(np.max(scores))


# ---------------------------------------------------------------------------
# Core Workload Execution via LangChain Abstraction
# ---------------------------------------------------------------------------

def call_llama_api(
    messages: list[dict],
    tools: list[dict],
    cache_prompt: bool = True,
    max_tokens: int = 128,
) -> tuple[dict, float, int]:
    payload = {
        "messages": messages,
        "tools": tools,
        "stream": True,
        "stream_options": {"include_usage": True},
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "cache_prompt": cache_prompt,
    }
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers={"Content-Type": "application/json"})

    t0 = time.perf_counter()
    status_code = 200
    assembled_role = "assistant"
    assembled_content = ""
    tool_calls_map: dict[int, dict] = {}
    finish_reason = None
    timings = {}
    usage = {}

    with urllib.request.urlopen(req, timeout=120) as resp:
        status_code = resp.status
        for raw_line in resp:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            content = line[5:].strip()
            if content == "[DONE]":
                break
            try:
                chunk = json.loads(content)
                t_chunk = chunk.get("timings")
                if t_chunk:
                    timings.update(t_chunk)
                u_chunk = chunk.get("usage")
                if u_chunk:
                    usage.update(u_chunk)
                choices = chunk.get("choices", [])
                if choices:
                    c0 = choices[0]
                    fr = c0.get("finish_reason")
                    if fr:
                        finish_reason = fr
                    delta = c0.get("delta", {})
                    if "content" in delta and delta["content"]:
                        assembled_content += delta["content"]
                    if "tool_calls" in delta and delta["tool_calls"]:
                        for tc in delta["tool_calls"]:
                            idx = tc.get("index", 0)
                            if idx not in tool_calls_map:
                                tool_calls_map[idx] = {
                                    "id": tc.get("id", f"call_lc_{idx}"),
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""},
                                }
                            fn = tc.get("function", {})
                            if "name" in fn and fn["name"]:
                                tool_calls_map[idx]["function"]["name"] += fn["name"]
                            if "arguments" in fn and fn["arguments"]:
                                tool_calls_map[idx]["function"]["arguments"] += fn["arguments"]
            except Exception:
                pass

    t_neural_elapsed_ms = (time.perf_counter() - t0) * 1000.0
    tool_calls = [tool_calls_map[i] for i in sorted(tool_calls_map.keys())]

    res_msg: dict[str, Any] = {"role": assembled_role}
    if assembled_content:
        res_msg["content"] = assembled_content
    if tool_calls:
        res_msg["tool_calls"] = tool_calls

    metrics = {
        "t_neural_ms": t_neural_elapsed_ms,
        "prompt_ms": float(timings.get("prompt_ms", 0.0)),
        "predicted_ms": float(timings.get("predicted_ms", 0.0)),
        "ttft_ms": float(timings.get("prompt_ms", t_neural_elapsed_ms)),
        "prompt_tokens": int(usage.get("prompt_tokens", timings.get("prompt_n", 0))),
        "completion_tokens": int(usage.get("completion_tokens", timings.get("predicted_n", 0))),
        "cached_tokens": int(timings.get("cache_n", 0)),
        "uncached_prompt_tokens": int(timings.get("prompt_n", 0)),
        "finish_reason": finish_reason or "stop",
        "http_status": status_code,
    }
    return res_msg, t_neural_elapsed_ms, status_code, metrics


def run_workload(tier: str, warmth: str = "Cold", rss_idle: float = 0.0) -> dict[str, Any]:
    cache_prompt = (warmth.lower() == "warm")
    t_start = time.perf_counter()

    # 1. Orchestration: build LangChain StructuredTools and convert to OpenAI schema
    t_orch_0 = time.perf_counter()
    lc_tools = build_langchain_tools(count=15)
    oa_tools = format_openai_tools(lc_tools)
    tool_lookup = {t.name: t for t in lc_tools}

    # Initialize LangChain message state
    system_prompt = (
        "You are an enterprise AI systems benchmark agent orchestrated via LangChain Core. "
        "Analyze requests, invoke available tools via StructuredTool schemas, and provide structured outputs."
    )
    lc_messages = [
        SystemMessage(content=system_prompt),
    ]

    t_dispatch_total = 0.0
    t_neural_total = 0.0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_cached_tokens = 0
    total_uncached_tokens = 0
    total_prompt_ms = 0.0
    total_predicted_ms = 0.0
    tool_calls_count = 0
    last_status = 200
    last_finish = "stop"
    ttft_first = 0.0

    if tier == "W1":
        lc_messages.append(HumanMessage(content="Evaluate the system environment status and confirm agent readiness."))
        t_orch_1 = time.perf_counter()
        t_orch_prep = (t_orch_1 - t_orch_0) * 1000.0

        raw_msgs = [{"role": "system", "content": lc_messages[0].content}, {"role": "user", "content": lc_messages[1].content}]
        res_msg, t_neural, status, m = call_llama_api(raw_msgs, oa_tools, cache_prompt=cache_prompt, max_tokens=16)

        t_neural_total = t_neural
        total_prompt_tokens = m["prompt_tokens"]
        total_completion_tokens = m["completion_tokens"]
        total_cached_tokens = m["cached_tokens"]
        total_uncached_tokens = m["uncached_prompt_tokens"]
        total_prompt_ms = m["prompt_ms"]
        total_predicted_ms = m["predicted_ms"]
        ttft_first = m["ttft_ms"]
        last_status = status
        last_finish = m["finish_reason"]

        t_orch_post_0 = time.perf_counter()
        # Parse into LangChain AIMessage
        lc_ai = AIMessage(content=res_msg.get("content", ""))
        lc_messages.append(lc_ai)
        t_orch_total = t_orch_prep + ((time.perf_counter() - t_orch_post_0) * 1000.0)

    elif tier == "W2":
        # Multi-tool ReAct dispatch loop
        lc_messages.append(HumanMessage(content="Analyze mock system logs in data directory: list directory files, grep error patterns, and calculate statistics."))
        t_orch_prep = (time.perf_counter() - t_orch_0) * 1000.0

        raw_msgs = [{"role": "system", "content": lc_messages[0].content}, {"role": "user", "content": lc_messages[1].content}]
        res_msg, t_neural, status, m = call_llama_api(raw_msgs, oa_tools, cache_prompt=cache_prompt, max_tokens=64)

        t_neural_total += t_neural
        total_prompt_tokens += m["prompt_tokens"]
        total_completion_tokens += m["completion_tokens"]
        total_cached_tokens += m["cached_tokens"]
        total_uncached_tokens += m["uncached_prompt_tokens"]
        total_prompt_ms += m["prompt_ms"]
        total_predicted_ms += m["predicted_ms"]
        ttft_first = m["ttft_ms"]
        last_status = status
        last_finish = m["finish_reason"]

        t_disp_0 = time.perf_counter()
        # Execute tools through LangChain StructuredTool dispatch
        t_calls = res_msg.get("tool_calls", [])
        if not t_calls:
            # Deterministic dispatch fall-through for benchmark standardization
            t_calls = [
                {"id": "call_0", "function": {"name": "system_tool_0", "arguments": json.dumps({"dir_path": ""})}},
                {"id": "call_1", "function": {"name": "system_tool_1", "arguments": json.dumps({"pattern": "WARN|ERROR", "file_path": ""})}},
                {"id": "call_2", "function": {"name": "system_tool_2", "arguments": json.dumps({"values": [12.5, 45.2, 88.1, 102.3, 14.7]})}},
            ]

        lc_ai = AIMessage(content=res_msg.get("content", ""), tool_calls=[{"name": tc["function"]["name"], "args": json.loads(tc["function"]["arguments"] or "{}"), "id": tc.get("id", "call")} for tc in t_calls])
        lc_messages.append(lc_ai)

        for tc in t_calls:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"] or "{}")
            t_obj = tool_lookup.get(fn_name)
            if t_obj:
                out_str = t_obj.invoke(fn_args)
            else:
                out_str = json.dumps({"status": "unknown_tool"})
            tool_calls_count += 1
            lc_messages.append(ToolMessage(content=str(out_str), tool_call_id=tc.get("id", "call_id")))

        t_dispatch_total = (time.perf_counter() - t_disp_0) * 1000.0

        # Follow-up completion turn
        raw_followup = [{"role": "system", "content": system_prompt}, {"role": "user", "content": "Execute log analysis and summarize."}]
        res_followup, t_n2, st2, m2 = call_llama_api(raw_followup, oa_tools, cache_prompt=cache_prompt, max_tokens=32)
        t_neural_total += t_n2
        total_prompt_tokens += m2["prompt_tokens"]
        total_completion_tokens += m2["completion_tokens"]
        total_cached_tokens += m2["cached_tokens"]
        total_uncached_tokens += m2["uncached_prompt_tokens"]
        total_prompt_ms += m2["prompt_ms"]
        total_predicted_ms += m2["predicted_ms"]

        t_orch_total = t_orch_prep + t_dispatch_total

    elif tier == "W3":
        # Vector RAG Workload
        t_disp_0 = time.perf_counter()
        rag_score = execute_vector_rag(BASE_DIR)
        t_dispatch_total = (time.perf_counter() - t_disp_0) * 1000.0
        tool_calls_count += 1

        lc_messages.append(HumanMessage(content=f"Synthesize the retrieved context with similarity score {rag_score:.4f}."))
        t_orch_prep = (time.perf_counter() - t_orch_0) * 1000.0

        raw_msgs = [{"role": "system", "content": system_prompt}, {"role": "user", "content": lc_messages[-1].content}]
        res_msg, t_neural, status, m = call_llama_api(raw_msgs, oa_tools, cache_prompt=cache_prompt, max_tokens=64)

        t_neural_total = t_neural
        total_prompt_tokens = m["prompt_tokens"]
        total_completion_tokens = m["completion_tokens"]
        total_cached_tokens = m["cached_tokens"]
        total_uncached_tokens = m["uncached_prompt_tokens"]
        total_prompt_ms = m["prompt_ms"]
        total_predicted_ms = m["predicted_ms"]
        ttft_first = m["ttft_ms"]
        last_status = status
        last_finish = m["finish_reason"]

        t_orch_total = t_orch_prep + t_dispatch_total

    elif tier == "W4":
        # 10-turn multi-turn autonomous ReAct loop
        n_turns = 10
        t_orch_accum = (time.perf_counter() - t_orch_0) * 1000.0
        for turn_idx in range(n_turns):
            user_msg = f"Turn {turn_idx+1}: Update log analysis state and query next records."
            lc_messages.append(HumanMessage(content=user_msg))

            raw_msgs = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_msg}]
            res_msg, t_neural, status, m = call_llama_api(raw_msgs, oa_tools, cache_prompt=cache_prompt, max_tokens=16)

            t_neural_total += t_neural
            total_prompt_tokens += m["prompt_tokens"]
            total_completion_tokens += m["completion_tokens"]
            total_cached_tokens += m["cached_tokens"]
            total_uncached_tokens += m["uncached_prompt_tokens"]
            total_prompt_ms += m["prompt_ms"]
            total_predicted_ms += m["predicted_ms"]
            if turn_idx == 0:
                ttft_first = m["ttft_ms"]
            last_status = status
            last_finish = m["finish_reason"]

            t_disp_0 = time.perf_counter()
            tool_res = tool_list_dir("")
            tool_calls_count += 1
            lc_messages.append(ToolMessage(content=tool_res, tool_call_id=f"turn_{turn_idx}"))
            t_dispatch_total += (time.perf_counter() - t_disp_0) * 1000.0

        t_orch_total = t_orch_accum + t_dispatch_total
    else:
        raise ValueError(f"Unknown workload tier: {tier}")

    t_task_ms = (time.perf_counter() - t_start) * 1000.0
    rss_peak = get_rss_mb()
    alpha_mem = rss_peak - rss_idle if rss_peak > rss_idle else 0.0

    phi_orch = (t_orch_total / t_task_ms * 100.0) if t_task_ms > 0 else 0.0
    itl_avg = (total_predicted_ms / total_completion_tokens) if total_completion_tokens > 0 else 0.0
    cache_hit_pct = (total_cached_tokens / total_prompt_tokens * 100.0) if total_prompt_tokens > 0 else 0.0

    return {
        "runtime": "langchain_core",
        "agent_key": "langchain_core",
        "workload": tier,
        "warmth": warmth,
        "t_task_ms": round(t_task_ms, 2),
        "t_neural_ms": round(t_neural_total, 2),
        "prompt_ms": round(total_prompt_ms, 2),
        "predicted_ms": round(total_predicted_ms, 2),
        "t_orch_ms": round(t_orch_total, 3),
        "phi_orch_pct": round(phi_orch, 3),
        "ttft_ms": round(ttft_first, 2),
        "itl_ms": round(itl_avg, 2),
        "t_dispatch_ms": round(t_dispatch_total, 3),
        "rss_idle_mb": round(rss_idle, 2),
        "rss_peak_mb": round(rss_peak, 2),
        "proc_peak_phys_mb": round(rss_peak, 2),
        "alpha_mem": round(alpha_mem, 2),
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "output_tokens": total_completion_tokens,
        "cached_tokens": total_cached_tokens,
        "uncached_prompt_tokens": total_uncached_tokens,
        "cache_hit_pct": round(cache_hit_pct, 2),
        "tool_calls": tool_calls_count,
        "http_status": last_status,
        "finish_reason": last_finish,
    }


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "version", "--help"):
        print("langchain_orch v1.0.0 (langchain-core 1.8.0)")
        sys.exit(0)
    tier = sys.argv[1] if len(sys.argv) > 1 else "W1"
    warmth = sys.argv[2] if len(sys.argv) > 2 else "Cold"
    reps = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    rss_idle = get_rss_mb()
    results = []
    for _ in range(reps):
        res = run_workload(tier, warmth, rss_idle)
        results.append(res)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
