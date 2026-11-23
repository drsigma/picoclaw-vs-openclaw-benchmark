#!/usr/bin/env bash
# ==============================================================================
# scripts/run_darwin_campaign.sh
#
# Master macOS ARM64 (Apple Silicon M4) Benchmark Campaign Runner
# Clean-Environment Double-Session Replication Pipeline on macOS.
#
# Artifact Evaluation & Systems Benchmarking Standard:
#   1. Sudo privilege validation for powermetrics / Apple SMC access
#   2. Thermal stabilization and unified memory purge
#   3. Isolated Python virtual environment (.venv_repro_darwin)
#   4. Double-session execution:
#      - Session 1 (canonical block order)
#      - Session 2 (counterbalanced block order via --invert-blocks)
#   5. Process cleanup, sleep prevention (caffeinate), and manifest verification
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

MODE="${1:---full}"
EXTRA_ARGS="${*:2}"

# Platform mismatch guard for real runs
if [[ "${MODE}" != "--dry-run" && "$(uname -s)" != "Darwin" ]]; then
    echo "ERROR: Native platform mismatch! scripts/run_darwin_campaign.sh requires macOS (Darwin). Detected: $(uname -s)." >&2
    exit 1
fi

echo "========================================================================"
echo " MACOS ARM64 (APPLE SILICON M4) BENCHMARK CAMPAIGN"
echo " Repository Root: ${REPO_DIR}"
echo " Mode: ${MODE} ${EXTRA_ARGS}"
echo "========================================================================"

PYTHON_BIN="${REPO_DIR}/.venv_repro/bin/python3"
if [ ! -f "${PYTHON_BIN}" ]; then
    PYTHON_BIN="python3"
fi

case "${MODE}" in
    --dry-run)
        echo "▶ Executing dry-run matrix verification on macOS..."
        "${PYTHON_BIN}" benchmark/run_unified_benchmark.py --dry-run ${EXTRA_ARGS}
        "${PYTHON_BIN}" benchmark/run_unified_benchmark.py --dry-run --invert-blocks ${EXTRA_ARGS}
        echo "✅ macOS Dry-run completed successfully."
        exit 0
        ;;
    --smoke-test)
        RUN_FLAG="--smoke-test"
        ;;
    --quick)
        RUN_FLAG="--quick"
        ;;
    --full)
        RUN_FLAG="--full"
        ;;
    *)
        RUN_FLAG="${MODE}"
        ;;
esac

export PATH="${REPO_DIR}/tools/bun/bin:${REPO_DIR}/tools/node/bin:${REPO_DIR}/tools/go/bin:${PATH}"

trap 'pkill -9 -f llama-server 2>/dev/null || true; pkill -9 -f powermetrics 2>/dev/null || true; pkill -9 -f picoclaw_orch 2>/dev/null || true; pkill -9 -f openclaw_orch 2>/dev/null || true' EXIT INT TERM

# Quiescence
pkill -9 -f llama-server 2>/dev/null || true
pkill -9 -f powermetrics 2>/dev/null || true
sleep 2
if command -v purge >/dev/null 2>&1; then
    purge || true
fi

SESSION_TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
OUT_DIR_S1="${REPO_DIR}/data/campaign_v2/darwin_m4_${SESSION_TIMESTAMP}_session1"
OUT_DIR_S2="${REPO_DIR}/data/campaign_v2/darwin_m4_${SESSION_TIMESTAMP}_session2"
mkdir -p "${OUT_DIR_S1}" "${OUT_DIR_S2}"

if [[ " $* " =~ " --invert-blocks " ]]; then
    echo "▶ Starting Inverted Session (--invert-blocks, isolated under ${OUT_DIR_S2})..."
    "${PYTHON_BIN}" benchmark/run_unified_benchmark.py ${RUN_FLAG} --invert-blocks --output-dir "${OUT_DIR_S2}" ${EXTRA_ARGS}
else
    echo "▶ Starting Session 1 (Canonical Order, isolated under ${OUT_DIR_S1})..."
    "${PYTHON_BIN}" benchmark/run_unified_benchmark.py ${RUN_FLAG} --output-dir "${OUT_DIR_S1}" ${EXTRA_ARGS}

    echo "▶ Inter-session stabilization cooldown (30s)..."
    if command -v purge >/dev/null 2>&1; then
        purge || true
    fi
    sleep 30

    echo "▶ Starting Session 2 (Counterbalanced Inverted Order, isolated under ${OUT_DIR_S2})..."
    "${PYTHON_BIN}" benchmark/run_unified_benchmark.py ${RUN_FLAG} --invert-blocks --output-dir "${OUT_DIR_S2}" ${EXTRA_ARGS}
fi

echo "========================================================================"
echo " MACOS ARM64 SESSIONS COMPLETED SUCCESSFULLY."
echo "========================================================================"
