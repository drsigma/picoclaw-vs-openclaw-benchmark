#!/usr/bin/env python3
"""
benchmark/python_orch.py - Reference Python 3.12 Agent Worker
Evaluates CPython VM dynamic interpretation, memory overhead, JSON serialization,
and tool dispatch under workloads identical to Go and Node.js workers.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import time
import urllib.request

import numpy as np

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


def build_tool_catalog(count: int = 15) -> list[dict]:
    catalog = []
    for i in range(count):
        catalog.append({
            "type": "function",
            "function": {
                "name": f"system_tool_{i}",
                "description": f"Standard system tool descriptor #{i} for agent runtime evaluation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "description": "Action to execute"},
                        "target": {"type": "string", "description": "Target parameter or file path"},
                    },
                    "required": ["action", "target"],
                },
            },
        })
    # Serialization pass
    return json.loads(json.dumps(catalog))


def build_tool_embeddings(n_tools: int = 54) -> np.ndarray:
    dim = 384
    d_idx = np.arange(dim, dtype=np.float64)[None, :]
    i_idx = np.arange(1, n_tools + 1, dtype=np.float64)[:, None]
    mat = np.sin(i_idx * 0.31 + d_idx * 0.13).astype(np.float32)
    norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-8
    return mat / norms


def prune_tools_vector_rag(catalog: list[dict], tool_emb: np.ndarray, tier: str, top_k: int = 5) -> tuple[list[dict], float]:
    t0 = time.monotonic()
    dim = 384
    n_tools = len(catalog)
    if n_tools <= top_k:
        return catalog, 0.0
    tier_seed = {"W1": 1.0, "W2": 2.0, "W3": 3.0, "W4": 4.0}.get(tier, 1.0)

    d_idx = np.arange(dim, dtype=np.float64)
    q_vec = np.cos(tier_seed * 0.37 + d_idx * 0.19).astype(np.float32)
    q_vec = q_vec / (np.linalg.norm(q_vec) + 1e-8)

    scores = np.dot(tool_emb, q_vec)
    top_indices = sorted(int(idx) for idx in np.argsort(scores)[::-1][:top_k])
    pruned = [catalog[idx] for idx in top_indices]
    elapsed_ms = (time.monotonic() - t0) * 1000.0
    return pruned, elapsed_ms


def execute_tool_list_dir(mock_dir: str) -> str:
    entries = sorted(os.listdir(mock_dir))
    files = []
    for name in entries:
        try:
            sz = os.path.getsize(os.path.join(mock_dir, name))
            files.append(f"{name}:{sz}")
        except Exception:
            files.append(f"{name}:0")
    return json.dumps({"count": len(files), "files": files[:10]}, separators=(",", ":"))


def execute_tool_grep_logs(log_file: str) -> tuple[list[float], str]:
    vals: list[float] = []
    pattern = re.compile(r'"subsystem":\s*"UMA_BUS_CONTROLLER"')
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if pattern.search(line):
                try:
                    obj = json.loads(line)
                    lat = obj.get("latency_ms")
                    if isinstance(lat, (int, float)):
                        vals.append(float(lat))
                except Exception:
                    pass
    summary = json.dumps({"matched_records": len(vals), "sample": vals[:5]}, separators=(",", ":"))
    return vals, summary


def execute_tool_calc_stats(vals: list[float]) -> str:
    n = len(vals)
    if n == 0:
        return "{}"
    sum_val = 0.0
    for v in vals:
        sum_val += v
    mean = sum_val / float(n)
    var = 0.0
    for v in vals:
        var += (v - mean) ** 2
    variance = var / float(n - 1) if n > 1 else 0.0
    return json.dumps({"n": n, "mean": mean, "variance": variance, "stddev": math.sqrt(variance)}, separators=(",", ":"))


def execute_vector_rag(base_dir: str) -> str:
    in_dim = 256
    out_dim = 384
    n_docs = 10000

    w_file = os.path.join(base_dir, "w_proj.bin")
    b_file = os.path.join(base_dir, "b_proj.bin")
    docs_bin = os.path.join(base_dir, "doc_embeddings.bin")

    if not (os.path.exists(w_file) and os.path.exists(b_file) and os.path.exists(docs_bin)):
        raise FileNotFoundError(f"FATAL: Required RAG binary datasets missing in {base_dir}")

    w_proj = np.fromfile(w_file, dtype=np.float32).reshape(in_dim, out_dim)
    b_proj = np.fromfile(b_file, dtype=np.float32)
    doc_matrix = np.fromfile(docs_bin, dtype=np.float32).reshape(n_docs, out_dim)

    # 1. Query vector initialization & linear projection
    d_idx = np.arange(in_dim, dtype=np.float32)
    q_raw = np.sin(d_idx * 0.17) * 0.05
    q_proj = np.dot(q_raw, w_proj) + b_proj

    # 2. L2 Normalization of projected query vector
    q_norm = q_proj / (np.linalg.norm(q_proj) + 1e-8)

    # 3. Cosine similarity against all 10,000 document vectors
    scores = np.dot(doc_matrix, q_norm)

    # 4. Descending sort to select Top-5 chunks
    top5_indices = np.argsort(scores)[::-1][:5]

    chunks_file = os.path.join(base_dir, "rag_chunks_10k.json")
    if not os.path.exists(chunks_file):
        raise FileNotFoundError(f"FATAL: rag_chunks_10k.json missing in {base_dir}")

    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    out_lines = []
    for idx in top5_indices:
        text = chunks.get(str(idx), f"[Chunk #{idx:04d}] Context reference document.")
        out_lines.append(text)
    return "\n".join(out_lines) + "\n"


def call_llama_stream(messages: list[dict], tools: list[dict], max_tokens: int) -> tuple[float, float, float, int, int, str, int, str]:
    payload = json.dumps({
        "model": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "messages": messages,
        "tools": tools,
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "seed": 42,
        "stream": True,
        "cache_prompt": os.environ.get("BENCH_CACHE_PROMPT", "false").lower() == "true",
    }, separators=(",", ":")).encode("utf-8")

    t0 = time.monotonic()
    req = urllib.request.Request(API_URL, data=payload, headers={"Content-Type": "application/json"})
    prompt_ms = 0.0
    predicted_ms = 0.0
    has_server_timings = False
    ttft_ms = 0.0
    first_chunk = True
    token_count = 0
    cached_tokens = 0
    uncached_prompt_tokens = 0
    usage_prompt_tokens = 0
    completion_tokens = 0
    finish_reason = ""
    out_text = []

    with urllib.request.urlopen(req, timeout=120) as resp:
        if resp.status != 200:
            raise RuntimeError(f"FATAL: llama-server returned HTTP {resp.status}")
        http_status = resp.status

        for raw_line in resp:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                timings = chunk.get("timings")
                if isinstance(timings, dict):
                    if "prompt_ms" in timings:
                        prompt_ms = float(timings["prompt_ms"])
                        has_server_timings = True
                    if "predicted_ms" in timings:
                        predicted_ms = float(timings["predicted_ms"])
                        has_server_timings = True
                    if "cache_n" in timings and int(timings["cache_n"]) >= 0:
                        cached_tokens = int(timings["cache_n"])
                    if "prompt_n" in timings and int(timings["prompt_n"]) >= 0:
                        uncached_prompt_tokens = int(timings["prompt_n"])
                    if "predicted_n" in timings and int(timings["predicted_n"]) > 0:
                        completion_tokens = int(timings["predicted_n"])

                usage = chunk.get("usage")
                if isinstance(usage, dict):
                    if "prompt_tokens" in usage and int(usage["prompt_tokens"]) > 0:
                        usage_prompt_tokens = int(usage["prompt_tokens"])
                    if "completion_tokens" in usage and int(usage["completion_tokens"]) > 0:
                        completion_tokens = int(usage["completion_tokens"])

                choices = chunk.get("choices")
                if choices and len(choices) > 0:
                    c0 = choices[0]
                    fr = c0.get("finish_reason")
                    if fr:
                        finish_reason = str(fr)
                    delta = c0.get("delta", {})
                    has_data = False
                    content = delta.get("content")
                    if content:
                        has_data = True
                        token_count += 1
                        out_text.append(content)
                    tool_calls = delta.get("tool_calls")
                    if tool_calls:
                        has_data = True
                        token_count += len(tool_calls)
                    if has_data and first_chunk:
                        ttft_ms = (time.monotonic() - t0) * 1000.0
                        first_chunk = False
            except Exception:
                pass

    prompt_tokens = usage_prompt_tokens if usage_prompt_tokens > 0 else (cached_tokens + uncached_prompt_tokens)
    if has_server_timings:
        total_neural_ms = prompt_ms + predicted_ms
    else:
        total_neural_ms = (time.monotonic() - t0) * 1000.0

    if completion_tokens == 0:
        completion_tokens = token_count
    if not finish_reason:
        finish_reason = "stop"

    itl_ms = (total_neural_ms - ttft_ms) / float(completion_tokens - 1) if completion_tokens > 1 else 0.0
    return total_neural_ms, ttft_ms, itl_ms, prompt_tokens, completion_tokens, cached_tokens, uncached_prompt_tokens, finish_reason, http_status, "".join(out_text)


def run_workload(tier: str, warmth: str, rss_idle: float) -> dict:
    t_start = time.monotonic()
    t_neural_total = 0.0
    ttft_first = 0.0
    itl_avg = 0.0
    t_dispatch_total = 0.0
    t_prune_total = 0.0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_cached_tokens = 0
    total_uncached_prompt_tokens = 0
    tool_calls = 0
    last_finish_reason = ""
    last_http_status = 200

    is_tool_rag = (
        os.environ.get("OPENCLAW_MODE") == "tool_rag"
        or os.environ.get("PICOCLAW_MODE") == "tool_rag"
        or os.environ.get("TOOL_RAG_MODE") == "true"
    )

    t_cat0 = time.monotonic()
    if is_tool_rag:
        full_catalog = build_tool_catalog(54)
        tool_emb = build_tool_embeddings(54)
        tool_catalog, tp_ms = prune_tools_vector_rag(full_catalog, tool_emb, tier, 5)
        t_prune_total += tp_ms
    else:
        full_catalog = []
        tool_emb = np.empty((0, 384), dtype=np.float32)
        tool_catalog = build_tool_catalog(15)
    t_cat_ms = (time.monotonic() - t_cat0) * 1000.0

    mock_dir = os.path.join(BASE_DIR, "mock_files")
    log_file = os.path.join(BASE_DIR, "system_logs.jsonl")

    if tier == "W1":
        t_dispatch_total = t_cat_ms
        prompt = (
            "Analyze Apple Silicon M4 Unified Memory Architecture cache coherence and LPDDR5X bandwidth allocation. " * 8
            + "Summarize the primary latency determinant in two concise sentences."
        )
        msgs = [
            {"role": "system", "content": "You are a concise technical systems assistant."},
            {"role": "user", "content": prompt},
        ]
        tn, ttft, itl, ptok, ctok, c_tok, unc_tok, fr, hstatus, _ = call_llama_stream(msgs, tool_catalog, 64)
        t_neural_total = tn
        ttft_first = ttft
        itl_avg = itl
        total_prompt_tokens = ptok
        total_completion_tokens = ctok
        total_cached_tokens = c_tok
        total_uncached_prompt_tokens = unc_tok
        last_finish_reason = fr
        last_http_status = hstatus
        tool_calls = 0

    elif tier == "W2":
        t0_tool = time.monotonic()
        res1 = execute_tool_list_dir(mock_dir)
        vals, res2 = execute_tool_grep_logs(log_file)
        res3 = execute_tool_calc_stats(vals)
        t_dispatch_total = t_cat_ms + (time.monotonic() - t0_tool) * 1000.0
        tool_calls = 3

        prompt = f"System Tool Chain Results:\n1. list_dir: {res1}\n2. grep_logs: {res2}\n3. calc_stats: {res3}\nEvaluate the bus latency metrics and execute the next diagnostic step."
        msgs = [
            {"role": "system", "content": "You are a concise technical systems assistant."},
            {"role": "user", "content": prompt},
        ]
        tn, ttft, itl, ptok, ctok, c_tok, unc_tok, fr, hstatus, _ = call_llama_stream(msgs, tool_catalog, 128)
        t_neural_total = tn
        ttft_first = ttft
        itl_avg = itl
        total_prompt_tokens = ptok
        total_completion_tokens = ctok
        total_cached_tokens = c_tok
        total_uncached_prompt_tokens = unc_tok
        last_finish_reason = fr
        last_http_status = hstatus

    elif tier == "W3":
        t0_tool = time.monotonic()
        rag_context = execute_vector_rag(BASE_DIR)
        t_dispatch_total = t_cat_ms + (time.monotonic() - t0_tool) * 1000.0
        tool_calls = 1

        msgs = [
            {"role": "system", "content": "You are a concise technical systems assistant."},
            {"role": "user", "content": "Retrieved Context:\n" + rag_context + "\nQuestion: How do UMA bandwidth and runtime GC interact during local agent execution?"},
        ]
        tn, ttft, itl, ptok, ctok, c_tok, unc_tok, fr, hstatus, _ = call_llama_stream(msgs, tool_catalog, 256)
        t_neural_total = tn
        ttft_first = ttft
        itl_avg = itl
        total_prompt_tokens = ptok
        total_completion_tokens = ctok
        total_cached_tokens = c_tok
        total_uncached_prompt_tokens = unc_tok
        last_finish_reason = fr
        last_http_status = hstatus

    elif tier == "W4":
        tool_calls = 10
        itl_sum = 0.0
        history = [
            {"role": "system", "content": "You are a concise technical systems assistant."},
        ]
        t_dispatch_total = t_cat_ms
        for step in range(1, 11):
            t0_tool = time.monotonic()
            if is_tool_rag and step > 1:
                tool_catalog, tp_ms = prune_tools_vector_rag(full_catalog, tool_emb, tier, 5)
                t_prune_total += tp_ms
            execute_tool_list_dir(mock_dir)
            vals, _ = execute_tool_grep_logs(log_file)
            stat_str = execute_tool_calc_stats(vals)
            t_dispatch_total += (time.monotonic() - t0_tool) * 1000.0

            history.append({
                "role": "user",
                "content": f"Turn {step} Observation: {stat_str}. State next brief diagnostic action.",
            })
            tn, ttft, itl, ptok, ctok, c_tok, unc_tok, fr, hstatus, reply = call_llama_stream(history, tool_catalog, 64)
            t_neural_total += tn
            if step == 1:
                ttft_first = ttft
            itl_sum += itl
            total_prompt_tokens += ptok
            total_completion_tokens += ctok
            total_cached_tokens += c_tok
            total_uncached_prompt_tokens += unc_tok
            last_finish_reason = fr
            last_http_status = hstatus
            history.append({"role": "assistant", "content": reply})
        itl_avg = itl_sum / 10.0

    if total_prompt_tokens <= 0 or total_completion_tokens <= 0:
        raise RuntimeError(f"FATAL: Validation failed - prompt_tokens ({total_prompt_tokens}) <= 0 or completion_tokens ({total_completion_tokens}) <= 0")

    t_task_ms = (time.monotonic() - t_start) * 1000.0
    t_http_ms = max(0.0, t_task_ms - t_neural_total - t_dispatch_total)
    t_orch_ms = max(0.0, t_task_ms - t_neural_total)
    phi_orch = (t_orch_ms / t_task_ms * 100.0) if t_task_ms > 0 else 0.0
    r_tool = (tool_calls / (t_dispatch_total / 1000.0)) if (tool_calls > 0 and t_dispatch_total > 0) else 0.0
    rss_peak = max(rss_idle, get_rss_mb())
    alpha_mem = rss_peak / max(1.0, rss_idle)
    cache_hit_pct = (total_cached_tokens / total_prompt_tokens * 100.0) if total_prompt_tokens > 0 else 0.0

    return {
        "architecture": "PythonNative (CPython 3.12)",
        "workload": tier,
        "warmth": warmth,
        "t_task_ms": t_task_ms,
        "t_neural_ms": t_neural_total,
        "t_orch_ms": t_orch_ms,
        "phi_orch_pct": phi_orch,
        "ttft_ms": ttft_first,
        "itl_ms": itl_avg,
        "t_dispatch_ms": t_dispatch_total,
        "t_prune_ms": t_prune_total,
        "t_http_ms": t_http_ms,
        "r_tool_ops_sec": r_tool,
        "rss_idle_mb": rss_idle,
        "rss_peak_mb": rss_peak,
        "alpha_mem": alpha_mem,
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "output_tokens": total_completion_tokens,
        "cached_tokens": total_cached_tokens,
        "uncached_prompt_tokens": total_uncached_prompt_tokens,
        "cache_hit_pct": cache_hit_pct,
        "tool_calls": tool_calls,
        "http_status": last_http_status,
        "finish_reason": last_finish_reason,
    }


def run_local_tools_benchmark(tier: str, iterations: int) -> dict:
    mock_dir = os.path.join(BASE_DIR, "mock_files")
    log_file = os.path.join(BASE_DIR, "system_logs.jsonl")
    total_ops = 0
    t0 = time.monotonic()
    if tier == "W2":
        for _ in range(iterations):
            build_tool_catalog(15)
            execute_tool_list_dir(mock_dir)
            vals, _ = execute_tool_grep_logs(log_file)
            execute_tool_calc_stats(vals)
            total_ops += 3
    elif tier == "W3":
        for _ in range(iterations):
            build_tool_catalog(15)
            execute_vector_rag(BASE_DIR)
            total_ops += 1
    else:
        raise ValueError(f"Unsupported tier for local tools: {tier}")
    elapsed_ms = (time.monotonic() - t0) * 1000.0
    return {
        "workload": tier,
        "iterations": iterations,
        "total_ops": total_ops,
        "t_exec_ms": round(elapsed_ms, 3),
    }


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "version", "--help"):
        print("python_orch v1.0.0")
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "--local-tools":
        tier = sys.argv[2] if len(sys.argv) > 2 else "W2"
        iterations = int(sys.argv[3]) if len(sys.argv) > 3 else 200
        res = run_local_tools_benchmark(tier, iterations)
        print(json.dumps([res]))
        return
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
