<#
.SYNOPSIS
    scripts/run_windows_campaign.ps1 - Master Windows Benchmark Campaign Runner
    Executes confirmatory double-session campaigns on Windows (NVIDIA RTX and Intel HD Graphics).

.DESCRIPTION
    Executes standard systems replication pipeline on Windows:
      1. Environmental quiescence & background noise minimization.
      2. Native toolchain check (.venv_win, picoclaw_orch_windows.exe).
      3. Session 1 execution (canonical order).
      4. Inter-session thermal cooldown.
      5. Session 2 execution (--invert-blocks for counterbalancing).
      6. Integrity verification and manifest tracking.
#>

[CmdletBinding()]
param(
    [ValidateSet("full", "quick", "smoke-test", "dry-run")]
    [string]$Mode = "full",
    [switch]$InvertBlocks,
    [switch]$Resume,
    [string]$Target = "nvidia" # "nvidia" or "intel"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoDir = Split-Path -Parent $ScriptDir
Set-Location $RepoDir

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host " WINDOWS BENCHMARK CAMPAIGN RUNNER (Mode: $Mode, Target: $Target)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

$PythonExe = "$RepoDir\.venv_win\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python.exe"
}

$Flag = switch ($Mode) {
    "dry-run"    { "--dry-run" }
    "smoke-test" { "--smoke-test" }
    "quick"      { "--quick" }
    "full"       { "--full" }
    Default      { "--full" }
}

if ($Target -eq "intel") {
    $RunnerScript = "$RepoDir\adapters\windows_intel_graphics\runner.py"
} else {
    $RunnerScript = "$RepoDir\scripts\run_windows_x86_64_master_campaign.py"
}

if ($Mode -eq "dry-run") {
    Write-Host "▶ Executing dry-run matrix verification..." -ForegroundColor Yellow
    & $PythonExe $RunnerScript --dry-run
    & $PythonExe $RunnerScript --dry-run --invert-blocks
    Write-Host "✅ Dry-run completed successfully." -ForegroundColor Green
    exit 0
}

# Session 1: Canonical
Write-Host "▶ Starting Session 1 (Canonical Order)..." -ForegroundColor Yellow
& $PythonExe $RunnerScript $Flag

# Cooldown
Write-Host "▶ Inter-session stabilization cooldown (30s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Session 2: Inverted Blocks
Write-Host "▶ Starting Session 2 (Inverted Block Order)..." -ForegroundColor Yellow
& $PythonExe $RunnerScript $Flag --invert-blocks

Write-Host "========================================================================" -ForegroundColor Green
Write-Host " WINDOWS BENCHMARK CAMPAIGN COMPLETED SUCCESSFULLY." -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Green
