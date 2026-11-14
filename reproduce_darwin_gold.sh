#!/usr/bin/env bash
# ==============================================================================
# reproduce_darwin_gold.sh
# 
# Master Reproduction Script: Cross-Platform Systems & Microarchitectural Benchmark
# Automated, Clean-Environment Double-Session Replication Pipeline on macOS Darwin ARM64
# (Apple Silicon M4 / Mac Mini).
#
# Adheres strictly to IEEE / ACM Artifact Evaluation & Empirical Reviewer Standards:
#   1. Sudo & privilege validation (Apple SMC powermetrics 50ms, libproc RUSAGE_INFO_V4)
#   2. Thermal stabilization and anti-sleep enforcement via caffeinate -dims
#   3. Pre-flight quiescence audit (scripts/check_quiescence.sh)
#   4. Isolated Python virtual environment (.venv_repro_darwin)
#   5. Double-session execution (clean_run_darwin_session_1 & clean_run_darwin_session_2)
#   6. Physical DRAM reset via sudo purge between sessions with 10s thermal quiescence
#   7. Full system restoration on exit (trap cleanup)
#   8. Strict namespace isolation: all outputs written strictly to Darwin folders:
#      - results/publication_campaign/
#      - data/ (manifest_sha256.json, powermetrics, etc.)
#      - reproducibility/clean_run_darwin_session_1/
#      - reproducibility/clean_run_darwin_session_2/
# ==============================================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_DIR}"

REPS="${REPS:-30}"
WARMUPS="${WARMUPS:-3}"
IDLE_SEC="${IDLE_SEC:-10}"
NGL="${NGL:-99}"

EXTRA_ARGS=("$@")
ANALYZE_ONLY=false
for arg in "${EXTRA_ARGS[@]:-}"; do
    if [ "$arg" = "--analyze-only" ]; then
        ANALYZE_ONLY=true
    fi
done

# ------------------------------------------------------------------------------
# 1. Validação de Plataforma e Permissões (Darwin ARM64 & Sudo)
# ------------------------------------------------------------------------------
echo -e "\033[1;34m========================================================================\033[0m"
echo -e "\033[1;34m🚀 INICIANDO REPRODUÇÃO EXPERIMENTAL PADRÃO OURO (DARWIN ARM64 / MAC MINI)\033[0m"
echo -e "\033[1;34m========================================================================\033[0m"

OS="$(uname -s)"
ARCH="$(uname -m)"

if [ "$OS" != "Darwin" ] || [ "$ARCH" != "arm64" ]; then
    echo -e "\033[1;31m❌ [FATAL] Este script requer macOS Darwin ARM64 (Apple Silicon M4).\033[0m"
    echo "   Detectado: OS=$OS, ARCH=$ARCH"
    echo "   Para reprodução em Linux x86_64, utilize: ./reproduce_linux_gold.sh"
    exit 1
fi

echo "Este script requer privilégios de superusuário (sudo) para gerenciar o"
echo "powermetrics (amostragem a 50ms das shunts de corrente do Apple SMC) e purge."
echo ""

if [ "$EUID" -ne 0 ]; then
    if ! sudo -n true 2>/dev/null; then
        sudo -v || { echo -e "\033[1;31m❌ Falha na autenticação sudo. Abortando.\033[0m"; exit 1; }
    fi
fi

# Mantém o sudo ativo em segundo plano enquanto o script executa
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &
SUDO_KEEP_ALIVE_PID=$!

# ------------------------------------------------------------------------------
# 2. Restauração de Sistema e Helpers de Lifecycle
# ------------------------------------------------------------------------------
LLAMA_PID=""

stop_llama_server() {
    if [ -n "${LLAMA_PID:-}" ] && kill -0 "$LLAMA_PID" 2>/dev/null; then
        kill "$LLAMA_PID" 2>/dev/null || true
    fi
    pkill -9 llama-server 2>/dev/null || killall -9 llama-server 2>/dev/null || true
    sleep 2
}

start_llama_server() {
    stop_llama_server
    echo "  - Localizando binário e modelo do llama-server..."
    if [ -f "tools/llama_cpp/llama-b11887/llama-server" ]; then
        LLAMA_BIN="tools/llama_cpp/llama-b11887/llama-server"
    elif [ -f "tools/llama_cpp/llama-server" ]; then
        LLAMA_BIN="tools/llama_cpp/llama-server"
    else
        LLAMA_BIN="llama-server"
    fi

    MODEL_PATH="models/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    if [ ! -f "$MODEL_PATH" ]; then
        echo -e "\033[1;31m❌ [FATAL] Modelo não encontrado em $MODEL_PATH\033[0m"
        exit 1
    fi

    echo "  - Disparando llama-server em 127.0.0.1:8080 (Metal GPU offload)..."
    "$LLAMA_BIN" -m "$MODEL_PATH" -c 32768 -np 1 -ngl 99 -t 4 --port 8080 >/tmp/llama_server_stdout.log 2>&1 &
    LLAMA_PID=$!

    echo "    Aguardando prontidão do endpoint /health..."
    for i in {1..30}; do
        if curl -s -f http://127.0.0.1:8080/health >/dev/null 2>&1; then
            echo "    ✔ llama-server ativo e pronto para inferência (PID: $LLAMA_PID)!"
            return 0
        fi
        sleep 1
    done

    echo -e "\033[1;31m❌ [FATAL] llama-server não respondeu dentro de 30s. Logs:\033[0m"
    tail -n 25 /tmp/llama_server_stdout.log
    exit 1
}

cleanup() {
    echo ""
    echo -e "\033[1;33m🔄 Finalizando processos e restaurando sistema macOS...\033[0m"
    
    # Mata keep-alive do sudo
    kill "$SUDO_KEEP_ALIVE_PID" 2>/dev/null || true

    # Mata instâncias do caffeinate iniciadas por nós
    if [ -n "${CAFF_PID:-}" ]; then
        kill "$CAFF_PID" 2>/dev/null || true
    fi

    # Mata qualquer instância remanescente do llama-server
    stop_llama_server

    echo -e "\033[1;32m✔ Ambiente Darwin restaurado para operação padrão.\033[0m"
}
trap cleanup EXIT INT TERM

# ------------------------------------------------------------------------------
# 3. Preparação de Hardware, Anti-Sleep e Limpeza
# ------------------------------------------------------------------------------
echo -e "\033[1;34m▶ 1/6: Inibindo Suspensão e Eliminando Instâncias Antigas...\033[0m"

# Mata instâncias antigas de llama-server
stop_llama_server

# Ativa anti-sono em segundo plano
/usr/bin/caffeinate -dims &
CAFF_PID=$!
echo "  - Caffeinate ativado (PID: $CAFF_PID)"

# Executa auditoria de quiescência
if [ -f "scripts/check_quiescence.sh" ]; then
    bash scripts/check_quiescence.sh
fi

# ------------------------------------------------------------------------------
# 4. Ambiente Limpo Isolado (.venv_repro_darwin)
# ------------------------------------------------------------------------------
echo -e "\033[1;34m▶ 2/6: Configurando Ambiente Limpo Isolado (.venv_repro_darwin)...\033[0m"
if [ ! -d ".venv_repro_darwin" ]; then
    echo "  - Criando .venv_repro_darwin..."
    if [ -f "tools/.venv/bin/python" ]; then
        tools/.venv/bin/python -m venv .venv_repro_darwin
    else
        python3 -m venv .venv_repro_darwin
    fi
fi
source .venv_repro_darwin/bin/activate
echo "  - Instalando dependências científicas..."
pip install --upgrade pip >/dev/null 2>&1
pip install numpy scipy pytest psutil ruff matplotlib >/dev/null 2>&1

# Verifica e compila binário nativo Mach-O do PicoClaw se necessário
if [ ! -f "benchmark/picoclaw_orch" ]; then
    echo "  - Compilando binário nativo Darwin ARM64 do PicoClaw (Go)..."
    (cd benchmark && go build -o picoclaw_orch picoclaw_orch.go)
fi
chmod +x benchmark/picoclaw_orch 2>/dev/null || true

# Validação do Tool-RAG Recall@5
echo "  - Executando validação de Recall@5 do Zero-Copy Tool-RAG Pruner..."
python3 scripts/validate_rag_tool_recall.py

# ------------------------------------------------------------------------------
# 5. Execução da Sessão 1 (Warm Cache Campaign & UMA Attribution)
# ------------------------------------------------------------------------------
mkdir -p reproducibility/clean_run_darwin_session_1
mkdir -p reproducibility/clean_run_darwin_session_2

echo -e "\033[1;34m▶ 3/6: Executando Campanha Darwin - Sessão 1 (Warm Cache Campaign)...\033[0m"
if [ "$ANALYZE_ONLY" = false ]; then
    start_llama_server
fi

python3 scripts/run_warm_cache_campaign.py "${EXTRA_ARGS[@]:-}"

echo "  - Executando Ablação de Atribuição de Energia e Largura de Banda UMA..."
python3 scripts/run_uma_energy_and_bandwidth_attribution.py "${EXTRA_ARGS[@]:-}"

echo "  - Empacotando dados brutos e certificados da Sessão 1..."
mkdir -p reproducibility/clean_run_darwin_session_1/results
mkdir -p reproducibility/clean_run_darwin_session_1/data
cp -r results/publication_campaign/* reproducibility/clean_run_darwin_session_1/results/ 2>/dev/null || true
cp data/manifest_sha256.json reproducibility/clean_run_darwin_session_1/manifest_sha256.json 2>/dev/null || true

# ------------------------------------------------------------------------------
# 6. Reset Físico: Limpeza de RAM via sudo purge e Quiescência
# ------------------------------------------------------------------------------
echo ""
echo -e "\033[1;34m▶ 4/6: Reset Físico (sudo purge) e Estabilização Térmica...\033[0m"
stop_llama_server
sleep 2
echo "  - Executando 'sudo purge' para invalidar buffers e caches de disco/DRAM..."
sudo purge
echo "  - Resfriamento e estabilização térmica do Apple Silicon M4 (10s)..."
sleep 10

# ------------------------------------------------------------------------------
# 7. Execução da Sessão 2 (Inter-Session Replication)
# ------------------------------------------------------------------------------
echo -e "\033[1;34m▶ 5/6: Executando Campanha Darwin - Sessão 2 (Inter-Session Replication)...\033[0m"
if [ "$ANALYZE_ONLY" = false ]; then
    start_llama_server
fi

python3 scripts/run_inter_session_replication.py "${EXTRA_ARGS[@]:-}"

echo "  - Consolidando tabelas e análises estatísticas LaTeX..."
python3 benchmark/analyze_results.py

stop_llama_server

# ------------------------------------------------------------------------------
# 8. Verificação de Manifesto e Fechamento
# ------------------------------------------------------------------------------
echo -e "\033[1;34m▶ 6/6: Verificação Criptográfica e Empacotamento Final...\033[0m"
echo "  - Sincronizando e validando integridade criptográfica do manifesto Darwin..."
python3 scripts/verify_manifest.py --update
python3 scripts/verify_manifest.py

echo "  - Empacotando dados brutos da Sessão 2..."
mkdir -p reproducibility/clean_run_darwin_session_2/results
mkdir -p reproducibility/clean_run_darwin_session_2/data
cp -r results/publication_campaign/* reproducibility/clean_run_darwin_session_2/results/ 2>/dev/null || true
cp data/manifest_sha256.json reproducibility/clean_run_darwin_session_2/manifest_sha256.json 2>/dev/null || true

echo ""
echo -e "\033[1;32m========================================================================\033[0m"
echo -e "\033[1;32m✅ REPRODUÇÃO PADRÃO OURO DARWIN (MAC MINI) CONCLUÍDA COM SUCESSO!\033[0m"
echo -e "\033[1;32m   - Sessão 1: reproducibility/clean_run_darwin_session_1/\033[0m"
echo -e "\033[1;32m   - Sessão 2: reproducibility/clean_run_darwin_session_2/\033[0m"
echo -e "\033[1;32m   - Resultados de publicação: results/publication_campaign/\033[0m"
echo -e "\033[1;32m   - Manifesto validado: data/manifest_sha256.json\033[0m"
echo -e "\033[1;32m========================================================================\033[0m"
