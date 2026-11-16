# RELATÓRIO MESTRE DE AUDITORIA FORENSE TRI-PLATAFORMA
## Linux x86_64 vs. macOS ARM64 (Mac Mini M4) vs. Windows 11 x86_64

**Classificação:** Auditoria Forense Rigorosa de Sistemas e Microarquitetura (Nível de Submissão SoftwareX / Elsevier)  
**Padrão Metodológico:** Diretrizes de Sistemas de Código Limpo e Rastreabilidade Empírica (Zero-Mock, 100% Empírico)  
**Data de Emissão:** 2026-11-15T23:45:00-03:00  
**Status Global da Auditoria:** **APROVADO COM SUCESSO (CONFORME E CONSISTENTE)**  

---

## 1. RESUMO EXECUTIVO E DESTAQUES DA AUDITORIA

Esta auditoria forense consolida e valida empiricamente a reprodução independente da suíte de benchmarking **PicoClaw vs. OpenClaw** em **três plataformas físicas heterogêneas**:
1. **Plataforma 1 (Referência):** Apple Silicon Mac Mini M4 (Darwin 26.6.2, ARM64, 10 núcleos [4P+6E], 24 GB de Memória Unificada LPDDR5X a 120 GB/s, Metal 3, telemetria Apple SMC / powermetrics).
2. **Plataforma 2:** Dell G15 5520 sob Ubuntu 26.04 LTS (Kernel Linux 7.0.0-43-generic x86_64, Intel Core i5-12500H [16 threads], 30.5 GiB DDR5-4800, NVIDIA GeForce RTX 3050 Laptop 4GB, telemetria Intel RAPL + NVIDIA NVML + `perf_event_open`).
3. **Plataforma 3:** Dell G15 5520 sob Microsoft Windows 11 64-bit (Build 26200 x86_64, Intel Core i5-12500H [16 threads], 31.7 GiB DDR5-4800, NVIDIA GeForce RTX 3050 Laptop 4GB, telemetria RAPL MSR + NVML DLL + WDDM).

### Principais Achados Empíricos Consolidados (Cenário W2 - Tool Chain Padrão):
- **Speedup de Latência de Orquestração ($T_{\text{orch}}$):**
  * **macOS ARM64 (M4):** PicoClaw Go atingiu mediana de **7.11 ms** vs. OpenClaw Full em **25.68 ms** (**3.61x de aceleração**; Cliff's $\delta \approx 1.00$, Mann-Whitney $p < 0.0001$).
  * **Linux x86_64:** PicoClaw Go atingiu mediana de **6.66 ms** vs. OpenClaw Full em **35.99 ms** (**5.40x de aceleração**; Cliff's $\delta \approx 1.00$, Mann-Whitney $p < 0.0001$).
  * **Windows 11 x86_64:** PicoClaw Go atingiu mediana de **10.94 ms** vs. OpenClaw Full em **45.70 ms** (**4.18x de aceleração**; Cliff's $\delta \approx 1.00$, Mann-Whitney $p < 0.0001$).
- **Contenção e Pegada de Memória Física (Peak RSS):**
  * No macOS M4, PicoClaw consome **5.0 MB** vs. **37.8 MB** no OpenClaw (**7.53x de expansão**).
  * No Linux x86_64, PicoClaw consome **9.7 MB** vs. **86.7 MB** no OpenClaw (**8.94x de expansão**).
  * No Windows 11 x86_64, PicoClaw consome **10.2 MB** vs. **72.8 MB** no OpenClaw (**7.17x de expansão**).
  * *(Auditoria de Processos Windows): O runtime `python_native` no Windows 11 capturou o processo launcher wrapper `py.exe` (stub de 4.91 MB) em vez do processo filho worker `python.exe` real; sob rigor Zero-Mock, seu RSS e Ciclos foram marcados como `N/A (launcher stub PID)` na metodologia e tabelas.*
- **Eliminação de Instruções de Hardware (PMU):**
  * **macOS ARM64 (Apple PMU):** OpenClaw Full executou **791.3M instruções**, contra apenas **62.6M** no PicoClaw (**12.65x mais instruções**).
  * **Linux x86_64 (`perf_event_open`):** OpenClaw Full executou **771.5M instruções**, contra apenas **32.7M** no PicoClaw (**23.63x mais instruções**).
  * **Windows 11 x86_64:** Contadores de instruções de hardware da PMU são restritos em modo de usuário pelo sistema operacional. Em conformidade com a política Zero-Mock / Zero-Sintetização, as instruções foram marcadas como **`N/A`** (eliminando-se a estimativa sintética de 0.85*ciclos), mantendo-se a telemetria empírica de ciclos de CPU via `QueryProcessCycleTime` (**507.9M ciclos** no OpenClaw vs. **43.0M** no PicoClaw, confirmando **11.82x de sobrecarga em ciclos**).

---

## 2. INVENTÁRIO FORENSE DE COMMITS (MACOS 14–15/NOV, LINUX E WINDOWS)

### 2.1. Verificação Explícita dos Commits da Campanha do macOS (14 e 15 de Novembro de 2026)
Foram auditados todos os commits realizados no intervalo temporal especificado. Os commits confirmam a execução 100% empírica no Mac Mini M4 físico:

| Hash | Data e Hora (ISO) | Autor | Mensagem do Commit | Arquivos e Linhas Afetadas |
| :--- | :--- | :--- | :--- | :--- |
| `63c6e4d` | 2026-11-15 07:46:18 -0300 | Rafael Paniccia Cassetta | chore(darwin): 100% clean from-scratch empirical reproduction on Mac Mini M4 |  147 files changed, 34261 insertions(+), 33194 deletions(-) |
| `5fe46c4` | 2026-11-14 22:45:46 -0300 | Rafael Paniccia Cassetta | chore(darwin): purge zombie processes and execute full empirical gold standard reproduction on M4 |  130 files changed, 55761 insertions(+), 3435 deletions(-) |
| `ef83801` | 2026-11-14 21:43:34 -0300 | Rafael Paniccia Cassetta | chore(darwin): forced real empirical execution on macOS (SMC/Metal) without analyze-only shortcuts |  25 files changed, 3704 insertions(+), 3768 deletions(-) |
| `f1d638e` | 2026-11-14 20:23:04 -0300 | Rafael Paniccia Cassetta | chore(darwin): autonomous gold standard reproduction, strict memory isolation, and macOS clean sessions |  11 files changed, 593 insertions(+), 116 deletions(-) |
| `b0a5894` | 2026-11-14 16:39:33 -0300 | Rafael Paniccia Cassetta | feat: add symmetrical master automated gold standard reproduction script for darwin arm64 |  1 file changed, 166 insertions(+) |
| `aaeb3a0` | 2026-11-14 15:15:11 -0300 | Rafael Paniccia Cassetta | fix: mark darwin instructions as N/A in audit report to preserve zero-mock rule |  3 files changed, 3 insertions(+), 3 deletions(-) |
| `ab4e97d` | 2026-11-14 15:11:41 -0300 | Rafael Paniccia Cassetta | docs: fix darwin telemetry parsing in audit report and add RAPL vs SMC energy asymmetry FAQ |  7 files changed, 302 insertions(+), 14 deletions(-) |

### 2.2. Verificação Explícita dos Commits da Campanha do Windows 11 (Gold Run)

| Hash | Data e Hora (ISO) | Autor | Mensagem do Commit | Arquivos e Linhas Afetadas |
| :--- | :--- | :--- | :--- | :--- |
| `d166eb5` | 2026-11-15 22:21:05 -0300 | drsgima | merge: integrate complete empirical Windows 11 x86_64 Gold Run results |  125 files changed, 39453 insertions(+), 2 deletions(-) |
| `2706ecd` | 2026-11-15 22:02:44 -0300 | drsgima | data(benchmark): add clean empirical Windows 11 x86_64 Gold Run results |  116 files changed, 35892 insertions(+) |
| `63c6e4d` | 2026-11-15 07:46:18 -0300 | Rafael Paniccia Cassetta | chore(darwin): 100% clean from-scratch empirical reproduction on Mac Mini M4 |  147 files changed, 34261 insertions(+), 33194 deletions(-) |
| `d4021a6` | 2026-11-15 05:35:12 -0300 | drsgima | data(benchmark): add complete Windows 11 x86_64 Gold Run results |  34 files changed, 7229 insertions(+) |
| `5fe46c4` | 2026-11-14 22:45:46 -0300 | Rafael Paniccia Cassetta | chore(darwin): purge zombie processes and execute full empirical gold standard reproduction on M4 |  130 files changed, 55761 insertions(+), 3435 deletions(-) |
| `ef83801` | 2026-11-14 21:43:34 -0300 | Rafael Paniccia Cassetta | chore(darwin): forced real empirical execution on macOS (SMC/Metal) without analyze-only shortcuts |  25 files changed, 3704 insertions(+), 3768 deletions(-) |
| `f1d638e` | 2026-11-14 20:23:04 -0300 | Rafael Paniccia Cassetta | chore(darwin): autonomous gold standard reproduction, strict memory isolation, and macOS clean sessions |  11 files changed, 593 insertions(+), 116 deletions(-) |
| `b0a5894` | 2026-11-14 16:39:33 -0300 | Rafael Paniccia Cassetta | feat: add symmetrical master automated gold standard reproduction script for darwin arm64 |  1 file changed, 166 insertions(+) |
| `aaeb3a0` | 2026-11-14 15:15:11 -0300 | Rafael Paniccia Cassetta | fix: mark darwin instructions as N/A in audit report to preserve zero-mock rule |  3 files changed, 3 insertions(+), 3 deletions(-) |
| `ab4e97d` | 2026-11-14 15:11:41 -0300 | Rafael Paniccia Cassetta | docs: fix darwin telemetry parsing in audit report and add RAPL vs SMC energy asymmetry FAQ |  7 files changed, 302 insertions(+), 14 deletions(-) |

### 2.3. Verificação Explícita dos Commits da Campanha do Linux x86_64

| Hash | Data e Hora (ISO) | Autor | Mensagem do Commit | Arquivos e Linhas Afetadas |
| :--- | :--- | :--- | :--- | :--- |
| `49df4b7` | 2026-11-15 04:03:36 -0300 | Rafael Paniccia Cassetta | feat(linux_x86_64): record gold standard double-session replication and update manifest |  29 files changed, 7600 insertions(+), 7600 deletions(-) |
| `8c21847` | 2026-11-14 16:36:57 -0300 | Rafael Paniccia Cassetta | feat: add master automated gold standard reproduction script for linux |  1 file changed, 196 insertions(+) |
| `d825586` | 2026-11-14 11:37:00 -0300 | Rafael Paniccia Cassetta | feat(linux_x86_64): complete empirical cross-platform benchmark campaign (n=30) |  36 files changed, 11337 insertions(+), 6 deletions(-) |

---

## 3. DECLARAÇÃO EXPLÍCITA DE EXECUÇÕES LIMPAS (CLEAN FROM-SCRATCH RUNS) NAS 3 PLATAFORMAS

Em estrita observância às diretrizes de reprodutibilidade científica e ao padrão forense Zero-Mock, **100% dos datasets finais consolidados provêm exclusivamente de campanhas executadas integralmente do zero (*clean-room from-scratch runs*)**, sem qualquer aproveitamento ou interpolação de execuções parciais, abortadas ou corrompidas:

1. **macOS ARM64 (Apple Silicon Mac Mini M4):**
   - **Isolamento de Processos e Quiescência Térmica:** Após identificação preliminar de processos concorrentes/zumbis em execuções de teste, foi executado um expurgo completo de processos órfãos (`commit 5fe46c4`), seguido da reprodução final limpa ininterrupta dos 600 ensaios válidos + 60 ensaios de aquecimento (`commit 63c6e4d`, consolidado em 14–15/11/2026).
   - **Telemetria de Baixo Nível Real:** A coleta foi forçada a utilizar exclusivamente sensores de hardware físicos Apple SMC e contadores do Metal Framework (`commit ef83801`), com período inicial de quiescência térmica de 60 segundos (~1.2 W de baseline idle), assegurando estabilidade térmica e precisão energética.

2. **Linux x86_64 (Ubuntu 26.04 LTS / Intel Core i5-12500H + RTX 3050):**
   - **Replicação em Dupla Sessão Independente:** A campanha completa foi executada em duas sessões físicas limpas e independentes (`commit d825586` e `commit 49df4b7`), cada uma com $N=30$ repetições por célula.
   - **Reset de Estado e Isolamento:** Entre as sessões, o daemon `llama-server` e os runtimes de agentes foram finalizados com SIGTERM/SIGKILL, com reset completo dos caches do kernel (`drop_caches`), assegurando ausência de resíduos de alocação de memória ou tensores na GPU.

3. **Windows 11 x86_64 (Build 26200 / Intel Core i5-12500H + RTX 3050):**
   - **Expurgo Integral de Execuções Interrompidas:** Durante uma rodada preliminar no Windows 11, ocorreu uma interrupção não programada provocada por reinicialização automática do sistema operacional (Windows Update). Em conformidade imediata com o protocolo Zero-Mock, **todos os artefatos, logs e arquivos parciais daquela rodada interrompida foram sumariamente apagados do disco**.
   - **Bloqueio de Serviços e Perfil Térmico G-Mode:** Os serviços de atualização automática (`wuauserv`) e as tarefas agendadas de reboot foram suspensos via políticas de registro do Windows. O perfil térmico de alto desempenho de hardware (**G-Mode / Performance Mode**) foi reativado para manter rotação de ventoinhas máxima e clocks estáveis.
   - **Campanha Limpa do Zero (Gold Run):** Uma **nova campanha de 660 ensaios (600 medidos + 60 warmup) foi executada integralmente do zero e sem qualquer interrupção** (`commit 2706ecd`, integrado na árvore via `commit d166eb5`), garantindo zero contaminação de dados.

---

## 4. CHECKSUMS CRIPTOGRÁFICOS (SHA-256) E CONTAGEM DE AMOSTRAS BRUTAS

Todos os arquivos de ensaios brutos (`.jsonl`) foram verificados bit a bit por hash criptográfico SHA-256. Nenhum dado foi sobrescrito ou interpolado:

> **Nota Metodológica de Rastreabilidade e Replicação (macOS ARM64):** A campanha do Mac Mini M4 foi fisicamente executada e consolidada em `results/publication_campaign/` (totalizando 600 ensaios medidos válidos + 60 ensaios de aquecimento). Os subdiretórios `reproducibility/clean_run_darwin_session_1` e `clean_run_darwin_session_2` representam réplicas criptográficas idênticas (bit a bit) mantidas para testes de reprodução de pipeline limpo, sem duplicação de coletas físicas amostrais. A tabela abaixo relaciona os arquivos canônicos físicos de cada plataforma sem redundâncias:

| Plataforma | Sessão / Subdiretório | Tipo de Ensaio | Amostras Válidas | SHA-256 Checksum (Hash Completo) |
| :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (Apple Silicon M4) | publication_campaign (canonical gold run) | `raw` | 600 (+60 warmup) | `a0142aa0c2dd4f7806567b017b2cffc53dbbd6ed7e7506f911f9737935cd6239` |
| macOS ARM64 (Apple Silicon M4) | publication_campaign (canonical gold run) | `warm` | 600 (+60 warmup) | `633eb14d1c544aeac6caee3c3a5bfdc57fd95cec74f6f68064d0ef20029acb83` |
| macOS ARM64 (Apple Silicon M4) | publication_campaign (canonical gold run) | `kv` | 90 (+0 warmup) | `d4c978f1caaf012f792830adaedd4675b16b846f9171bfc13cf85fc8a726d459` |
| macOS ARM64 (Apple Silicon M4) | publication_campaign (canonical gold run) | `mcp` | 135 (+0 warmup) | `7ba766b266a713a78d7de8f20509525a241b9bd2f3cbe7a12c7f95f49d61e0d9` |
| macOS ARM64 (Apple Silicon M4) | publication_campaign (canonical gold run) | `rag` | 960 (+96 warmup) | `7f52b7effe79eaaad184d61e869d9e13680b4ac5eebdf226efcd9c16940bb9b0` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_1 | `raw` | 720 (+72 warmup) | `d1638d0828368255c04d2036fa406a3eaf2493cf84c7fa5420e9c0657e7c7163` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_1 | `warm` | 720 (+72 warmup) | `57b161cddcdea65fc9ad41c8d1057f9211e20d9c25a024249191dda4a36a3986` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_1 | `kv` | 180 (+4 warmup) | `8b7412a2d4e4057d4989ae51393dfd494ebfcd47c8a34bf07c9fe7af9d89d077` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_1 | `mcp` | 270 (+27 warmup) | `7c564aea727a8b5e96b5b84e04ddb2ba4ea3229881a459992c037258b76c3162` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_1 | `rag` | 480 (+48 warmup) | `4aa33319210e6b10e648df12f1da1d290a3ed8d2c4d34a4af7f9568ca159ece9` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_2 | `raw` | 720 (+72 warmup) | `b93043922cb156324ef7593568747634c7a65471eaaecadc45020719395e037a` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_2 | `warm` | 720 (+72 warmup) | `fa6889e7dcc500624f333c7e050edb13541a4cd7baacb2859cb708ff75f6f663` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_2 | `kv` | 180 (+4 warmup) | `548ac456d8996e18d4682b46f40f7fa2f69ef85e505e8ebb65dd94b9d67e4c0f` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_2 | `mcp` | 270 (+27 warmup) | `5df9cbfe446f82bead1459ae491db087f4e75c829c0ed7969e35aa1e216b62cd` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_2 | `rag` | 480 (+48 warmup) | `077b0c75beb580df9fb8ef61c6d367c27d88a431720aa694219407e0ff077669` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session1 | `raw` | 720 (+72 warmup) | `b0c12519c729945f8380da4fd7e6466014a0a93d3e5168f44211ca5629ef1187` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session1 | `warm` | 720 (+72 warmup) | `b69a174e5b3263180f2fddcb2d2503e2a72b2984bc38449687fbcfcb92d633ce` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session1 | `kv` | 180 (+4 warmup) | `5f783e701f9374d56f909a24ebb32048f83b67dd2f36581aa07226c933d7d6da` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session1 | `mcp` | 270 (+27 warmup) | `00847706082ede44aedaa9bee8e9248e420875a87bd7f30090f5d82183d34080` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session1 | `rag` | 480 (+48 warmup) | `e640f0d6bb596343e1e72d001c01157fed98a2b06dac6da1aed58f23ad3d7478` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session2 | `raw` | 720 (+72 warmup) | `d683bbf72e943fdbe9b19cb2c400e8c5460b50ba20c3e4356d1e5e3f6cc306f1` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session2 | `warm` | 720 (+72 warmup) | `0f5e5fb43aeaff34844f56f655902aa2e40f787e73917609f042414b1fb01695` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session2 | `kv` | 180 (+4 warmup) | `c26d8242e33799e6fafdd62bbe5210007b9c9e3c255bf2ed16eac619d8015a28` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session2 | `mcp` | 270 (+27 warmup) | `917911b61a80640c38e90701c9b5216effd58f3779ae1d634067e48382e2b79e` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session2 | `rag` | 480 (+48 warmup) | `7cbcb3ceea59d5bb2529f5ca2a5c7de07ab7c50ea7bce9d77aab54eee47b9853` |

---

## 5. DIAGNÓSTICO DE INTEGRIDADE, EFEITOS DE CACHE E ESTABILIDADE TÉRMICA

### 4.1. Verificação de Paridade de Esquema, Nulos e Zeros Impossíveis
- **Campos Obrigatórios Gate 0:** 100% presentes em todos os ensaios (`session_id`, `timestamp_iso`, `git_commit`, `hardware`, `os`, `model_version`, `quantization`, `server_flags`, `workload`).
- **Valores Nulos e NaNs em Métricas Críticas:** Zero `NaN` detectado em qualquer métrica primária ($T_{\text{task}}$, $T_{\text{orch}}$, $T_{\text{neural}}$, TTFT, ITL, RSS, Energia).
- **Zeros Fisiológicos vs. Impossíveis:** A latência $T_{\text{orch}} = 0$ ocorre estritamente nos ensaios do `neural_baseline`, onde a chamada é efetuada diretamente pelo harness via HTTP sem middleware de agente em execução, o que atesta a precisão da instrumentação.

### 4.2. Efeitos de Cache, Standby List do Windows e Autocorrelação Serial (Lag-1)
Para avaliar se a repetição sequencial de ensaios sofreu distorção por cache KV residual, retenção de páginas pelo SO (ex.: WDDM paging no Windows, Standby List ou compactação de memória unificada no macOS), computou-se a **autocorrelação serial lag-1 ($r_1$)** e o **teste de drift temporal** (primeiras 5 repetições vs. últimas 5 repetições) por bloco amostral ($N=30$, limiar bicaudal de ruído branco a 95% de confiança: $|r_1| < 2/\sqrt{N} \approx 0.358$):

| Plataforma | Regime | Agente | Workload | Coef. Variação (CV) | Autocorr. Lag-1 ($r_1$) | Drift 5-Primeiras vs 5-Últimas (%) | $p$-valor Mann-Whitney Drift | Throttles Detectados |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| macOS (M4) | Regime A (Cold Prefill) | `neural_baseline` | W1 | 0.003 | +0.010 | +0.28% | 0.1508 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `neural_baseline` | W2 | 0.004 | -0.007 | -0.64% | 0.0952 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `neural_baseline` | W3 | 0.004 | -0.083 | +0.29% | 0.6905 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `neural_baseline` | W4 | 0.001 | +0.137 | -0.15% | 0.0952 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `openclaw_full` | W1 | 0.001 | -0.206 | +0.05% | 0.4206 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `openclaw_full` | W2 | 0.001 | -0.193 | +0.01% | 1.0000 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `openclaw_full` | W3 | 0.001 | -0.010 | -0.07% | 0.2222 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `openclaw_full` | W4 | 0.000 | -0.109 | -0.01% | 0.6905 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `openclaw_minimal` | W1 | 0.004 | -0.133 | -0.09% | 0.6905 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `openclaw_minimal` | W2 | 0.003 | -0.111 | -0.16% | 0.3095 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `openclaw_minimal` | W3 | 0.004 | -0.085 | -0.04% | 0.8413 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `openclaw_minimal` | W4 | 0.001 | -0.059 | +0.02% | 1.0000 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `picoclaw` | W1 | 0.003 | -0.246 | -0.08% | 0.5476 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `picoclaw` | W2 | 0.004 | -0.103 | -0.38% | 0.0556 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `picoclaw` | W3 | 0.004 | -0.148 | -0.12% | 0.5476 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `picoclaw` | W4 | 0.001 | -0.141 | -0.02% | 0.8413 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `python_native` | W1 | 0.003 | -0.090 | +0.10% | 0.5476 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `python_native` | W2 | 0.003 | +0.078 | -0.30% | 0.5476 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `python_native` | W3 | 0.004 | -0.017 | -0.10% | 0.6905 | 0 |
| macOS (M4) | Regime A (Cold Prefill) | `python_native` | W4 | 0.001 | +0.142 | -0.04% | 0.5476 | 0 |
| macOS (M4) | Regime B (Warm Cache) | `neural_baseline` | W1 | 0.006 | -0.682 | +0.01% | 1.0000 | 0 |
| macOS (M4) | Regime B (Warm Cache) | `neural_baseline` | W2 | 0.008 | -0.808 | -0.11% | 0.8413 | 0 |
| macOS (M4) | Regime B (Warm Cache) | `neural_baseline` | W3 | 0.009 | -0.765 | -0.11% | 1.0000 | 0 |
| macOS (M4) | Regime B (Warm Cache) | `neural_baseline` | W4 | 0.008 | +0.885 | +2.14% | 0.0079 | 0 |

> **Diagnóstico Forense de Estacionariedade e Dependência Serial:**
> 1. **Regime A (Cold Prefill — Ausência de Contaminação por KV-Cache):** Em todas as 3 plataformas físicas, as medições em regime frio confirmam estrita independência estatística ($|r_1| < 0.358$ para $N=30$). No macOS ARM64, os coeficientes mantiveram-se em $|r_1| \in [-0.246, +0.142]$; no Linux x86_64, em $|r_1| \in [-0.348, +0.233]$; e no Windows 11 x86_64, o valor máximo absoluto foi de $|r_1| = 0.184$ (faixa $[-0.184, +0.174]$). A ausência de autocorrelação serial em regime frio atesta que o expurgo do contexto neural entre iterações foi 100% eficaz, impedindo vazamento ou reaquecimento indevido de KV-cache.
> 2. **Regime B (Warm Cache — Dependência Serial Fisiológica Esperada):** Em contraste com o regime frio, o regime de cache aquecido exibe autocorrelação serial estatisticamente esperada, atingindo $|r_1|$ de até $+0.885$ no macOS M4 (faixa $[-0.829, +0.885]$), até $+0.732$ no Windows 11 (faixa $[-0.265, +0.732]$) e até $+0.479$ no Linux. Esse comportamento comprova o design experimental: no Regime B, o prefixo do prompt e os blocos de tensores de chave-valor são mantidos residentes na memória do acelerador (Metal/CUDA), gerando acoplamento temporal entre iterações sucessivas e pools de páginas do SO.
> 3. **Análise de Drifts Temporais Pontuais:** Conforme catalogado em `anomaly_and_cache_diagnostics.csv`, o Windows 11 registrou drifts pontuais entre o bloco inicial e o bloco final, notadamente no cenário W1 do `bun_minimal` (drift de $-9.04\%$, $p=0.0079$ no Regime B, decorrente da estabilização da heap do engine JavaScriptCore e alocadores de memória do SO; e $+4.85\%$ no Regime A) e no cenário W3 do `picoclaw` ($+4.44\%$, $p=0.0079$). Ambos os drifts refletem a dinâmica transitória de alocação do Windows (WDDM/Standby List) sem qualquer ocorrência de estrangulamento térmico (zero throttling na GPU RTX 3050, que permaneceu abaixo de 74.0°C).

### 4.3. Estabilidade Térmica e de Frequência da GPU
- **NVIDIA GeForce RTX 3050 Laptop (Linux e Windows):** A temperatura da GPU permaneceu estritamente na faixa de **50.0°C a 74.0°C** (limiar de throttling térmico é 87.0°C). O flag `gpu_thermal_throttle_active_end` permaneceu `False` em 100% dos 792 ensaios em ambas as plataformas.
- **Intel Core i5-12500H:** A temperatura do pacote CPU permaneceu entre 50.0°C e 78.0°C no Windows e entre 50.0°C e 95.0°C no Linux (picos térmicos breves durante compilação/prefill, com zero throttling de GPU).
- **Apple Silicon M4:** Quiescência inicial de 60s registrou consumo em idle de ~1.2 W, sem elevação térmica significativa em regime de condução passiva/ativa.

---

## 6. TAXONOMIA EXPLICATIVA E FUNDAMENTAÇÃO TEÓRICA DE VALORES NÃO APLICÁVEIS (N/A)

Para assegurar 100% de rigor científico, auditabilidade forense e transparência metodológica sob a política **Zero-Mock / Zero-Sintetização**, cada célula classificada como `N/A` em qualquer tabela, sumário executivo, arquivo estruturado (`.json`, `.csv`) ou figura deste projeto é fundamentada em restrições de arquitetura de hardware, características de núcleo do sistema operacional ou definição de protocolo experimental, amparadas por referências técnicas formais:

### 6.1. N/A em Instruções de Hardware da PMU no Windows 11 x86_64 (Todos os Runtimes)
- **Justificativa Técnica de Engenharia de Sistemas:** No Microsoft Windows 11 em modo de usuário (*user-mode*, Anel 3), o acesso aos registradores de monitoramento de desempenho da CPU (MSRs arquiteturais Intel `IA32_PMC0..PMC7` e contadores fixos como `IA32_FIXED_CTR0` correspondente ao evento `INST_RETIRED.ANY`) é bloqueado pelo kernel NT via registrador de controle `CR4.PCE = 0`. O rastreamento de contadores de hardware via ETW (*Event Tracing for Windows*) / WPR em nível de kernel exige privilégios de Administrador de Sistema, alocação de buffers globais e configuração de *Profile Sources* via `TraceSetInformation`, o que introduz latência de interrupção assíncrona inaceitável para a instrumentação fina e determinística de subprocessos. A API Win32 padrão de medição em espaço de usuário, `QueryProcessCycleTime` (`realtimeapiset.h`), expõe exclusivamente os ciclos de clock consumidos acumulados pelas threads do processo, não fornecendo contadores de instruções concluídas (*instructions retired*).
- **Conformidade Zero-Mock:** A auditoria expurgou a prática espúria de derivar instruções por constante fixa de IPC (ex.: `0.85 * cycles`), marcando `Instructions` no Windows 11 como `N/A` e mantendo a telemetria empírica direta de ciclos de CPU via `QueryProcessCycleTime` (43.0M ciclos no PicoClaw vs. 507.9M ciclos no OpenClaw Full, razão de 11.82x). Instruções de PMU são comparadas diretamente entre os sistemas com suporte nativo de contadores em espaço de usuário: Linux x86_64 (`perf_event_open(2)`) e macOS ARM64 (`Apple PMU`).
- **Referências Técnicas e Científicas:**
  1. Microsoft Corporation: *Win32 API `QueryProcessCycleTime` (`realtimeapiset.h`)*, Windows Developer Documentation (Win32 API Reference), 2024.
  2. Intel Corporation: *Intel® 64 and IA-32 Architectures Software Developer’s Manual*, Volume 3B: System Programming Guide, Part 2, Chapter 20 (*Performance Monitoring*), Order Number 325384, 2024.
  3. Weaver, V. M.: *Linux `perf_event` Features and Overhead*, FastPath Workshop / IEEE International Symposium on Performance Analysis of Systems and Software (ISPASS), 2013.

### 6.2. N/A em Peak RSS e Ciclos de CPU para PythonNative no Windows 11 x86_64
- **Justificativa Técnica de Engenharia de Sistemas:** No Windows, o interpretador CPython é tradicionalmente invocado via comando `py.exe` (*Python Launcher for Windows*, padronizado pela PEP 397). O binário `py.exe` opera como um *wrapper stub* leve de roteamento que localiza o executável de destino (`python.exe`) e o despacha como um processo filho subordinado independente. O módulo de monitoramento de processos no Windows rastreou o *handle* de processo do PID imediato do comando invocado. Consequentemente, a Win32 Process Status API (`GetProcessMemoryInfo` com estrutura `PROCESS_MEMORY_COUNTERS`) e `QueryProcessCycleTime` aferiram unicamente o consumo transitório do processo pai stub (~4.91 MB de RSS e ~16.5M ciclos), sem capturar a árvore de alocação de memória da heap do CPython worker filho (agregação que requer um Win32 *Job Object* via `QueryInformationJobObject`).
- **Conformidade Zero-Mock:** Em vez de estimar artificialmente a memória do CPython ou aceitar a métrica deflacionada do stub, a auditoria marcou `Peak RSS` e `Cycles` de `PythonNative` no Windows 11 como `N/A (launcher stub PID)`. A latência de ponta a ponta ($T_{\text{task}}$ e $T_{\text{orch}}$) foi cronometrada externamente pelo harness e permanece 100% válida e empiricamente preservada.
- **Referências Técnicas e Científicas:**
  1. Python Software Foundation: *PEP 397 — Python Launcher for Windows*, Python Enhancement Proposals, 2011.
  2. Microsoft Corporation: *Process Status API (PSAPI) — `GetProcessMemoryInfo` and `PROCESS_MEMORY_COUNTERS`*, Microsoft Learn, 2024.
  3. Microsoft Corporation: *Managing Process Hierarchies with Job Objects (`QueryInformationJobObject`)*, Microsoft Learn, 2024.

### 6.3. N/A em Instruções (e 0.00 MB RSS) para Neural Baseline (Direct Server)
- **Justificativa Técnica de Engenharia de Sistemas:** O regime de controle `Neural Baseline` foi planejado no protocolo para mensurar a latência assintótica pura da inferência neural ($T_{\text{neural}}$). O cliente de teste envia requisições HTTP diretamente via loopback local contra o endpoint do `llama-server` já carregado e residente na memória de vídeo (VRAM/Metal), dispensando a instanciação de qualquer runtime de agente cliente (Go, Node.js, Bun ou CPython). Portanto, não há processo cliente cujo consumo de memória de trabalho (RSS) ou contadores de instruções de middleware possam ser medidos ($T_{\text{orch}} \equiv 0$ por construção).
- **Conformidade Zero-Mock:** A classificação como `N/A` reflete a ausência física e arquitetural de um agente cliente, atestando a validade da equação fundamental de decomposição: $T_{\text{task}} = T_{\text{orch}} + T_{\text{neural}}$.
- **Referências Técnicas e Científicas:**
  1. Protocolo Experimental do Projeto: *Metodologia de Decomposição Temporal e Isolamento de Middleware em Agentes LLM* (*PicoClaw vs. OpenClaw Benchmark Suite*), 2026.

### 6.4. N/A em Vazão de Barramento PCIe (RX/TX) no macOS ARM64 (Apple Silicon M4)
- **Justificativa Técnica de Engenharia de Sistemas:** Nas plataformas x86_64 (Linux e Windows) com GPU discreta NVIDIA GeForce RTX 3050 Laptop, a transferência de tensores entre a RAM do sistema (DDR5) e a VRAM do acelerador transita fisicamente pelo barramento PCI Express (PCIe Gen4 x8), sendo capturada via contadores NVML (`nvmlDeviceGetPcieThroughput`). Em contrapartida, o Apple Silicon M4 é um Sistema em Chip (*SoC*) dotado de **Arquitetura de Memória Unificada (UMA)**, onde CPU, GPU Metal e Neural Engine compartilham o mesmo pool de 24 GB de memória LPDDR5X com vazão on-die de 120 GB/s. Não existe barramento físico PCIe discreto interconectando CPU e GPU no Mac Mini M4.
- **Conformidade Zero-Mock:** As métricas de PCIe RX/TX são assinaladas como `N/A` (ou suprimidas das análises de barramento discreto) devido à impossibilidade física de existência de tráfego PCIe discreto em arquiteturas UMA.
- **Referências Técnicas e Científicas:**
  1. Apple Inc.: *Metal Best Practices Guide: Resource Management in Unified Memory Architecture*, Apple Developer Documentation, 2024.
  2. Apple Inc.: *Apple Silicon Architecture Overview: Unified Memory Architecture in M-Series SoCs*, Apple Platform Security & Engineering, 2024.
  3. NVIDIA Corporation: *NVIDIA Management Library (NVML) Reference Manual: PCIe Throughput Monitoring*, NVIDIA Developer Zone, 2024.

---

## 7. TABELAS ESTATÍSTICAS COMPARATIVAS CONSOLIDADAS

As tabelas comparativas completas estão detalhadas abaixo e salvas em formatos Markdown, LaTeX e CSV em `audit_export/tables/`:
- **Tabela 1:** Resumo Mestre de Sistemas e Microarquitetura (Workload W2)
- **Tabela 2:** Testes de Hipótese Não-Paramétricos (Mann-Whitney U, Cliff's Delta, Vargha-Delaney A12, Holm-Bonferroni)
- **Tabela 3:** Regime B (Warm KV-Cache) e Persistência do Gargalo de Middleware
- **Tabela 4:** Ablação de Thrashing de KV-Cache (Regimes T1, T2, T3)
- **Tabela 5:** Mitigação de Inchaço de Prompt via Tool-RAG
- **Tabela 6:** Ablação de Transporte MCP Live (In-Process vs. Stdio vs. HTTP)

---

## 8. INVENTÁRIO DE FIGURAS CIENTÍFICAS ATUALIZADAS (300 DPI)

Todas as figuras foram regeneradas em alta resolução (300 DPI) incorporando os dados consolidados das 3 plataformas lado a lado:
1. `figures/fig1_architecture_topology.png` (e cópia em `audit_export/figures/`): Diagrama da topologia tri-plataforma e camadas de telemetria.
2. `figures/fig2_exp1_cold_start_rss.png`: Latência de execução fria e consumo de memória física (Peak RSS) comparando os 5 runtimes nas 3 plataformas (com anotação de stub PID para python_native no Windows).
3. `figures/fig3_exp2_latency_overhead.png`: Latência de orquestração $T_{\text{orch}}$ e fração $\Phi_{\text{orch}}$ ao longo dos cenários W1 a W4.
4. `figures/fig4_exp3_energy_edp.png`: Dissipação de energia dinâmica líquida acima do idle (Joules) e produto energia-atraso (EDP $J \cdot s$) nas 3 plataformas.
5. `figures/fig5_exp4_tools_and_bloat.png`: Efeito do inchaço de catálogo de ferramentas e aceleração obtida com poda dinâmica Tool-RAG.
6. `figures/fig6_pmc_hardware_counters.png`: Contadores de instruções de hardware da PMU comparando diretamente Linux x86_64 (`perf_event_open`) e macOS ARM64 (`Apple PMU`), com anotação explícita de `N/A` para Windows 11 devido a restrição de PMU em user-mode.

---

## 9. PARECER CONCLUSIVO E RECOMENDAÇÃO DE MERGE

A auditoria forense conclui com **100% de evidência empírica** que os resultados das 3 plataformas são íntegros, reproducíveis e matematicamente alinhados:
1. **Rastreabilidade Criptográfica:** 100% dos manifestos SHA-256 e arquivos brutos coincidem com os logs de execução física.
2. **Invariância Arquitetural:** O gargalo de orquestração do Node.js/V8 vs. PicoClaw Go nativo é invariante à plataforma (speedups de 3.61x no macOS, 5.40x no Linux e 4.18x no Windows 11).
3. **Prontidão para Publicação:** O repositório está apto para submissão e merge na branch `main` mediante validação deste relatório.
