"""
Adapters Package Initialization and Factory Function
Inicialização do Pacote de Adaptadores e Função Factory

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""
from typing import Callable, Dict

from benchmark.adapters.base import AgentOrchestratorAdapter
from benchmark.adapters.bun_minimal_adapter import BunMinimalAdapter
from benchmark.adapters.neural_baseline_adapter import NeuralBaselineAdapter
from benchmark.adapters.openclaw_adapter import OpenClawAdapter
from benchmark.adapters.picoclaw_adapter import PicoClawAdapter
from benchmark.adapters.python_native_adapter import PythonNativeAdapter

ADAPTER_REGISTRY: Dict[str, Callable[[str], AgentOrchestratorAdapter]] = {
    "picoclaw": lambda repo_dir: PicoClawAdapter(repo_dir),
    "openclaw_minimal": lambda repo_dir: OpenClawAdapter(repo_dir, mode="minimal"),
    "openclaw_full": lambda repo_dir: OpenClawAdapter(repo_dir, mode="full"),
    "python_native": lambda repo_dir: PythonNativeAdapter(repo_dir),
    "neural_baseline": lambda repo_dir: NeuralBaselineAdapter(),
    "bun_minimal": lambda repo_dir: BunMinimalAdapter(repo_dir),
}


def get_adapter(name: str, repo_dir: str) -> AgentOrchestratorAdapter:
    """
    Instantiate and return an orchestrator adapter by registry key.
    Instancia e retorna um adaptador de orquestrador pela chave de registro.
    """
    key = name.lower()
    if key not in ADAPTER_REGISTRY:
        raise ValueError(f"Unknown adapter '{name}'. Available: {list(ADAPTER_REGISTRY.keys())}")
    factory = ADAPTER_REGISTRY[key]
    return factory(repo_dir)


__all__ = [
    "AgentOrchestratorAdapter",
    "PicoClawAdapter",
    "OpenClawAdapter",
    "PythonNativeAdapter",
    "NeuralBaselineAdapter",
    "BunMinimalAdapter",
    "get_adapter",
    "ADAPTER_REGISTRY",
]
