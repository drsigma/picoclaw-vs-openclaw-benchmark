"""
Unit Tests for Adapter Registry & Fail-Fast Architecture
Testes Unitários para Registro de Adaptadores e Arquitetura Fail-Fast

Author / Autor: Rafael Paniccia Cassetta (UFABC)
Language / Idioma: Bilingual (PT-BR & EN-US comments, English code)
"""

import os

import pytest

from benchmark.adapters import ADAPTER_REGISTRY, get_adapter
from benchmark.adapters.base import AgentOrchestratorAdapter
from benchmark.run_unified_benchmark import (
    check_server_health,
    run_campaign,
    start_mock_server_if_needed,
)

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_adapter_registry_contains_all_five_agents():
    """Verify all 5 evaluation targets are registered in ADAPTER_REGISTRY."""
    expected_agents = {
        "picoclaw",
        "openclaw_minimal",
        "openclaw_full",
        "python_native",
        "neural_baseline",
    }
    registered = set(ADAPTER_REGISTRY.keys())
    assert expected_agents.issubset(registered), f"Missing agents: {expected_agents - registered}"


def test_adapter_instances_subclass_base_adapter():
    """Verify every registered adapter conforms to AgentOrchestratorAdapter interface."""
    for name in ADAPTER_REGISTRY:
        adapter = get_adapter(name, REPO_DIR)
        assert isinstance(adapter, AgentOrchestratorAdapter)
        assert hasattr(adapter, "run_workload")
        assert hasattr(adapter, "setup")
        assert hasattr(adapter, "cold_start_cmd")
        assert hasattr(adapter, "name")
        assert hasattr(adapter, "language")
        assert hasattr(adapter, "runtime")


def test_adapter_run_workload_across_targets(monkeypatch):
    """Verify each adapter runs workload W1 deterministically in standard test environment."""
    mock_port = 8088
    start_mock_server_if_needed(mock_port)
    monkeypatch.setenv("LLAMA_API_URL", f"http://127.0.0.1:{mock_port}/v1/chat/completions")

    for name in ADAPTER_REGISTRY:
        adapter = get_adapter(name, REPO_DIR)
        result = adapter.run_workload("W1")
        assert isinstance(result, dict)
        assert len(result) > 0


def test_fail_fast_on_unreachable_server(monkeypatch):
    """
    Verify fail-fast policy: when dry_run=False and the neural server port is offline,
    the pipeline immediately raises RuntimeError instead of generating synthetic data.
    """
    # Test health check against an offline loopback port (59999)
    offline_url = "http://127.0.0.1:59999/health"
    is_healthy = check_server_health(url=offline_url, timeout=0.2)
    assert is_healthy is False

    # Point LLAMA_HEALTH_URL to the offline port
    monkeypatch.setenv("LLAMA_HEALTH_URL", offline_url)

    # Verify run_campaign fails fast with RuntimeError when target port is offline
    with pytest.raises(RuntimeError) as exc_info:
        run_campaign(reps_per_condition=1, dry_run=False)

    assert "llama-server not reachable" in str(exc_info.value)
