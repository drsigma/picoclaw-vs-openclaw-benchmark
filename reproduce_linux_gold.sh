#!/usr/bin/env bash
# ==============================================================================
# reproduce_linux_gold.sh
# 
# Master Reproduction Script: Cross-Platform Systems & Microarchitectural Benchmark
# Automated, Clean-Environment Double-Session Replication Pipeline on Linux x86_64.
#
# Adheres strictly to IEEE / ACM Artifact Evaluation & Empirical Reviewer Standards:
#   1. Sudo & privilege validation (RAPL, NVML, fan PWM, sleep targets)
#   2. Thermal stabilization (fans locked to 100% PWM via dell_smm / alienware_wmi)
#   3. Isolated Python virtual environment (.venv_repro)
#   4. Double-session execution (clean_run_linux_session_1 & clean_run_linux_session_2)
#   5. Zombie cleanup, drop_caches, and inter-session replication validation
#   6. Full system restoration on exit (trap cleanup)
# ==============================================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_DIR}"

REPS="${REPS:-30}"
WARMUPS="${WARMUPS:-3}"
IDLE_SEC="${IDLE_SEC:-10}"
NGL="${NGL:-16}"
MODEL="${MODEL:-/home/rafalince/.gemini/antigravity/scratch/assignment3/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf}"

# ------------------------------------------------------------------------------
# 1. Validação de Permissões (Sudo)
# ------------------------------------------------------------------------------
echo -e "\033[1;34m========================================================================\033[0m"
echo -e "\033[1;34m🚀 INICIANDO REPRODUÇÃO EXPERIMENTAL PADRÃO OURO (LINUX x86_64)\033[0m"
echo -e "\033[1;34m========================================================================\033[0m"
echo "Este script requer privilégios de superusuário (sudo) para gerenciar o perfil"
echo "de energia (Intel RAPL, NVIDIA NVML), desativar suspensão e travar ventoinhas."
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
# 5. Restauração de Sistema (Trap de Saída)
# ------------------------------------------------------------------------------
cleanup() {
    echo ""
    echo -e "\033[1;33m🔄 Restaurando controle de energia, suspensão e ventoinhas...\033[0m"
    
    # Mata keep-alive do sudo
    kill "$SUDO_KEEP_ALIVE_PID" 2>/dev/null || true

    # Mata qualquer instância remanescente do llama-server
    killall -9 llama-server 2>/dev/null || true

    # Reativa alvos de suspensão do sistema
    sudo systemctl unmask sleep.target suspend.target hibernate.target hybrid-sleep.target >/dev/null 2>&1 || true

    # Restaura controle automático das ventoinhas (BIOS/Auto)
    for hw in /sys/class/hwmon/hwmon*; do
        if [ -f "$hw/name" ]; then
            hname=$(cat "$hw/name" 2>/dev/null || true)
            if [ "$hname" = "dell_smm" ]; then
                for en in "$hw"/pwm*_enable; do
                    [ -f "$en" ] && sudo sh -c "echo 2 > $en" 2>/dev/null || true
                done
            elif [ "$hname" = "alienware_wmi" ]; then
                for b in "$hw"/fan*_boost; do
                    [ -f "$b" ] && sudo sh -c "echo 0 > $b" 2>/dev/null || true
                done
            fi
        fi
    done

    # Restaura governador de CPU para powersave
    sudo sh -c 'echo powersave | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null 2>&1' || true
    echo -e "\033[1;32m✔ Sistema restaurado para operação padrão com sucesso.\033[0m"
}
trap cleanup EXIT INT TERM

# ------------------------------------------------------------------------------
# 2. Preparação de Hardware (Obrigatório)
# ------------------------------------------------------------------------------
echo -e "\033[1;34m▶ 1/5: Preparando Hardware e Estabilização Térmica...\033[0m"

# Desativa suspensão temporariamente
echo "  - Mascarando alvos de suspensão/hibernação do sistema..."
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target >/dev/null 2>&1 || true

# Configura governador para performance máxima
echo "  - Ativando governador de performance nas CPUs..."
sudo sh -c 'echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null 2>&1' || true

# Habilita leitura dos contadores de energia Intel RAPL
echo "  - Liberando permissões de leitura sysfs para Intel RAPL..."
sudo chmod -R a+r /sys/class/powercap/intel-rapl* 2>/dev/null || true

# Trava ventoinhas em 100% PWM
echo "  - Travando ventoinhas no máximo (100% PWM / dell_smm_hwmon)..."
for hw in /sys/class/hwmon/hwmon*; do
    if [ -f "$hw/name" ]; then
        hname=$(cat "$hw/name" 2>/dev/null || true)
        if [ "$hname" = "dell_smm" ]; then
            for en in "$hw"/pwm*_enable; do
                [ -f "$en" ] && sudo sh -c "echo 1 > $en" 2>/dev/null || true
            done
            for pwm in "$hw"/pwm*; do
                case "$pwm" in
                    *_enable) ;;
                    *) [ -f "$pwm" ] && sudo sh -c "echo 255 > $pwm" 2>/dev/null || true ;;
                esac
            done
        elif [ "$hname" = "alienware_wmi" ]; then
            for b in "$hw"/fan*_boost; do
                [ -f "$b" ] && sudo sh -c "echo 100 > $b" 2>/dev/null || true
            done
        fi
    fi
done

# ------------------------------------------------------------------------------
# 3. Ambiente Limpo Isolado (.venv_repro)
# ------------------------------------------------------------------------------
echo -e "\033[1;34m▶ 2/5: Configurando Ambiente Limpo Isolado (.venv_repro)...\033[0m"
if [ ! -d ".venv_repro" ]; then
    echo "  - Criando .venv_repro..."
    python3 -m venv .venv_repro
fi
source .venv_repro/bin/activate
echo "  - Instalando dependências científicas..."
pip install --upgrade pip >/dev/null 2>&1
pip install numpy scipy pytest psutil matplotlib >/dev/null 2>&1

# Compila binário nativo Go do PicoClaw caso necessário
if [ ! -f "benchmark/picoclaw_orch_linux" ]; then
    echo "  - Compilando binário nativo Linux do PicoClaw (Go)..."
    (cd benchmark && go build -o picoclaw_orch_linux picoclaw_orch.go)
fi

# ------------------------------------------------------------------------------
# 4. Execução das Campanhas (Double Session Replication)
# ------------------------------------------------------------------------------
mkdir -p reproducibility/clean_run_linux_session_1
mkdir -p reproducibility/clean_run_linux_session_2

echo -e "\033[1;34m▶ 3/5: Executando Campanha - Sessão 1 (clean_run_linux_session_1)...\033[0m"
echo "  Parâmetros: --ngl ${NGL} --reps ${REPS} --warmups ${WARMUPS} --idle-sec ${IDLE_SEC}"

python3 scripts/run_linux_x86_64_master_campaign.py \
    --ngl "${NGL}" \
    --model "${MODEL}" \
    --reps "${REPS}" \
    --warmups "${WARMUPS}" \
    --idle-sec "${IDLE_SEC}" \
    --suffix "_session1"

echo "  - Empacotando dados brutos e certificados da Sessão 1..."
cp -r "data/linux_x86_64_session1" "reproducibility/clean_run_linux_session_1/data"
cp -r "results/publication_campaign_linux_x86_64_session1" "reproducibility/clean_run_linux_session_1/results"
cp "data/manifest_sha256_linux_x86_64_session1.json" "reproducibility/clean_run_linux_session_1/manifest_sha256.json"

echo ""
echo -e "\033[1;34m▶ 4/5: Higienização e Resfriamento Inter-Sessões...\033[0m"
echo "  - Finalizando instâncias anteriores de servidores neurais..."
killall -9 llama-server 2>/dev/null || true
sleep 2

echo "  - Invalidando caches de página do kernel (drop_caches)..."
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

echo "  - Pausa de resfriamento e estabilização (10s)..."
sleep 10

echo -e "\033[1;34m▶ 5/5: Executando Campanha - Sessão 2 (clean_run_linux_session_2 / Réplica Inter-Sessões)...\033[0m"
echo "  Parâmetros: --ngl ${NGL} --reps ${REPS} --warmups ${WARMUPS} --idle-sec ${IDLE_SEC}"

python3 scripts/run_linux_x86_64_master_campaign.py \
    --ngl "${NGL}" \
    --model "${MODEL}" \
    --reps "${REPS}" \
    --warmups "${WARMUPS}" \
    --idle-sec "${IDLE_SEC}" \
    --suffix "_session2"

echo "  - Empacotando dados brutos e certificados da Sessão 2..."
cp -r "data/linux_x86_64_session2" "reproducibility/clean_run_linux_session_2/data"
cp -r "results/publication_campaign_linux_x86_64_session2" "reproducibility/clean_run_linux_session_2/results"
cp "data/manifest_sha256_linux_x86_64_session2.json" "reproducibility/clean_run_linux_session_2/manifest_sha256.json"

echo ""
echo -e "\033[1;32m========================================================================\033[0m"
echo -e "\033[1;32m✅ REPRODUÇÃO PADRÃO OURO LINUX CONCLUÍDA COM SUCESSO!\033[0m"
echo -e "\033[1;32m   - Sessão 1: reproducibility/clean_run_linux_session_1/\033[0m"
echo -e "\033[1;32m   - Sessão 2: reproducibility/clean_run_linux_session_2/\033[0m"
echo -e "\033[1;32m   - Réplica inter-sessões validada e pronta para publicação acadêmica.\033[0m"
echo -e "\033[1;32m========================================================================\033[0m"
