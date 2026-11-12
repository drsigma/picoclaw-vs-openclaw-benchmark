import json
import os
import shutil

from benchmark.adapters.base import AgentOrchestratorAdapter
from benchmark.telemetry import run_subprocess_with_rusage


class BunMinimalAdapter(AgentOrchestratorAdapter):
    """Adapter for OpenClaw Minimal executing atop Bun with Node.js fallback."""

    def __init__(self, repo_dir: str):
        super().__init__(name="BunMinimal", runtime="Bun / JSC (Fallback: Node.js V8)", language="TypeScript / JavaScript", mode="minimal")
        self.repo_dir, self.script_path = repo_dir, os.path.join(repo_dir, "benchmark", "openclaw_orch.mjs")
        n = os.path.join(repo_dir, "tools", "node", "bin", "node")
        self.runner_bin = shutil.which("bun") or (n if os.path.exists(n) else "node")
    def setup(self) -> bool:
        return os.path.exists(self.script_path)
    def cold_start_cmd(self) -> list[str]:
        return [self.runner_bin, "--version"]
    def teardown(self) -> None:
        pass
    def metadata(self) -> dict:
        return {"name": self.name, "runtime": self.runtime, "language": self.language, "mode": self.mode}
    def run_workload(self, workload_id: str, prompt: str = "", iterations: int = 1) -> dict:
        cmd = [c for c in [self.runner_bin, "run" if "bun" in os.path.basename(self.runner_bin) else "", self.script_path, workload_id] if c]
        stdout, stderr, rc, hw = run_subprocess_with_rusage(cmd, cwd=self.repo_dir, env={**os.environ, "OPENCLAW_MODE": "minimal"})
        if rc != 0:
            raise RuntimeError(f"BunMinimal execution failed (code {rc}): {stderr}")
        res = json.loads(stdout.strip())
        res = res[0] if isinstance(res, list) and res else res
        res.update({k: hw.get(k, 0) for k in ("proc_instructions", "proc_cycles", "proc_billed_energy", "proc_peak_phys_mb")})
        return res
