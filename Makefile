# ==============================================================================
# PicoClaw vs. OpenClaw Benchmark Suite — Unified Automation Makefile
# Suíte de Benchmark PicoClaw vs. OpenClaw — Makefile de Automação Unificada
#
# Author / Autor: Rafael Paniccia Cassetta (UFABC)
# Platform / Plataforma: Apple Silicon M4 (macOS darwin-arm64)
# ==============================================================================

SHELL := /bin/bash
VENV_PY := tools/.venv/bin/python
VENV_PYTEST := tools/.venv/bin/pytest

.PHONY: help setup check-quiescence test benchmark reproduce-figures clean

help:
	@echo "========================================================================"
	@echo " 🚀 PicoClaw vs. OpenClaw: Comandos do Makefile / Makefile Targets"
	@echo "========================================================================"
	@echo " [PT-BR] Comandos disponíveis:"
	@echo "   make setup              - Configura venv Python, Node.js e ferramentas embarcadas"
	@echo "   make check-quiescence   - Audita estado térmico, CPU idle e modo anti-sono caffeinate"
	@echo "   make test               - Executa suíte de testes unitários automatizados (pytest)"
	@echo "   make benchmark          - Executa a campanha experimental completa com ablação"
	@echo "   make reproduce-figures  - Regenera todas as 8 figuras científicas em 300 DPI"
	@echo "   make clean              - Remove caches e arquivos temporários de execução"
	@echo ""
	@echo " [EN-US] Available targets:"
	@echo "   make setup              - Provisions isolated Python venv, Node.js, and embedded tools"
	@echo "   make check-quiescence   - Audits thermal state, CPU idle, and caffeinate anti-sleep"
	@echo "   make test               - Runs automated unit test suite via pytest"
	@echo "   make benchmark          - Runs publication-grade benchmark campaign with ablation"
	@echo "   make reproduce-figures  - Recompiles all 8 publication-ready 300-DPI scientific figures"
	@echo "   make clean              - Purges Python/Node caches and temporary execution files"
	@echo "========================================================================"

setup:
	@echo "📦 [PT-BR] Provisionando ambiente de teste..."
	@echo "   [EN-US] Provisioning testbed environment..."
	./tools/setup_environment.sh

check-quiescence:
	@./scripts/check_quiescence.sh

test:
	@echo "🧪 [PT-BR] Executando linter (ruff) e testes unitários automatizados (pytest)..."
	@echo "   [EN-US] Running linter (ruff) and automated unit test suite (pytest)..."
	tools/.venv/bin/ruff check benchmark/ tests/
	$(VENV_PY) -m pytest -v tests/

benchmark: check-quiescence
	@echo "⚡ [PT-BR] Disparando campanha física completa com matriz de ablação..."
	@echo "   [EN-US] Dispatching full physical benchmark campaign with ablation matrix..."
	$(VENV_PY) benchmark/run_unified_benchmark.py

reproduce-figures:
	@echo "📊 [PT-BR] Regenerando figuras científicas em 300 DPI..."
	@echo "   [EN-US] Re-rendering 300-DPI scientific publication figures..."
	$(VENV_PY) benchmark/generate_charts.py

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "🧹 [PT-BR] Caches temporários limpos."
	@echo "   [EN-US] Temporary caches purged."
