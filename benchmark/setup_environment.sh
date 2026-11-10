#!/usr/bin/env bash
# ==============================================================================
# Setup Environment for PicoClaw vs. OpenClaw Benchmark on Apple Silicon
# Automatically provisions isolated runtimes without requiring root/sudo or Xcode.
# ==============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_DIR="$REPO_DIR/tools"
MODELS_DIR="$REPO_DIR/models"
DATA_DIR="$REPO_DIR/data"
BENCH_DIR="$REPO_DIR/benchmark"

mkdir -p "$TOOLS_DIR" "$MODELS_DIR" "$DATA_DIR"

echo "========================================================================"
echo " [Step 1/6] Provisioning Standalone Astral uv & CPython 3.12.3 Environment"
echo "========================================================================"
if [ ! -f "$TOOLS_DIR/uv/uv" ]; then
    echo "Downloading standalone uv (aarch64-apple-darwin)..."
    mkdir -p "$TOOLS_DIR/uv"
    curl -fsSL "https://github.com/astral-sh/uv/releases/download/0.13.5/uv-aarch64-apple-darwin.tar.gz" | tar -xz -C "$TOOLS_DIR/uv" --strip-components=1
fi

export PATH="$TOOLS_DIR/uv:$PATH"

if [ ! -d "$REPO_DIR/.venv" ]; then
    echo "Creating Python 3.12.3 virtual environment..."
    "$TOOLS_DIR/uv/uv" venv "$REPO_DIR/.venv" --python 3.12.3
    echo "Installing benchmark scientific dependencies..."
    "$TOOLS_DIR/uv/uv" pip install --python "$REPO_DIR/.venv/bin/python" \
        aiohttp websockets psutil numpy scipy matplotlib python-docx pillow chromadb onnxruntime
fi

echo "========================================================================"
echo " [Step 2/6] Provisioning Standalone Node.js v26.12.1 and OpenClaw v2026.10.7"
echo "========================================================================"
if [ ! -f "$TOOLS_DIR/node-v26.12.1/bin/node" ]; then
    echo "Downloading Node.js v26.12.1 (darwin-arm64)..."
    mkdir -p "$TOOLS_DIR/node-v26.12.1"
    curl -fsSL "https://nodejs.org/dist/v26.12.1/node-v26.12.1-darwin-arm64.tar.gz" | tar -xz -C "$TOOLS_DIR/node-v26.12.1" --strip-components=1
fi

export PATH="$TOOLS_DIR/node-v26.12.1/bin:$PATH"

if [ ! -f "$TOOLS_DIR/openclaw_npm/node_modules/.bin/openclaw" ]; then
    echo "Installing openclaw@2026.10.7 via npm..."
    mkdir -p "$TOOLS_DIR/openclaw_npm"
    npm install --prefix "$TOOLS_DIR/openclaw_npm" openclaw@2026.10.7
fi

echo "========================================================================"
echo " [Step 3/6] Provisioning Go v1.23.2 & PicoClaw v0.3.1 (Darwin ARM64)"
echo "========================================================================"
if [ ! -f "$TOOLS_DIR/go/bin/go" ]; then
    echo "Downloading Go 1.23.2 compiler (darwin-arm64)..."
    mkdir -p "$TOOLS_DIR/go"
    curl -fsSL "https://go.dev/dl/go1.23.2.darwin-arm64.tar.gz" | tar -xz -C "$TOOLS_DIR/go" --strip-components=1
fi

export PATH="$TOOLS_DIR/go/bin:$PATH"

if [ ! -f "$TOOLS_DIR/picoclaw_bin/picoclaw" ]; then
    echo "Downloading PicoClaw v0.3.1 native binary (Sipeed)..."
    mkdir -p "$TOOLS_DIR/picoclaw_bin"
    curl -fsSL "https://github.com/sipeed/picoclaw/releases/download/v0.3.1/picoclaw_Darwin_arm64.tar.gz" | tar -xz -C "$TOOLS_DIR/picoclaw_bin"
    chmod +x "$TOOLS_DIR/picoclaw_bin/picoclaw"
fi

echo "========================================================================"
echo " [Step 4/6] Provisioning hyperfine v2.0.0 Micro-Benchmarking Engine"
echo "========================================================================"
if [ ! -f "$TOOLS_DIR/hyperfine/hyperfine" ]; then
    echo "Downloading hyperfine v2.0.0..."
    mkdir -p "$TOOLS_DIR/hyperfine"
    curl -fsSL "https://github.com/sharkdp/hyperfine/releases/download/v2.0.0/hyperfine-v2.0.0-aarch64-apple-darwin.tar.gz" | tar -xz -C "$TOOLS_DIR/hyperfine" --strip-components=1
    chmod +x "$TOOLS_DIR/hyperfine/hyperfine"
fi

echo "========================================================================"
echo " [Step 5/6] Provisioning llama.cpp (Metal GPU) & Llama-3.2-3B-Instruct GGUF"
echo "========================================================================"
if [ ! -f "$TOOLS_DIR/llama_cpp/llama-server" ]; then
    echo "Downloading llama.cpp b11887 (Metal accelerated binary)..."
    mkdir -p "$TOOLS_DIR/llama_cpp"
    curl -fsSL "https://github.com/ggml-org/llama.cpp/releases/download/b11887/llama-b11887-bin-macos-arm64.zip" -o "$TOOLS_DIR/llama_cpp/llama.zip"
    unzip -q -o "$TOOLS_DIR/llama_cpp/llama.zip" -d "$TOOLS_DIR/llama_cpp"
    rm "$TOOLS_DIR/llama_cpp/llama.zip"
    chmod +x "$TOOLS_DIR/llama_cpp/llama-server"
fi

if [ ! -f "$MODELS_DIR/Llama-3.2-3B-Instruct-Q4_K_M.gguf" ]; then
    echo "Downloading Meta Llama-3.2-3B-Instruct Q4_K_M GGUF (1.92 GiB)..."
    curl -L "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf" -o "$MODELS_DIR/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
fi

echo "========================================================================"
echo " [Step 6/6] Compiling Native ARM64 Go Benchmark Orchestrator"
echo "========================================================================"
CGO_ENABLED=0 "$TOOLS_DIR/go/bin/go" build -o "$BENCH_DIR/picoclaw_orch" "$BENCH_DIR/picoclaw_orch.go"
chmod +x "$BENCH_DIR/picoclaw_orch"

echo "========================================================================"
echo " Environment setup completed successfully! All tools verified."
echo "========================================================================"
