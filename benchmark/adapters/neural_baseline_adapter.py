"""
Neural Baseline Direct Adapter (llama.cpp Metal GPU Loopback)
Adaptador Direto de Linha de Base Neural (llama.cpp Metal GPU Loopback)

Author / Autor: Rafael Paniccia Cassetta (UFABC)
Language / Idioma: Python 3.12+ (English source code, bilingual docstrings)
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from typing import Any

from benchmark.adapters.base import AgentOrchestratorAdapter
from benchmark.python_orch import (
    build_tool_catalog,
    execute_tool_calc_stats,
    execute_tool_grep_logs,
    execute_tool_list_dir,
    execute_vector_rag,
)

REPO_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = os.environ.get("WORKLOAD_DATA_DIR", os.path.join(REPO_DIR, "data", "workload_data"))


class NeuralBaselineAdapter(AgentOrchestratorAdapter):
    """
    Direct neural inference adapter bypassing agent orchestration layers.
    Measures pure LLM inference latency directly via loopback HTTP (127.0.0.1:8080)
    executing the exact same sequence of HTTP completions, tool schemas (15 tools),
    and prompt payloads as the worker runtimes, ensuring identical prompt_tokens on Metal GPU.
    """

    def __init__(self, api_url: str | None = None):
        super().__init__(
            name="NeuralBaseline",
            runtime="llama.cpp b11887 (Metal GPU Shaders)",
            language="C++20 Native",
            mode="direct_neural",
        )
        self.api_url = api_url or os.environ.get("LLAMA_API_URL", "http://127.0.0.1:8080/v1/chat/completions")
        self.tools = build_tool_catalog(15)

    def setup(self) -> bool:
        health_url = self.api_url.replace("/v1/chat/completions", "/health")
        try:
            req = urllib.request.Request(health_url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def cold_start_cmd(self) -> list[str]:
        return ["curl", "-s", "http://127.0.0.1:8080/health"]

    def _call_stream(self, messages: list[dict], tools: list[dict], max_tokens: int) -> tuple[float, float, float, int, str]:
        payload = json.dumps({
            "model": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            "messages": messages,
            "tools": tools,
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "seed": 42,
            "stream": True,
        }).encode("utf-8")

        t0 = time.monotonic()
        req = urllib.request.Request(self.api_url, data=payload, headers={"Content-Type": "application/json"})
        prompt_ms = 0.0
        predicted_ms = 0.0
        has_server_timings = False
        ttft_ms = 0.0
        first_chunk = True
        token_count = 0
        out_text = []

        with urllib.request.urlopen(req, timeout=120) as resp:
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

                    choices = chunk.get("choices")
                    if choices and len(choices) > 0:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            if first_chunk:
                                ttft_ms = (time.monotonic() - t0) * 1000.0
                                first_chunk = False
                            token_count += 1
                            out_text.append(content)
                        tool_calls = delta.get("tool_calls")
                        if tool_calls:
                            if first_chunk:
                                ttft_ms = (time.monotonic() - t0) * 1000.0
                                first_chunk = False
                            token_count += len(tool_calls)
                except Exception:
                    pass

        if has_server_timings:
            total_neural_ms = prompt_ms + predicted_ms
        else:
            total_neural_ms = (time.monotonic() - t0) * 1000.0

        itl_ms = (total_neural_ms - ttft_ms) / float(token_count - 1) if token_count > 1 else 0.0
        return total_neural_ms, ttft_ms, itl_ms, token_count, "".join(out_text)

    def run_workload(self, workload_id: str, prompt: str = "", iterations: int = 1) -> dict[str, Any]:
        t_neural_total = 0.0
        ttft_first = 0.0
        itl_avg = 0.0
        total_tokens = 0

        mock_dir = os.path.join(BASE_DIR, "mock_files")
        log_file = os.path.join(BASE_DIR, "system_logs.jsonl")

        if workload_id == "W1":
            p = (
                "Analyze Apple Silicon M4 Unified Memory Architecture cache coherence and LPDDR5X bandwidth allocation. " * 8
                + "Summarize the primary latency determinant in two concise sentences."
            )
            msgs = [
                {"role": "system", "content": "You are a concise technical systems assistant."},
                {"role": "user", "content": p},
            ]
            tn, ttft, itl, ntok, _ = self._call_stream(msgs, self.tools, 64)
            t_neural_total = tn
            ttft_first = ttft
            itl_avg = itl
            total_tokens = ntok

        elif workload_id == "W2":
            res1 = execute_tool_list_dir(mock_dir)
            vals, res2 = execute_tool_grep_logs(log_file)
            res3 = execute_tool_calc_stats(vals)
            p = f"System Tool Chain Results:\n1. list_dir: {res1}\n2. grep_logs: {res2}\n3. calc_stats: {res3}\nProvide a concise technical diagnostic summary of the bus latency metrics."
            msgs = [
                {"role": "system", "content": "You are a concise technical systems assistant."},
                {"role": "user", "content": p},
            ]
            tn, ttft, itl, ntok, _ = self._call_stream(msgs, self.tools, 128)
            t_neural_total = tn
            ttft_first = ttft
            itl_avg = itl
            total_tokens = ntok

        elif workload_id == "W3":
            rag_context = execute_vector_rag(BASE_DIR)
            msgs = [
                {"role": "system", "content": "You are a concise technical systems assistant."},
                {"role": "user", "content": "Retrieved Context:\n" + rag_context + "\nQuestion: How do UMA bandwidth and runtime GC interact during local agent execution?"},
            ]
            tn, ttft, itl, ntok, _ = self._call_stream(msgs, self.tools, 256)
            t_neural_total = tn
            ttft_first = ttft
            itl_avg = itl
            total_tokens = ntok

        elif workload_id == "W4":
            history = [
                {"role": "system", "content": "You are a concise technical systems assistant."},
            ]
            itl_sum = 0.0
            for step in range(1, 11):
                vals, _ = execute_tool_grep_logs(log_file)
                stat_str = execute_tool_calc_stats(vals)
                history.append({
                    "role": "user",
                    "content": f"Turn {step} Observation: {stat_str}. State next brief diagnostic action.",
                })
                tn, ttft, itl, ntok, reply = self._call_stream(history, self.tools, 64)
                t_neural_total += tn
                if step == 1:
                    ttft_first = ttft
                itl_sum += itl
                total_tokens += ntok
                history.append({"role": "assistant", "content": reply})
            itl_avg = itl_sum / 10.0

        # For Neural Baseline, task time is exactly neural inference time with 0 orchestrator overhead
        t_task_ms = t_neural_total

        return {
            "architecture": "Neural Baseline (Direct llama.cpp)",
            "workload": workload_id,
            "warmth": "Cold",
            "t_task_ms": t_task_ms,
            "t_neural_ms": t_neural_total,
            "t_orch_ms": 0.0,
            "phi_orch_pct": 0.0,
            "ttft_ms": ttft_first,
            "itl_ms": itl_avg,
            "t_dispatch_ms": 0.0,
            "r_tool_ops_sec": 0.0,
            "rss_idle_mb": 0.0,
            "rss_peak_mb": 0.0,
            "proc_instructions": 0,
            "proc_cycles": 0,
            "proc_billed_energy": 0,
            "proc_peak_phys_mb": 0.0,
            "alpha_mem": 1.0,
            "output_tokens": total_tokens,
            "tool_calls": 0,
        }

    def teardown(self) -> None:
        pass

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "runtime": self.runtime,
            "language": self.language,
            "mode": self.mode,
            "tool_catalog_size": 15,
            "endpoint": self.api_url,
            "gc_architecture": "None (C++ Manual Allocation)",
            "concurrency_model": "Native POSIX Threads (OpenMP / pthread)",
        }
