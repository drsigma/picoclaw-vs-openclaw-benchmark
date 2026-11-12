"""
OpenClaw Orchestrator Adapter (Node.js v26 / TypeScript on Google V8)
Adaptador do Orquestrador OpenClaw (Node.js v26 / TypeScript sobre Google V8)

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

import json
import os
from typing import Any, Dict, List

from benchmark.adapters.base import AgentOrchestratorAdapter
from benchmark.telemetry import run_subprocess_with_rusage


class OpenClawAdapter(AgentOrchestratorAdapter):
    """
    Adapter for OpenClaw orchestrator executing atop Node.js V8.
    Supports ablation modes: 'minimal' (equalized 3 tools) and 'full' (54 tools stock enterprise).
    """

    def __init__(self, repo_dir: str, mode: str = "minimal"):
        super().__init__(
            name="OpenClaw",
            runtime="Node.js v26.12.1 (Google V8 JIT)",
            language="TypeScript / JavaScript",
            mode=mode
        )
        self.repo_dir = repo_dir
        self.script_path = os.path.join(repo_dir, "benchmark", "openclaw_orch.mjs")

        # Locate node binary
        embedded_node = os.path.join(repo_dir, "tools", "node", "bin", "node")
        if os.path.exists(embedded_node):
            self.node_bin = embedded_node
        else:
            self.node_bin = "node"

    def setup(self) -> bool:
        return os.path.exists(self.script_path) and (os.path.exists(self.node_bin) or self.node_bin == "node")

    def cold_start_cmd(self) -> List[str]:
        return [self.node_bin, self.script_path, "--version"]

    def run_workload(self, workload_id: str, prompt: str = "", iterations: int = 1) -> Dict[str, Any]:
        env = os.environ.copy()
        env["OPENCLAW_MODE"] = self.mode
        cmd = [self.node_bin, self.script_path, workload_id]
        stdout, stderr, rc, hw_stats = run_subprocess_with_rusage(cmd, cwd=self.repo_dir, env=env)
        if rc != 0:
            raise RuntimeError(f"OpenClaw execution failed (code {rc}): {stderr}")
        raw_output = stdout.strip()
        data = json.loads(raw_output)
        if isinstance(data, list) and len(data) > 0:
            res = data[0]
        else:
            res = data
        res["proc_instructions"] = hw_stats.get("proc_instructions", 0)
        res["proc_cycles"] = hw_stats.get("proc_cycles", 0)
        res["proc_billed_energy"] = hw_stats.get("proc_billed_energy", 0)
        res["proc_peak_phys_mb"] = hw_stats.get("proc_peak_phys_mb", 0.0)
        if res.get("rss_peak_mb", 0.0) == 0.0 and hw_stats.get("proc_rss_mb", 0.0) > 0.0:
            res["rss_peak_mb"] = hw_stats["proc_rss_mb"]
        return res

    def teardown(self) -> None:
        pass

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "runtime": self.runtime,
            "language": self.language,
            "mode": self.mode,
            "tool_catalog_size": 54 if self.mode == "full" else 15,
            "node_binary": self.node_bin,
            "gc_architecture": "Generational mark-compact (Scavenger + Old Space)",
            "schema_validator": "TypeBox (@sinclair/typebox JSON-Schema)"
        }
