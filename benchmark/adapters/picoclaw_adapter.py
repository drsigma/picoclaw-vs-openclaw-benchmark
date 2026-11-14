"""
PicoClaw Orchestrator Adapter (Go 1.23.2 Mach-O ARM64)
Adaptador do Orquestrador PicoClaw (Go 1.23.2 Mach-O ARM64)

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

import json
import os
import shutil
import subprocess
import sys
from typing import Any, Dict, List

from benchmark.adapters.base import AgentOrchestratorAdapter
from benchmark.telemetry import run_subprocess_with_rusage


class PicoClawAdapter(AgentOrchestratorAdapter):
    """
    Adapter for Sipeed PicoClaw compiled native Mach-O ARM64 or Linux ELF x86_64 Go binary.
    Adaptador para o binário nativo Go compilado do Sipeed PicoClaw.
    """

    def __init__(self, repo_dir: str, mode: str = "native_static"):
        is_linux = sys.platform.startswith("linux")
        bin_name = "picoclaw_orch_linux" if is_linux else "picoclaw_orch"
        runtime_str = "Go (Native Linux ELF x86_64)" if is_linux else "Go 1.23.2 (Native Mach-O ARM64)"
        super().__init__(
            name="PicoClaw" if mode != "tool_rag" else "PicoClawToolRAG",
            runtime=runtime_str,
            language="Go",
            mode=mode
        )
        self.repo_dir = repo_dir
        self.bin_path = os.path.join(repo_dir, "benchmark", bin_name)
        self.cli_path = os.path.join(repo_dir, "tools", "picoclaw", "picoclaw")

    def setup(self) -> bool:
        if not os.path.exists(self.bin_path):
            go_src = os.path.join(self.repo_dir, "benchmark", "picoclaw_orch.go")
            go_bin = os.path.join(self.repo_dir, "tools", "go", "bin", "go")
            go_cmd = go_bin if os.path.exists(go_bin) else (shutil.which("go") or "go")
            if os.path.exists(go_src):
                subprocess.run(
                    [go_cmd, "build", "-o", self.bin_path, go_src],
                    cwd=os.path.join(self.repo_dir, "benchmark"),
                    check=True
                )
        return os.path.exists(self.bin_path)

    def cold_start_cmd(self) -> List[str]:
        if os.path.exists(self.cli_path):
            return [self.cli_path, "version"]
        return [self.bin_path, "version"]

    def run_workload(self, workload_id: str, prompt: str = "", iterations: int = 1) -> Dict[str, Any]:
        env = os.environ.copy()
        if self.mode == "tool_rag":
            env["PICOCLAW_MODE"] = "tool_rag"
            env["OPENCLAW_MODE"] = "tool_rag"
        cmd = [self.bin_path, workload_id]
        stdout, stderr, rc, hw_stats = run_subprocess_with_rusage(cmd, cwd=self.repo_dir, env=env)
        if rc != 0:
            raise RuntimeError(f"PicoClaw execution failed (code {rc}): {stderr}")
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
            "binary_path": self.bin_path,
            "gc_architecture": "Non-generational tri-color concurrent mark-sweep",
            "concurrency_model": "M:N lightweight Goroutines (~2 KB initial stack)"
        }
