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
    [string]$Target = "nvidia", # "nvidia" or "intel"
    [string]$Suffix = "",
    [string]$Stages = "",
    [string]$Model = "",
    [int]$Reps = 0,
    [int]$Warmups = -1
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoDir = Split-Path -Parent $ScriptDir
Set-Location $RepoDir

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host " WINDOWS BENCHMARK CAMPAIGN RUNNER (Mode: $Mode, Target: $Target)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

$isRealWindows = ($PSVersionTable.PSVersion.Major -ge 6 -and $IsWindows) -or ($env:OS -like "*Windows*")
if ($Mode -ne "dry-run" -and -not $isRealWindows) {
    Write-Error "ERROR: Native platform mismatch! scripts/run_windows_campaign.ps1 requires Windows. Detected non-Windows environment."
    exit 1
}

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

# Construct additional propagated parameters
$ExtraParams = @()
if ($Resume) {
    $ExtraParams += "--resume"
}
if ($Stages) {
    $ExtraParams += @("--stages", $Stages)
}
if ($Model) {
    $ExtraParams += @("--model", $Model)
}
if ($Reps -gt 0) {
    $ExtraParams += @("--reps", $Reps)
}
if ($Warmups -ge 0) {
    $ExtraParams += @("--warmups", $Warmups)
}
if ($Target -eq "intel") {
    # Ensure Intel runner does not double-expand sessions
    $ExtraParams += @("--sessions", "1")
}

if ($Mode -eq "dry-run") {
    Write-Host "▶ Executing dry-run matrix verification..." -ForegroundColor Yellow
    $dryCmd1 = @($RunnerScript, "--dry-run") + $ExtraParams
    Write-Host "Command: & $PythonExe $dryCmd1"
    & $PythonExe @dryCmd1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "FAIL-FAST: Dry run canonical failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }

    $dryCmd2 = @($RunnerScript, "--dry-run", "--invert-blocks") + $ExtraParams
    Write-Host "Command: & $PythonExe $dryCmd2"
    & $PythonExe @dryCmd2
    if ($LASTEXITCODE -ne 0) {
        Write-Error "FAIL-FAST: Dry run inverted failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
    Write-Host "✅ Dry-run completed successfully." -ForegroundColor Green
    exit 0
}

$SessionTimestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$BaseSuffix = if ($Suffix) { $Suffix } else { "_v2_${SessionTimestamp}" }

if ($InvertBlocks) {
    # If explicit invert blocks requested by caller, run single inverted counterbalanced session
    $SuffixInv = "${BaseSuffix}_session2"
    Write-Host "▶ Starting Inverted Session (--invert-blocks, isolated under $SuffixInv)..." -ForegroundColor Yellow
    $invCmd = @($RunnerScript, $Flag, "--invert-blocks", "--suffix", $SuffixInv) + $ExtraParams
    Write-Host "Executing: & $PythonExe $invCmd"
    & $PythonExe @invCmd
    if ($LASTEXITCODE -ne 0) {
        Write-Error "FAIL-FAST: Inverted session failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
} else {
    # Session 1: Canonical
    $SuffixS1 = "${BaseSuffix}_session1"
    $SuffixS2 = "${BaseSuffix}_session2"

    Write-Host "▶ Starting Session 1 (Canonical Order, isolated under $SuffixS1)..." -ForegroundColor Yellow
    $s1Cmd = @($RunnerScript, $Flag, "--suffix", $SuffixS1) + $ExtraParams
    Write-Host "Executing: & $PythonExe $s1Cmd"
    & $PythonExe @s1Cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Error "FAIL-FAST: Session 1 failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }

    # Cooldown
    Write-Host "▶ Inter-session stabilization cooldown (30s)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30

    # Session 2: Inverted Blocks
    Write-Host "▶ Starting Session 2 (Inverted Block Order, isolated under $SuffixS2)..." -ForegroundColor Yellow
    $s2Cmd = @($RunnerScript, $Flag, "--invert-blocks", "--suffix", $SuffixS2) + $ExtraParams
    Write-Host "Executing: & $PythonExe $s2Cmd"
    & $PythonExe @s2Cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Error "FAIL-FAST: Session 2 failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

Write-Host "========================================================================" -ForegroundColor Green
Write-Host " WINDOWS BENCHMARK CAMPAIGN COMPLETED SUCCESSFULLY." -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Green
