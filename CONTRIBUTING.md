# Contributing to the AI Agent Benchmark Suite
# Guia de Contribuição e Extensibilidade da Suíte de Benchmark

Welcome! This document guides researchers and software engineers on extending the benchmark suite with new AI agent runtimes (e.g., Rust, C++, Zig, Mojo, Java, Elixir).

Bem-vindo! Este documento orienta pesquisadores e engenheiros de software sobre como estender a suíte de benchmark com novos ambientes de execução de agentes de IA (ex: Rust, C++, Zig, Mojo, Java, Elixir).

---

## 3-Step Guide to Implementing a New Agent Adapter
## Guia em 3 Passos para Implementar um Novo Adaptador de Agente

The benchmark framework employs the **Strategy / Adapter Pattern** (`benchmark/adapters/base.py`) to decouple agent execution from workload orchestration and telemetry.

O framework utiliza o **Padrão Strategy / Adapter** (`benchmark/adapters/base.py`) para desacoplar a execução do agente da orquestração de cargas e telemetria.

### Step 1: Subclass `AgentOrchestratorAdapter` / Passo 1: Subclassificar `AgentOrchestratorAdapter`

Create a new adapter file in `benchmark/adapters/my_agent_adapter.py`:
Crie um novo arquivo de adaptador em `benchmark/adapters/my_agent_adapter.py`:

```python
"""
benchmark/adapters/my_agent_adapter.py - Example Custom Adapter
"""
from typing import Any, Dict, List
import json
import os

from benchmark.adapters.base import AgentOrchestratorAdapter
from benchmark.telemetry import run_subprocess_with_rusage


class MyAgentAdapter(AgentOrchestratorAdapter):
    """Custom Agent Orchestrator Adapter."""

    def __init__(self, repo_dir: str, mode: str = "standard"):
        super().__init__(
            name="MyAgent",
            runtime="Rust / Native (Mach-O ARM64)",
            language="Rust",
            mode=mode,
        )
        self.repo_dir = repo_dir
        self.bin_path = os.path.join(repo_dir, "bin", "my_agent")

    def setup(self) -> bool:
        """Verify binary exists or compile from source."""
        return os.path.exists(self.bin_path)

    def cold_start_cmd(self) -> List[str]:
        """CLI invocation command for cold-start benchmarking via hyperfine."""
        return [self.bin_path, "--version"]

    def run_workload(self, workload_id: str, prompt: str = "", iterations: int = 1) -> Dict[str, Any]:
        """
        Execute workload W1-W4, polling POSIX Darwin libproc / Linux psutil counters.
        Returns a dictionary containing latency, memory, and token metrics.
        """
        cmd = [self.bin_path, workload_id]
        stdout, stderr, rc, hw_stats = run_subprocess_with_rusage(cmd, cwd=self.repo_dir)
        if rc != 0:
            raise RuntimeError(f"MyAgent execution failed (code {rc}): {stderr}")

        data = json.loads(stdout.strip())
        res = data[0] if isinstance(data, list) else data

        # Incorporate kernel microarchitectural counters
        res["proc_instructions"] = hw_stats.get("proc_instructions", 0)
        res["proc_cycles"] = hw_stats.get("proc_cycles", 0)
        res["proc_billed_energy"] = hw_stats.get("proc_billed_energy", 0)
        res["proc_peak_phys_mb"] = hw_stats.get("proc_peak_phys_mb", 0.0)
        if res.get("rss_peak_mb", 0.0) == 0.0:
            res["rss_peak_mb"] = hw_stats.get("proc_rss_mb", 0.0)

        return res

    def teardown(self) -> None:
        """Cleanup temporary caches or daemons."""
        pass

    def metadata(self) -> Dict[str, Any]:
        """Return architectural descriptors for reproducibility reporting."""
        return {
            "name": self.name,
            "runtime": self.runtime,
            "language": self.language,
            "mode": self.mode,
        }
```

### Step 2: Register in `ADAPTER_REGISTRY` / Passo 2: Registrar no `ADAPTER_REGISTRY`

Open `benchmark/adapters/__init__.py` and add your factory constructor:
Abra `benchmark/adapters/__init__.py` e adicione o construtor factory:

```python
from benchmark.adapters.my_agent_adapter import MyAgentAdapter

ADAPTER_REGISTRY: Dict[str, Callable[[str], AgentOrchestratorAdapter]] = {
    "picoclaw": lambda repo_dir: PicoClawAdapter(repo_dir),
    "openclaw_minimal": lambda repo_dir: OpenClawAdapter(repo_dir, mode="minimal"),
    "openclaw_full": lambda repo_dir: OpenClawAdapter(repo_dir, mode="full"),
    "python_native": lambda repo_dir: PythonNativeAdapter(repo_dir),
    "neural_baseline": lambda repo_dir: NeuralBaselineAdapter(),
    "my_agent": lambda repo_dir: MyAgentAdapter(repo_dir),  # <-- Added
}
```

### Step 3: Verify with Automated Tests / Passo 3: Validar com Testes Automatizados

Run the test suite and fast verification to ensure contract compliance:
Execute a suíte de testes e a verificação rápida para garantir conformidade de contrato:

```bash
# 1. Run unit test suite and ruff linter
make test

# 2. Verify portable dry-run pipeline in /tmp
tools/.venv/bin/python benchmark/run_unified_benchmark.py --dry-run --output-dir /tmp/test_eval
```

---

## Code of Conduct & Academic Standards / Código de Conduta e Padrões Acadêmicos

1. **Strict Zero Synthetic Proxies / Proibição Estrita de Dados Sintéticos:**
   Never substitute failed live executions with hardcoded constants or synthetic random generators (`np.random.normal`). Implement loud fail-fast exceptions (`RuntimeError`) if a live server is unreachable.
   Nunca substitua falhas de execução real por constantes fixas ou geradores sintéticos. Implemente exceções ruidosas fail-fast (`RuntimeError`).

2. **Bilingual Documentation / Documentação Bilíngue:**
   Maintain symmetry between Portuguese (PT-BR) and English (EN-US) across all docstrings, commit messages, and Markdown documentation.
   Mantenha simetria entre Português (PT-BR) e Inglês (EN-US) em docstrings e documentação.

3. **Non-Destructive Testing / Testes Não-Destrutivos:**
   Never overwrite `results/publication_campaign/raw_trials.jsonl` during unit testing or dry-runs. Always use `--output-dir /tmp/...` for ad-hoc evaluations.
   Nunca sobrescreva os dados da campanha física de publicação durante testes unitários ou verificações locais.
