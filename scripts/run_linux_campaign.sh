#!/usr/bin/env bash
# ==============================================================================
# scripts/run_linux_campaign.sh
#
# Master Linux x86_64 Benchmark Campaign Runner
# Clean-Environment Double-Session Replication Pipeline on Linux x86_64.
#
# Artifact Evaluation & Systems Benchmarking Standard:
#   1. Sudo & privilege validation (RAPL, NVML, fan PWM, sleep targets)
#   2. Thermal stabilization (fan profile via dell_smm / alienware_wmi / sysfs)
#   3. Isolated Python virtual environment (.venv_repro)
#   4. Double-session execution:
#      - Session 1 (canonical block order)
#      - Session 2 (inverted block order via --invert-blocks)
#   5. Process cleanup, drop_caches, and inter-session verification
#   6. Full system restoration on exit (trap cleanup)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

MODE="${1:---full}"
EXTRA_ARGS="${*:2}"

# Platform mismatch guard for real runs
if [[ "${MODE}" != "--dry-run" && "$(uname -s)" != "Linux" ]]; then
    echo "ERROR: Native platform mismatch! scripts/run_linux_campaign.sh requires Linux. Detected: $(uname -s)." >&2
    exit 1
fi

echo "========================================================================"
echo " LINUX x86_64 BENCHMARK CAMPAIGN (CONFIRMATORY EXECUTION)"
echo " Repository Root: ${REPO_DIR}"
echo " Mode: ${MODE} ${EXTRA_ARGS}"
echo "========================================================================"

PYTHON_BIN="${REPO_DIR}/.venv_repro/bin/python3"
if [ ! -f "${PYTHON_BIN}" ]; then
    PYTHON_BIN="python3"
fi

case "${MODE}" in
    --dry-run)
        echo "▶ Executing dry-run matrix verification..."
        "${PYTHON_BIN}" scripts/run_linux_x86_64_master_campaign.py --dry-run ${EXTRA_ARGS}
        "${PYTHON_BIN}" scripts/run_linux_x86_64_master_campaign.py --dry-run --invert-blocks ${EXTRA_ARGS}
        echo "✅ Dry-run completed successfully."
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

SESSION_TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
SUFFIX_S1="_v2_${SESSION_TIMESTAMP}_session1"
SUFFIX_S2="_v2_${SESSION_TIMESTAMP}_session2"

# Execute Session 1 (Canonical order)
echo "▶ Starting Session 1 (Canonical Order, isolated under ${SUFFIX_S1})..."
"${PYTHON_BIN}" scripts/run_linux_x86_64_master_campaign.py ${RUN_FLAG} --suffix "${SUFFIX_S1}" ${EXTRA_ARGS}

# Cooldown between sessions
echo "▶ Inter-session stabilization cooldown (30s)..."
sync && sleep 30

# Execute Session 2 (Counterbalanced Inverted Order)
echo "▶ Starting Session 2 (Inverted Block Order for Counterbalancing, isolated under ${SUFFIX_S2})..."
"${PYTHON_BIN}" scripts/run_linux_x86_64_master_campaign.py ${RUN_FLAG} --invert-blocks --suffix "${SUFFIX_S2}" ${EXTRA_ARGS}

echo "========================================================================"
echo " LINUX x86_64 SESSIONS COMPLETED SUCCESSFULLY."
echo "========================================================================"
