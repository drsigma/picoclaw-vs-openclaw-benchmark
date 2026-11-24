<#
.SYNOPSIS
    launch_sentinel_intel_win.ps1 - Official Shielded Protocol V2 Entry Point for Windows Intel HD Graphics 4600.
    Spawns sentinel_intel_win.ps1 truly detached via WMI Win32_Process.Create (outside parent Job Object)
    and verifies liveness + exclusive lock acquisition.
#>
[CmdletBinding()]
param(
    [int]$Reps = 30,
    [int]$Warmups = 3,
    [string]$Workloads = "W1,W2,W3,W4,W5",
    [string]$Stages = "B,TOOLRAG,A,ANALYZE",
    [string]$Model = "",
    [string]$RunId = ""
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $Model) {
    $Model = Join-Path $RepoDir "models\Llama-3.2-3B-Instruct-Q4_K_M.gguf"
}
if (-not $RunId) {
    $RunId = "{0}_{1}_{2}" -f (Get-Date -Format "yyyyMMdd_HHmmss"), $env:COMPUTERNAME, "windows_intel"
}
$Desktop = [Environment]::GetFolderPath("Desktop")
$OvernightDir = Join-Path $Desktop "overnight_runs"
$RunRoot = Join-Path $OvernightDir $RunId
New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null

$LockFile = Join-Path $OvernightDir "windows_intel.lock"
if (Test-Path $LockFile) {
    throw "FAIL-FAST: Exclusive lock file already exists ($LockFile). Another instance may be running."
}

$LogDir = "C:\bench_intel\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$SentinelScript = Join-Path $RepoDir "sentinel_intel_win.ps1"
$PidFile = Join-Path $LogDir "sentinel.pid"

Write-Output "Plataforma: Windows Intel HD Graphics 4600"
Write-Output "Workloads: $Workloads"
Write-Output "Regimes: Cold e Warm"
Write-Output "Sessoes: S1 (canonica) e S2 (--invert-blocks)"
Write-Output "Repeticoes: $Reps"
Write-Output "Warmups: $Warmups"
Write-Output "Energia Intel GPU: N/A, nao zero"
Write-Output "Modelo: Meta-Llama-3.2-3B-Instruct Q4_K_M ($Model)"
Write-Output "Execucao: launch_sentinel_intel_win.ps1"
Write-Output "RunId: $RunId"
Write-Output "RunRoot: $RunRoot"

$cmdLine = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$SentinelScript`" -Reps $Reps -Warmups $Warmups -Workloads `"$Workloads`" -Stages `"$Stages`" -Model `"$Model`" -RunId `"$RunId`" -RunRoot `"$RunRoot`""

$wmiRes = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = $cmdLine
    CurrentDirectory = $RepoDir
}
if ($wmiRes.ReturnValue -ne 0 -or -not $wmiRes.ProcessId) {
    throw "Win32_Process.Create failed with ReturnValue=$($wmiRes.ReturnValue)"
}

$sentinelPid = [int]$wmiRes.ProcessId
$sentinelPid | Set-Content -Path $PidFile -Encoding ASCII
Start-Sleep -Seconds 5

$alive = Get-Process -Id $sentinelPid -ErrorAction SilentlyContinue
if (-not $alive) {
    throw "Sentinel process PID=$sentinelPid exited immediately after launch!"
}

Write-Output "SENTINEL_ACTIVE_DETACHED PID=$sentinelPid RUN_ID=$RunId RUN_ROOT=$RunRoot"
$hb = Join-Path $RunRoot "sentinel_heartbeat.log"
if (Test-Path $hb) {
    Get-Content $hb -Tail 5
}
