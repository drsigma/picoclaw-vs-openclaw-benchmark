<#
.SYNOPSIS
    scripts/run_windows_nvidia_campaign.ps1 - Dedicated Windows 11 + NVIDIA GPU Campaign Runner (Protocol V2)
    Strictly isolated from Windows-Intel (`scripts/run_windows_campaign.ps1`), Linux, and macOS.

.DESCRIPTION
    Orchestrates the confirmatory Windows-NVIDIA double-session campaign:
      1. Native Windows + physical NVIDIA GPU verification (nvidia-smi).
      2. Session 1 (S1, canonical block order) isolated under data\campaign_v2\windows_x86_64_nvidia_<RunId>_S1.
      3. Mandatory inter-session thermal cooldown (>= 60 s and GPU <= 72 C).
      4. Session 2 (S2, counterbalanced --invert-blocks) isolated under data\campaign_v2\windows_x86_64_nvidia_<RunId>_S2.
    Contains zero automatic Git mutations or destructive cleanup commands.
#>

[CmdletBinding()]
param(
    [ValidateSet("full", "quick", "smoke-test", "dry-run")]
    [string]$Mode = "full",
    [string]$RunId = "",
    [string]$SessionId = "",
    [string]$OutputDir = "",
    [string]$OutputDirS1 = "",
    [string]$OutputDirS2 = "",
    [int]$Ngl = 16,
    [int]$CooldownSeconds = 60,
    [int]$GpuTargetTempC = 72,
    [switch]$InvertBlocks,
    [switch]$Resume,
    [string]$Stages = "",
    [string]$Model = "",
    [int]$Reps = 0,
    [int]$Warmups = -1
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoDir = Split-Path -Parent $ScriptDir
Set-Location $RepoDir

if ($CooldownSeconds -lt 60) {
    $CooldownSeconds = 60
}

$isRealWindows = ($PSVersionTable.PSVersion.Major -ge 6 -and $IsWindows) -or ($env:OS -like "*Windows*")
if ($Mode -ne "dry-run" -and -not $isRealWindows) {
    Write-Error "ERROR: Native platform mismatch! scripts/run_windows_nvidia_campaign.ps1 requires Windows."
    exit 1
}

if ($Mode -ne "dry-run") {
    $smiCmd = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if (-not $smiCmd) {
        Write-Error "ERROR: nvidia-smi not found in PATH. Physical NVIDIA GPU required."
        exit 1
    }
    $gpuCheck = & nvidia-smi --query-gpu=index,uuid,name,driver_version --format=csv,noheader 2>&1
    if ($LASTEXITCODE -ne 0 -or -not $gpuCheck) {
        Write-Error "ERROR: Physical NVIDIA GPU check failed: $gpuCheck"
        exit 1
    }
    Write-Host "Verified NVIDIA GPU: $gpuCheck" -ForegroundColor Green
}

$PythonExe = Join-Path $RepoDir ".venv_win\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python.exe"
}

$RunnerScript = Join-Path $RepoDir "scripts\run_windows_nvidia_master_campaign.py"
if (-not (Test-Path $RunnerScript)) {
    Write-Error "ERROR: Runner script not found: $RunnerScript"
    exit 1
}

if (-not $RunId) {
    $RunId = "{0}_{1}_windows_nvidia" -f (Get-Date -Format "yyyyMMdd_HHmmss"), $env:COMPUTERNAME
}

$Flag = switch ($Mode) {
    "dry-run"    { "--dry-run" }
    "smoke-test" { "--smoke-test" }
    "quick"      { "--quick" }
    "full"       { "--full" }
    Default      { "--full" }
}

$CommonParams = @("--ngl", "$Ngl")
if ($Resume) { $CommonParams += "--resume" }
if ($Stages) { $CommonParams += @("--stages", $Stages) }
if ($Model)  { $CommonParams += @("--model", $Model) }
if ($Reps -gt 0) { $CommonParams += @("--reps", "$Reps") }
if ($Warmups -ge 0) { $CommonParams += @("--warmups", "$Warmups") }

function Wait-InterSessionCooldown {
    param([int]$MinSec, [int]$TargetGpuC)
    Write-Host "Inter-session thermal cooldown: minimum ${MinSec}s and GPU <= ${TargetGpuC}C..." -ForegroundColor Yellow
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    Start-Sleep -Seconds $MinSec
    while ($sw.Elapsed.TotalSeconds -lt 600) {
        $tRaw = (& nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>$null | Select-Object -First 1)
        $tVal = 0
        if ([int]::TryParse(($tRaw -as [string]).Trim(), [ref]$tVal)) {
            if ($tVal -le $TargetGpuC) {
                Write-Host "GPU stabilized at ${tVal}C after $([int]$sw.Elapsed.TotalSeconds)s." -ForegroundColor Green
                return
            }
            Write-Host "Waiting for GPU cooldown: current=${tVal}C target<=${TargetGpuC}C..." -ForegroundColor Yellow
        } else {
            return
        }
        Start-Sleep -Seconds 5
    }
}

if ($Mode -eq "dry-run") {
    $s1Out = if ($OutputDirS1) { $OutputDirS1 } else { "data\campaign_v2\windows_x86_64_nvidia_${RunId}_S1" }
    $s2Out = if ($OutputDirS2) { $OutputDirS2 } else { "data\campaign_v2\windows_x86_64_nvidia_${RunId}_S2" }
    & $PythonExe $RunnerScript --dry-run --session-id "${RunId}_S1" --output-dir $s1Out @CommonParams
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $PythonExe $RunnerScript --dry-run --invert-blocks --session-id "${RunId}_S2" --output-dir $s2Out @CommonParams
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    exit 0
}

if ($OutputDir -or $InvertBlocks) {
    $sid = if ($SessionId) { $SessionId } elseif ($InvertBlocks) { "${RunId}_S2" } else { "${RunId}_S1" }
    $out = if ($OutputDir) { $OutputDir } elseif ($InvertBlocks) { "data\campaign_v2\windows_x86_64_nvidia_${RunId}_S2" } else { "data\campaign_v2\windows_x86_64_nvidia_${RunId}_S1" }
    $cmdArgs = @($RunnerScript, $Flag, "--session-id", $sid, "--output-dir", $out) + $CommonParams
    if ($InvertBlocks) { $cmdArgs += "--invert-blocks" }
    Write-Host "Executing single Windows-NVIDIA session: $PythonExe $($cmdArgs -join ' ')" -ForegroundColor Cyan
    & $PythonExe @cmdArgs
    exit $LASTEXITCODE
}

$s1Id = "${RunId}_S1"
$s2Id = "${RunId}_S2"
$s1Dir = if ($OutputDirS1) { $OutputDirS1 } else { "data\campaign_v2\windows_x86_64_nvidia_${RunId}_S1" }
$s2Dir = if ($OutputDirS2) { $OutputDirS2 } else { "data\campaign_v2\windows_x86_64_nvidia_${RunId}_S2" }

Write-Host "=== Starting Windows-NVIDIA Session 1 (Canonical) ===" -ForegroundColor Cyan
& $PythonExe $RunnerScript $Flag --session-id $s1Id --output-dir $s1Dir @CommonParams
if ($LASTEXITCODE -ne 0) {
    Write-Error "FAIL-FAST: Session 1 exited with code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Wait-InterSessionCooldown -MinSec $CooldownSeconds -TargetGpuC $GpuTargetTempC

Write-Host "=== Starting Windows-NVIDIA Session 2 (Inverted Blocks) ===" -ForegroundColor Cyan
& $PythonExe $RunnerScript $Flag --invert-blocks --session-id $s2Id --output-dir $s2Dir @CommonParams
if ($LASTEXITCODE -ne 0) {
    Write-Error "FAIL-FAST: Session 2 exited with code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "WINDOWS-NVIDIA DOUBLE-SESSION CAMPAIGN COMPLETE." -ForegroundColor Green
exit 0
