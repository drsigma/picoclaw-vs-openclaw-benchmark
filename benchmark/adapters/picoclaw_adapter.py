"""
PicoClaw Orchestrator Adapter (Go 1.23.2 Mach-O ARM64)
Adaptador do Orquestrador PicoClaw (Go 1.23.2 Mach-O ARM64)

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

import json
import os
import subprocess
from typing import Any, Dict, List

from benchmark.adapters.base import AgentOrchestratorAdapter


class PicoClawAdapter(AgentOrchestratorAdapter):
    """
    Adapter for Sipeed PicoClaw compiled native Mach-O ARM64 Go binary.
    Adaptador para o binário nativo Go Mach-O ARM64 compilado do Sipeed PicoClaw.
    """

    def __init__(self, repo_dir: str):
        super().__init__(
            name="PicoClaw",
            runtime="Go 1.23.2 (Native Mach-O ARM64)",
            language="Go",
            mode="native_static"
        )
        self.repo_dir = repo_dir
        self.bin_path = os.path.join(repo_dir, "benchmark", "picoclaw_orch")
        self.cli_path = os.path.join(repo_dir, "tools", "picoclaw", "picoclaw")

    def setup(self) -> bool:
        if not os.path.exists(self.bin_path):
            go_src = os.path.join(self.repo_dir, "benchmark", "picoclaw_orch.go")
            if os.path.exists(go_src):
                subprocess.run(
                    ["go", "build", "-o", self.bin_path, go_src],
                    cwd=os.path.join(self.repo_dir, "benchmark"),
                    check=True
                )
        return os.path.exists(self.bin_path)

    def cold_start_cmd(self) -> List[str]:
        if os.path.exists(self.cli_path):
            return [self.cli_path, "version"]
        return [self.bin_path, "version"]

    def run_workload(self, workload_id: str, prompt: str = "", iterations: int = 1) -> Dict[str, Any]:
        cmd = [self.bin_path, workload_id]
        res = subprocess.run(
            cmd,
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
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
            "binary_path": self.bin_path,
            "gc_architecture": "Non-generational tri-color concurrent mark-sweep",
            "concurrency_model": "M:N lightweight Goroutines (~2 KB initial stack)"
        }
