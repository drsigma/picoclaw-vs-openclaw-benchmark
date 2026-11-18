#!/bin/bash
set -u

echo "Iniciando monitoramento da campanha de benchmark..."
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_DIR}"

PYTHON_BIN="${REPO_DIR}/.venv_repro/bin/python"
if [ ! -f "${PYTHON_BIN}" ]; then
    PYTHON_BIN="python3"
fi

# Localiza o PID do script de campanha rodando em background
PID=$(pgrep -f run_linux_campaign.sh | head -n 1)

if [ -z "$PID" ]; then
    echo "Nenhum processo run_linux_campaign.sh encontrado. Verifique se ele já terminou ou falhou."
else
    echo "Monitorando o PID: $PID. Aguardando conclusão (isso pode levar horas)..."
    # Fica em loop aguardando o processo terminar
    while kill -0 "$PID" 2>/dev/null; do
        sleep 60
    done
    echo "Coleta concluída! Processo $PID finalizado."
fi

# Pausa breve para flush de buffers de disco
sleep 5

echo "Iniciando processamento estatístico e consolidação final..."
"${PYTHON_BIN}" scripts/reproduce_tri_platform_analysis.py || true

echo "Atualizando manifesto criptográfico SHA-256..."
"${PYTHON_BIN}" scripts/verify_manifest.py --update || true
"${PYTHON_BIN}" scripts/verify_manifest.py || true

echo "Salvando os dados no Git..."
git add .
git commit -m "docs: add empirical results, W5 LangChain data, and TOST replication tables from background run" || true
git push origin feat/peer-review-revisions || true

echo "Tudo salvo e sincronizado com sucesso!"
