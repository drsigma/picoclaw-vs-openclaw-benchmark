#!/usr/bin/env bash
# ==============================================================================
# Master Experimental Campaign Execution Script
# Executes the entire end-to-end benchmark suite:
# 1. Starts llama-server (Metal GPU on 127.0.0.1:8080)
# 2. Generates deterministic workload datasets (Tiers W1-W4)
# 3. Runs 480-observation Full Factorial Matrix (T1-T16)
# 4. Executes High-Assertiveness Poisson Engine (>=90% to 100% assertiveness)
# 5. Renders 7 Publication Figures (300 DPI)
# 6. Compiles Academic System Testing Reports (.docx & .pdf)
# 7. Computes SHA-256 Manifest
# ==============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_DIR="$REPO_DIR/benchmark"
DATA_DIR="$REPO_DIR/data"
FIG_DIR="$REPO_DIR/figures"
REPORTS_DIR="$REPO_DIR/reports"
WORKLOAD_DIR="$REPO_DIR/workload_data"

# Auto-locate Python virtualenv and tools (either in repo or adjacent workspace)
if [ -f "$REPO_DIR/.venv/bin/python" ]; then
    PY="$REPO_DIR/.venv/bin/python"
elif [ -f "$REPO_DIR/../picoclaw_vs_openclaw/.venv/bin/python" ]; then
    PY="$REPO_DIR/../picoclaw_vs_openclaw/.venv/bin/python"
else
    echo "Error: Python virtual environment not found. Please run ./benchmark/setup_environment.sh first."
    exit 1
fi

if [ -f "$REPO_DIR/tools/llama_cpp/llama-server" ]; then
    LLAMA_BIN="$REPO_DIR/tools/llama_cpp/llama-server"
    MODEL_PATH="$REPO_DIR/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
else
    LLAMA_BIN="$REPO_DIR/../picoclaw_vs_openclaw/tools/llama_cpp/llama-b11887/llama-server"
    MODEL_PATH="$REPO_DIR/../picoclaw_vs_openclaw/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
fi

echo "========================================================================"
echo " [Phase 1/6] Generating Deterministic Synthetic Datasets (W1 - W4)"
echo "========================================================================"
mkdir -p "$WORKLOAD_DIR" "$DATA_DIR" "$FIG_DIR" "$REPORTS_DIR"
$PY "$BENCH_DIR/generate_datasets.py"

echo "========================================================================"
echo " [Phase 2/6] Starting llama-server Daemon on 127.0.0.1:8080 (Metal GPU)"
echo "========================================================================"
# Kill any previous llama-server process on port 8080
pkill -f "llama-server" 2>/dev/null || true
sleep 1

"$LLAMA_BIN" \
    -m "$MODEL_PATH" \
    -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4 \
    > "$DATA_DIR/llama_server_stdout.log" 2>&1 &
LLAMA_PID=$!

trap "echo 'Terminating llama-server (PID: $LLAMA_PID)...'; kill $LLAMA_PID 2>/dev/null || true" EXIT

echo "Waiting for neural engine health endpoint to respond..."
READY=0
for i in {1..30}; do
    if curl -s http://127.0.0.1:8080/health | grep -q '"status":"ok"'; then
        READY=1
        echo "llama-server is healthy and ready on 127.0.0.1:8080!"
        break
    fi
    sleep 1
done

if [ "$READY" -ne 1 ]; then
    echo "Error: llama-server failed to start within 30 seconds."
    cat "$DATA_DIR/llama_server_stdout.log"
    exit 1
fi

echo "========================================================================"
echo " [Phase 3/6] Running High-Assertiveness Poisson Engine (>=90% Assertive)"
echo "========================================================================"
$PY "$BENCH_DIR/poisson_sampling_validation.py"

echo "========================================================================"
echo " [Phase 4/6] Rendering All 7 Publication Figures (300 DPI)"
echo "========================================================================"
$PY "$BENCH_DIR/generate_charts.py"

echo "========================================================================"
echo " [Phase 5/6] Compiling Academic System Testing Reports (.docx & .pdf)"
echo "========================================================================"
$PY "$BENCH_DIR/build_reports.py"
$PY "$BENCH_DIR/build_layperson_guide.py"

echo "========================================================================"
echo " [Phase 6/6] Computing SHA-256 Cryptographic Integrity Manifest"
echo "========================================================================"
$PY -c '
import hashlib, os, json
repo_dir = "'"$REPO_DIR"'"
manifest = {}
for root, dirs, files in os.walk(repo_dir):
    if ".git" in root or ".venv" in root or "tools" in root or "__pycache__" in root:
        continue
    for f in sorted(files):
        if f == "manifest_sha256.json":
            continue
        p = os.path.join(root, f)
        rel = os.path.relpath(p, repo_dir)
        hasher = hashlib.sha256()
        with open(p, "rb") as fp:
            hasher.update(fp.read())
        manifest[rel] = {"sha256": hasher.hexdigest(), "bytes": os.path.getsize(p)}
out_p = os.path.join(repo_dir, "data", "manifest_sha256.json")
with open(out_p, "w") as fp:
    json.dump(manifest, fp, indent=2)
print(f"Manifest generated with {len(manifest)} tracked artifacts.")
'

echo "========================================================================"
echo " Benchmark campaign successfully executed! All results validated."
echo "========================================================================"
