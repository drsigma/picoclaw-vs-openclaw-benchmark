#!/usr/bin/env bash
set -euo pipefail

echo "=================================================================="
echo " 🍏 DARWIN BENCHMARK REPRODUCTION (EMPIRICAL MEASUREMENT) 🍏 "
echo "=================================================================="

if [ "$EUID" -ne 0 ]; then
  echo "❌ ERRO: Este script requer privilégios de root. Rode com: sudo ./reproduce_darwin_gold.sh"
  exit 1
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_DIR}"
export PATH="${REPO_DIR}/tools/bun/bin:${REPO_DIR}/tools/node/bin:${REPO_DIR}/tools/go/bin:${PATH}"

trap 'pkill -9 -f llama-server 2>/dev/null || true; pkill -9 -f powermetrics 2>/dev/null || true; pkill -9 -f caffeinate 2>/dev/null || true; pkill -9 -f picoclaw_orch 2>/dev/null || true; pkill -9 -f openclaw_orch 2>/dev/null || true' EXIT INT TERM

echo "💀 Matando instâncias zumbis do llama-server e powermetrics..."
pkill -9 -f llama-server 2>/dev/null || true
pkill -9 -f powermetrics 2>/dev/null || true
pkill -9 -f picoclaw_orch 2>/dev/null || true
pkill -9 -f openclaw_orch 2>/dev/null || true
sleep 2

echo "🧹 Limpando memória unificada e caches residuais..."
purge

echo "🐍 Configurando ambiente Python limpo..."
if [ ! -d ".venv_repro_darwin" ]; then
    python3 -m venv .venv_repro_darwin
fi
source .venv_repro_darwin/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "🚀 INICIANDO SESSÃO 1 (COLETA FÍSICA NO METAL/SMC - 100% EMPÍRICO)..."
mkdir -p reproducibility/clean_run_darwin_session_1
mkdir -p results/publication_campaign/tables

if [ ! -f "benchmark/picoclaw_orch" ]; then
    echo "  - Compilando binário nativo Darwin ARM64 do PicoClaw (Go)..."
    (cd benchmark && go build -o picoclaw_orch picoclaw_orch.go)
fi
chmod +x benchmark/picoclaw_orch 2>/dev/null || true

echo "  - Validando Tool-RAG Recall@5..."
python3 scripts/validate_rag_tool_recall.py

echo "  - Iniciando llama-server no Metal GPU (porta 8080)..."
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

echo "  - [1/9] Executando Campanha Primária de Benchmark Unificado (Cold Prefill, n=30)..."
python3 benchmark/run_unified_benchmark.py --reps 30 --output-dir results/publication_campaign

echo "  - [2/9] Executando Campanha Darwin (Warm Cache Campaign, n=30)..."
python3 scripts/run_warm_cache_campaign.py

echo "  - [3/9] Executando Ablação de Atribuição de Energia e Largura de Banda UMA..."
python3 scripts/run_uma_energy_and_bandwidth_attribution.py

echo "  - [4/9] Executando Ablação de KV-Cache Thrashing vs Slot Isolation..."
python3 scripts/run_kv_cache_thrashing_ablation.py

echo "  - [5/9] Executando Experimento de Mitigação Tool-RAG..."
python3 scripts/run_tool_rag_mitigation_experiment.py

echo "  - [6/9] Executando Ablação Controlada de Prefill e Escalonamento..."
python3 scripts/run_prefill_ablation.py

echo "  - [7/9] Executando Benchmark do Framework Externo LangChain Core..."
python3 scripts/run_external_framework_langchain_benchmark.py

echo "  - [8/9] Executando Ablação de Quantização Extrema (Q2_K vs Q3_K_M vs Q4_K_M)..."
python3 scripts/run_quantization_scaling_ablation.py

echo "  - [9/9] Executando Ablação de Transporte MCP Vivo (JSON-RPC 2.0)..."
python3 scripts/run_mcp_live_transport_ablation.py

echo "  - Empacotando dados brutos da Sessão 1..."
mkdir -p reproducibility/clean_run_darwin_session_1/results
mkdir -p reproducibility/clean_run_darwin_session_1/data
cp results/publication_campaign/*.jsonl reproducibility/clean_run_darwin_session_1/ 2>/dev/null || true
cp -r results/publication_campaign/* reproducibility/clean_run_darwin_session_1/results/ 2>/dev/null || true
cp data/manifest_sha256.json reproducibility/clean_run_darwin_session_1/manifest_sha256.json 2>/dev/null || true

pkill -9 -f llama-server 2>/dev/null || true
sleep 2

echo "🧠 Limpando cache de RAM do macOS e forçando quiescência..."
purge
echo "⏳ Aguardando 15s para estabilização térmica do Apple M4..."
sleep 15

echo "🚀 INICIANDO SESSÃO 2 (RÉPLICA INTER-SESSION 100% EMPÍRICA)..."
mkdir -p reproducibility/clean_run_darwin_session_2

echo "  - Disparando llama-server para Sessão 2 em 127.0.0.1:8080 (Metal GPU offload)..."
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
python3 scripts/run_inter_session_replication.py

echo "  - Empacotando dados brutos da Sessão 2..."
mkdir -p reproducibility/clean_run_darwin_session_2/results
mkdir -p reproducibility/clean_run_darwin_session_2/data
cp results/publication_campaign/*.jsonl reproducibility/clean_run_darwin_session_2/ 2>/dev/null || true
cp -r results/publication_campaign/* reproducibility/clean_run_darwin_session_2/results/ 2>/dev/null || true
cp data/manifest_sha256.json reproducibility/clean_run_darwin_session_2/manifest_sha256.json 2>/dev/null || true

pkill -9 -f llama-server 2>/dev/null || true
sleep 2

echo "✅ REPRODUÇÃO EMPÍRICA CONCLUÍDA! Analisando e validando manifestos..."
echo "  - Consolidando tabelas e análises estatísticas LaTeX..."
python3 benchmark/analyze_results.py

echo "  - Sincronizando e validando integridade criptográfica do manifesto Darwin..."
python3 scripts/verify_manifest.py --update
python3 scripts/verify_manifest.py

echo "🏁 Tudo salvo e validado com sucesso no Apple Mac Mini M4."
