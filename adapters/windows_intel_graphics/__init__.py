"""
adapters/windows_intel_graphics - Dedicated Windows Intel Graphics (iGPU / UMA) Benchmark Adapter.

Strictly isolated from Mac Mini M4 (darwin), Windows NVIDIA (windows_x86_64), and Linux campaigns.
Zero NVML / nvidia-smi calls; explicit 'N/A' for hardware metrics unavailable in Windows user-mode.
"""

from adapters.windows_intel_graphics.hardware_manifest import (
    collect_intel_windows_manifest,
    detect_intel_windows_provenance,
    save_machine_manifest,
)
from adapters.windows_intel_graphics.telemetry import (
    IntelGraphicsThermalAndLoadMonitor,
    assert_windows_process_counters_available,
    cleanup_orphan_processes,
    run_subprocess_with_intel_win_counters,
)
from adapters.windows_intel_graphics.validator import (
    validate_trial_extraction,
)

__all__ = [
    "collect_intel_windows_manifest",
    "detect_intel_windows_provenance",
    "save_machine_manifest",
    "IntelGraphicsThermalAndLoadMonitor",
    "assert_windows_process_counters_available",
    "cleanup_orphan_processes",
    "run_subprocess_with_intel_win_counters",
    "validate_trial_extraction",
]
