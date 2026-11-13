"""
Bun / JavaScriptCore Orchestrator Adapter (Independent 4th Runtime Adapter)
Adaptador Independente Bun / JavaScriptCore executando benchmark/bun_jsc_agent.mjs

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

import json
import os
import shutil
from typing import Any, Dict, List

from benchmark.adapters.base import AgentOrchestratorAdapter
from benchmark.telemetry import run_subprocess_with_rusage


class BunJSCOrchestratorAdapter(AgentOrchestratorAdapter):
    """Independent 4th runtime adapter executing benchmark/bun_jsc_agent.mjs atop native Bun / JavaScriptCore."""

    def __init__(self, repo_dir: str):
        super().__init__(
            name="BunJSCOrchestrator",
            runtime="Bun v1.4.4 / JavaScriptCore (darwin-aarch64)",
            language="JavaScript (ES2024 / Bun JSC Native APIs)",
            mode="minimal",
        )
        self.repo_dir = repo_dir
        self.script_path = os.path.join(repo_dir, "benchmark", "bun_jsc_agent.mjs")
        local_bun = os.path.join(repo_dir, "tools", "bun", "bin", "bun")
        local_node = os.path.join(repo_dir, "tools", "node", "bin", "node")
        self.runner_bin = (
            local_bun
            if os.path.exists(local_bun)
            else (
                shutil.which("bun")
                or (local_node if os.path.exists(local_node) else "node")
            )
        )

    def setup(self) -> bool:
        return os.path.exists(self.script_path)

    def cold_start_cmd(self) -> List[str]:
        return [self.runner_bin, "run", self.script_path, "--version"]

    def teardown(self) -> None:
        pass

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "runtime": self.runtime,
            "language": self.language,
            "mode": self.mode,
            "worker_script": "benchmark/bun_jsc_agent.mjs",
            "runner_binary_used": os.path.basename(self.runner_bin),
            "is_fallback_node": "bun" not in os.path.basename(self.runner_bin),
        }

    def run_workload(
        self, workload_id: str, prompt: str = "", iterations: int = 1
    ) -> Dict[str, Any]:
        runner_base = os.path.basename(self.runner_bin)
        is_bun = "bun" in runner_base
        cmd = [self.runner_bin]
        if is_bun:
            cmd.append("run")
        cmd.extend([self.script_path, workload_id, "Warm", str(iterations)])

        stdout, stderr, rc, hw = run_subprocess_with_rusage(
            cmd,
            cwd=self.repo_dir,
            env={**os.environ},
        )
        if rc != 0:
            raise RuntimeError(f"BunJSCOrchestrator execution failed (code {rc}): {stderr}")

        res = json.loads(stdout.strip())
        res = res[0] if isinstance(res, list) and res else res
        res.update(
            {
                k: hw.get(k, 0)
                for k in (
                    "proc_instructions",
                    "proc_cycles",
                    "proc_billed_energy",
                    "proc_peak_phys_mb",
                )
            }
        )
        res["runner_binary_used"] = runner_base
        res["is_fallback_node"] = not is_bun
        res["worker_script"] = "benchmark/bun_jsc_agent.mjs"
        return res


# Backward-compatible alias
BunMinimalAdapter = BunJSCOrchestratorAdapter
