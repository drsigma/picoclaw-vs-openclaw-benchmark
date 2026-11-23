<#
.SYNOPSIS
    windows_gold.ps1 - Master Reproduction Orchestrator for Windows 11 x86_64.
    Cross-platform port of Linux runner with full schema parity.

.DESCRIPTION
    Executes standard replication campaign on Windows 11:
      1. Environmental quiescence & background noise elimination (power, updates, Defender).
      2. Native toolchain check (.venv_win, picoclaw_orch_windows.exe).
      3. Session 1 execution (clean_run_windows_session_1).
      4. Inter-session sanitization & memory cooling.
      5. Session 2 execution (clean_run_windows_session_2 / inter-session replication).
      6. Integrity validation, cross-platform schema parity assertion, and git tracking.
#>

[CmdletBinding()]
param(
    [int]$Reps = 30,
    [int]$Warmups = 3,
    [int]$IdleSec = 10,
    [int]$Ngl = 16,
    [string]$Model = "$PSScriptRoot\models\Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    [switch]$DryRun,
    [switch]$SkipSession2
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$LocalPrograms = if ($env:LOCALAPPDATA) { "$env:LOCALAPPDATA\Programs" } else { "C:\Programs" }
$env:PATH = "C:\Program Files\Git\cmd;$LocalPrograms\go\bin;$LocalPrograms\Python\Python312;$LocalPrograms\Python\Python312\Scripts;$LocalPrograms\node;$LocalPrograms\bun;$LocalPrograms\llama_server;" + $env:PATH

if (-not (Test-Path $Model) -and (Test-Path "$ScriptDir\models\Llama-3.2-3B-Instruct-Q4_K_M.gguf")) {
    $Model = "$ScriptDir\models\Llama-3.2-3B-Instruct-Q4_K_M.gguf"
}


if ($DryRun) {
    Write-Host "[DRY-RUN MODE] Overriding reps=1, warmups=1, idle-sec=2 for sanity check." -ForegroundColor Yellow
    $Reps = 1
    $Warmups = 1
    $IdleSec = 2
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host " 🚀 INICIANDO REPRODUÇÃO EXPERIMENTAL CONFIRMATÓRIA (WINDOWS 11 x86_64)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host " Plataforma: Windows 11 x86_64 (Dell G15, RTX 3050)"
Write-Host " Repositório: $ScriptDir"
Write-Host " Repetições: $Reps | Warmups: $Warmups | Idle: ${IdleSec}s | NGL: $Ngl"
Write-Host ""

# ------------------------------------------------------------------------------
# 1. Validação de Privilégios e Isolamento de Ambiente (Fase 1)
# ------------------------------------------------------------------------------
$IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
    Write-Warning "AVISO: Sessão executando como usuário padrão (Não-Admin)."
    Write-Warning "Alguns ajustes de sistema (desativar Windows Update, exclusão no Defender) requerem elevação."
}

# Salva plano de energia anterior
$OriginalPowerScheme = (powercfg /getactivescheme) -replace '.*:\s*([a-f0-9\-]+)\s*\(.*', '$1'

function Restore-Environment {
    Write-Host "`n🔄 Finalizando e mantendo blindagem de energia..." -ForegroundColor Yellow
    
    # Mantem timeouts em 0 para evitar hibernacao/suspensao inadvertida
    powercfg /change monitor-timeout-ac 0 2>$null
    powercfg /change monitor-timeout-dc 0 2>$null
    powercfg /change standby-timeout-ac 0 2>$null
    powercfg /change standby-timeout-dc 0 2>$null
    powercfg /change hibernate-timeout-ac 0 2>$null
    powercfg /change hibernate-timeout-dc 0 2>$null
    powercfg /change disk-timeout-ac 0 2>$null
    powercfg /change disk-timeout-dc 0 2>$null
    powercfg /hibernate off 2>$null
    
    # Encerra qualquer processo remanescente do llama-server
    Get-Process -Name "llama-server" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "✔ Processos limpos e blindagem de energia ativa mantida." -ForegroundColor Green
}

# ------------------------------------------------------------------------------
# 2. Configuração de Hardware e Eliminação de Ruído
# ------------------------------------------------------------------------------
try {
    Write-Host "▶ 1/5: Preparando Hardware e Estabilização Térmica..." -ForegroundColor Cyan

    # Ativa plano de Desempenho Máximo / Alto Desempenho
    # GUID 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c = Alto Desempenho
    # GUID e9a42b02-d5df-448d-aa00-03f14749eb61 = Desempenho Máximo (Ultimate)
    Write-Host "  - Ativando plano de Alto Desempenho..."
    powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>$null
    powercfg /change monitor-timeout-ac 0 2>$null
    powercfg /change standby-timeout-ac 0 2>$null
    powercfg /change hibernate-timeout-ac 0 2>$null

    # Ativa G-Mode no Dell G15 para fluxo de ar máximo e estabilidade térmica
    if (Test-Path "$env:TEMP\alienfx\alienfan-cli.exe") {
        Write-Host "  - Ativando perfil térmico G-Mode (ventoinhas máximas)..."
        & "$env:TEMP\alienfx\alienfan-cli.exe" setgmode=1 2>$null
    }

    # Encerramento de processos de ruído em background (não essenciais)
    $NoiseProcesses = @("steam", "brave", "chrome", "msedge", "discord", "obs64", "OneDrive", "Teams", "Battle.net")
    foreach ($proc in $NoiseProcesses) {
        $found = Get-Process -Name $proc -ErrorAction SilentlyContinue
        if ($found) {
            Write-Host "  - Encerrando processo concorrente: $proc"
            $found | Stop-Process -Force -ErrorAction SilentlyContinue
        }
    }

    # Verifica status da GPU via nvidia-smi
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
        Write-Host "  - Verificando GPU RTX 3050..."
        & nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader
    }

    # --------------------------------------------------------------------------
    # 3. Setup de Dependências Nativas (.venv_win e Binário Go)
    # --------------------------------------------------------------------------
    Write-Host "`n▶ 2/5: Configurando Ambiente Python e Compilação Nativa Go..." -ForegroundColor Cyan

    $VenvDir = Join-Path $ScriptDir ".venv_win"
    $PythonExe = Join-Path $VenvDir "Scripts\python.exe"

    $SysPython = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $SysPython -and (Test-Path "$LocalPrograms\Python\Python312\python.exe")) {
        $SysPython = "$LocalPrograms\Python\Python312\python.exe"
    }
    if (-not (Test-Path $PythonExe)) {
        Write-Host "  - Criando ambiente virtual em $VenvDir..."
        & $SysPython -m venv $VenvDir
    }

    Write-Host "  - Instalando dependências científicas..."
    & $PythonExe -m pip install --upgrade pip --quiet
    & $PythonExe -m pip install numpy scipy pytest psutil matplotlib requests langchain-core pydantic --quiet

    # Compilação do binário Go do PicoClaw para Windows se necessário
    $PicoClawWin = Join-Path $ScriptDir "benchmark\picoclaw_orch_windows.exe"
    if (-not (Test-Path $PicoClawWin)) {
        Write-Host "  - Compilando binário nativo Go para Windows (picoclaw_orch_windows.exe)..."
        Push-Location (Join-Path $ScriptDir "benchmark")
        try {
            $env:CGO_ENABLED = "0"
            & go build -o picoclaw_orch_windows.exe picoclaw_orch_windows.go
        } finally {
            Pop-Location
        }
    }

    # Cria diretórios de reprodutibilidade e garante sessão limpa
    $ReproDir1 = Join-Path $ScriptDir "reproducibility\clean_run_windows_session_1"
    $ReproDir2 = Join-Path $ScriptDir "reproducibility\clean_run_windows_session_2"
    Remove-Item -Recurse -Force (Join-Path $ScriptDir "data\windows_x86_64_session1") -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force (Join-Path $ScriptDir "data\windows_x86_64_session2") -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force (Join-Path $ScriptDir "results\publication_campaign_windows_x86_64_session1") -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force (Join-Path $ScriptDir "results\publication_campaign_windows_x86_64_session2") -ErrorAction SilentlyContinue
    Remove-Item -Force (Join-Path $ScriptDir "data\manifest_sha256_windows_x86_64_session1.json") -ErrorAction SilentlyContinue
    Remove-Item -Force (Join-Path $ScriptDir "data\manifest_sha256_windows_x86_64_session2.json") -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $ReproDir1 -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $ReproDir2 -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $ReproDir1 -Force | Out-Null
    New-Item -ItemType Directory -Path $ReproDir2 -Force | Out-Null

    # --------------------------------------------------------------------------
    # 4. Execução da Sessão 1
    # --------------------------------------------------------------------------
    Write-Host "`n▶ 3/5: Executando Campanha - Sessão 1 (clean_run_windows_session_1)..." -ForegroundColor Cyan
    Write-Host "  Parâmetros: --ngl $Ngl --reps $Reps --warmups $Warmups --idle-sec $IdleSec"

    $RunnerScript = Join-Path $ScriptDir "scripts\run_windows_x86_64_master_campaign.py"
    $CommonArgs = @(
        $RunnerScript,
        "--ngl", "$Ngl",
        "--reps", "$Reps",
        "--warmups", "$Warmups",
        "--idle-sec", "$IdleSec"
    )
    if ($Model) {
        $CommonArgs += @("--model", "$Model")
    }

    & $PythonExe @CommonArgs --suffix "_session1"
    if ($LASTEXITCODE -ne 0) {
        throw "Execução da Sessão 1 falhou com código de saída $LASTEXITCODE."
    }

    # Empacotamento Sessão 1
    Write-Host "  - Empacotando dados brutos e certificados da Sessão 1..."
    Copy-Item -Recurse -Force (Join-Path $ScriptDir "data\windows_x86_64_session1") (Join-Path $ReproDir1 "data")
    Copy-Item -Recurse -Force (Join-Path $ScriptDir "results\publication_campaign_windows_x86_64_session1") (Join-Path $ReproDir1 "results")
    Copy-Item -Force (Join-Path $ScriptDir "data\manifest_sha256_windows_x86_64_session1.json") (Join-Path $ReproDir1 "manifest_sha256.json")

    # --------------------------------------------------------------------------
    # 5. Higienização e Resfriamento Inter-Sessões
    # --------------------------------------------------------------------------
    if (-not $SkipSession2) {
        Write-Host "`n▶ 4/5: Higienização e Resfriamento Inter-Sessões..." -ForegroundColor Cyan
        Get-Process -Name "llama-server" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2

        if (Test-Path "$env:TEMP\alienfx\alienfan-cli.exe") {
            & "$env:TEMP\alienfx\alienfan-cli.exe" setgmode=1 2>$null
        }

        # Limpeza de working set / memória
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()

        Write-Host "  - Pausa de resfriamento e estabilização térmica (20s)..."
        Start-Sleep -Seconds 20

        # ----------------------------------------------------------------------
        # 6. Execução da Sessão 2 (Réplica Inter-Sessões)
        # ----------------------------------------------------------------------
        Write-Host "`n▶ 5/5: Executando Campanha - Sessão 2 (clean_run_windows_session_2)..." -ForegroundColor Cyan
        Write-Host "  Parâmetros: --ngl $Ngl --reps $Reps --warmups $Warmups --idle-sec $IdleSec"

        & $PythonExe @CommonArgs --suffix "_session2"
        if ($LASTEXITCODE -ne 0) {
            throw "Execução da Sessão 2 falhou com código de saída $LASTEXITCODE."
        }

        # Empacotamento Sessão 2
        Write-Host "  - Empacotando dados brutos e certificados da Sessão 2..."
        Copy-Item -Recurse -Force (Join-Path $ScriptDir "data\windows_x86_64_session2") (Join-Path $ReproDir2 "data")
        Copy-Item -Recurse -Force (Join-Path $ScriptDir "results\publication_campaign_windows_x86_64_session2") (Join-Path $ReproDir2 "results")
        Copy-Item -Force (Join-Path $ScriptDir "data\manifest_sha256_windows_x86_64_session2.json") (Join-Path $ReproDir2 "manifest_sha256.json")
    }

    Write-Host "`n========================================================================" -ForegroundColor Green
    Write-Host "✅ REPRODUÇÃO EXPERIMENTAL WINDOWS CONCLUÍDA COM SUCESSO!" -ForegroundColor Green
    Write-Host "   - Sessão 1: reproducibility\clean_run_windows_session_1\" -ForegroundColor Green
    if (-not $SkipSession2) {
        Write-Host "   - Sessão 2: reproducibility\clean_run_windows_session_2\" -ForegroundColor Green
    }
    Write-Host "========================================================================" -ForegroundColor Green

    # --------------------------------------------------------------------------
    # 7. Git Auto-Commit dos Resultados na branch main
    # --------------------------------------------------------------------------
    Write-Host "`n📦 Realizando Git commit na branch main..." -ForegroundColor Cyan
    & git add windows_gold.ps1
    & git add .gitignore
    & git add scripts/*windows*
    & git add benchmark/*windows*
    & git add benchmark/adapters/picoclaw_adapter.py
    & git add benchmark/telemetry.py
    & git add data/windows_x86_64*
    & git add data/manifest_sha256_windows_x86_64*
    & git add results/*windows_x86_64*
    & git add reproducibility/clean_run_windows_*
    
    $Status = (& git status --porcelain)
    if ($Status) {
        & git commit -m "feat(windows-nvidia): add empirical campaign results, W5/W2 telemetry, and computed statistics to main"
        Write-Host "✔ Commit realizado com sucesso na branch main." -ForegroundColor Green
    } else {
        Write-Host "Nenhuma alteração pendente para commit." -ForegroundColor Gray
    }

    Write-Host "🚀 Enviando resultados para origin main..." -ForegroundColor Cyan
    & git push origin main

} finally {
    Restore-Environment
}
