#!/usr/bin/env bash
# ==============================================================================
# PicoClaw vs. OpenClaw Benchmark Suite - Automated Environment Provisioner
# Provisionador Automático de Ambiente para o Benchmark PicoClaw vs. OpenClaw
#
# Author / Autor: Rafael Paniccia Cassetta (UFABC)
# Multi-OS: macOS Apple Silicon (Darwin arm64), Linux (x86_64 / arm64), WSL2
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
TOOLS_DIR="$REPO_DIR/tools"

echo "========================================================================"
echo " Initializing PicoClaw vs. OpenClaw Benchmark Testbed"
echo " Repository Root: $REPO_DIR"
echo " Tools Directory: $TOOLS_DIR"
echo "========================================================================"

# 1. Verificar arquitetura e sistema operacional / OS & Architecture detection
ARCH="$(uname -m)"
OS="$(uname -s)"
echo "[INFO] Detected Operating System: $OS ($ARCH)"
if [ "$OS" != "Darwin" ] || [ "$ARCH" != "arm64" ]; then
    echo "[INFO] Running on non-Darwin-arm64 platform ($OS $ARCH)."
    echo "       Physical SMC hardware telemetry is exclusive to Apple Silicon."
    echo "       All workloads, statistical pipelines, and figures are 100% reproducible via:"
    echo "       -> make test"
    echo "       -> make simulate-campaign"
    echo "       -> make reproduce-figures"
fi

# 2. Permissões de execução para binários embarcados (se compatíveis)
chmod +x "$TOOLS_DIR/uv/uv" 2>/dev/null || true
chmod +x "$TOOLS_DIR/hyperfine/hyperfine" 2>/dev/null || true
chmod +x "$TOOLS_DIR/picoclaw/picoclaw" 2>/dev/null || true
chmod +x "$TOOLS_DIR/llama_cpp/llama-b11887/llama-server" 2>/dev/null || true
chmod +x "$REPO_DIR/benchmark/picoclaw_orch" 2>/dev/null || true

# 3. Provisionar Node.js
if [ ! -x "$TOOLS_DIR/node/bin/node" ]; then
    if command -v node >/dev/null 2>&1; then
        echo "[INFO] Using system Node.js binary: $(command -v node) ($(node --version))"
    elif [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
        echo "---> Provisioning Node.js (darwin-arm64)..."
        mkdir -p "$TOOLS_DIR/node"
        NODE_TAR="node-v26.12.1-darwin-arm64.tar.gz"
        curl -fsSL -o "$TOOLS_DIR/$NODE_TAR" "https://nodejs.org/dist/v26.12.1/$NODE_TAR"
        tar -xzf "$TOOLS_DIR/$NODE_TAR" -C "$TOOLS_DIR/node" --strip-components=1
        rm -f "$TOOLS_DIR/$NODE_TAR"
        chmod +x "$TOOLS_DIR/node/bin/node" 2>/dev/null || true
    else
        echo "[WARNING] Node.js not detected in system PATH. Install Node.js or use simulated mode."
    fi
fi

# 4. Provisionar Python Virtualenv via uv ou python3 venv padrão
if [ ! -d "$TOOLS_DIR/.venv" ]; then
    echo "---> Provisioning Python 3.12 Virtual Environment..."
    if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ] && [ -x "$TOOLS_DIR/uv/uv" ]; then
        export UV_PYTHON_INSTALL_DIR="$TOOLS_DIR/python_runtime"
        export UV_CACHE_DIR="$TOOLS_DIR/uv_cache"
        "$TOOLS_DIR/uv/uv" venv "$TOOLS_DIR/.venv" --python 3.12
        "$TOOLS_DIR/uv/uv" pip install --python "$TOOLS_DIR/.venv/bin/python" \
            numpy scipy matplotlib python-docx dulwich pytest ruff
    elif command -v uv >/dev/null 2>&1; then
        uv venv "$TOOLS_DIR/.venv" --python 3.12
        uv pip install --python "$TOOLS_DIR/.venv/bin/python" \
            numpy scipy matplotlib python-docx dulwich pytest ruff
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m venv "$TOOLS_DIR/.venv"
        "$TOOLS_DIR/.venv/bin/python" -m pip install --upgrade pip
        "$TOOLS_DIR/.venv/bin/python" -m pip install \
            numpy scipy matplotlib python-docx dulwich pytest ruff
    else
        echo "[ERROR] No suitable Python interpreter found (python3 or uv). Please install Python 3.12+."
        exit 1
    fi
fi
echo "[OK] Python virtual environment ready at: $TOOLS_DIR/.venv/bin/python"

# 5. Garantir que os dados sintéticos em data/workload_data estão presentes
if [ ! -f "$REPO_DIR/data/workload_data/syslog_750.jsonl" ]; then
    echo "---> Generating deterministic workload data (W1-W4)..."
    "$TOOLS_DIR/.venv/bin/python" "$REPO_DIR/benchmark/generate_datasets.py"
fi

echo "========================================================================"
echo " [SUCCESS] Benchmark Testbed Successfully Configured!"
echo " Use: $TOOLS_DIR/.venv/bin/python benchmark/run_unified_benchmark.py --simulate"
echo "========================================================================"
