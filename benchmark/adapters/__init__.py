"""
Adapters Package Initialization and Factory Function
Inicialização do Pacote de Adaptadores e Função Factory

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""
from typing import Callable, Dict

from benchmark.adapters.base import AgentOrchestratorAdapter
from benchmark.adapters.bun_minimal_adapter import (
    BunJSCOrchestratorAdapter,
    BunMinimalAdapter,
)
from benchmark.adapters.neural_baseline_adapter import NeuralBaselineAdapter
from benchmark.adapters.openclaw_adapter import OpenClawAdapter
from benchmark.adapters.picoclaw_adapter import PicoClawAdapter
from benchmark.adapters.python_native_adapter import PythonNativeAdapter

# Neutral Architecture-First Class Aliases
GoNativeOrchestratorAdapter = PicoClawAdapter
NodeV8OrchestratorAdapter = OpenClawAdapter
PythonReferenceAdapter = PythonNativeAdapter
LocalLLMBaselineAdapter = NeuralBaselineAdapter

ADAPTER_REGISTRY: Dict[str, Callable[[str], AgentOrchestratorAdapter]] = {
    # Canonical Neutral Architecture Keys
    "go_orchestrator": lambda repo_dir: GoNativeOrchestratorAdapter(repo_dir),
    "go_orchestrator_tool_rag": lambda repo_dir: GoNativeOrchestratorAdapter(repo_dir, mode="tool_rag"),
    "node_orchestrator": lambda repo_dir: NodeV8OrchestratorAdapter(repo_dir, mode="minimal"),
    "node_orchestrator_minimal": lambda repo_dir: NodeV8OrchestratorAdapter(repo_dir, mode="minimal"),
    "node_orchestrator_full": lambda repo_dir: NodeV8OrchestratorAdapter(repo_dir, mode="full"),
    "node_orchestrator_tool_rag": lambda repo_dir: NodeV8OrchestratorAdapter(repo_dir, mode="tool_rag"),
    "python_reference_agent": lambda repo_dir: PythonReferenceAdapter(repo_dir),
    "local_llm_baseline": lambda repo_dir: LocalLLMBaselineAdapter(),
    "bun_jsc_orchestrator": lambda repo_dir: BunJSCOrchestratorAdapter(repo_dir),
    # Compatible Product-Reference Aliases
    "picoclaw": lambda repo_dir: GoNativeOrchestratorAdapter(repo_dir),
    "picoclaw_tool_rag": lambda repo_dir: GoNativeOrchestratorAdapter(repo_dir, mode="tool_rag"),
    "openclaw_minimal": lambda repo_dir: NodeV8OrchestratorAdapter(repo_dir, mode="minimal"),
    "openclaw_full": lambda repo_dir: NodeV8OrchestratorAdapter(repo_dir, mode="full"),
    "openclaw_tool_rag": lambda repo_dir: NodeV8OrchestratorAdapter(repo_dir, mode="tool_rag"),
    "python_native": lambda repo_dir: PythonReferenceAdapter(repo_dir),
    "neural_baseline": lambda repo_dir: LocalLLMBaselineAdapter(),
    "bun_minimal": lambda repo_dir: BunJSCOrchestratorAdapter(repo_dir),
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
    "GoNativeOrchestratorAdapter",
    "NodeV8OrchestratorAdapter",
    "PythonReferenceAdapter",
    "LocalLLMBaselineAdapter",
    "BunJSCOrchestratorAdapter",
    "PicoClawAdapter",
    "OpenClawAdapter",
    "PythonNativeAdapter",
    "NeuralBaselineAdapter",
    "BunMinimalAdapter",
    "get_adapter",
    "ADAPTER_REGISTRY",
]
