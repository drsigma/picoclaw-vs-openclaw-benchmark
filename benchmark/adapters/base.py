"""
Base Abstract Adapter for AI Agent Orchestrators
Interface Base Abstrata para Adaptadores de Orquestradores de Agentes de IA

Author / Autor: Rafael Paniccia Cassetta (UFABC)
Language / Idioma: Python 3.12+ (English source code, bilingual docstrings)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class AgentOrchestratorAdapter(ABC):
    """
    Abstract Base Class defining the contract for benchmarking AI agent orchestrators.
    Classe Base Abstrata que define o contrato para benchmark de orquestradores de agentes de IA.
    """

    def __init__(self, name: str, runtime: str, language: str, mode: str = "standard"):
        self.name = name
        self.runtime = runtime
        self.language = language
        self.mode = mode

    @abstractmethod
    def setup(self) -> bool:
        """
        Verify prerequisites, compile binaries or install dependencies.
        Verifica pré-requisitos, compila binários ou instala dependências.
        """
        pass

    @abstractmethod
    def cold_start_cmd(self) -> List[str]:
        """
        Return the CLI command used for cold-start latency measurement via hyperfine.
        Retorna o comando CLI usado para medição de cold-start via hyperfine.
        """
        pass

    @abstractmethod
    def run_workload(self, workload_id: str, prompt: str, iterations: int = 1) -> Dict[str, Any]:
        """
        Execute a standardized workload (W1-W4) and return structured telemetry.
        Executa uma carga de trabalho padronizada (W1-W4) e retorna telemetria estruturada.
        """
        pass

    @abstractmethod
    def teardown(self) -> None:
        """
        Cleanup temporary session files, caches, or background processes.
        Limpa arquivos temporários de sessão, caches ou processos em segundo plano.
        """
        pass

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Return architectural and environment metadata for provenance tracking.
        Retorna metadados arquiteturais e de ambiente para rastreabilidade de proveniência.
        """
        pass
