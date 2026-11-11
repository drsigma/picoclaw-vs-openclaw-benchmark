#!/usr/bin/env bash
# ==============================================================================
# PicoClaw vs. OpenClaw Benchmark Suite - Automated Environment Provisioner
# Seta automaticamente o ambiente completo em qualquer máquina Apple Silicon (M1-M4)
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

# 1. Verificar arquitetura
ARCH="$(uname -m)"
OS="$(uname -s)"
if [ "$OS" != "Darwin" ] || [ "$ARCH" != "arm64" ]; then
    echo "[WARNING] This benchmark is calibrated for macOS Apple Silicon (darwin-arm64)."
fi

# 2. Tornar executáveis os binários embarcados
chmod +x "$TOOLS_DIR/uv/uv" 2>/dev/null || true
chmod +x "$TOOLS_DIR/hyperfine/hyperfine" 2>/dev/null || true
chmod +x "$TOOLS_DIR/picoclaw/picoclaw" 2>/dev/null || true
chmod +x "$TOOLS_DIR/llama_cpp/llama-b11887/llama-server" 2>/dev/null || true
chmod +x "$REPO_DIR/benchmark/picoclaw_orch" 2>/dev/null || true

# 3. Provisionar Node.js v26.12.1 (caso não exista em tools/node)
if [ ! -x "$TOOLS_DIR/node/bin/node" ]; then
    echo "---> Provisioning Node.js (darwin-arm64)..."
    mkdir -p "$TOOLS_DIR/node"
    if command -v node >/dev/null 2>&1; then
        echo "Using system node binary..."
    else
        NODE_TAR="node-v26.12.1-darwin-arm64.tar.gz"
        curl -fsSL -o "$TOOLS_DIR/$NODE_TAR" "https://nodejs.org/dist/v26.12.1/$NODE_TAR"
        tar -xzf "$TOOLS_DIR/$NODE_TAR" -C "$TOOLS_DIR/node" --strip-components=1
        rm -f "$TOOLS_DIR/$NODE_TAR"
    fi
    chmod +x "$TOOLS_DIR/node/bin/node" 2>/dev/null || true
fi

# 4. Provisionar Python Virtualenv via uv embarcado
if [ ! -d "$TOOLS_DIR/.venv" ]; then
    echo "---> Provisioning Python 3.12 Virtual Environment via embedded Astral uv..."
    export UV_PYTHON_INSTALL_DIR="$TOOLS_DIR/python_runtime"
    export UV_CACHE_DIR="$TOOLS_DIR/uv_cache"
    "$TOOLS_DIR/uv/uv" venv "$TOOLS_DIR/.venv" --python 3.12
    "$TOOLS_DIR/uv/uv" pip install --python "$TOOLS_DIR/.venv/bin/python" \
        numpy scipy matplotlib python-docx dulwich pytest ruff
fi
    echo "[OK] Python virtual environment ready at: $TOOLS_DIR/.venv/bin/python"
fi

# 5. Garantir que os dados sintéticos em data/workload_data estão presentes
if [ ! -f "$REPO_DIR/data/workload_data/syslog_750.jsonl" ]; then
    echo "---> Generating deterministic workload data (W1-W4)..."
    "$TOOLS_DIR/.venv/bin/python" "$REPO_DIR/benchmark/generate_datasets.py"
fi

echo "========================================================================"
echo " [SUCCESS] Benchmark Testbed Successfully Configured and 100% Self-Contained!"
echo " Use: $TOOLS_DIR/.venv/bin/python benchmark/poisson_sampling_validation.py"
echo "========================================================================"
