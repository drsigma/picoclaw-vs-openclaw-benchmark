"""
OpenClaw Orchestrator Adapter (Node.js v26 / TypeScript on Google V8)
Adaptador do Orquestrador OpenClaw (Node.js v26 / TypeScript sobre Google V8)

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

import json
import os
import subprocess
from typing import Any, Dict, List

from benchmark.adapters.base import AgentOrchestratorAdapter


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
        res = subprocess.run(
            cmd,
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            env=env,
            check=True
        )
        raw_output = res.stdout.strip()
        data = json.loads(raw_output)
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return data

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
