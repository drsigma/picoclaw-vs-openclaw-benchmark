#!/bin/bash
set -e
echo "=== INICIANDO CAMPANHA LIMPA LINUX (W1-W5, TOST, TELEMETRIA GRANULAR) ==="

# Garante energia ativa
xset s off 2>/dev/null || true
xset -dpms 2>/dev/null || true
setterm -blank 0 -powerdown 0 2>/dev/null || true
sudo chmod -R a+r /sys/class/powercap/intel-rapl* 2>/dev/null || true
sudo modprobe dell_smm_hwmon 2>/dev/null || true

# Executa a suíte completa (Sessão 1 e Sessão 2)
bash ./run_linux_campaign.sh

echo "=== CAMPANHA CONCLUÍDA. SINCRONIZANDO COM O GIT ==="
git add .
git commit -m "fix(linux): clean restart execution with W5 LangChain, granular telemetry, and TOST replication" || true
git push origin feat/peer-review-revisions

echo "=== CONSOLIDANDO E SINCRONIZANDO NA MAIN ==="
git checkout main
git merge feat/peer-review-revisions
git add .
git commit -m "feat(benchmark): complete 9.0+ tri-platform execution, W5 LangChain real-world RAG, and TOST replication results" || true
git push origin main
git checkout feat/peer-review-revisions

echo "=== TUDO PRONTO E ENVIADO PARA O GITHUB (BRANCHES feat/peer-review-revisions E main) ==="
