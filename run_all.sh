#!/usr/bin/env bash
# ==============================================================================
# run_all.sh - Tri-Platform Master Replication Launcher
# Automates Double-Session Replication (Session 1 + Session 2) across
# ALL workloads (W1, W2, W3, W4, W5) in BOTH regimes (A - Cold Prefill, B - Warm Cache)
# Compatible with macOS ARM64 (Darwin), Linux x86_64, and Windows x86_64 (Git Bash/WSL).
# ==============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_DIR}"

UNAME_S="$(uname -s)"

echo "========================================================================"
echo "🚀 INICIANDO ORQUESTRADOR MESTRE TRI-PLATAFORMA (run_all.sh)"
echo "   Plataforma Detectada: ${UNAME_S}"
echo "   Workloads: W1, W2, W3, W4, W5 | Regimes: Cold (A) & Warm (B)"
echo "   Sessões: Sessão 1 + Sessão 2 (Double Session Replication)"
echo "========================================================================"

case "${UNAME_S}" in
    Linux*)
        echo "▶ Disparando pipeline mestre Linux x86_64..."
        chmod +x ./run_linux_campaign.sh
        exec ./run_linux_campaign.sh "$@"
        ;;
    Darwin*)
        echo "▶ Disparando pipeline mestre macOS ARM64 (Darwin Gold)..."
        chmod +x ./reproduce_darwin_gold.sh
        exec ./reproduce_darwin_gold.sh "$@"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "▶ Disparando pipeline mestre Windows 11 x86_64 (PowerShell)..."
        exec powershell.exe -ExecutionPolicy Bypass -File "./windows_gold.ps1" "$@"
        ;;
    *)
        echo "❌ Sistema operacional não reconhecido: ${UNAME_S}"
        exit 1
        ;;
esac
