"""
Python Native Reference Orchestrator Adapter (CPython 3.12 VM)
Adaptador do Orquestrador de Referência Nativo em Python (CPython 3.12 VM)

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

from benchmark.adapters.base import AgentOrchestratorAdapter


class PythonNativeAdapter(AgentOrchestratorAdapter):
    """
    Adapter for Python 3.12 reference agent orchestrator.
    Evaluates CPython VM interpretation, memory layout, and tool dispatch.
    """

    def __init__(self, repo_dir: str, mode: str = "python_stdlib"):
        super().__init__(
            name="PythonNative",
            runtime=f"Python {sys.version.split()[0]} (CPython VM)",
            language="Python",
            mode=mode,
        )
        self.repo_dir = repo_dir
        self.script_path = os.path.join(repo_dir, "benchmark", "python_orch.py")
        venv_py = os.path.join(repo_dir, "tools", ".venv", "bin", "python")
        if os.path.exists(venv_py):
            self.py_bin = venv_py
        else:
            self.py_bin = sys.executable

    def setup(self) -> bool:
        return os.path.exists(self.script_path) and os.path.exists(self.py_bin)

    def cold_start_cmd(self) -> list[str]:
        return [self.py_bin, "-c", "import sys; print(sys.version)"]

    def run_workload(self, workload_id: str, prompt: str = "", iterations: int = 1) -> dict[str, Any]:
        cmd = [self.py_bin, self.script_path, workload_id, "Warm", str(iterations)]
        res = subprocess.run(
            cmd,
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        raw_output = res.stdout.strip()
        data = json.loads(raw_output)
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return data

    def teardown(self) -> None:
        pass

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "runtime": self.runtime,
            "language": self.language,
            "mode": self.mode,
            "tool_catalog_size": 15,
            "interpreter_path": self.py_bin,
            "gc_architecture": "Reference Counting + Cyclic Garbage Collector",
            "concurrency_model": "1:1 OS Threads (GIL bound)",
        }
