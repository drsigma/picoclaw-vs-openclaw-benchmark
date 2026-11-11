#!/usr/bin/env bash
# ==============================================================================
# System Quiescence and Host Thermal Pre-Flight Audit
# Auditoria Pré-Voo de Quiescência do Sistema e Estado Térmico do Host
#
# Author / Autor: Rafael Paniccia Cassetta (UFABC)
# Language / Idioma: Bilingual (PT-BR & EN-US)
# ==============================================================================
set -euo pipefail

echo "========================================================================"
echo " 🔍 [PT-BR] Auditoria Pré-Voo de Quiescência do Apple Silicon M4"
echo "    [EN-US] Apple Silicon M4 System Quiescence Pre-Flight Audit"
echo "========================================================================"

# 1. Architecture Check / Verificação de Arquitetura
ARCH=$(uname -m)
OS=$(uname -s)
if [ "$ARCH" != "arm64" ] || [ "$OS" != "Darwin" ]; then
    echo "❌ [PT-BR] Erro: Este benchmark exige macOS ARM64 (Apple Silicon). Detectado: $OS $ARCH"
    echo "   [EN-US] Error: This benchmark requires macOS ARM64 (Apple Silicon). Detected: $OS $ARCH"
    exit 1
fi
echo "✅ [PT-BR] Plataforma verificada: Apple Silicon macOS ($ARCH)"
echo "   [EN-US] Verified platform: Apple Silicon macOS ($ARCH)"

# 2. Check caffeinate daemon / Verificar processo anti-sono caffeinate
if pgrep -l caffeinate >/dev/null; then
    CAFF_PID=$(pgrep -d ',' caffeinate)
    echo "✅ [PT-BR] Modo anti-sono ativo (caffeinate PID: $CAFF_PID)"
    echo "   [EN-US] Anti-sleep mode active (caffeinate PID: $CAFF_PID)"
else
    echo "⚠️  [PT-BR] caffeinate inativo. Ativando '/usr/bin/caffeinate -dims' em segundo plano..."
    echo "   [EN-US] caffeinate inactive. Spawning '/usr/bin/caffeinate -dims' in background..."
    /usr/bin/caffeinate -dims &
fi

# 3. Check Spotlight indexing / Verificar indexação do Spotlight
if command -v mdutil >/dev/null 2>&1; then
    MD_STATUS=$(mdutil -s / 2>/dev/null || true)
    echo "ℹ️  [PT-BR] Estado do Spotlight: $MD_STATUS"
    echo "   [EN-US] Spotlight state: $MD_STATUS"
fi

# 4. Thermal & Background Contention Check / Verificação de Carga Concorrente
CPU_LOAD=$(top -l 1 -n 0 | awk '/CPU usage/ {print $3, $5}')
echo "ℹ️  [PT-BR] Utilização atual de CPU: $CPU_LOAD"
echo "   [EN-US] Current CPU load: $CPU_LOAD"

# 5. Check llama-server local daemon / Verificar servidor neural local
if curl -s http://127.0.0.1:8080/health >/dev/null 2>&1; then
    echo "✅ [PT-BR] Servidor llama-server respondendo na porta 8080 (Metal GPU pronta)"
    echo "   [EN-US] Local llama-server responding on port 8080 (Metal GPU ready)"
else
    echo "⚠️  [PT-BR] Servidor llama-server NÃO detectado na porta 8080. O runner tentará iniciá-lo."
    echo "   [EN-US] Local llama-server NOT detected on port 8080. Runner will attempt startup."
fi

echo "========================================================================"
echo " ✅ [PT-BR] Auditoria concluída. Ambiente pronto para benchmark."
echo "    [EN-US] Pre-flight audit completed. Testbed ready for benchmarking."
echo "========================================================================"
