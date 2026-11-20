<#
.SYNOPSIS
    launch_sentinel_intel_win.ps1 - Detaches sentinel_intel_win.ps1 into background and confirms liveness.
#>
[CmdletBinding()]
param(
    [int]$Reps = 30,
    [int]$Warmups = 3,
    [string]$Workloads = "W2,W5",
    [string]$Stages = "B,TOOLRAG,A,ANALYZE",
    [string]$Sessions = "1,2"
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = "C:\bench_intel\logs"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
$SentinelScript = Join-Path $RepoDir "sentinel_intel_win.ps1"
$PidFile = Join-Path $LogDir "sentinel.pid"

$argsList = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $SentinelScript,
    "-Reps", "$Reps",
    "-Warmups", "$Warmups",
    "-Workloads", $Workloads,
    "-Stages", $Stages,
    "-Sessions", $Sessions
)

$p = Start-Process -FilePath "powershell.exe" -ArgumentList $argsList -WorkingDirectory $RepoDir -WindowStyle Hidden -PassThru
$p.Id | Set-Content -Path $PidFile -Encoding ASCII
Start-Sleep -Seconds 3

$alive = Get-Process -Id $p.Id -ErrorAction SilentlyContinue
if (-not $alive) {
    throw "Sentinel process exited immediately after launch!"
}

Write-Output "SENTINEL_ACTIVE PID=$($p.Id) LOG_DIR=$LogDir"
if (Test-Path (Join-Path $LogDir "sentinel_heartbeat.log")) {
    Get-Content (Join-Path $LogDir "sentinel_heartbeat.log") -Tail 5
}
