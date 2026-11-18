#!/usr/bin/env bash
# ==============================================================================
# run_linux_campaign.sh / run_linux.sh
# Master Double-Session Replication Pipeline on Linux x86_64
# Executes Session 1 and Session 2 across all workloads (W1-W5) in both regimes (Cold & Warm)
# ==============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_DIR}"

# 0. Desativa imediatamente a suspensão e proteção de tela & libera RAPL
echo "▶ [Passo 0] Desativando suspensão e proteção de tela (xset)..."
xset s off 2>/dev/null || true
xset -dpms 2>/dev/null || true
sudo chmod -R a+r /sys/class/powercap/intel-rapl* 2>/dev/null || true

# Ativa virtual environment
if [ -d ".venv_repro" ]; then
    PYTHON_BIN="${REPO_DIR}/.venv_repro/bin/python"
elif [ -d ".venv" ]; then
    PYTHON_BIN="${REPO_DIR}/.venv/bin/python"
else
    PYTHON_BIN="$(which python3)"
fi

REPS="${REPS:-30}"
WARMUPS="${WARMUPS:-3}"
IDLE_SEC="${IDLE_SEC:-10}"
NGL="${NGL:-16}"
MODEL="${MODEL:-${REPO_DIR}/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf}"
COOL_CPU_C="${COOL_CPU_C:-70.0}"
COOL_GPU_C="${COOL_GPU_C:-60.0}"

echo "========================================================================"
echo "🚀 INICIANDO CAMPANHA COMPLETA LINUX x86_64 (NGL=${NGL}, REPS=${REPS})"
echo "   Sessão 1 + Sessão 2 (W1-W5, Cold & Warm)"
echo "   Python: ${PYTHON_BIN}"
echo "========================================================================"

# SESSÃO 1
sudo fuser -k 8080/tcp 2>/dev/null || true
killall -9 llama-server 2>/dev/null || true
sleep 1
echo ""
echo "▶ [1/3] Executando Sessão 1 (W1-W5, Cold Prefill & Warm Cache)..."
"${PYTHON_BIN}" scripts/run_linux_x86_64_master_campaign.py \
    --ngl "${NGL}" \
    --model "${MODEL}" \
    --reps "${REPS}" \
    --warmups "${WARMUPS}" \
    --idle-sec "${IDLE_SEC}" \
    --cool-cpu-c "${COOL_CPU_C}" \
    --cool-gpu-c "${COOL_GPU_C}" \
    --suffix "_session1"

# Higienização e resfriamento
echo ""
echo "▶ [2/3] Higienização e Resfriamento Inter-Sessões..."
killall -9 llama-server 2>/dev/null || true
sleep 3
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null || true
sleep 30

# SESSÃO 2
echo ""
echo "▶ [3/3] Executando Sessão 2 (Réplica Inter-Sessões W1-W5, Cold & Warm)..."
"${PYTHON_BIN}" scripts/run_linux_x86_64_master_campaign.py \
    --ngl "${NGL}" \
    --model "${MODEL}" \
    --reps "${REPS}" \
    --warmups "${WARMUPS}" \
    --idle-sec "${IDLE_SEC}" \
    --cool-cpu-c "${COOL_CPU_C}" \
    --cool-gpu-c "${COOL_GPU_C}" \
    --suffix "_session2"

echo ""
echo "▶ Consolidando Análise Estatística TOST e Contratos..."
"${PYTHON_BIN}" scripts/reproduce_tri_platform_analysis.py

echo "========================================================================"
echo "✅ Campanha Completa (Sessão 1 + Sessão 2) concluída com sucesso!"
echo "========================================================================"
