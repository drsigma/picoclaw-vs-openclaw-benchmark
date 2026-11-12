# ==============================================================================
# PicoClaw vs. OpenClaw Benchmark Suite — Unified Automation Makefile
# Suíte de Benchmark PicoClaw vs. OpenClaw — Makefile de Automação Unificada
#
# Author / Autor: Rafael Paniccia Cassetta (UFABC)
# Platform / Plataforma: Apple Silicon M4 (macOS darwin-arm64)
# ==============================================================================

SHELL := /bin/bash
VENV_PY := $(shell if [ -f tools/.venv/bin/python ]; then echo tools/.venv/bin/python; else echo python3; fi)

.PHONY: help setup check-quiescence test verify dry-run simulate-campaign benchmark benchmark-full-smc reproduce-figures clean

help:
	@echo "========================================================================"
	@echo " 🚀 PicoClaw vs. OpenClaw: Comandos do Makefile / Makefile Targets"
	@echo "========================================================================"
	@echo " [PT-BR] Comandos disponíveis:"
	@echo "   make setup              - Configura venv Python, Node.js e ferramentas embarcadas"
	@echo "   make check-quiescence   - Audita estado térmico, CPU idle e modo anti-sono caffeinate"
	@echo "   make test               - Executa linter (ruff) e testes unitários automatizados"
	@echo "   make verify             - Valida integridade criptográfica dos artefatos (SHA-256)"
	@echo "   make dry-run            - Verificação rápida portátil para revisores (Modo Dry-Run / CI)"
	@echo "   make benchmark          - Executa campanha experimental completa (espaço de usuário comum)"
	@echo "   make benchmark-full-smc - Executa com sudo powermetrics para telemetria elétrica completa do SMC"
	@echo "   make reproduce-figures  - Regenera todas as figuras científicas em 300 DPI"
	@echo "   make clean              - Remove caches e arquivos temporários de execução"
	@echo ""
	@echo " [EN-US] Available targets:"
	@echo "   make setup              - Provisions isolated Python venv, Node.js, and embedded tools"
	@echo "   make check-quiescence   - Audits thermal state, CPU idle, and caffeinate anti-sleep"
	@echo "   make test               - Runs linter (ruff) and automated unit test suite"
	@echo "   make verify             - Validates cryptographic artifact integrity (SHA-256)"
	@echo "   make dry-run            - Reviewer fast portable dry-run verification (No Sudo / CI)"
	@echo "   make benchmark          - Runs publication-grade campaign (standard unprivileged user mode)"
	@echo "   make benchmark-full-smc - Runs with sudo powermetrics for full hardware electrical SMC telemetry"
	@echo "   make reproduce-figures  - Recompiles all 300-DPI scientific publication figures"
	@echo "   make clean              - Purges Python/Node caches and temporary execution files"
	@echo "========================================================================"

setup:
	@echo "📦 [PT-BR] Provisionando ambiente de teste..."
	@echo "   [EN-US] Provisioning testbed environment..."
	./scripts/setup_environment.sh

check-quiescence:
	@./scripts/check_quiescence.sh

test:
	@echo "🧪 [PT-BR] Executando linter (ruff) e testes unitários automatizados (pytest)..."
	@echo "   [EN-US] Running linter (ruff) and automated unit test suite (pytest)..."
	$(VENV_PY) -m ruff check benchmark/ tests/ scripts/
	$(VENV_PY) -m pytest -v tests/

verify:
	@$(VENV_PY) scripts/verify_manifest.py

dry-run:
	@echo "🧪 [PT-BR] Executando verificação rápida portátil para revisores (Modo Dry-Run)..."
	@echo "   [EN-US] Running fast reviewer portable dry-run verification..."
	$(VENV_PY) benchmark/run_unified_benchmark.py --dry-run

simulate-campaign: dry-run

benchmark:
	@echo "⚡ [PT-BR] Disparando campanha de benchmark em espaço de usuário comum..."
	@echo "   [EN-US] Dispatching benchmark campaign in unprivileged user space..."
	$(VENV_PY) benchmark/run_unified_benchmark.py

benchmark-full-smc: check-quiescence
	@echo "⚡ [PT-BR] Validando privilégios sudo para o leitor de sensores SMC..."
	@echo "   [EN-US] Validating sudo credentials for SMC powermetrics reader..."
	@sudo -n powermetrics -i 50 -n 1 >/dev/null 2>&1 || sudo -v
	@echo "⚡ [PT-BR] Disparando campanha com telemetria elétrica do Apple SMC em espaço de usuário comum..."
	@echo "   [EN-US] Dispatching full physical benchmark campaign in unprivileged user space..."
	$(VENV_PY) benchmark/run_unified_benchmark.py --reps 30

reproduce-figures:
	@echo "📊 [PT-BR] Regenerando figuras científicas em 300 DPI..."
	@echo "   [EN-US] Re-rendering 300-DPI scientific publication figures..."
	$(VENV_PY) benchmark/generate_charts.py

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "🧹 [PT-BR] Caches temporários limpos."
	@echo "   [EN-US] Temporary caches purged."
