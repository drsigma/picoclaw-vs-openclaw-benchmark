"""
Adapters Package Initialization and Factory Function
Inicialização do Pacote de Adaptadores e Função Factory

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

from typing import Dict, Type
from benchmark.adapters.base import AgentOrchestratorAdapter
from benchmark.adapters.picoclaw_adapter import PicoClawAdapter
from benchmark.adapters.openclaw_adapter import OpenClawAdapter
from benchmark.adapters.neural_baseline_adapter import NeuralBaselineAdapter


ADAPTER_REGISTRY: Dict[str, Type[AgentOrchestratorAdapter]] = {
    "picoclaw": PicoClawAdapter,
    "openclaw_minimal": lambda repo_dir: OpenClawAdapter(repo_dir, mode="minimal"),
    "openclaw_full": lambda repo_dir: OpenClawAdapter(repo_dir, mode="full"),
    "neural_baseline": lambda repo_dir: NeuralBaselineAdapter(),
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
    "NeuralBaselineAdapter",
    "get_adapter",
    "ADAPTER_REGISTRY"
]
