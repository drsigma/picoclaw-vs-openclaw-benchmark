#!/usr/bin/env python3
"""
tests/test_sse_cache_hit_usage.py

Regression test for 100% KV-cache hit SSE responses from llama-server:
  - Verifies stream_options.include_usage=True is sent in streaming requests across
    Go (PicoClaw), Python (python_orch.py), Node.js (openclaw_orch.mjs), and Bun.
  - Simulates a llama-server SSE stream returning prompt_n=0, cache_n=917 and/or
    usage.prompt_tokens=917 with a final EOF chunk lacking a trailing newline,
    confirming prompt_tokens == 917 (> 0) with zero panic or dropped final chunk.
"""
from __future__ import annotations

import http.server
import json
import os
import platform
import shutil
import socketserver
import subprocess
import sys
import threading

import pytest

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _MockLlamaSSEServer:
    """Ephemeral local HTTP server returning controlled llama-server SSE streams."""

    def __init__(self, sse_body: bytes) -> None:
        self.sse_body = sse_body
        self.captured_requests: list[dict] = []
        self._httpd: socketserver.TCPServer | None = None
        self._thread: threading.Thread | None = None
        self.url: str = ""

    def __enter__(self) -> "_MockLlamaSSEServer":
        parent = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                parent.captured_requests.append(json.loads(raw.decode("utf-8")))
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(parent.sse_body)))
                self.end_headers()
                self.wfile.write(parent.sse_body)
                self.wfile.flush()

            def log_message(self, format, *args):  # noqa: A002
                return

        self._httpd = socketserver.TCPServer(("127.0.0.1", 0), Handler)
        port = self._httpd.server_address[1]
        self.url = f"http://127.0.0.1:{port}/v1/chat/completions"
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self._thread:
            self._thread.join(timeout=3.0)


def _picoclaw_binary_for_host() -> str | None:
    sys_name = platform.system()
    if sys_name == "Windows":
        p = os.path.join(REPO_DIR, "benchmark", "picoclaw_orch_windows.exe")
    elif sys_name == "Linux":
        p = os.path.join(REPO_DIR, "benchmark", "picoclaw_orch_linux")
    else:
        p = os.path.join(REPO_DIR, "benchmark", "picoclaw_orch")
    return p if os.path.isfile(p) else None


def test_all_streaming_orchestrators_request_include_usage():
    """Static verification that every streaming orchestrator sets include_usage=true."""
    targets = [
        ("benchmark/picoclaw_orch_windows.go", "IncludeUsage: true"),
        ("benchmark/picoclaw_orch.go", "IncludeUsage: true"),
        ("benchmark/openclaw_orch.mjs", "include_usage: true"),
        ("benchmark/bun_jsc_agent.mjs", "include_usage: true"),
        ("benchmark/python_orch.py", '"include_usage": True'),
        ("benchmark/adapters/neural_baseline_adapter.py", '"include_usage": True'),
        ("adapters/windows_intel_graphics/w5_intel_worker.py", '"include_usage": True'),
        ("scripts/run_linux_x86_64_master_campaign.py", '"include_usage": True'),
        ("scripts/run_windows_x86_64_master_campaign.py", '"include_usage": True'),
    ]
    for rel_path, needle in targets:
        full_path = os.path.join(REPO_DIR, rel_path)
        assert os.path.isfile(full_path), f"Missing orchestrator file: {rel_path}"
        with open(full_path, "r", encoding="utf-8") as f:
            src = f.read()
        assert needle in src, f"{rel_path} missing streaming usage option ({needle!r})"


@pytest.mark.parametrize(
    "include_usage_field",
    [True, False],
    ids=["usage_plus_timings_eof_no_newline", "timings_only_prompt_n_zero_eof_no_newline"],
)
def test_picoclaw_binary_handles_100pct_kv_cache_hit_and_eof_chunk(include_usage_field: bool):
    """
    Runs the compiled Go PicoClaw binary against a mock SSE server simulating a 100% KV-cache
    hit (prompt_n=0, cache_n=917) where the final chunk carrying timings/usage has NO trailing
    newline before EOF. Verifies zero panic, stream_options.include_usage=True, and prompt_tokens=917.
    """
    bin_path = _picoclaw_binary_for_host()
    if bin_path is None:
        pytest.skip("No compiled picoclaw binary available for this host OS")
    # Skip if binary is an ELF binary on macOS Darwin
    if platform.system() == "Darwin":
        with open(bin_path, "rb") as bf:
            if bf.read(4) == b"\x7fELF":
                pytest.skip("benchmark/picoclaw_orch is Linux ELF; cannot execute on Darwin")

    final_payload: dict = {
        "choices": [{"delta": {}, "finish_reason": "stop"}],
        "timings": {
            "prompt_n": 0,
            "cache_n": 917,
            "predicted_n": 28,
            "prompt_ms": 0.0,
            "predicted_ms": 125.4,
        },
    }
    if include_usage_field:
        final_payload["usage"] = {
            "prompt_tokens": 917,
            "completion_tokens": 28,
            "prompt_tokens_details": {"cached_tokens": 917},
        }

    # Intentionally omit trailing '\n' on the final EOF chunk to test EOF line processing
    chunk1 = 'data: {"choices":[{"delta":{"content":"ok"},"finish_reason":null}]}\n\n'
    chunk2 = "data: " + json.dumps(final_payload, separators=(",", ":"))
    sse_bytes = (chunk1 + chunk2).encode("utf-8")

    with _MockLlamaSSEServer(sse_bytes) as srv:
        env = os.environ.copy()
        env["LLAMA_API_URL"] = srv.url
        env["BENCH_CACHE_PROMPT"] = "true"
        env["PICOCLAW_MODE"] = "tool_rag"
        env["OPENCLAW_MODE"] = "tool_rag"

        res = subprocess.run(
            [bin_path, "W1", "Warm", "1"],
            cwd=REPO_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=20.0,
        )
        assert res.returncode == 0, f"PicoClaw panicked/failed (rc={res.returncode}): stderr={res.stderr}"
        assert len(srv.captured_requests) == 1
        req_json = srv.captured_requests[0]
        assert req_json.get("stream") is True
        assert req_json.get("stream_options") == {"include_usage": True}

        records = json.loads(res.stdout.strip())
        assert isinstance(records, list) and len(records) == 1
        rec = records[0]
        assert rec["prompt_tokens"] == 917
        assert rec["cached_tokens"] == 917
        assert rec["uncached_prompt_tokens"] == 0
        assert rec["completion_tokens"] == 28
        assert rec["cache_hit"] is True
        assert rec["http_status"] == 200


def test_python_and_node_orchestrators_handle_100pct_kv_cache_hit_eof_chunk():
    """Verifies python_orch.py and openclaw_orch.mjs parse 100% cache-hit EOF chunks cleanly."""
    final_payload = {
        "choices": [{"delta": {}, "finish_reason": "stop"}],
        "timings": {
            "prompt_n": 0,
            "cache_n": 917,
            "predicted_n": 28,
            "prompt_ms": 0.0,
            "predicted_ms": 110.0,
        },
        "usage": {
            "prompt_tokens": 917,
            "completion_tokens": 28,
            "prompt_tokens_details": {"cached_tokens": 917},
        },
    }
    sse_bytes = (
        'data: {"choices":[{"delta":{"content":"ok"},"finish_reason":null}]}\n\n'
        + "data: "
        + json.dumps(final_payload, separators=(",", ":"))
    ).encode("utf-8")

    # 1. Python native orchestrator
    with _MockLlamaSSEServer(sse_bytes) as srv:
        env = os.environ.copy()
        env["LLAMA_API_URL"] = srv.url
        env["BENCH_CACHE_PROMPT"] = "true"
        res_py = subprocess.run(
            [sys.executable, os.path.join(REPO_DIR, "benchmark", "python_orch.py"), "W1", "Warm", "1"],
            cwd=REPO_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=20.0,
        )
        assert res_py.returncode == 0, f"python_orch.py failed: {res_py.stderr}"
        assert srv.captured_requests[0].get("stream_options") == {"include_usage": True}
        rec_py = json.loads(res_py.stdout.strip())[0]
        assert rec_py["prompt_tokens"] == 917
        assert rec_py["cached_tokens"] == 917
        assert rec_py["completion_tokens"] == 28

    # 2. Node.js OpenClaw orchestrator (requires Node >= 18 for global fetch)
    node_exe = shutil.which("node")
    if node_exe:
        ver_out = subprocess.check_output([node_exe, "--version"], text=True).strip().lstrip("v")
        major = int(ver_out.split(".")[0]) if ver_out and ver_out[0].isdigit() else 0
        if major >= 18:
            with _MockLlamaSSEServer(sse_bytes) as srv:
                env = os.environ.copy()
                env["LLAMA_API_URL"] = srv.url
                env["BENCH_CACHE_PROMPT"] = "true"
                env["OPENCLAW_MODE"] = "tool_rag"
                res_js = subprocess.run(
                    [node_exe, os.path.join(REPO_DIR, "benchmark", "openclaw_orch.mjs"), "W1", "Warm", "1"],
                    cwd=REPO_DIR,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=20.0,
                )
                assert res_js.returncode == 0, f"openclaw_orch.mjs failed: {res_js.stderr}"
                assert srv.captured_requests[0].get("stream_options") == {"include_usage": True}
                rec_js = json.loads(res_js.stdout.strip())[0]
                assert rec_js["prompt_tokens"] == 917
                assert rec_js["cached_tokens"] == 917
                assert rec_js["completion_tokens"] == 28

            # 3. Bun/JSC minimal agent orchestrator (compatible with Bun or Node >= 18)
            js_runner = shutil.which("bun") or node_exe
            with _MockLlamaSSEServer(sse_bytes) as srv:
                env = os.environ.copy()
                env["LLAMA_API_URL"] = srv.url
                env["BENCH_CACHE_PROMPT"] = "true"
                res_bun = subprocess.run(
                    [js_runner, os.path.join(REPO_DIR, "benchmark", "bun_jsc_agent.mjs"), "W1", "Warm", "1"],
                    cwd=REPO_DIR,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=20.0,
                )
                assert res_bun.returncode == 0, f"bun_jsc_agent.mjs failed: {res_bun.stderr}"
                assert srv.captured_requests[0].get("stream_options") == {"include_usage": True}
                rec_bun = json.loads(res_bun.stdout.strip())[0]
                assert rec_bun["prompt_tokens"] == 917
                assert rec_bun["cached_tokens"] == 917
                assert rec_bun["completion_tokens"] == 28
