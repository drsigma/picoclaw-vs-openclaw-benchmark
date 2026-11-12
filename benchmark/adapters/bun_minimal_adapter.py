"""
Bun Minimal Adapter for OpenClaw
Adaptador Bun Minimal para OpenClaw com suporte a fallback Node.js

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

import json
import os
import shutil
from typing import Any, Dict, List

from benchmark.adapters.base import AgentOrchestratorAdapter
from benchmark.telemetry import run_subprocess_with_rusage


class BunMinimalAdapter(AgentOrchestratorAdapter):
    """Adapter for OpenClaw Minimal executing atop Bun with Node.js fallback."""

    def __init__(self, repo_dir: str):
        super().__init__(
            name="BunMinimal",
            runtime="Bun / JSC (Fallback: Node.js V8)",
            language="TypeScript / JavaScript",
            mode="minimal",
        )
        self.repo_dir = repo_dir
        self.script_path = os.path.join(repo_dir, "benchmark", "openclaw_orch.mjs")
        local_node = os.path.join(repo_dir, "tools", "node", "bin", "node")
        self.runner_bin = shutil.which("bun") or (
            local_node if os.path.exists(local_node) else "node"
        )

    def setup(self) -> bool:
        return os.path.exists(self.script_path)

    def cold_start_cmd(self) -> List[str]:
        return [self.runner_bin, "--version"]

    def teardown(self) -> None:
        pass

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "runtime": self.runtime,
            "language": self.language,
            "mode": self.mode,
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
        cmd.extend([self.script_path, workload_id])

        stdout, stderr, rc, hw = run_subprocess_with_rusage(
            cmd,
            cwd=self.repo_dir,
            env={**os.environ, "OPENCLAW_MODE": "minimal"},
        )
        if rc != 0:
            raise RuntimeError(f"BunMinimal execution failed (code {rc}): {stderr}")

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
        return res
