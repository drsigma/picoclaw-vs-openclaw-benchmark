#!/usr/bin/env bash
# ==============================================================================
# scripts/run_cross_hardware_replica.sh - Single-Command Cross-Hardware Runner
# Elsevier SoftwareX: picoclaw-vs-openclaw-benchmark (Gates B2 / E3)
#
# Usage:
#   bash scripts/run_cross_hardware_replica.sh
#
# Requirements:
#   1. llama-server running on http://127.0.0.1:8080
#   2. Python 3.9+ with numpy, scipy (or tools/.venv)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
cd "$REPO_DIR"

echo "================================================================================"
echo "🚀 INICIANDO REPLICACAO CROSS-HARDWARE (LINUX / GPU / INTEL-AMD RAPL)"
echo "   picoclaw-vs-openclaw-benchmark"
echo "================================================================================"

# 1. Check Python environment
if [ -f "tools/.venv/bin/python" ]; then
    PYTHON_CMD="tools/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    echo "❌ [FATAL] Python 3 não encontrado no ambiente."
    exit 1
fi
echo "🐍 Python: $($PYTHON_CMD --version)"

# 2. Check llama-server availability
echo "🔍 Verificando conectividade com llama-server em 127.0.0.1:8080..."
if ! curl -s -f http://127.0.0.1:8080/health >/dev/null 2>&1; then
    echo "❌ [FATAL] llama-server não está respondendo em http://127.0.0.1:8080/health"
    echo "💡 Por favor, inicie o servidor com:"
    echo "   llama-server -m <caminho_modelo_Q4_K_M.gguf> -c 32768 -np 1 --port 8080"
    exit 1
fi
echo "✅ llama-server ativo e respondendo!"

# 3. Execute cross-hardware replica campaign
echo "🏃 Executando bateria de replicação..."
$PYTHON_CMD scripts/run_cross_hardware_replica.py

echo "================================================================================"
echo "🎉 REPLICACAO CONCLUIDA COM SUCESSO!"
echo "   - Dados brutos: data/linux_replica_trials.jsonl"
echo "   - Comparação:   data/cross_hardware_comparison.json"
echo "================================================================================"
