#!/usr/bin/env bash
# ==============================================================================
# run_linux_campaign.sh / run_linux.sh
# Master Double-Session Replication Pipeline on Linux x86_64
# Executes Session 1 and Session 2 across all workloads (W1-W5) in both regimes (Cold & Warm)
# ==============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_DIR}"

# 0. Desativa imediatamente a suspensão e proteção de tela
echo "▶ [Passo 0] Desativando suspensão e proteção de tela (xset)..."
xset s off 2>/dev/null || true
xset -dpms 2>/dev/null || true

# Ativa virtual environment
if [ -d ".venv_repro" ]; then
    source .venv_repro/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

REPS="${REPS:-30}"
WARMUPS="${WARMUPS:-3}"
IDLE_SEC="${IDLE_SEC:-10}"
NGL="${NGL:-16}"
MODEL="${MODEL:-${REPO_DIR}/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf}"

echo "========================================================================"
echo "🚀 INICIANDO CAMPANHA COMPLETA LINUX x86_64 (NGL=${NGL}, REPS=${REPS})"
echo "   Sessão 1 + Sessão 2 (W1-W5, Cold & Warm)"
echo "========================================================================"

# SESSÃO 1
echo ""
echo "▶ [1/3] Executando Sessão 1 (W1-W5, Cold Prefill & Warm Cache)..."
python3 scripts/run_linux_x86_64_master_campaign.py \
    --ngl "${NGL}" \
    --model "${MODEL}" \
    --reps "${REPS}" \
    --warmups "${WARMUPS}" \
    --idle-sec "${IDLE_SEC}" \
    --suffix "_session1"

# Higienização e resfriamento
echo ""
echo "▶ [2/3] Higienização e Resfriamento Inter-Sessões..."
killall -9 llama-server 2>/dev/null || true
sleep 3
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null || true
sleep 10

# SESSÃO 2
echo ""
echo "▶ [3/3] Executando Sessão 2 (Réplica Inter-Sessões W1-W5, Cold & Warm)..."
python3 scripts/run_linux_x86_64_master_campaign.py \
    --ngl "${NGL}" \
    --model "${MODEL}" \
    --reps "${REPS}" \
    --warmups "${WARMUPS}" \
    --idle-sec "${IDLE_SEC}" \
    --suffix "_session2"

echo ""
echo "▶ Consolidando Análise Estatística TOST e Contratos..."
python3 scripts/reproduce_tri_platform_analysis.py

echo "========================================================================"
echo "✅ Campanha Completa (Sessão 1 + Sessão 2) concluída com sucesso!"
echo "========================================================================"
