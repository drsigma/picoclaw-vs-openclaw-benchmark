#!/usr/bin/env bash
# ==============================================================================
# run_mac_campaign.sh
# Master Double-Session Replication Pipeline on macOS ARM64 (Apple Silicon M4)
# Executes Session 1 and Session 2 across all workloads (W1-W5, Cold & Warm)
# ==============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_DIR}"

echo "=================================================================="
echo " 🍏 DARWIN BENCHMARK CAMPAIGN (APPLE SILICON M4 - METAL/UMA) 🍏 "
echo "=================================================================="

# 0. Encerra aplicativos que possam interferir no sleep e na frequência
killall -9 Caffeine Amphetamine 2>/dev/null || true
pkill -9 -f llama-server 2>/dev/null || true
pkill -9 -f powermetrics 2>/dev/null || true
pkill -9 -f picoclaw_orch 2>/dev/null || true
pkill -9 -f openclaw_orch 2>/dev/null || true

export PATH="${REPO_DIR}/tools/bun/bin:${REPO_DIR}/tools/node/bin:${REPO_DIR}/tools/go/bin:${PATH}"

# Resolução de ambiente Python
if [ -d ".venv_repro_darwin" ]; then
    PYTHON_BIN="${REPO_DIR}/.venv_repro_darwin/bin/python"
elif [ -d ".venv_repro" ]; then
    PYTHON_BIN="${REPO_DIR}/.venv_repro/bin/python"
elif [ -d "tools/.venv" ]; then
    PYTHON_BIN="${REPO_DIR}/tools/.venv/bin/python"
elif [ -d ".venv" ]; then
    PYTHON_BIN="${REPO_DIR}/.venv/bin/python"
else
    PYTHON_BIN="$(which python3)"
fi

echo "🐍 Ambiente Python: ${PYTHON_BIN}"
"${PYTHON_BIN}" -m pip install -r requirements.txt -q 2>/dev/null || true

echo "🧹 Purgando memória unificada e caches..."
purge 2>/dev/null || true

# Garante binário Go do PicoClaw compilado nativo ARM64
if [ ! -f "benchmark/picoclaw_orch" ]; then
    echo "🔨 Compilando binário nativo Darwin ARM64 do PicoClaw (Go)..."
    (cd benchmark && go build -o picoclaw_orch picoclaw_orch.go)
fi
chmod +x benchmark/picoclaw_orch 2>/dev/null || true

# Cria diretórios necessários
mkdir -p results/publication_campaign/tables
mkdir -p reproducibility/clean_run_darwin_session_1
mkdir -p reproducibility/clean_run_darwin_session_2

# SESSÃO 1
echo ""
echo "🚀 [1/3] INICIANDO SESSÃO 1 (W1-W5, Cold Prefill & Warm Cache, n=30)..."
echo "  - Validando Tool-RAG Recall@5..."
"${PYTHON_BIN}" scripts/validate_rag_tool_recall.py

echo "  - Iniciando llama-server no Metal GPU (porta 8080)..."
tools/llama_cpp/llama-b11887/llama-server -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf -c 32768 -np 1 -ngl 99 -t 4 --port 8080 >/tmp/llama_server_stdout.log 2>&1 &
LLAMA_PID=$!

echo "    Aguardando prontidão do endpoint /health..."
for i in {1..30}; do
    if curl -s -f http://127.0.0.1:8080/health >/dev/null 2>&1; then
        echo "    ✔ llama-server ativo e pronto (PID: $LLAMA_PID)!"
        break
    fi
    sleep 1
done

if [ -f "results/publication_campaign/raw_trials.jsonl" ] && [ "$(wc -l < results/publication_campaign/raw_trials.jsonl)" -ge 825 ]; then
    echo "  ✔ Campanha Primária de Benchmark Unificado já concluída com sucesso (825 trials)."
else
    echo "  - Executando Campanha Primária de Benchmark Unificado (Cold Prefill, n=30)..."
    "${PYTHON_BIN}" benchmark/run_unified_benchmark.py --reps 30 --output-dir results/publication_campaign
fi

if [ -f "results/publication_campaign/warm_cache_trials.jsonl" ] && [ "$(wc -l < results/publication_campaign/warm_cache_trials.jsonl)" -ge 825 ]; then
    echo "  ✔ Campanha Warm Cache (Regime B) já coletada (825 trials). Consolidando análises..."
    "${PYTHON_BIN}" scripts/run_warm_cache_campaign.py --analyze-only
else
    echo "  - Executando Campanha Warm Cache (Regime B, n=30)..."
    "${PYTHON_BIN}" scripts/run_warm_cache_campaign.py
fi

if [ -f "results/publication_campaign/external_framework_langchain_trials.jsonl" ] && \
   [ -f "results/publication_campaign/quantization_scaling_ablation.json" ] && \
   [ -f "results/publication_campaign/mcp_live_transport_ablation.json" ]; then
    echo "  ✔ Todas as 7 ablações empíricas da Sessão 1 já coletadas e validadas."
else
    echo "  - Executando Ablações de Apoio e Paridade (UMA, KV-Cache, Tool-RAG, Prefill, LangChain, Quant, MCP)..."
    "${PYTHON_BIN}" scripts/run_uma_energy_and_bandwidth_attribution.py
    "${PYTHON_BIN}" scripts/run_kv_cache_thrashing_ablation.py
    "${PYTHON_BIN}" scripts/run_tool_rag_mitigation_experiment.py
    "${PYTHON_BIN}" scripts/run_prefill_ablation.py
    "${PYTHON_BIN}" scripts/run_external_framework_langchain_benchmark.py
    "${PYTHON_BIN}" scripts/run_quantization_scaling_ablation.py
    "${PYTHON_BIN}" scripts/run_mcp_live_transport_ablation.py
fi

echo "  - Empacotando dados brutos da Sessão 1..."
mkdir -p reproducibility/clean_run_darwin_session_1/results
mkdir -p reproducibility/clean_run_darwin_session_1/data
cp results/publication_campaign/*.jsonl reproducibility/clean_run_darwin_session_1/ 2>/dev/null || true
cp -r results/publication_campaign/* reproducibility/clean_run_darwin_session_1/results/ 2>/dev/null || true
cp data/manifest_sha256.json reproducibility/clean_run_darwin_session_1/manifest_sha256.json 2>/dev/null || true

# Higienização e resfriamento
echo ""
echo "▶ [2/3] Higienização e Estabilização Térmica Inter-Sessões..."
kill -9 $LLAMA_PID 2>/dev/null || true
pkill -9 -f llama-server 2>/dev/null || true
sleep 3
purge 2>/dev/null || true
echo "⏳ Aguardando 15s para estabilização térmica do Apple M4..."
sleep 15

# SESSÃO 2
echo ""
echo "🚀 [3/3] INICIANDO SESSÃO 2 (RÉPLICA INTER-SESSION 100% EMPÍRICA, n=30)..."
tools/llama_cpp/llama-b11887/llama-server -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf -c 32768 -np 1 -ngl 99 -t 4 --port 8080 >/tmp/llama_server_stdout.log 2>&1 &
LLAMA_PID=$!

echo "    Aguardando prontidão do endpoint /health..."
for i in {1..30}; do
    if curl -s -f http://127.0.0.1:8080/health >/dev/null 2>&1; then
        echo "    ✔ llama-server ativo e pronto para inferência (PID: $LLAMA_PID)!"
        break
    fi
    sleep 1
done

echo "  - Executando Campanha Darwin - Sessão 2 (Inter-Session Replication, n=30)..."
"${PYTHON_BIN}" scripts/run_inter_session_replication.py

echo "  - Empacotando dados brutos da Sessão 2..."
mkdir -p reproducibility/clean_run_darwin_session_2/results
mkdir -p reproducibility/clean_run_darwin_session_2/data
cp results/publication_campaign/*.jsonl reproducibility/clean_run_darwin_session_2/ 2>/dev/null || true
cp -r results/publication_campaign/* reproducibility/clean_run_darwin_session_2/results/ 2>/dev/null || true
cp data/manifest_sha256.json reproducibility/clean_run_darwin_session_2/manifest_sha256.json 2>/dev/null || true

kill -9 $LLAMA_PID 2>/dev/null || true
pkill -9 -f llama-server 2>/dev/null || true
sleep 2

echo ""
echo "▶ Consolidando Análise Estatística TOST e Contratos..."
"${PYTHON_BIN}" benchmark/analyze_results.py
"${PYTHON_BIN}" scripts/reproduce_tri_platform_analysis.py
"${PYTHON_BIN}" scripts/verify_manifest.py --update
"${PYTHON_BIN}" scripts/verify_manifest.py

echo "=================================================================="
echo "✅ Campanha Completa Darwin M4 concluída com sucesso!"
echo "=================================================================="
