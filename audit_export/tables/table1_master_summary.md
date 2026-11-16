# Table 1: Tri-Platform Master Systems & Microarchitectural Conformance (W2 Tool Chain)

| Architecture & Runtime | Platform OS | $T_{\text{task}}$ Median (ms) | $T_{\text{orch}}$ Median (ms) [95% CI] | $\Phi_{\text{orch}}$ (%) | Peak RSS (MB) | Net Energy (J) | EDP ($J \cdot s$) | Instructions (M) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| PicoClaw (Native Go) | macOS ARM64 (M4) | 5265.14 | 7.11 [6.70, 7.35] | 0.14% | 5.03 | 83.88 | 442.18 | 62.56M |
| PicoClaw (Native Go) | Linux x86_64 | 2725.00 | 6.66 [6.05, 7.29] | 0.24% | 9.70 | 204.61 | 555.93 | 32.65M |
| PicoClaw (Native Go) | Windows 11 x86_64 | 2746.68 | 10.94 [10.72, 11.11] | 0.40% | 10.15 | 128.17 | 351.97 | N/A* |
| OpenClaw (Node.js Minimal 15) | macOS ARM64 (M4) | 5269.28 | 21.69 [21.48, 21.78] | 0.41% | 37.62 | 84.69 | 445.75 | 789.34M |
| OpenClaw (Node.js Minimal 15) | Linux x86_64 | 2760.46 | 31.45 [31.04, 32.14] | 1.14% | 86.42 | 203.81 | 560.20 | 768.09M |
| OpenClaw (Node.js Minimal 15) | Windows 11 x86_64 | 2767.66 | 38.80 [38.51, 39.23] | 1.40% | 72.82 | 130.25 | 360.87 | N/A* |
| OpenClaw (Node.js Full 54) | macOS ARM64 (M4) | 18335.53 | 25.68 [25.38, 25.78] | 0.14% | 37.83 | 291.28 | 5342.60 | 791.35M |
| OpenClaw (Node.js Full 54) | Linux x86_64 | 7891.12 | 35.99 [35.60, 37.42] | 0.46% | 86.67 | 553.76 | 4364.61 | 771.51M |
| OpenClaw (Node.js Full 54) | Windows 11 x86_64 | 7663.76 | 45.70 [45.49, 46.20] | 0.59% | 72.82 | 461.66 | 3529.62 | N/A* |
| PythonNative (CPython VM) | macOS ARM64 (M4) | 5263.19 | 11.00 [10.76, 11.32] | 0.21% | 24.00 | 84.48 | 444.58 | 651.89M |
| PythonNative (CPython VM) | Linux x86_64 | 2747.65 | 17.13 [16.87, 18.23] | 0.62% | 40.15 | 205.49 | 567.20 | 2544.43M |
| PythonNative (CPython VM) | Windows 11 x86_64 | 2750.00 | 34.49 [28.54, 36.30] | 1.26% | N/A† | 130.79 | 361.76 | N/A* |
| Bun JSC Minimal 15 | Linux x86_64 | 2773.73 | 7.28 [7.13, 7.36] | 0.26% | 23.93 | 206.67 | 572.71 | 54.47M |
| Bun JSC Minimal 15 | Windows 11 x86_64 | 2745.86 | 15.16 [15.01, 15.67] | 0.56% | 24.62 | 131.48 | 361.91 | N/A* |
| Neural Baseline (Direct Server) | macOS ARM64 (M4) | 5261.41 | 0.00 [0.00, 0.00] | 0.00% | N/A‡ | 83.69 | 439.82 | N/A‡ |
| Neural Baseline (Direct Server) | Linux x86_64 | 2735.55 | 0.00 [0.00, 0.00] | 0.00% | N/A‡ | 204.41 | 558.57 | N/A‡ |
| Neural Baseline (Direct Server) | Windows 11 x86_64 | 2733.74 | 0.00 [0.00, 0.00] | 0.00% | N/A‡ | 126.34 | 345.64 | N/A‡ |

> **Notas Metodológicas e Referências da Tabela 1:**  
> `*` **N/A\*** (*Instruções PMU no Windows 11*): No Windows 11 em *user-mode*, contadores de instruções de hardware da PMU são restritos pelo kernel do SO sem drivers privilegiados (ETW/WPR kernel-mode tracing introduz overhead proibitivo para subprocessos isolados). A API Win32 expõe apenas ciclos acumulados via `QueryProcessCycleTime` (`realtimeapiset.h`), impedindo acesso determinístico a `IA32_FIXED_CTR0` (`INST_RETIRED.ANY`). Sob a política estrita Zero-Mock / Zero-Sintetização, qualquer extrapolação sintética de IPC é recusada, mantendo-se a telemetria empírica de ciclos (43.0M ciclos no PicoClaw vs. 507.9M ciclos no OpenClaw Full, razão de 11.82x). *Refs:* Microsoft Learn (Win32 `QueryProcessCycleTime`); Intel® 64 and IA-32 SDM Vol. 3B Ch. 20 (Performance Monitoring, bit `CR4.PCE`); Weaver, V. M. (2013), *Linux perf_event Features and Overhead*, FastPath/IEEE ISPASS.  
> `†` **N/A†** (*Peak RSS do PythonNative no Windows 11*): A invocação padrão no Windows via `py.exe` (PEP 397) opera como um processo launcher stub que despacha um processo filho `python.exe` independente. A telemetria via Win32 PSAPI (`GetProcessMemoryInfo` / `PROCESS_MEMORY_COUNTERS`) monitorou o PID do wrapper pai imediato (~4.91 MB) e não a heap do CPython worker filho (já que a agregação em árvore exige Win32 *Job Object* via `QueryInformationJobObject`). Sob conformidade Zero-Mock, reporta-se `N/A` em vez de valores truncados do stub. *Refs:* Python Enhancement Proposal PEP 397 (*Python Launcher for Windows*); Microsoft Learn (Win32 PSAPI `GetProcessMemoryInfo`).  
> `‡` **N/A‡** (*Baseline Neural Direto*): O baseline neural executa uma requisição HTTP direta do harness de teste para o endpoint do `llama-server` residente, sem intermediar nenhum framework ou runtime de agente cliente. Por definição arquitetural, a latência de orquestração é nula ($T_{\text{orch}} \equiv 0$) e não existe processo de agente cliente associado para atribuição de RSS ou instruções de middleware. *Refs:* Protocolo Experimental de Decomposição $T_{\text{task}} = T_{\text{orch}} + T_{\text{neural}}$.  
> `||` **N/A para Bun no macOS**: O Bun (JSC) foi avaliado como ablação secundária do motor JavaScript nos nós x86_64 (Linux e Windows 11) após o congelamento da campanha de referência Darwin ARM64.  
> `§` **Declaração de Execuções Limpas (*Clean-Room Runs*):** 100% dos dados consolidados foram coletados a partir de execuções ininterruptas executadas do zero (*clean from-scratch runs*), com isolamento de processos concorrentes/zumbis e políticas de bloqueio de updates/reboots automáticos de SO (zero dados parciais ou interrompidos reaproveitados).
