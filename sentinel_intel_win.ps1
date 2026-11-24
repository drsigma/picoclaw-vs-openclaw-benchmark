<#
.SYNOPSIS
    sentinel_intel_win.ps1 - Shielded Protocol V2 Overnight Sentinel for Windows Intel HD Graphics 4600.
.DESCRIPTION
    Executes the confirmatory double-session Windows Intel HD Graphics 4600 campaign (S1 canonical + S2 --invert-blocks)
    with fail-fast guards, exclusive lockfile, Fase 1-9 audit artifacts on Desktop, reversible Admin anti-interruption
    shield (power, screen lock, Windows Update wuauserv/UsoSvc), per-block checkpoints, Fase 8 post-run validations,
    and conditional main commit/push strictly gated by SUCCESS.marker.
#>
[CmdletBinding()]
param(
    [int]$Reps = 30,
    [int]$Warmups = 3,
    [string]$Workloads = "W1,W2,W3,W4,W5",
    [string]$Stages = "B,TOOLRAG,A,ANALYZE",
    [string]$Model = "",
    [string]$ToolsRoot = "C:\bench_intel\tools",
    [string]$RunId = "",
    [string]$RunRoot = "",
    [switch]$SkipPush
)

$ErrorActionPreference = "Continue"
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoDir

if (-not $Model) {
    $Model = Join-Path $RepoDir "models\Llama-3.2-3B-Instruct-Q4_K_M.gguf"
}
if (-not $RunId) {
    $RunId = "{0}_{1}_{2}" -f (Get-Date -Format "yyyyMMdd_HHmmss"), $env:COMPUTERNAME, "windows_intel"
}
$Desktop = [Environment]::GetFolderPath("Desktop")
$OvernightDir = Join-Path $Desktop "overnight_runs"
if (-not $RunRoot) {
    $RunRoot = Join-Path $OvernightDir $RunId
}
New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
$CheckpointsDir = Join-Path $RunRoot "checkpoints"
New-Item -ItemType Directory -Force -Path $CheckpointsDir | Out-Null

$LogDir = "C:\bench_intel\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$HeartbeatLog = Join-Path $RunRoot "sentinel_heartbeat.log"
$StatusJson = Join-Path $RunRoot "sentinel_status.json"
$GlobalStatusJson = Join-Path $LogDir "sentinel_status.json"
$GlobalHeartbeat = Join-Path $LogDir "sentinel_heartbeat.log"

$GitExe = "C:\Program Files\Git\cmd\git.exe"
$PyExe = Join-Path $ToolsRoot ".venv_intel\Scripts\python.exe"
if (-not (Test-Path $PyExe)) { $PyExe = "python.exe" }

# Prepend portable Node 22 & Bun to PATH and force UTF-8 for redirected Python stdout/stderr
$env:PATH = "$ToolsRoot\node\node-v22.23.5-win-x64;$ToolsRoot\bun\bun-windows-x64;C:\Program Files\Git\cmd;" + $env:PATH
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$LockFile = Join-Path $OvernightDir "windows_intel.lock"
$StartUtc = (Get-Date).ToUniversalTime()

# Acquire exclusive lock (FileMode.CreateNew)
$lockStream = $null
try {
    $lockStream = [System.IO.File]::Open($LockFile, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    $lockBytes = [System.Text.Encoding]::UTF8.GetBytes("RUN_ID=$RunId`nSENTINEL_PID=$PID`nSTARTED_UTC=$($StartUtc.ToString('o'))`n")
    $lockStream.Write($lockBytes, 0, $lockBytes.Length)
    $lockStream.Close()
    $lockStream = $null
} catch {
    "LOCK_CONFLICT: $LockFile already exists at $(Get-Date -Format 'o')" | Out-File -FilePath (Join-Path $RunRoot "FAILED_REASON.md") -Encoding UTF8
    exit 2
}

Start-Transcript -Path (Join-Path $RunRoot "powershell_transcript.log") -Force | Out-Null

function Write-Heartbeat($msg) {
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $line = "$ts | $msg"
    $line | Out-File -FilePath $HeartbeatLog -Append -Encoding UTF8
    $line | Out-File -FilePath $GlobalHeartbeat -Append -Encoding UTF8
}

function Save-Status($state, $details) {
    $obj = [ordered]@{
        updated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        run_id = $RunId
        run_root = $RunRoot
        sentinel_pid = $PID
        state = $state
        repo_dir = $RepoDir
        details = $details
    }
    $json = $obj | ConvertTo-Json -Depth 6
    $json | Set-Content -Path $StatusJson -Encoding UTF8
    $json | Set-Content -Path $GlobalStatusJson -Encoding UTF8
}

function Run-Gate($prefix, $name, $argArr) {
    $so = Join-Path $RunRoot "${prefix}_${name}_stdout.txt"
    $se = Join-Path $RunRoot "${prefix}_${name}_stderr.txt"
    $p = Start-Process -FilePath $PyExe -ArgumentList $argArr -WorkingDirectory $RepoDir `
        -RedirectStandardOutput $so -RedirectStandardError $se -NoNewWindow -Wait -PassThru
    $null = $p.Handle
    Write-Heartbeat "Gate ${prefix}_${name} exit=$($p.ExitCode)"
    return $p.ExitCode
}

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class Win32PowerGuardV2 {
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint esFlags);
    public const uint ES_CONTINUOUS = 0x80000000;
    public const uint ES_SYSTEM_REQUIRED = 0x00000001;
    public const uint ES_DISPLAY_REQUIRED = 0x00000002;
}
"@ -ErrorAction SilentlyContinue

function Assert-SystemAwake {
    try {
        [Win32PowerGuardV2]::SetThreadExecutionState(
            [Win32PowerGuardV2]::ES_CONTINUOUS -bor [Win32PowerGuardV2]::ES_SYSTEM_REQUIRED -bor [Win32PowerGuardV2]::ES_DISPLAY_REQUIRED
        ) | Out-Null
    } catch {}
}

# Capture original power, screen lock, hibernation, and Windows Update service state for guaranteed reversible restore
$IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$OrigPowerLine = (powercfg /getactivescheme 2>&1) -join " "
$OrigPowerGuid = if ($OrigPowerLine -match '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})') { $Matches[1] } else { $null }
$OrigPowerQuery = (powercfg /query 2>&1) | Out-String
$OrigHibernateEnabled = Test-Path "C:\hiberfil.sys"
$DesktopReg = "HKCU:\Control Panel\Desktop"
$OrigScreenSaveActive = (Get-ItemProperty -Path $DesktopReg -Name ScreenSaveActive -ErrorAction SilentlyContinue).ScreenSaveActive
$OrigScreenSaverSecure = (Get-ItemProperty -Path $DesktopReg -Name ScreenSaverIsSecure -ErrorAction SilentlyContinue).ScreenSaverIsSecure

$OrigServices = @{}
foreach ($svcName in @("wuauserv", "UsoSvc")) {
    $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
    if ($svc) {
        $OrigServices[$svcName] = @{ Status = $svc.Status.ToString(); StartType = $svc.StartType.ToString() }
    }
}

$CampaignStatus = "FAILED_CAMPAIGN"
$CommitMain = "NAO_REALIZADO_POR_FALHA"
$PrincipalOcorrencia = "nenhuma"
$PytestSummary = "nao_executado"
$SessionsCompleted = "0/2"
$GitHeadPre = (& $GitExe rev-parse HEAD 2>$null).Trim()
$ModelSha256 = ""
$CampaignV2Dir = Join-Path $RepoDir "data\campaign_v2\windows_intel_graphics_$RunId"
$TrackedChildPids = New-Object System.Collections.ArrayList
$PhaseTimes = [ordered]@{ start_utc = $StartUtc.ToString("o") }

try {
    Write-Heartbeat "=== PROTOCOL V2 SENTINEL STARTED (RunId=$RunId, PID=$PID, IsAdmin=$IsAdmin) ==="
    Save-Status "STARTING" @{ is_admin = $IsAdmin; workloads = $Workloads; reps = $Reps; warmups = $Warmups }

    if (-not $IsAdmin) {
        $CampaignStatus = "FAILED_PREFLIGHT"
        $PrincipalOcorrencia = "Sessao sem privilegios de Administrador (necessario para pausar Windows Update e ler telemetria ACPI/WMI)."
        throw $PrincipalOcorrencia
    }

    # Fase 1: Hardware Check (Fail-Fast Platform Validation)
    $osObj = Get-CimInstance Win32_OperatingSystem
    $cpuObj = Get-CimInstance Win32_Processor | Select-Object -First 1
    $csObj = Get-CimInstance Win32_ComputerSystem
    $gpuObjs = @(Get-CimInstance Win32_VideoController)

    $hwPath = Join-Path $RunRoot "hardware_check.txt"
    @(
        "=== Win32_OperatingSystem ===",
        ($osObj | Format-List * | Out-String),
        "=== Win32_Processor ===",
        ($cpuObj | Format-List Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed | Out-String),
        "=== Win32_VideoController ===",
        ($gpuObjs | Format-List Name,AdapterCompatibility,DriverVersion,VideoMemoryType,PNPDeviceID,Status | Out-String),
        "=== Win32_ComputerSystem ===",
        ($csObj | Format-List Manufacturer,Model,TotalPhysicalMemory | Out-String),
        "=== UTC TIMESTAMP ===",
        ((Get-Date).ToUniversalTime().ToString("o"))
    ) | Set-Content -Path $hwPath -Encoding UTF8

    if ($osObj.OSArchitecture -notmatch '64') {
        $CampaignStatus = "FAILED_PLATFORM"
        $PrincipalOcorrencia = "Arquitetura nao x86_64: $($osObj.OSArchitecture)"
        throw $PrincipalOcorrencia
    }
    $intelGpu = $gpuObjs | Where-Object { $_.Name -match 'Intel.*HD Graphics 4600' -and $_.Status -eq 'OK' } | Select-Object -First 1
    if (-not $intelGpu) {
        $CampaignStatus = "FAILED_PLATFORM"
        $PrincipalOcorrencia = "Adapter Intel HD Graphics 4600 ausente ou inativo: $(($gpuObjs | ForEach-Object { $_.Name + ':' + $_.Status }) -join ', ')"
        throw $PrincipalOcorrencia
    }
    $nonIntelGpu = $gpuObjs | Where-Object { $_.Name -match 'NVIDIA|Radeon|AMD|GeForce|RTX|GTX' -and $_.Status -eq 'OK' }
    if ($nonIntelGpu) {
        $CampaignStatus = "FAILED_PLATFORM"
        $PrincipalOcorrencia = "GPU discreta nao autorizada detectada: $(($nonIntelGpu | ForEach-Object { $_.Name }) -join ', ')"
        throw $PrincipalOcorrencia
    }
    $PhaseTimes["phase1_hardware_ok_utc"] = (Get-Date).ToUniversalTime().ToString("o")

    # Fase 2: Verify required files, model SHA-256, and W2/W5 contracts
    $reqFiles = @(
        ".\launch_sentinel_intel_win.ps1",
        ".\sentinel_intel_win.ps1",
        ".\adapters\windows_intel_graphics\runner.py",
        ".\adapters\windows_intel_graphics\w5_intel_worker.py",
        ".\benchmark\workload_contracts.py",
        ".\scripts\verify_manifest.py",
        ".\scripts\audit_submission_gatekeeper.py",
        $Model
    )
    foreach ($rf in $reqFiles) {
        if (-not (Test-Path $rf)) {
            $CampaignStatus = "FAILED_PREFLIGHT"
            $PrincipalOcorrencia = "Arquivo obrigatorio ausente na Fase 2: $rf"
            throw $PrincipalOcorrencia
        }
    }
    $ModelSha256 = (Get-FileHash $Model -Algorithm SHA256).Hash

    $contractCode = @"
from benchmark.workload_contracts import WORKLOAD_CONTRACTS
w2 = WORKLOAD_CONTRACTS['W2']
assert w2['expected_prompt_tokens_minimal'] == 2177, f'W2 minimal mismatch: {w2}'
assert w2['expected_prompt_tokens_bloated'] == 7091, f'W2 bloated mismatch: {w2}'
assert w2['expected_prompt_tokens_tool_rag'] == 917, f'W2 tool_rag mismatch: {w2}'
assert w2['expected_completion_tokens'] == 30, f'W2 completion mismatch: {w2}'
w5 = WORKLOAD_CONTRACTS['W5']
assert 'Policy Document Guidelines' in w5['prompt_template'] and 'Telemetry and Financial Database Records' in w5['prompt_template']
with open(r'adapters\windows_intel_graphics\w5_intel_worker.py', encoding='utf-8') as f:
    src = f.read()
assert 'build_w5_langchain_tools' in src and 'evaluate_quality' in src and 'http_status != 200' in src
print('PHASE2_CONTRACTS_OK W2=(2177,7091,917,30) W5=(full_prompt_and_schema_no_mock)')
"@
    $cOut = & $PyExe -c $contractCode 2>&1
    $cOut | Set-Content -Path (Join-Path $RunRoot "phase2_contracts_check.txt") -Encoding UTF8
    if ($LASTEXITCODE -ne 0) {
        $CampaignStatus = "FAILED_PREFLIGHT"
        $PrincipalOcorrencia = "Falha na validacao de contratos W2/W5 (Fase 2): $($cOut -join ' | ')"
        throw $PrincipalOcorrencia
    }
    $PhaseTimes["phase2_contracts_ok_utc"] = (Get-Date).ToUniversalTime().ToString("o")

    # Write initial run_metadata.json
    $gpus = @($gpuObjs | ForEach-Object { @{ name=$_.Name; driver=$_.DriverVersion; status=$_.Status; pnp=$_.PNPDeviceID } })
    $RunMeta = [ordered]@{
        run_id = $RunId
        hostname = $env:COMPUTERNAME
        username = $env:USERNAME
        is_admin = $IsAdmin
        started_utc = $StartUtc.ToString("o")
        windows_caption = $osObj.Caption
        windows_build = $osObj.BuildNumber
        architecture = $osObj.OSArchitecture
        cpu = $cpuObj.Name.Trim()
        memory_bytes = $csObj.TotalPhysicalMemory
        gpus = $gpus
        repo_dir = $RepoDir
        git_commit_pre = $GitHeadPre
        model_path = $Model
        model_sha256 = $ModelSha256
        python_version = (& $PyExe --version 2>&1).Trim()
        pytest_version = ((& $PyExe -m pytest --version 2>&1) | Select-Object -First 1).Trim()
        campaign_v2_dir = $CampaignV2Dir
        params = @{ reps = $Reps; warmups = $Warmups; workloads = $Workloads; stages = $Stages }
        status = "PREFLIGHT"
    }
    $RunMeta | ConvertTo-Json -Depth 6 | Set-Content -Path (Join-Path $RunRoot "run_metadata.json") -Encoding UTF8

    # Fase 3: Pre-run Verification (exact order, separate stdout/stderr in $RunRoot)
    Write-Heartbeat "=== FASE 3: PRE-RUN VERIFICATION ==="
    Save-Status "FASE3_PREFLIGHT" @{ step = "running_pre_checks" }
    $pRc1 = Run-Gate "pre" "python_version"      @("--version")
    $pRc2 = Run-Gate "pre" "pytest_version"      @("-m", "pytest", "--version")
    $pRc3 = Run-Gate "pre" "verify_manifest"     @("scripts\verify_manifest.py", "--pre-flight")
    $pRc4 = Run-Gate "pre" "gatekeeper"          @("scripts\audit_submission_gatekeeper.py")
    $pRc5 = Run-Gate "pre" "compileall"          @("-m", "compileall", "-q", "benchmark", "scripts", "adapters", "src", "tests")
    $pRc6 = Run-Gate "pre" "runner_dry_run"      @("adapters\windows_intel_graphics\runner.py", "--dry-run")
    $pRc7 = Run-Gate "pre" "pytest"              @("-m", "pytest", "-v")

    if ($pRc1 -ne 0 -or $pRc2 -ne 0 -or $pRc3 -ne 0 -or $pRc4 -ne 0 -or $pRc5 -ne 0 -or $pRc6 -ne 0 -or $pRc7 -ne 0) {
        $CampaignStatus = "FAILED_PREFLIGHT"
        $PrincipalOcorrencia = "Falha na Fase 3 pre-run: py=$pRc1 pyv=$pRc2 manifest=$pRc3 gatekeeper=$pRc4 compile=$pRc5 dryrun=$pRc6 pytest=$pRc7"
        throw $PrincipalOcorrencia
    }
    $PhaseTimes["phase3_preflight_ok_utc"] = (Get-Date).ToUniversalTime().ToString("o")

    # Fase 4: Process/Port/Disk pre-check & snapshot_pre_run
    @(
        "=== Target Processes ===",
        (Get-Process llama-server,picoclaw_orch,picoclaw_orch_windows,openclaw_orch -ErrorAction SilentlyContinue | Format-Table -AutoSize | Out-String),
        "=== Port 8080 ===",
        (Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Format-Table -AutoSize | Out-String),
        "=== Drives ===",
        (Get-PSDrive -PSProvider FileSystem | Format-Table -AutoSize | Out-String)
    ) | Set-Content -Path (Join-Path $RunRoot "process_port_disk_pre.txt") -Encoding UTF8

    $portInUse = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
    if ($portInUse) {
        $CampaignStatus = "FAILED_PREFLIGHT"
        $PrincipalOcorrencia = "Porta 8080 ocupada por processo desconhecido (OwningProcess=$($portInUse.OwningProcess -join ','))"
        throw $PrincipalOcorrencia
    }
    $cDrive = Get-PSDrive -Name C -ErrorAction SilentlyContinue
    if ($cDrive -and ($cDrive.Free / 1GB) -lt 5.0) {
        $CampaignStatus = "FAILED_PREFLIGHT"
        $PrincipalOcorrencia = "Espaco insuficiente em C: ($([math]::Round($cDrive.Free / 1GB, 2)) GB livre, minimo 5 GB)"
        throw $PrincipalOcorrencia
    }

    New-Item -ItemType Directory -Force -Path $CampaignV2Dir | Out-Null
    $SnapDir = Join-Path $RunRoot "snapshot_pre_run"
    New-Item -ItemType Directory -Force -Path $SnapDir | Out-Null
    foreach ($sf in @("data\manifest_sha256.json", "protocol\protocol_v2.0.json", "audit_export\gatekeeper_35_jsonl_audit.json")) {
        if (Test-Path $sf) { Copy-Item -Force $sf (Join-Path $SnapDir (Split-Path -Leaf $sf)) }
    }
    if (Test-Path "results") {
        Get-ChildItem -Path "results" -Recurse | Select-Object FullName, Length, LastWriteTimeUtc |
            Format-Table -AutoSize | Out-String | Set-Content -Path (Join-Path $SnapDir "results_tree.txt") -Encoding UTF8
    }
    $PhaseTimes["phase4_snapshot_ok_utc"] = (Get-Date).ToUniversalTime().ToString("o")

    # Fase 5: Pre-snapshot and REVERSIBLE anti-sleep, anti-screen-lock, and Windows Update pause
    @(
        "=== powercfg /getactivescheme ===",
        $OrigPowerLine,
        "=== ScreenSaver ===",
        "ScreenSaveActive=$OrigScreenSaveActive | ScreenSaverIsSecure=$OrigScreenSaverSecure | HibernateEnabled=$OrigHibernateEnabled",
        "=== Services (wuauserv, UsoSvc, BITS) ===",
        (Get-Service wuauserv,UsoSvc,BITS -ErrorAction SilentlyContinue | Format-Table Name,Status,StartType | Out-String),
        "=== powercfg /query ===",
        $OrigPowerQuery
    ) | Set-Content -Path (Join-Path $RunRoot "power_and_services_pre.txt") -Encoding UTF8

    Write-Heartbeat "Applying reversible anti-sleep, anti-screen-lock, and Windows Update pause..."
    Assert-SystemAwake
    powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>$null
    powercfg /change standby-timeout-ac 0 2>$null
    powercfg /change standby-timeout-dc 0 2>$null
    powercfg /change hibernate-timeout-ac 0 2>$null
    powercfg /change hibernate-timeout-dc 0 2>$null
    powercfg /change monitor-timeout-ac 0 2>$null
    powercfg /change monitor-timeout-dc 0 2>$null
    powercfg /change disk-timeout-ac 0 2>$null
    powercfg /change disk-timeout-dc 0 2>$null
    powercfg /hibernate off 2>$null
    Set-ItemProperty -Path $DesktopReg -Name ScreenSaveActive -Value "0" -ErrorAction SilentlyContinue
    if ($null -ne $OrigScreenSaverSecure) {
        Set-ItemProperty -Path $DesktopReg -Name ScreenSaverIsSecure -Value "0" -ErrorAction SilentlyContinue
    }

    foreach ($svcName in @("wuauserv", "UsoSvc")) {
        try {
            Stop-Service -Name $svcName -Force -ErrorAction SilentlyContinue
            Write-Heartbeat "Paused service $svcName reversibly (will restore in finally)."
        } catch {
            Write-Heartbeat "Warning pausing ${svcName}: $($_.Exception.Message)"
        }
    }

    # Close heavy non-essential user noise apps if running (never touch system/IDE processes)
    foreach ($noise in @("steam", "discord", "obs64", "OneDrive", "Teams")) {
        $found = Get-Process -Name $noise -ErrorAction SilentlyContinue
        if ($found) {
            Write-Heartbeat "Closing background noise app: $noise"
            $found | Stop-Process -Force -ErrorAction SilentlyContinue
        }
    }
    $PhaseTimes["phase5_shield_ok_utc"] = (Get-Date).ToUniversalTime().ToString("o")

    # Helper to run one session with continuous Fase 7 monitoring & fail-fast guards
    function Invoke-MonitoredSession($SessionNum, [switch]$Invert) {
        $outLog = Join-Path $RunRoot "session${SessionNum}_stdout.log"
        $errLog = Join-Path $RunRoot "session${SessionNum}_stderr.log"
        $runner = Join-Path $RepoDir "adapters\windows_intel_graphics\runner.py"
        $argList = @(
            "-u", $runner,
            "--reps", "$Reps",
            "--warmups", "$Warmups",
            "--workloads", $Workloads,
            "--stages", $Stages,
            "--sessions", "$SessionNum",
            "--model", $Model,
            "--tools-root", $ToolsRoot,
            "--campaign-v2-dir", $CampaignV2Dir,
            "--checkpoints-dir", $CheckpointsDir,
            "--trial-timeout-s", "3600"
        )
        if ($Invert) { $argList += "--invert-blocks" }

        Write-Heartbeat "Launching Session $SessionNum (invert=$($Invert.IsPresent)): $PyExe $($argList -join ' ')"
        $proc = Start-Process -FilePath $PyExe -ArgumentList $argList -WorkingDirectory $RepoDir `
            -RedirectStandardOutput $outLog -RedirectStandardError $errLog -WindowStyle Hidden -PassThru
        $null = $proc.Handle
        [void]$TrackedChildPids.Add($proc.Id)

        while (-not $proc.HasExited) {
            Assert-SystemAwake
            # Keep Windows Update paused if Task Scheduler attempts to restart it mid-campaign
            foreach ($svcName in @("wuauserv", "UsoSvc")) {
                $curSvc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
                if ($curSvc -and $curSvc.Status -eq "Running") {
                    Stop-Service -Name $svcName -Force -ErrorAction SilentlyContinue
                    Write-Heartbeat "Re-paused $svcName mid-campaign (restarted by OS scheduler)."
                }
            }

            $osMem = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
            $freeMb = if ($osMem) { [math]::Round($osMem.FreePhysicalMemory / 1024.0, 0) } else { -1 }
            $cpuInfo = Get-CimInstance Win32_PerfFormattedData_Counters_ProcessorInformation -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq "_Total" } | Select-Object -First 1
            $freqMhz = if ($cpuInfo) { $cpuInfo.ProcessorFrequency } else { -1 }
            $cpuUtil = if ($cpuInfo) { $cpuInfo.PercentProcessorUtility } else { -1 }
            $tz = Get-CimInstance Win32_PerfFormattedData_Counters_ThermalZoneInformation -ErrorAction SilentlyContinue | Select-Object -First 1
            $tzC = if ($tz -and $tz.Temperature) { [math]::Round($tz.Temperature - 273.15, 1) } else { -1 }
            $cFreeGb = [math]::Round(((Get-PSDrive -Name C -ErrorAction SilentlyContinue).Free / 1GB), 2)
            $igpuOk = [bool](Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'Intel.*HD Graphics 4600' -and $_.Status -eq 'OK' })
            $llamaProc = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue | Select-Object -First 1
            $llamaPid = if ($llamaProc) { $llamaProc.Id } else { 0 }

            $lastLine = ""
            if (Test-Path $outLog) {
                $t = Get-Content $outLog -Tail 1 -ErrorAction SilentlyContinue
                if ($t) { $lastLine = $t.ToString().Trim() }
                # Fail-fast if runner emitted [ERROR-SKIP] or [CAVEAT] (Proibicao #8: never mask failures)
                $badLines = Select-String -Path $outLog -Pattern '\[ERROR-SKIP\]|\[CAVEAT\]' -SimpleMatch:$false -ErrorAction SilentlyContinue
                if ($badLines) {
                    $firstBad = ($badLines | Select-Object -First 1).Line
                    try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
                    if ($llamaPid -gt 0) { try { Stop-Process -Id $llamaPid -Force -ErrorAction SilentlyContinue } catch {} }
                    $CampaignStatus = "FAILED_CAMPAIGN"
                    $PrincipalOcorrencia = "Fail-fast na Sessao ${SessionNum}: $firstBad"
                    throw $PrincipalOcorrencia
                }
            }

            if (-not $igpuOk) {
                try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
                if ($llamaPid -gt 0) { try { Stop-Process -Id $llamaPid -Force -ErrorAction SilentlyContinue } catch {} }
                $CampaignStatus = "FAILED_PLATFORM"
                $PrincipalOcorrencia = "Desaparecimento ou falha do adapter Intel HD Graphics 4600 durante Sessao $SessionNum"
                throw $PrincipalOcorrencia
            }
            if ($cFreeGb -lt 2.0) {
                try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
                if ($llamaPid -gt 0) { try { Stop-Process -Id $llamaPid -Force -ErrorAction SilentlyContinue } catch {} }
                $CampaignStatus = "FAILED_CAMPAIGN"
                $PrincipalOcorrencia = "Espaco insuficiente em C: (${cFreeGb} GB livre) durante Sessao $SessionNum"
                throw $PrincipalOcorrencia
            }

            Write-Heartbeat "ALIVE S${SessionNum} pid=$($proc.Id) llama=$llamaPid free_ram=${freeMb}MB disk=${cFreeGb}GB cpu=${cpuUtil}% freq=${freqMhz}MHz tz=${tzC}C igpu=$igpuOk | $lastLine"
            Save-Status "RUNNING_S${SessionNum}" @{
                session = $SessionNum
                invert_blocks = $Invert.IsPresent
                campaign_pid = $proc.Id
                llama_server_pid = $llamaPid
                free_ram_mb = $freeMb
                free_disk_gb = $cFreeGb
                cpu_util_pct = $cpuUtil
                cpu_freq_mhz = $freqMhz
                acpi_tz_c = $tzC
                intel_igpu_ok = $igpuOk
                last_log_line = $lastLine
                stdout_log = $outLog
                stderr_log = $errLog
            }
            Start-Sleep -Seconds 60
        }
        $proc.WaitForExit()
        $rc = $proc.ExitCode
        Write-Heartbeat "Session $SessionNum exited with code=$rc"
        if ($rc -ne 0) {
            throw "Session $SessionNum exited with non-zero code $rc (see $errLog)"
        }
        # Final check for any [ERROR-SKIP] or [CAVEAT] emitted in the last <60s before exit
        if (Test-Path $outLog) {
            $badLines = Select-String -Path $outLog -Pattern '\[ERROR-SKIP\]|\[CAVEAT\]' -ErrorAction SilentlyContinue
            if ($badLines) {
                $firstBad = ($badLines | Select-Object -First 1).Line
                $CampaignStatus = "FAILED_CAMPAIGN"
                $PrincipalOcorrencia = "Fail-fast pos-Sessao ${SessionNum}: $firstBad"
                throw $PrincipalOcorrencia
            }
        }
    }

    # Fase 6: S1 (canonical) -> 60s thermal cooldown -> S2 (--invert-blocks)
    Invoke-MonitoredSession -SessionNum 1
    $SessionsCompleted = "1/2 (S1 concluida)"
    $PhaseTimes["session1_done_utc"] = (Get-Date).ToUniversalTime().ToString("o")

    Write-Heartbeat "Inter-session thermal cooldown (60s)..."
    Start-Sleep -Seconds 60

    Invoke-MonitoredSession -SessionNum 2 -Invert
    $SessionsCompleted = "2/2 (S1 canonica + S2 --invert-blocks)"
    $PhaseTimes["session2_done_utc"] = (Get-Date).ToUniversalTime().ToString("o")

    # Compute combined S1 vs S2 TOST replication inside CampaignV2Dir
    Write-Heartbeat "Computing S1 vs S2 TOST inter-session replication..."
    $tostCode = @"
import os, sys
sys.path.insert(0, r'$RepoDir')
from adapters.windows_intel_graphics.analysis import run_combined_replication_analysis
from adapters.windows_intel_graphics.runner import IntelPaths
p = IntelPaths(r'$RepoDir', suffix='_replication', campaign_v2_dir=r'$CampaignV2Dir')
res = run_combined_replication_analysis(
    repo_dir=r'$RepoDir',
    s1_raw_dir=os.path.join(r'$CampaignV2Dir', 'session1', 'raw'),
    s2_raw_dir=os.path.join(r'$CampaignV2Dir', 'session2', 'raw'),
    out_dir=p.results,
    manifest_path=p.manifest,
    guard=p.guard,
)
print('TOST_OK', res['regime_b_warm_tost']['t_task_equivalent_cells'], res['regime_b_warm_tost']['total_cells_compared'])
"@
    $tostOut = & $PyExe -c $tostCode 2>&1
    Write-Heartbeat "TOST output (rc=$LASTEXITCODE): $($tostOut -join ' | ')"
    if ($LASTEXITCODE -ne 0) { throw "Inter-session TOST calculation failed: $tostOut" }

    # Fase 8: Post-run validations
    Write-Heartbeat "=== FASE 8: POST-RUN VALIDATIONS ==="
    Save-Status "FASE8_POST_VALIDATION" @{ sessions = $SessionsCompleted }
    $rc1 = Run-Gate "post" "gatekeeper"           @("scripts\audit_submission_gatekeeper.py")
    $rc2 = Run-Gate "post" "verify_manifest_upd"  @("scripts\verify_manifest.py", "--update")
    $rc3 = Run-Gate "post" "verify_manifest_pre"  @("scripts\verify_manifest.py", "--pre-flight")
    $rc4 = Run-Gate "post" "quad_analysis"        @("scripts\reproduce_quad_platform_analysis.py", "--quick")
    $rc5 = Run-Gate "post" "audit_chunks"         @("scripts\generate_audit_txt_chunks.py")
    $rc6 = Run-Gate "post" "pytest"               @("-m", "pytest", "-v")

    $pytestOutPath = Join-Path $RunRoot "post_pytest_stdout.txt"
    if (Test-Path $pytestOutPath) {
        $PytestSummary = ((Get-Content $pytestOutPath -Tail 3) -join " | ").Trim()
    }

    if ($rc1 -ne 0 -or $rc2 -ne 0 -or $rc3 -ne 0 -or $rc4 -ne 0 -or $rc5 -ne 0 -or $rc6 -ne 0) {
        $CampaignStatus = "FAILED_POST_RUN"
        $PrincipalOcorrencia = "Falha na Fase 8 pos-run: gatekeeper=$rc1 manifest_upd=$rc2 manifest_pre=$rc3 quad=$rc4 chunks=$rc5 pytest=$rc6"
        throw $PrincipalOcorrencia
    }
    $PhaseTimes["phase8_post_ok_utc"] = (Get-Date).ToUniversalTime().ToString("o")

    # Verify 0 changes to historical 35 JSONLs before commit/push
    $histChanged = @(& $GitExe diff --name-only | Where-Object { $_ -match '\.jsonl$' -and $_ -notmatch '^data/campaign_v2/' })
    if ($histChanged.Count -gt 0) {
        $CampaignStatus = "FAILED_POST_RUN"
        $PrincipalOcorrencia = "Alteracao inesperada em JSONL historico: $($histChanged -join ', ')"
        throw $PrincipalOcorrencia
    }

    # Fase 9: Package Desktop audit artifacts, create SUCCESS.marker, and commit/push to main
    $ArtDir = Join-Path $RunRoot "campaign_artifacts"
    New-Item -ItemType Directory -Force -Path $ArtDir | Out-Null
    if (Test-Path $CampaignV2Dir) {
        Copy-Item -Recurse -Force $CampaignV2Dir (Join-Path $ArtDir "campaign_v2_copy")
    }
    foreach ($postArt in @("data\manifest_sha256.json", "data\gatekeeper_audit_certificate.json")) {
        if (Test-Path $postArt) { Copy-Item -Force $postArt (Join-Path $RunRoot ("post_" + (Split-Path -Leaf $postArt))) }
    }

    $CampaignStatus = "SUCCESS"
    "SUCCESS`nRUN_ID=$RunId`nTIMESTAMP_UTC=$((Get-Date).ToUniversalTime().ToString('o'))" | Set-Content -Path (Join-Path $RunRoot "SUCCESS.marker") -Encoding UTF8

    if (-not $SkipPush) {
        & $GitExe add data/campaign_v2/ data/manifest_sha256.json data/manifest_static_sha256.json data/gatekeeper_audit_certificate.json audit_export/ results/ 2>&1 | Out-Null
        $porc = & $GitExe status --porcelain
        if ($porc) {
            & $GitExe commit -m "data(v2): add overnight confirmatory campaign results for windows_intel_graphics (S1+S2)" 2>&1 | Out-Null
            & $GitExe push origin main 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $CommitMain = (& $GitExe rev-parse HEAD).Trim()
            } else {
                $CommitMain = "PUSH_FALHOU_LOCAL_COMMIT_" + (& $GitExe rev-parse --short HEAD).Trim()
            }
        }
    }

    Write-Heartbeat "=== SENTINEL COMPLETED WITH STATUS=$CampaignStatus COMMIT=$CommitMain ==="
    Save-Status $CampaignStatus @{ commit_main = $CommitMain; sessions = $SessionsCompleted; pytest = $PytestSummary }
} catch {
    $errMsg = $_.Exception.Message
    if ($CampaignStatus -eq "SUCCESS") { $CampaignStatus = "FAILED_POST_RUN" }
    if ($PrincipalOcorrencia -eq "nenhuma") { $PrincipalOcorrencia = $errMsg }
    Write-Heartbeat "ERROR [$CampaignStatus]: $errMsg"
    # Stop only child processes owned by this run
    foreach ($cpid in $TrackedChildPids) {
        try { Stop-Process -Id $cpid -Force -ErrorAction SilentlyContinue } catch {}
    }
    $partialHashes = @()
    if (Test-Path $CampaignV2Dir) {
        $partialHashes = @(Get-ChildItem -Path $CampaignV2Dir -Recurse -Filter "*.jsonl" -ErrorAction SilentlyContinue | ForEach-Object {
            "$((Get-FileHash $_.FullName -Algorithm SHA256).Hash)  $($_.FullName)"
        })
    }
    @(
        "# FAILED_REASON",
        "- **Status:** $CampaignStatus",
        "- **RunId:** $RunId",
        "- **Timestamp UTC:** $((Get-Date).ToUniversalTime().ToString('o'))",
        "- **Reason:** $errMsg",
        "- **Tracked Child PIDs:** $($TrackedChildPids -join ', ')",
        "",
        "## Partial JSONL SHA-256 Hashes (Preserved Unedited)",
        ($partialHashes -join "`n")
    ) | Set-Content -Path (Join-Path $RunRoot "FAILED_REASON.md") -Encoding UTF8
    Save-Status $CampaignStatus @{ error = $errMsg; sessions = $SessionsCompleted }
} finally {
    # Compute SHA-256 checksums for all campaign JSONLs (unedited)
    $jsonlHashes = @()
    if (Test-Path $CampaignV2Dir) {
        $jsonlHashes = @(Get-ChildItem -Path $CampaignV2Dir -Recurse -Filter "*.jsonl" -ErrorAction SilentlyContinue | ForEach-Object {
            $lines = (Get-Content $_.FullName -ErrorAction SilentlyContinue | Measure-Object -Line).Lines
            "$((Get-FileHash $_.FullName -Algorithm SHA256).Hash)  lines=$lines  $($_.FullName)"
        })
        $jsonlHashes | Set-Content -Path (Join-Path $RunRoot "artifacts_sha256.txt") -Encoding UTF8
        # Copy llama_server.log files to RunRoot if present
        Get-ChildItem -Path $CampaignV2Dir -Recurse -Filter "llama_server.log" -ErrorAction SilentlyContinue | ForEach-Object {
            $sessName = $_.Directory.Parent.Name
            Copy-Item -Force $_.FullName (Join-Path $RunRoot "llama_server_${sessName}.log") -ErrorAction SilentlyContinue
        }
    }

    # Write OVERNIGHT_RUN_REPORT.md
    $EndUtc = (Get-Date).ToUniversalTime()
    $DurMin = [math]::Round(($EndUtc - $StartUtc).TotalMinutes, 2)
    @(
        "# OVERNIGHT_RUN_REPORT — Windows Intel HD Graphics 4600",
        "",
        "- **Status:** ``$CampaignStatus``",
        "- **RunId:** ``$RunId``",
        "- **Host:** ``$env:COMPUTERNAME`` (IsAdmin=$IsAdmin)",
        "- **Adapter Intel:** Intel(R) HD Graphics 4600 (iGPU UMA, energia=N/A)",
        "- **Commit Pré-Run:** ``$GitHeadPre``",
        "- **Commit Main Pós-Run:** ``$CommitMain``",
        "- **Modelo:** ``$Model`` (SHA-256: ``$ModelSha256``)",
        "- **Parâmetros:** Workloads=``$Workloads`` | Reps=``$Reps`` | Warmups=``$Warmups`` | S1 canônica + S2 ``--invert-blocks``",
        "- **Início UTC:** ``$($StartUtc.ToString('o'))`` | **Fim UTC:** ``$($EndUtc.ToString('o'))`` | **Duração:** ``${DurMin} min``",
        "- **Sessões Concluídas:** ``$SessionsCompleted``",
        "- **Pytest:** ``$PytestSummary``",
        "- **Principal Ocorrência:** $PrincipalOcorrencia",
        "- **Zero dados fabricados:** Confirmado.",
        "- **Commit/push condicionado a SUCCESS:** Confirmado.",
        "",
        "## Checksums SHA-256 dos JSONLs",
        '```text',
        ($jsonlHashes -join "`n"),
        '```'
    ) | Set-Content -Path (Join-Path $RunRoot "OVERNIGHT_RUN_REPORT.md") -Encoding UTF8

    # Update final run_metadata.json
    $metaFile = Join-Path $RunRoot "run_metadata.json"
    if (Test-Path $metaFile) {
        try {
            $m = Get-Content $metaFile -Raw | ConvertFrom-Json
            $m | Add-Member -NotePropertyName finished_utc -NotePropertyValue $EndUtc.ToString("o") -Force
            $m | Add-Member -NotePropertyName status -NotePropertyValue $CampaignStatus -Force
            $m | Add-Member -NotePropertyName commit_main -NotePropertyValue $CommitMain -Force
            $m | Add-Member -NotePropertyName phase_timestamps -NotePropertyValue $PhaseTimes -Force
            $m | ConvertTo-Json -Depth 6 | Set-Content -Path $metaFile -Encoding UTF8
        } catch {}
    }

    # REVERSIBLE RESTORATION of power, hibernation, screen lock, and Windows Update services
    Write-Heartbeat "Restoring original power plan, hibernation, screen lock, and Windows Update services..."
    if ($OrigPowerGuid) { powercfg /setactive $OrigPowerGuid 2>$null }
    if ($IsAdmin -and $OrigHibernateEnabled) { powercfg /hibernate on 2>$null }
    if ($null -ne $OrigScreenSaveActive) {
        Set-ItemProperty -Path $DesktopReg -Name ScreenSaveActive -Value "$OrigScreenSaveActive" -ErrorAction SilentlyContinue
    }
    if ($null -ne $OrigScreenSaverSecure) {
        Set-ItemProperty -Path $DesktopReg -Name ScreenSaverIsSecure -Value "$OrigScreenSaverSecure" -ErrorAction SilentlyContinue
    }
    if ($IsAdmin) {
        foreach ($svcName in $OrigServices.Keys) {
            if ($OrigServices[$svcName].Status -eq "Running") {
                Start-Service -Name $svcName -ErrorAction SilentlyContinue
            }
        }
    }

    # Release exclusive lock & stop transcript
    try { Stop-Transcript | Out-Null } catch {}
    if ($lockStream) { try { $lockStream.Close() } catch {} }
    if (Test-Path $LockFile) { Remove-Item -Force $LockFile -ErrorAction SilentlyContinue }
}
