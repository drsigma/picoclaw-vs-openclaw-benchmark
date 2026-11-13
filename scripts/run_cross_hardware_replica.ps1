# scripts/run_cross_hardware_replica.ps1 - Windows 11 / x86_64 Cross-Hardware Replication Runner
# Elsevier SoftwareX: picoclaw-vs-openclaw-benchmark (Gates B2 / E3)
#
# Usage (PowerShell):
#   powershell -ExecutionPolicy Bypass -File scripts\run_cross_hardware_replica.ps1

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  PicoClaw vs. OpenClaw Cross-Hardware Benchmark Replica (Windows 11)" -ForegroundColor Cyan
Write-Host "  Target: Intel/AMD x86_64 CPU + NVIDIA RTX GPU (NVML + Win32 Peak WSet)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# Check Python environment
$PythonCmd = "python"
if (Test-Path "tools\.venv\Scripts\python.exe") {
    $PythonCmd = "tools\.venv\Scripts\python.exe"
}

# Run replication battery
& $PythonCmd scripts\run_cross_hardware_replica.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Windows 11 cross-hardware replication completed successfully!" -ForegroundColor Green
    Write-Host "Results saved to data\linux_replica_trials.jsonl and data\cross_hardware_comparison.json" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Replication failed with exit code $LASTEXITCODE" -ForegroundColor Red
}
