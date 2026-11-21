<#
.SYNOPSIS
    launch_sentinel_intel_win.ps1 - Spawns sentinel_intel_win.ps1 truly detached via WMI Win32_Process.Create
    so it survives parent shell / Job Object termination, and confirms liveness.
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

$cmdLine = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$SentinelScript`" -Reps $Reps -Warmups $Warmups -Workloads `"$Workloads`" -Stages `"$Stages`" -Sessions `"$Sessions`""

# Use WMI Win32_Process.Create so the process runs outside any parent Win32 Job Object (JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)
$wmiRes = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = $cmdLine
    CurrentDirectory = $RepoDir
}
if ($wmiRes.ReturnValue -ne 0 -or -not $wmiRes.ProcessId) {
    throw "Win32_Process.Create failed with ReturnValue=$($wmiRes.ReturnValue)"
}

$sentinelPid = [int]$wmiRes.ProcessId
$sentinelPid | Set-Content -Path $PidFile -Encoding ASCII
Start-Sleep -Seconds 4

$alive = Get-Process -Id $sentinelPid -ErrorAction SilentlyContinue
if (-not $alive) {
    throw "Sentinel process PID=$sentinelPid exited immediately after launch!"
}

Write-Output "SENTINEL_ACTIVE_DETACHED PID=$sentinelPid LOG_DIR=$LogDir"
if (Test-Path (Join-Path $LogDir "sentinel_heartbeat.log")) {
    Get-Content (Join-Path $LogDir "sentinel_heartbeat.log") -Tail 5
}
