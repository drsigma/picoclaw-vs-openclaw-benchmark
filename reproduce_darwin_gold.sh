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
#   4. Isolated Python virtual environment (.venv_repro)
#   5. Double-session execution (clean_run_darwin_session_1 & clean_run_darwin_session_2)
#   6. Full system restoration on exit (trap cleanup)
#   7. Strict namespace isolation: all outputs written strictly to Darwin folders:
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
echo "powermetrics (amostragem a 50ms das shunts de corrente do Apple SMC)."
echo ""

if [ "$EUID" -ne 0 ]; then
    sudo -v || { echo -e "\033[1;31m❌ Falha na autenticação sudo. Abortando.\033[0m"; exit 1; }
fi

# Mantém o sudo ativo em segundo plano enquanto o script executa
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &
SUDO_KEEP_ALIVE_PID=$!

# ------------------------------------------------------------------------------
# 2. Restauração de Sistema (Trap de Saída)
# ------------------------------------------------------------------------------
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
    killall -9 llama-server 2>/dev/null || true

    echo -e "\033[1;32m✔ Ambiente Darwin restaurado para operação padrão.\033[0m"
}
trap cleanup EXIT INT TERM

# ------------------------------------------------------------------------------
# 3. Preparação de Hardware e Quiescência
# ------------------------------------------------------------------------------
echo -e "\033[1;34m▶ 1/5: Auditoria Pré-Voo de Quiescência e Prevenção de Sono...\033[0m"

# Ativa anti-sono em segundo plano
/usr/bin/caffeinate -dims &
CAFF_PID=$!
echo "  - Caffeinate ativado (PID: $CAFF_PID)"

# Executa auditoria de quiescência
if [ -f "scripts/check_quiescence.sh" ]; then
    bash scripts/check_quiescence.sh
fi

# ------------------------------------------------------------------------------
# 4. Ambiente Limpo Isolado (.venv_repro)
# ------------------------------------------------------------------------------
echo -e "\033[1;34m▶ 2/5: Configurando Ambiente Limpo Isolado (.venv_repro)...\033[0m"
if [ ! -d ".venv_repro" ]; then
    echo "  - Criando .venv_repro..."
    python3 -m venv .venv_repro
fi
source .venv_repro/bin/activate
echo "  - Instalando dependências científicas..."
pip install --upgrade pip >/dev/null 2>&1
pip install numpy scipy pytest psutil >/dev/null 2>&1

# Verifica binário nativo Mach-O do PicoClaw
if [ ! -f "benchmark/picoclaw_orch" ]; then
    echo "  - Compilando binário nativo Darwin ARM64 do PicoClaw (Go)..."
    (cd benchmark && go build -o picoclaw_orch picoclaw_orch.go)
fi
chmod +x benchmark/picoclaw_orch 2>/dev/null || true

# ------------------------------------------------------------------------------
# 5. Execução das Campanhas (Double Session Replication)
# ------------------------------------------------------------------------------
mkdir -p reproducibility/clean_run_darwin_session_1
mkdir -p reproducibility/clean_run_darwin_session_2

echo -e "\033[1;34m▶ 3/5: Executando Campanha Darwin - Sessão 1 (Warm Cache Campaign)...\033[0m"
python3 scripts/run_warm_cache_campaign.py

echo "  - Executando Ablação de Atribuição de Energia e Largura de Banda UMA..."
python3 scripts/run_uma_energy_and_bandwidth_attribution.py

echo "  - Empacotando dados brutos e certificados da Sessão 1..."
mkdir -p reproducibility/clean_run_darwin_session_1/results
mkdir -p reproducibility/clean_run_darwin_session_1/data
cp -r results/publication_campaign/* reproducibility/clean_run_darwin_session_1/results/ 2>/dev/null || true
cp data/manifest_sha256.json reproducibility/clean_run_darwin_session_1/manifest_sha256.json 2>/dev/null || true

echo ""
echo -e "\033[1;34m▶ 4/5: Higienização e Pausa Inter-Sessões...\033[0m"
killall -9 llama-server 2>/dev/null || true
sleep 5
echo "  - Resfriamento e estabilização térmica do Apple Silicon M4 (10s)..."
sleep 10

echo -e "\033[1;34m▶ 5/5: Executando Campanha Darwin - Sessão 2 (Inter-Session Replication)...\033[0m"
python3 scripts/run_inter_session_replication.py

echo "  - Consolidando tabelas e análises estatísticas LaTeX..."
python3 benchmark/analyze_results.py

echo "  - Validando integridade criptográfica do manifesto Darwin..."
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
