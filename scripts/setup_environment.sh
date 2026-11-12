#!/usr/bin/env bash
# ==============================================================================
# PicoClaw vs. OpenClaw Benchmark Suite - Master Testbed Setup Script
# Script de Configuração Mestra do Ambiente de Testes
#
# Sets up Python virtual environment, dependencies, dataset generation,
# and compiles picoclaw_orch if Go is available.
# Cross-platform: macOS (Apple Silicon / Intel), Linux (x86_64 / arm64), WSL2.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
BENCH_DIR="$REPO_DIR/benchmark"
TOOLS_DIR="$REPO_DIR/tools"
DATA_DIR="$REPO_DIR/data"

echo "========================================================================"
echo " 🚀 Initializing PicoClaw vs. OpenClaw Testbed Environment"
echo "    Repository: $REPO_DIR"
echo "========================================================================"

OS="$(uname -s)"
ARCH="$(uname -m)"
echo "[INFO] Detected Platform: $OS ($ARCH)"

# 1. Tornar executáveis os binários e scripts do repositório
chmod +x "$REPO_DIR/scripts/"*.sh 2>/dev/null || true
chmod +x "$REPO_DIR/benchmark/"*.sh 2>/dev/null || true
chmod +x "$REPO_DIR/benchmark/picoclaw_orch" 2>/dev/null || true
chmod +x "$TOOLS_DIR/uv/uv" 2>/dev/null || true
chmod +x "$TOOLS_DIR/hyperfine/hyperfine" 2>/dev/null || true
chmod +x "$TOOLS_DIR/picoclaw/picoclaw" 2>/dev/null || true
chmod +x "$TOOLS_DIR/llama_cpp/llama-b11887/llama-server" 2>/dev/null || true

# 2. Provisionar ambiente virtual Python
VENV_DIR="$TOOLS_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "---> [1/4] Creating Python 3.12 Virtual Environment..."
    if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ] && [ -x "$TOOLS_DIR/uv/uv" ]; then
        export UV_PYTHON_INSTALL_DIR="$TOOLS_DIR/python_runtime"
        export UV_CACHE_DIR="$TOOLS_DIR/uv_cache"
        "$TOOLS_DIR/uv/uv" venv "$VENV_DIR" --python 3.12
    elif command -v uv >/dev/null 2>&1; then
        uv venv "$VENV_DIR" --python 3.12
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m venv "$VENV_DIR"
    else
        echo "[ERROR] Python 3 not found in PATH. Please install Python 3.12+."
        exit 1
    fi
fi

PYTHON_BIN="$VENV_DIR/bin/python"

# 3. Instalar dependências científicas
echo "---> [2/4] Installing Python dependencies (numpy, scipy, matplotlib, pytest, ruff, python-docx, Pillow, psutil)..."
if [ -x "$TOOLS_DIR/uv/uv" ] && [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    "$TOOLS_DIR/uv/uv" pip install --python "$PYTHON_BIN" \
        numpy scipy matplotlib pytest ruff python-docx Pillow dulwich psutil
else
    "$PYTHON_BIN" -m pip install --upgrade pip
    "$PYTHON_BIN" -m pip install \
        numpy scipy matplotlib pytest ruff python-docx Pillow dulwich psutil
fi

# 4. Compilar orquestrador Go nativo se go estiver disponível
echo "---> [3/4] Checking Go toolchain for picoclaw_orch compilation..."
if command -v go >/dev/null 2>&1; then
    echo "       Compiling benchmark/picoclaw_orch with system go ($(go version))..."
    CGO_ENABLED=0 go build -o "$BENCH_DIR/picoclaw_orch" "$BENCH_DIR/picoclaw_orch.go"
    chmod +x "$BENCH_DIR/picoclaw_orch"
elif [ -x "$TOOLS_DIR/go/bin/go" ]; then
    echo "       Compiling benchmark/picoclaw_orch with embedded tools/go..."
    CGO_ENABLED=0 "$TOOLS_DIR/go/bin/go" build -o "$BENCH_DIR/picoclaw_orch" "$BENCH_DIR/picoclaw_orch.go"
    chmod +x "$BENCH_DIR/picoclaw_orch"
else
    echo "       [INFO] Go compiler not detected. Using precompiled picoclaw_orch binary (if present)."
fi

# 5. Garantir integridade dos datasets de carga sintética W1-W4
echo "---> [4/4] Verifying deterministic workload datasets in data/workload_data/..."
if [ ! -f "$DATA_DIR/workload_data/system_logs.jsonl" ] || [ ! -f "$DATA_DIR/workload_data/embedding_head_100k.npz" ]; then
    echo "       Generating workload datasets (mock_files, syslog, RAG vectors)..."
    "$PYTHON_BIN" "$BENCH_DIR/generate_datasets.py"
else
    echo "       Deterministic datasets verified."
fi

echo "========================================================================"
echo " ✅ Testbed Setup Complete!"
echo "    Python: $PYTHON_BIN"
echo "    To test: make test"
echo "    To simulate: make simulate-campaign"
echo "========================================================================"
