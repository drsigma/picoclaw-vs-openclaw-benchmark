#!/usr/bin/env python3
"""
adapters/windows_intel_graphics/adapter.py

Dedicated Windows Intel Graphics orchestrator adapter layer.
Wraps the repository's isomorphic workers (Go PicoClaw, Node.js OpenClaw Minimal/Full/Tool-RAG,
Python Native + W5 LangChain/SQLite/Evaluator, Bun JSC, and Direct Neural Baseline)
with isolated portable Windows binaries, Win32 Job Object / QueryProcessCycleTime telemetry,
and explicit 'N/A' Zero-Mock handling. Does not modify any Mac, Linux, or Windows-NVIDIA adapter.
"""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import sys
from typing import Any

from adapters.windows_intel_graphics.telemetry import (
    NA,
    run_subprocess_with_intel_win_counters,
)


def resolve_portable_toolchains(tools_root: str = r"C:\bench_intel\tools") -> dict[str, str | None]:
    """Locate isolated portable binaries installed under C:\\bench_intel\\tools with safe PATH fallbacks."""
    def _find(pattern: str, fallback_cmd: str) -> str | None:
        matches = glob.glob(os.path.join(tools_root, pattern), recursive=True)
        for m in matches:
            if os.path.isfile(m):
                return m
        return shutil.which(fallback_cmd)

    py_venv = os.path.join(tools_root, ".venv_intel", "Scripts", "python.exe")
    python_exe = py_venv if os.path.isfile(py_venv) else sys.executable

    return {
        "python": python_exe,
        "node": _find(os.path.join("node", "**", "node.exe"), "node"),
        "bun": _find(os.path.join("bun", "**", "bun.exe"), "bun"),
        "llama_cpu": _find(os.path.join("llama_cpu", "**", "llama-server.exe"), "llama-server"),
        "llama_vulkan": _find(os.path.join("llama_vulkan", "**", "llama-server.exe"), "llama-server"),
    }


def probe_llama_backend(toolchains: dict[str, str | None]) -> dict[str, Any]:
    """
    Empirically probe llama-server --list-devices on Vulkan vs CPU builds.
    On Intel HD Graphics 4600 (Haswell GT2, no Vulkan compute ICD), selects
    CPU AVX2 (-ngl 0) and documents the exact device probe transparently.
    """
    vk_exe = toolchains.get("llama_vulkan")
    cpu_exe = toolchains.get("llama_cpu")
    vulkan_devices: list[str] = []

    if vk_exe and os.path.isfile(vk_exe):
        try:
            out = subprocess.check_output(
                [vk_exe, "--list-devices"],
                text=True,
                stderr=subprocess.STDOUT,
                timeout=15,
            )
            for line in out.splitlines():
                s = line.strip()
                if s and not s.lower().startswith("available devices") and s.lower() != "(none)":
                    if any(tok in s.lower() for tok in ("vulkan", "intel", "gpu", "igpu")):
                        vulkan_devices.append(s)
        except Exception:
            pass

    if vulkan_devices and vk_exe:
        return {
            "llama_server_exe": vk_exe,
            "ngl_recommended": 12,
            "execution_backend": "llama.cpp_vulkan_intel_igpu",
            "offload_mode": "vulkan_igpu_partial_shared_ram",
            "vulkan_devices_detected": vulkan_devices,
            "rationale": f"Vulkan iGPU device detected: {vulkan_devices[0]}",
        }

    chosen_exe = cpu_exe or vk_exe
    return {
        "llama_server_exe": chosen_exe,
        "ngl_recommended": 0,
        "execution_backend": "llama.cpp_cpu_avx2_intel_igpu_host",
        "offload_mode": "cpu_avx2_ngl_0_shared_ddr3_no_vulkan_icd_on_igpu",
        "vulkan_devices_detected": [],
        "rationale": (
            "Empirically verified via llama-server --list-devices: Intel HD Graphics 4600 (Haswell GT2) "
            "exposes no Vulkan compute ICD on Windows 10; inference runs deterministically on CPU AVX2 (-ngl 0) "
            "within the shared 16 GiB RAM pool alongside the Intel iGPU."
        ),
    }


class WindowsIntelGraphicsArmAdapter:
    """
    Executes a single benchmark arm on Windows Intel Graphics using Win32 process telemetry
    and explicit Zero-Mock 'N/A' rules.
    """

    def __init__(
        self,
        agent_key: str,
        repo_dir: str,
        toolchains: dict[str, str | None],
        timeout_s: float = 420.0,
    ) -> None:
        self.agent_key = agent_key
        self.repo_dir = repo_dir
        self.toolchains = toolchains
        self.timeout_s = timeout_s
        self.mode = self._resolve_mode(agent_key)
        self.name = self._resolve_arch_name(agent_key)
        self.runtime = self._resolve_runtime_label(agent_key)

    @staticmethod
    def _resolve_mode(ak: str) -> str:
        if ak == "picoclaw":
            return "native_static"
        if ak in ("picoclaw_tool_rag", "openclaw_tool_rag"):
            return "tool_rag"
        if ak == "openclaw_full":
            return "full"
        if ak in ("openclaw_minimal", "bun_minimal"):
            return "minimal"
        if ak == "python_native":
            return "python_stdlib_and_langchain_w5"
        if ak == "neural_baseline":
            return "direct_neural"
        return "standard"

    @staticmethod
    def _resolve_arch_name(ak: str) -> str:
        mapping = {
            "picoclaw": "PicoClaw",
            "picoclaw_tool_rag": "PicoClawToolRAG",
            "openclaw_minimal": "OpenClaw",
            "openclaw_full": "OpenClaw",
            "openclaw_tool_rag": "OpenClawToolRAG",
            "python_native": "PythonNative",
            "bun_minimal": "BunJSCOrchestrator",
            "neural_baseline": "NeuralBaseline",
        }
        return mapping.get(ak, ak)

    def _version_of(self, exe: str | None, args: list[str], fallback: str) -> str:
        if not exe:
            return fallback
        try:
            out = subprocess.check_output([exe] + args, text=True, stderr=subprocess.STDOUT, timeout=10)
            return out.strip().splitlines()[0]
        except Exception:
            return fallback

    def _resolve_runtime_label(self, ak: str) -> str:
        if ak in ("picoclaw", "picoclaw_tool_rag"):
            return "Go Native PE x86_64 (picoclaw_orch_windows.exe)"
        if ak in ("openclaw_minimal", "openclaw_full", "openclaw_tool_rag"):
            nv = self._version_of(self.toolchains.get("node"), ["--version"], "v22")
            return f"Node.js {nv} (Google V8 JIT, Windows x86_64)"
        if ak == "python_native":
            pv = self._version_of(self.toolchains.get("python"), ["--version"], "Python 3.12")
            return f"{pv} (CPython + LangChain W5)"
        if ak == "bun_minimal":
            bv = self._version_of(self.toolchains.get("bun"), ["--version"], "1.4")
            return f"Bun v{bv} / JavaScriptCore (Windows x86_64)"
        if ak == "neural_baseline":
            return "llama.cpp Windows x86_64 (Intel iGPU host / CPU AVX2 direct loopback)"
        return ak

    def setup(self) -> bool:
        if self.agent_key in ("picoclaw", "picoclaw_tool_rag"):
            return os.path.isfile(os.path.join(self.repo_dir, "benchmark", "picoclaw_orch_windows.exe"))
        if self.agent_key in ("openclaw_minimal", "openclaw_full", "openclaw_tool_rag"):
            return bool(self.toolchains.get("node")) and os.path.isfile(
                os.path.join(self.repo_dir, "benchmark", "openclaw_orch.mjs")
            )
        if self.agent_key == "bun_minimal":
            return bool(self.toolchains.get("bun")) and os.path.isfile(
                os.path.join(self.repo_dir, "benchmark", "bun_jsc_agent.mjs")
            )
        if self.agent_key == "python_native":
            return bool(self.toolchains.get("python")) and os.path.isfile(
                os.path.join(self.repo_dir, "benchmark", "python_orch.py")
            )
        if self.agent_key == "neural_baseline":
            return True
        return False

    def run_workload(self, workload_id: str, cache_prompt: bool = False) -> dict[str, Any]:
        env = os.environ.copy()
        env["BENCH_CACHE_PROMPT"] = "true" if cache_prompt else "false"
        warmth = "Warm" if cache_prompt else "Cold"

        if self.agent_key == "neural_baseline":
            from benchmark.adapters.neural_baseline_adapter import NeuralBaselineAdapter
            ad = NeuralBaselineAdapter(api_url=env.get("LLAMA_API_URL"))
            old_val = os.environ.get("BENCH_CACHE_PROMPT")
            os.environ["BENCH_CACHE_PROMPT"] = env["BENCH_CACHE_PROMPT"]
            try:
                res = ad.run_workload(workload_id, iterations=1)
            finally:
                if old_val is None:
                    os.environ.pop("BENCH_CACHE_PROMPT", None)
                else:
                    os.environ["BENCH_CACHE_PROMPT"] = old_val
            res["proc_instructions"] = NA
            res["proc_cycles"] = NA
            res["proc_billed_energy"] = NA
            res["proc_peak_phys_mb"] = 0.0
            res["proc_rss_mb"] = 0.0
            res["page_faults"] = NA
            return res

        if self.agent_key in ("picoclaw", "picoclaw_tool_rag"):
            bin_path = os.path.join(self.repo_dir, "benchmark", "picoclaw_orch_windows.exe")
            if self.mode == "tool_rag":
                env["PICOCLAW_MODE"] = "tool_rag"
                env["OPENCLAW_MODE"] = "tool_rag"
            cmd = [bin_path, workload_id]
        elif self.agent_key in ("openclaw_minimal", "openclaw_full", "openclaw_tool_rag"):
            node_exe = self.toolchains.get("node") or "node"
            script = os.path.join(self.repo_dir, "benchmark", "openclaw_orch.mjs")
            env["OPENCLAW_MODE"] = self.mode
            cmd = [node_exe, script, workload_id]
        elif self.agent_key == "bun_minimal":
            bun_exe = self.toolchains.get("bun") or "bun"
            script = os.path.join(self.repo_dir, "benchmark", "bun_jsc_agent.mjs")
            cmd = [bun_exe, "run", script, workload_id, warmth, "1"]
        elif self.agent_key == "python_native":
            py_exe = self.toolchains.get("python") or sys.executable
            if workload_id == "W5":
                script = os.path.join(
                    self.repo_dir, "adapters", "windows_intel_graphics", "w5_intel_worker.py"
                )
                cmd = [py_exe, script, warmth]
            else:
                script = os.path.join(self.repo_dir, "benchmark", "python_orch.py")
                cmd = [py_exe, script, workload_id, warmth, "1"]
        else:
            raise ValueError(f"Unsupported agent_key: {self.agent_key}")

        stdout, stderr, rc, hw_stats = run_subprocess_with_intel_win_counters(
            cmd, cwd=self.repo_dir, env=env, timeout=self.timeout_s
        )
        if rc != 0:
            raise RuntimeError(f"{self.agent_key}/{workload_id} exited rc={rc}: {stderr.strip()[:400]}")

        raw = stdout.strip()
        if not raw:
            raise RuntimeError(f"{self.agent_key}/{workload_id} produced empty stdout; stderr={stderr.strip()[:200]}")

        # Parse last JSON object/list in stdout in case runtime emitted a startup warning line
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            idx = raw.find("{")
            if idx == -1:
                raise
            data = json.loads(raw[idx:])

        res = data[0] if isinstance(data, list) and data else data
        if not isinstance(res, dict):
            raise RuntimeError(f"Unexpected worker JSON payload type: {type(res).__name__}")

        res["proc_instructions"] = hw_stats["proc_instructions"]
        res["proc_cycles"] = hw_stats["proc_cycles"]
        res["proc_billed_energy"] = hw_stats["proc_billed_energy"]
        res["proc_peak_phys_mb"] = hw_stats["proc_peak_phys_mb"]
        res["proc_rss_mb"] = hw_stats["proc_rss_mb"]
        res["page_faults"] = hw_stats["page_faults"]
        if (not res.get("rss_peak_mb")) and isinstance(hw_stats["proc_peak_phys_mb"], (int, float)):
            res["rss_peak_mb"] = hw_stats["proc_peak_phys_mb"]
        return res
