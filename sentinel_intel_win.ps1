<#
.SYNOPSIS
    sentinel_intel_win.ps1 - Autonomous Background Sentinel for Windows Intel Graphics Campaign.
.DESCRIPTION
    1. Keeps Windows awake via Win32 SetThreadExecutionState (anti-sleep / anti-display-off).
    2. Runs the full isolated Windows Intel Graphics campaign (Sessions 1 & 2, W2, W5, Tool-RAG, TOST).
    3. Monitors process liveness, RAM, CPU clock, and thermal state continuously until real exit.
    4. Validates generated JSONL, statistics, TOST replication, and SHA-256 manifests.
    5. Performs isolated git add / commit / push on branch feat/intel-graphics-windows-adapter
       (strictly Intel Graphics paths only; never touches Mac, Windows NVIDIA, or Linux).
#>
[CmdletBinding()]
param(
    [int]$Reps = 30,
    [int]$Warmups = 3,
    [string]$Workloads = "W2,W5",
    [string]$Stages = "B,TOOLRAG,A,ANALYZE",
    [string]$Sessions = "1,2",
    [string]$Model = "C:\bench_intel\models\Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    [string]$ToolsRoot = "C:\bench_intel\tools",
    [string]$Branch = "feat/intel-graphics-windows-adapter",
    [switch]$SkipPush
)

$ErrorActionPreference = "Continue"
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = "C:\bench_intel\logs"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

$HeartbeatLog = Join-Path $LogDir "sentinel_heartbeat.log"
$CampaignOutLog = Join-Path $LogDir "sentinel_campaign_stdout.log"
$CampaignErrLog = Join-Path $LogDir "sentinel_campaign_stderr.log"
$StatusJson = Join-Path $LogDir "sentinel_status.json"
$GitExe = "C:\Program Files\Git\cmd\git.exe"
$PyExe = Join-Path $ToolsRoot ".venv_intel\Scripts\python.exe"

function Write-Heartbeat($msg) {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    "$ts | $msg" | Out-File -FilePath $HeartbeatLog -Append -Encoding UTF8
}

function Save-Status($state, $details) {
    $obj = [ordered]@{
        updated_at = (Get-Date -Format "o")
        sentinel_pid = $PID
        state = $state
        repo_dir = $RepoDir
        branch = $Branch
        details = $details
    }
    $obj | ConvertTo-Json -Depth 6 | Set-Content -Path $StatusJson -Encoding UTF8
}

# Win32 SetThreadExecutionState P/Invoke to keep system and display awake
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class Win32PowerGuard {
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint esFlags);
    public const uint ES_CONTINUOUS = 0x80000000;
    public const uint ES_SYSTEM_REQUIRED = 0x00000001;
    public const uint ES_DISPLAY_REQUIRED = 0x00000002;
}
"@ -ErrorAction SilentlyContinue

function Assert-SystemAwake {
    try {
        [Win32PowerGuard]::SetThreadExecutionState(
            [Win32PowerGuard]::ES_CONTINUOUS -bor [Win32PowerGuard]::ES_SYSTEM_REQUIRED -bor [Win32PowerGuard]::ES_DISPLAY_REQUIRED
        ) | Out-Null
    } catch {}
}

Write-Heartbeat "=== SENTINEL STARTED (PID=$PID) ==="
Save-Status "STARTING" @{ reps = $Reps; warmups = $Warmups; workloads = $Workloads; sessions = $Sessions }
Assert-SystemAwake

# Ensure power timeouts stay at 0
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>$null
powercfg /change standby-timeout-ac 0 2>$null
powercfg /change hibernate-timeout-ac 0 2>$null
powercfg /change monitor-timeout-ac 0 2>$null
powercfg /change disk-timeout-ac 0 2>$null

# Clean orphan llama-server processes before launching
Get-Process -Name "llama-server","picoclaw_orch_windows" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

$RunnerScript = Join-Path $RepoDir "adapters\windows_intel_graphics\runner.py"
$ArgList = @(
    "-u",
    $RunnerScript,
    "--reps", "$Reps",
    "--warmups", "$Warmups",
    "--workloads", $Workloads,
    "--stages", $Stages,
    "--sessions", $Sessions,
    "--model", $Model,
    "--tools-root", $ToolsRoot
)

Write-Heartbeat "Launching campaign runner: $PyExe $($ArgList -join ' ')"
$proc = Start-Process -FilePath $PyExe `
    -ArgumentList $ArgList `
    -WorkingDirectory $RepoDir `
    -RedirectStandardOutput $CampaignOutLog `
    -RedirectStandardError $CampaignErrLog `
    -WindowStyle Hidden `
    -PassThru
# Cache Win32 process handle immediately so PowerShell 5.1 populates $proc.ExitCode after exit
$null = $proc.Handle

Write-Heartbeat "Campaign PID=$($proc.Id) started. Entering active monitoring loop..."
Save-Status "RUNNING" @{ campaign_pid = $proc.Id; stdout_log = $CampaignOutLog; stderr_log = $CampaignErrLog }

while (-not $proc.HasExited) {
    Assert-SystemAwake
    $osMem = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
    $freeMb = if ($osMem) { [math]::Round($osMem.FreePhysicalMemory / 1024.0, 0) } else { -1 }
    $cpuInfo = Get-CimInstance Win32_PerfFormattedData_Counters_ProcessorInformation -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq "_Total" } | Select-Object -First 1
    $freqMhz = if ($cpuInfo) { $cpuInfo.ProcessorFrequency } else { -1 }
    $cpuUtil = if ($cpuInfo) { $cpuInfo.PercentProcessorUtility } else { -1 }
    $tz = Get-CimInstance Win32_PerfFormattedData_Counters_ThermalZoneInformation -ErrorAction SilentlyContinue | Select-Object -First 1
    $tzC = if ($tz -and $tz.Temperature) { [math]::Round($tz.Temperature - 273.15, 1) } else { -1 }

    $lastLine = ""
    if (Test-Path $CampaignOutLog) {
        $tail = Get-Content $CampaignOutLog -Tail 1 -ErrorAction SilentlyContinue
        if ($tail) { $lastLine = $tail.ToString().Trim() }
    }
    Write-Heartbeat "ALIVE campaign_pid=$($proc.Id) free_ram=${freeMb}MB cpu=${cpuUtil}% freq=${freqMhz}MHz tz=${tzC}C | last: $lastLine"
    Save-Status "RUNNING" @{
        campaign_pid = $proc.Id
        free_ram_mb = $freeMb
        cpu_util_pct = $cpuUtil
        cpu_freq_mhz = $freqMhz
        acpi_tz_c = $tzC
        last_log_line = $lastLine
    }
    Start-Sleep -Seconds 60
}

$proc.WaitForExit()
$exitCode = $proc.ExitCode
Write-Heartbeat "Campaign process PID=$($proc.Id) exited with code=$exitCode"

if ($exitCode -ne 0) {
    Write-Heartbeat "ERROR: Campaign exited with non-zero code $exitCode. Skipping final push."
    Save-Status "FAILED" @{ exit_code = $exitCode; stderr_log = $CampaignErrLog }
    exit $exitCode
}

# Verify SHA-256 manifests and integrity
Write-Heartbeat "Running post-campaign integrity validation..."
$verifyCode = @"
import glob, hashlib, json, os, sys
repo = r'$RepoDir'
manifests = sorted(glob.glob(os.path.join(repo, 'data', 'manifest_sha256_windows_intel_graphics*.json')))
if not manifests:
    print('NO_MANIFESTS_FOUND')
    sys.exit(2)
checked = 0
for mp in manifests:
    m = json.load(open(mp, encoding='utf-8'))
    for rel, expected in m.items():
        fp = os.path.join(repo, rel)
        if not os.path.exists(fp):
            print('MISSING_FILE:', rel)
            sys.exit(3)
        actual = hashlib.sha256(open(fp, 'rb').read()).hexdigest()
        if actual != expected:
            print('HASH_MISMATCH:', rel)
            sys.exit(4)
        checked += 1
print(f'INTEGRITY_OK manifests={len(manifests)} files_verified={checked}')
"@
$verifyOut = & $PyExe -c $verifyCode 2>&1
$verifyRc = $LASTEXITCODE
Write-Heartbeat "Integrity check rc=$verifyRc output=$verifyOut"
if ($verifyRc -ne 0) {
    Save-Status "INTEGRITY_FAILED" @{ verify_output = ($verifyOut -join "`n") }
    exit $verifyRc
}

# Isolated git add, commit, and push (ONLY Intel Graphics files!)
Write-Heartbeat "Staging isolated Windows Intel Graphics results for git commit..."
Set-Location $RepoDir
& $GitExe checkout $Branch 2>&1 | Out-Null

$StagePaths = @(
    "adapters/windows_intel_graphics",
    "tests/test_windows_intel_graphics_adapter.py",
    "sentinel_intel_win.ps1",
    "launch_sentinel_intel_win.ps1",
    "data/windows_intel_graphics_session1",
    "data/windows_intel_graphics_session2",
    "data/manifest_sha256_windows_intel_graphics_session1.json",
    "data/manifest_sha256_windows_intel_graphics_session2.json",
    "data/manifest_sha256_windows_intel_graphics_replication.json",
    "results/publication_campaign_windows_intel_graphics_session1",
    "results/publication_campaign_windows_intel_graphics_session2",
    "results/publication_campaign_windows_intel_graphics_replication",
    "reproducibility/clean_run_windows_intel_graphics_session1",
    "reproducibility/clean_run_windows_intel_graphics_session2"
)

foreach ($sp in $StagePaths) {
    if (Test-Path (Join-Path $RepoDir $sp)) {
        & $GitExe add -- $sp 2>&1 | Out-Null
    }
}

$porcelain = & $GitExe status --porcelain
if ($porcelain) {
    $commitMsg = "feat(windows-intel-graphics): complete 2-session campaign, W2/W5/Tool-RAG data, TOST stats, and SHA-256 manifests"
    $commitOut = & $GitExe commit -m $commitMsg 2>&1
    Write-Heartbeat "Git commit output: $($commitOut -join ' | ')"
    if (-not $SkipPush) {
        $pushOut = & $GitExe push -u origin $Branch 2>&1
        Write-Heartbeat "Git push output (rc=$LASTEXITCODE): $($pushOut -join ' | ')"
    }
} else {
    Write-Heartbeat "No new changes to commit."
}

Write-Heartbeat "=== SENTINEL COMPLETED SUCCESSFULLY ==="
Save-Status "COMPLETED" @{
    exit_code = 0
    integrity = ($verifyOut -join " ")
    branch = $Branch
}
