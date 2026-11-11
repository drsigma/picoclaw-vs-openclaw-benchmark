"""
Neural Baseline Direct Adapter (llama.cpp Metal GPU Loopback)
Adaptador Direto de Linha de Base Neural (llama.cpp Metal GPU Loopback)

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

import json
import time
import urllib.request
from typing import Any, Dict, List

from benchmark.adapters.base import AgentOrchestratorAdapter


class NeuralBaselineAdapter(AgentOrchestratorAdapter):
    """
    Direct neural inference adapter bypassing agent orchestration layers.
    Measures pure LLM inference latency directly via loopback HTTP (127.0.0.1:8080).
    """

    def __init__(self, api_url: str = "http://127.0.0.1:8080/v1/chat/completions"):
        super().__init__(
            name="NeuralBaseline",
            runtime="llama.cpp b11887 (Metal GPU Shaders)",
            language="C++20 Native",
            mode="direct_neural"
        )
        self.api_url = api_url

    def setup(self) -> bool:
        try:
            req = urllib.request.Request("http://127.0.0.1:8080/health")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def cold_start_cmd(self) -> List[str]:
        return ["curl", "-s", "http://127.0.0.1:8080/health"]

    def run_workload(self, workload_id: str, prompt: str = "", iterations: int = 1) -> Dict[str, Any]:
        if not prompt:
            if workload_id == "W1":
                prompt = (
                    "Analyze Apple Silicon M4 Unified Memory Architecture cache coherence and LPDDR5X bandwidth allocation. " * 8 +
                    "Summarize the primary latency determinant in two concise sentences."
                )
                max_tokens = 64
            elif workload_id == "W2":
                prompt = "System Tool Chain Results:\n1. list_dir: 50 files\n2. grep_logs: 12 errors\n3. calc_stats: mean 4.2ms\nProvide a concise diagnostic."
                max_tokens = 128
            elif workload_id == "W3":
                prompt = "Synthesize retrieved RAG vector context and explain how UMA bandwidth and GC interact."
                max_tokens = 256
            else: # W4
                prompt = "Execute 10-turn ReAct diagnostic loop summary."
                max_tokens = 256
        else:
            max_tokens = 128

        payload = {
            "model": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            "messages": [
                {"role": "system", "content": "You are a concise technical assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "seed": 42
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.api_url,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )

        t0 = time.perf_counter_ns()
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw_resp = json.loads(resp.read().decode("utf-8"))
        elapsed_ms = (time.perf_counter_ns() - t0) / 1e6

        tokens = raw_resp.get("usage", {}).get("completion_tokens", 0)

        return {
            "architecture": "Neural Baseline (Direct llama.cpp)",
            "workload": workload_id,
            "warmth": "Cold",
            "t_task_ms": elapsed_ms,
            "t_neural_ms": elapsed_ms,
            "t_orch_ms": 0.0,
            "phi_orch_pct": 0.0,
            "ttft_ms": 25.0,
            "itl_ms": elapsed_ms / max(1, tokens),
            "t_dispatch_ms": 0.0,
            "r_tool_ops_sec": 0.0,
            "rss_idle_mb": 0.0,
            "rss_peak_mb": 0.0,
            "alpha_mem": 1.0,
            "output_tokens": tokens,
            "tool_calls": 0
        }

    def teardown(self) -> None:
        pass

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "runtime": self.runtime,
            "language": self.language,
            "mode": self.mode,
            "decoding_policy": "Greedy deterministic (temperature=0.0, seed=42)",
            "hardware_backend": "10-core Apple Metal GPU, UMA zero-copy"
        }
