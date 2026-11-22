<p align="center">
  <img src="figures/benchmark_logo.png" alt="PicoClaw vs. OpenClaw Benchmark Suite Logo" width="850"/>
</p>

# A Reproducible Quad-Platform Benchmark Suite for Isolating Orchestration Overhead, Schema Prefill Scaling, and Microarchitectural Dynamics in Local LLM Agents (macOS, Linux, Windows NVIDIA, Windows Intel iGPU)

<p align="center">
  <a href="https://github.com/drsigma/picoclaw-vs-openclaw-benchmark/actions"><img src="https://github.com/drsigma/picoclaw-vs-openclaw-benchmark/actions/workflows/ci.yml/badge.svg" alt="CI"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Code%20License-MIT-yellow.svg" alt="Code License: MIT"/></a>
  <a href="DATA_LICENSE"><img src="https://img.shields.io/badge/Data%20License-CC%20BY%204.0-lightgrey.svg" alt="Data License: CC BY 4.0"/></a>
  <a href="https://github.com/drsigma/picoclaw-vs-openclaw-benchmark"><img src="https://img.shields.io/badge/Hardware-M4%20%7C%20Linux%20x86__64%20%7C%20Win11%20NVIDIA%20%7C%20Intel%20iGPU-purple.svg" alt="Hardware: Quad-Platform"/></a>
  <a href="#"><img src="https://img.shields.io/badge/Docs-Bilingual%20(PT--BR%20%7C%20EN--US)-blue.svg" alt="Documentation: Bilingual"/></a>
  <a href="CITATION.cff"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.14187265-blue.svg" alt="DOI"/></a>
</p>

**Author / Autor:** Rafael Paniccia Cassetta  
**Affiliation / Afiliação:** Universidade Federal do ABC (UFABC), Santo André, SP, Brazil  
**Repository / Repositório:** [https://github.com/drsigma/picoclaw-vs-openclaw-benchmark](https://github.com/drsigma/picoclaw-vs-openclaw-benchmark)  

---

## 📌 Resumo Executivo / Executive Summary

### 🇧🇷 Português (PT-BR)
Este repositório apresenta um framework experimental reprodutível e uma avaliação comparativa rigorosa entre arquiteturas paradigmáticas de orquestração de agentes autônomos de Inteligência Artificial avaliadas em **quatro plataformas físicas de computação**: **macOS ARM64 (Apple M4)**, **Linux x86_64 (Ubuntu 26.04 LTS)**, **Windows 11 x86_64 (NVIDIA dGPU)** e **Windows 10/11 x86_64 (Intel HD Graphics 4600 iGPU UMA)**:
1. **PicoClaw v0.3.1 (Sipeed):** Binário nativo compilado em Go 1.23.2, com concorrência leve baseada em *goroutines* (~2 KB por pilha) e coletor de lixo não-geracional tri-color com pausas sub-milissegundo.
2. **OpenClaw v2026.10.7:** Orquestrador corporativo modular em TypeScript/Node.js v26.12.1 executando sobre a Google V8 (compilação JIT multinível), com validação de esquemas via TypeBox e persistência nativa `node:sqlite`.
3. **Runtimes Isomórficos Secundários:** CPython 3.12/3.14 (referência dinâmica) e Bun v1.4.4 (JavaScriptCore AOT micro-VM).

Ambos os agentes comunicam-se via loopback TCP (`127.0.0.1:8080`) com uma instância neural local servida por **llama.cpp** hospedando o modelo **Meta Llama-3.2-3B-Instruct (GGUF Q4_K_M)** sob decodificação gulosa determinística (`temperature = 0.0`, `seed = 42`). Principais resultados medidos:
* **Speedups de Orquestração ($T_{\text{orch}}$) no Workload W2:** PicoClaw atinge **$4{,}44\times$ no macOS M4**, **$5{,}31\times$ no Linux x86_64**, **$3{,}70\times$ no Windows 11 NVIDIA** e **$4{,}91\times$ no Windows Intel iGPU** em relação ao OpenClaw Full.
* **Redução de Instruções de Hardware (PMU) e Ciclos de CPU:** Redução de **$12{,}71\times$ no macOS ARM64** (Apple PMU) e **$23{,}87\times$ no Linux x86_64** (`perf_event_open`). No Windows, contadores de instruções de PMU em *user-mode* são restritos pelo kernel (`CR4.PCE`), mantendo-se a telemetria empírica direta de ciclos de CPU via `QueryProcessCycleTime` (**$45{,}8\text{M}$ ciclos no PicoClaw vs. $528{,}1\text{M}$ no OpenClaw Full, razão de $11{,}54\times$** no Windows 11 NVIDIA; **$87{,}8\text{M}$ vs. $1{,}446{,}1\text{M}$, razão de $16{,}47\times$** no Windows Intel iGPU).
* **Mitigação Tool-RAG:** Poda dinâmica de esquemas ($54 \rightarrow \text{Top-}5$, $-87{,}1\%$ tokens de prompt) gerando speedups de cold prefill de **$7{,}28\times$ no macOS M4**, **$5{,}16\times$ no Linux x86_64**, **$4{,}64\times$ no Windows NVIDIA** e **$9{,}96\times$ no Windows Intel Graphics**.
* **Telemetria de Potência e Energia:** Apple SMC Shunts no macOS, Intel RAPL + NVIDIA NVML no Linux e Windows 11. Na iGPU Intel, energia de pacote é identificada como `N/A**` por limitações de modo usuário (sem acesso ring-0 MSR/NVML).
* **Estatística Não-Paramétrica:** Intervalos de confiança Bootstrap e Moving Block Bootstrap ($b=3$) de 95% sobre a mediana, testes Mann-Whitney U com correção de Holm-Bonferroni, Kruskal-Wallis, testes de equivalência TOST, Cliff's Delta $d$ e $\hat{A}_{12}$ de Vargha-Delaney.

### 🇺🇸 English (EN-US)
This repository delivers an open-source, reproducible experimental benchmark framework comparing autonomous AI agent orchestration architectures evaluated across **four physical computing platforms**: **macOS ARM64 (Apple M4)**, **Linux x86_64 (Ubuntu 26.04 LTS)**, **Windows 11 x86_64 (NVIDIA dGPU)**, and **Windows 10/11 x86_64 (Intel HD Graphics 4600 iGPU UMA)**:
1. **PicoClaw v0.3.1 (Sipeed):** Statically compiled Go 1.23.2 binary leveraging concurrent goroutines (~2 KB starting stack) and non-generational tri-color mark-sweep garbage collection with sub-millisecond pauses.
2. **OpenClaw v2026.10.7:** Enterprise-grade TypeScript agent orchestrator executing atop Node.js v26.12.1 (Google V8 tiered JIT), dynamic TypeBox schema validation, and native `node:sqlite` session state storage.
3. **Secondary Isomorphic Runtimes:** CPython 3.12/3.14 (dynamic reference) and Bun v1.4.4 (JavaScriptCore AOT micro-VM).

All orchestrators interface via local loopback (`127.0.0.1:8080`) with a unified neural server powered by **llama.cpp** serving **Meta Llama-3.2-3B-Instruct (Q4_K_M)** under greedy deterministic decoding (`temperature = 0.0`, `seed = 42`). Key measured findings:
* **Orchestration Speedups ($T_{\text{orch}}$) on W2:** PicoClaw achieves **$4.44\times$ on macOS M4**, **$5.31\times$ on Linux x86_64**, **$3.70\times$ on Windows 11 NVIDIA**, and **$4.91\times$ on Windows Intel Graphics** over OpenClaw Full.
* **Hardware Instruction Reduction (PMU) & CPU Cycles:** **$12.71\times$ on macOS ARM64** (Apple PMU) and **$23.87\times$ on Linux x86_64** (`perf_event_open`). On Windows, user-mode PMU instruction counters are restricted by kernel policy (`CR4.PCE`); empirical CPU cycles tracked via `QueryProcessCycleTime` measure **$45.8\text{M}$ cycles in PicoClaw vs. $528.1\text{M}$ in OpenClaw Full ($11.54\times$ ratio)** on Windows 11 NVIDIA, and **$87.8\text{M}$ vs. $1{,}446.1\text{M}$ ($16.47\times$ ratio)** on Windows Intel iGPU.
* **Tool-RAG Mitigation:** Dynamic schema pruning ($54 \rightarrow \text{Top-}5$, $-87.1\%$ prompt tokens) yields cold-prefill speedups of **$7.28\times$ on macOS M4**, **$5.16\times$ on Linux x86_64**, **$4.64\times$ on Windows NVIDIA**, and **$9.96\times$ on Windows Intel Graphics**.
* **Power & Energy Telemetry:** Apple SMC Shunts on macOS, Intel RAPL + NVIDIA NVML on Linux and Windows 11. Uninstrumented user-mode package energy on Intel iGPU is explicitly reported as `N/A**`.
* **Non-Parametric Statistics:** 95% Bootstrap and Moving Block Bootstrap ($b=3$) confidence intervals on sample medians, Mann-Whitney U tests with step-down Holm-Bonferroni adjustment, Kruskal-Wallis omnibus tests, TOST equivalence testing, Cliff's Delta $d$, and Vargha-Delaney $\hat{A}_{12}$.

---

### ⚖️ Aviso de Escopo e Marcas Registradas / Trademark & Scope Disclaimer
* **🇧🇷 PT-BR:** Este benchmark avalia implementações de referência isomórficas *clean-room* em Go (`picoclaw_orch.go`), Node.js/TypeScript (`openclaw_orch.mjs`) e Python (`python_orch.py`), projetadas para mensurar o impacto microarquitetural e de runtime (compilado nativo vs. JIT/interpretado) sob esquemas e prompts idênticos. PicoClaw e OpenClaw são marcas de seus respectivos criadores; este projeto é um benchmark acadêmico independente não afiliado ou endossado pelos mantenedores originais.
* **🇺🇸 EN-US:** This benchmark evaluates clean-room, isomorphic reference implementations in Go (`picoclaw_orch.go`), Node.js/TypeScript (`openclaw_orch.mjs`), and Python (`python_orch.py`) designed to isolate systems runtime overhead (native compiled vs. JIT/interpreted) under strictly identical prompts and tool schemas. PicoClaw and OpenClaw are trademarks of their respective owners; this software is an independent academic performance benchmark not affiliated with or endorsed by upstream project maintainers.

> [!WARNING]
> **Provenance Notice / Aviso de Proveniência:** All consolidated findings, statistical tables, and 300 DPI figures derive strictly from physical, hardware-instrumented trials across 35 validated raw `.jsonl` datasets spanning all 4 platforms (`results/publication_campaign/`, `data/linux_x86_64_session{1,2}/raw/`, `data/windows_x86_64_session{1,2}/raw/`, `data/windows_intel_graphics_session{1,2}/raw/`). Legacy exploratory files in `results/exploratory_campaigns/` (including early calibration runs, synthetic checks in `poisson_results.json`, and exploratory figures `fig7`/`fig8`) represent historical engineering milestones prior to protocol standardization and are excluded from consolidated tables and canonical manifests.

---

## ❓ Pergunta de Pesquisa / Research Question

### 🇧🇷 Português (PT-BR)
> **"Qual arquitetura de orquestrador de IA — Go nativo (PicoClaw) ou Node.js (OpenClaw) — entrega menor latência, menor consumo de memória RAM e maior eficiência energética no Apple Silicon M4 sob o mesmo modelo neural local?"**

### 🇺🇸 English (EN-US)
> **"Which AI agent architecture — native Go (PicoClaw) or Node.js (OpenClaw) — delivers lower latency, minimal RAM footprint, and higher energy efficiency on Apple Silicon M4 under an identical local neural model?"**

---

## 🏛️ Arquitetura Experimental do Testbed / Experimental Architecture

```mermaid
flowchart TD
    subgraph WG["Deterministic Workload Generator"]
        W1["W1: Simple Reflection (Pure In-Memory)"]
        W2["W2: 3-Step Tool Chain (APFS Disk I/O)"]
        W3["W3: Vector RAG (384d Cosine Similarity)"]
        W4["W4: 10-Turn Autonomous ReAct Loop"]
    end

    subgraph ADAPTER["Agent Adapter Interface Layer (Strategy Pattern)"]
        PC["PicoClaw Go Native Mach-O"]
        OC_MIN["OpenClaw Minimal (Node.js V8, 15 Tools)"]
        OC_FULL["OpenClaw Full (Node.js V8, 54 Tools and SQLite)"]
        NB["Neural Baseline (Direct HTTP Pass-Through)"]
    end

    subgraph LLM["Local Neural Server (Apple Silicon M4)"]
        SERVER["llama.cpp b11887 Metal GPU (Llama-3.2-3B-Instruct Q4_K_M, temp=0.0, seed=42)"]
    end

    subgraph TELEM["Asynchronous Telemetry Suite (Parallel)"]
        SMC["Apple SMC powermetrics (50ms Shunt Sampling: mW)"]
        LIBPROC["Darwin XNU libproc (ri_instructions, cycles, max_rss)"]
        HYPER["Hyperfine (30-run Cold-Start Timing)"]
        CAFF["caffeinate -dims (System Quiescence & Anti-Sleep)"]
    end

    WG --> ADAPTER
    ADAPTER -->|"Loopback TCP 127.0.0.1:8080"| SERVER
    TELEM -.->|"Non-Intrusive Hardware Telemetry"| ADAPTER
```

<p align="center">
  <img src="figures/fig1_architecture_topology.png" alt="Hardware Telemetry Topology and Pipeline" width="850"/>
</p>

### Explicação do Fluxo / Architecture Description:
* **🇧🇷 PT-BR:** O gerador de carga submete os 4 níveis de dificuldade padronizados (W1–W4) através da camada de adaptação (*Adapter Pattern*). Os agentes executam suas ferramentas e se comunicam exclusivamente via loopback TCP local com o servidor `llama.cpp` na GPU Metal, eliminando latências de rede externa. Paralelamente, daemons independentes de telemetria coletam miliwatts do SoC M4 via SMC e contadores de ciclo do kernel Darwin via `libproc`.
* **🇺🇸 EN-US:** The workload generator dispatches standardized tasks (W1–W4) through an extensible Adapter layer. Agent orchestrators execute file/vector tools and communicate via localhost loopback TCP with `llama.cpp` running on the Metal GPU, strictly isolating runtime overhead from network jitter. Concurrently, asynchronous telemetry daemons sample SMC electrical power and Darwin XNU performance counters.

---

## 📊 Matriz de Resultados e Estudo de Ablação / Results & Ablation Matrix

Os resultados empíricos consolidados da matriz de avaliação (5 configurações x 4 workloads, cobrindo mediana e dispersão robusta) estão sumarizados abaixo:

| Workload | Configuração / Configuration | Mediana Latência Total / Median Task Latency (ms) | Overhead Agente / Orch Delay $T_{\text{orch}}$ (ms) | Pico RAM / Peak RSS (MB) | Energia Líquida Média / Mean Net Energy (J) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **W1 (Reflexão / Simple Reflection)** | **NeuralBaseline (Direct)** | $5489{,}6$ | $0{,}000$ | $0{,}0^*$ | $88{,}11$ |
| | **PicoClaw (Go Native)** | $5497{,}0$ | $29{,}728$ | **$11{,}2$** | $88{,}97$ |
| | **OpenClaw Minimal (15 Tools)** | $5847{,}5$ | $51{,}283$ | $85{,}6$ | $94{,}06$ |
| | **OpenClaw Full 54-Tool (Ablation)** | $20674{,}1$ | $66{,}441$ | $85{,}6$ | $329{,}50$ |
| | **PythonNative (CPython Reference)** | $5485{,}6$ | $10{,}415$ | $38{,}2$ | $89{,}44$ |
| **W2 (3 Ferramentas / 3-Tool Chain)** | **NeuralBaseline (Direct)** | $5600{,}7$ | $0{,}000$ | $0{,}0^*$ | $84{,}85$ |
| | **PicoClaw (Go Native)** | $5556{,}1$ | $5{,}579$ | **$12{,}2$** | $84{,}81$ |
| | **OpenClaw Minimal (15 Tools)** | $5557{,}1$ | $20{,}952$ | $85{,}8$ | $85{,}04$ |
| | **OpenClaw Full 54-Tool (Ablation)** | $19733{,}7$ | $24{,}884$ | $86{,}0$ | $308{,}56$ |
| | **PythonNative (CPython Reference)** | $5609{,}9$ | $11{,}229$ | $38{,}2$ | $86{,}29$ |
| **W3 (Busca Vetorial / Vector RAG)** | **NeuralBaseline (Direct)** | $5752{,}9$ | $0{,}000$ | $0{,}0^*$ | $94{,}07$ |
| | **PicoClaw (Go Native)** | $5816{,}9$ | $46{,}107$ | **$52{,}5$** | $94{,}13$ |
| | **OpenClaw Minimal (15 Tools)** | $6343{,}5$ | $67{,}617$ | $114{,}3$ | $102{,}91$ |
| | **OpenClaw Full 54-Tool (Ablation)** | $20786{,}4$ | $88{,}954$ | $112{,}7$ | $333{,}52$ |
| | **PythonNative (CPython Reference)** | $5801{,}5$ | $21{,}646$ | $69{,}7$ | $94{,}83$ |
| **W4 (Loop ReAct / 10-Turn ReAct)** | **NeuralBaseline (Direct)** | $55924{,}9$ | $0{,}000$ | $0{,}0^*$ | $883{,}24$ |
| | **PicoClaw (Go Native)** | $55354{,}8$ | $66{,}028$ | **$16{,}6$** | $876{,}64$ |
| | **OpenClaw Minimal (15 Tools)** | $58201{,}2$ | $143{,}357$ | $89{,}7$ | $919{,}40$ |
| | **OpenClaw Full 54-Tool (Ablation)** | $201797{,}0$ | $199{,}328$ | $89{,}4$ | $3219{,}72$ |
| | **PythonNative (CPython Reference)** | $55934{,}8$ | $64{,}718$ | $38{,}3$ | $886{,}19$ |

$^*$*Nota sobre o Baseline Neural / Note on Neural Baseline:* O valor de **`0,0 MB` de Pico RAM RSS** no *Neural Baseline* refere-se estritamente à pegada de memória do processo orquestrador (inexistente na invocação HTTP direta via socket), excluindo o consumo de memória unificada (UMA) residente do daemon `llama-server` na GPU Metal. / The **`0.0 MB` Peak RAM RSS** for *Neural Baseline* refers strictly to the orchestrator process memory footprint (non-existent in direct HTTP socket calls), excluding the unified memory (UMA) footprint of the background `llama-server` Metal GPU daemon.

> [!NOTE]
> **🇧🇷 Telemetria Elétrica e Modo de Execução:** A tabela acima reflete os resultados automatizados da matriz de avaliação gerada pelo pipeline (`results/publication_campaign/tables/metrics_summary.csv`). Em modo de usuário comum ou CI portátil (`make dry-run`), as métricas elétricas são reportadas como `N/A` em conformidade com o princípio de zero dados sintéticos; na campanha com telemetria via Apple SMC (`make benchmark-full-smc` com sudo), a integração trapezoidal dos sensores de silício afere Joules e EDP com amostragem a cada 50 ms.
>
> **🇺🇸 Electrical Telemetry and Execution Modes:** The table above reflects the automated evaluation matrix generated by the pipeline (`results/publication_campaign/tables/metrics_summary.csv`). In unprivileged or portable CI mode (`make dry-run`), electrical metrics are reported as `N/A` adhering to the strict zero synthetic data principle; during full physical campaigns with Apple SMC telemetry (`make benchmark-full-smc` with sudo), continuous trapezoidal integration of silicon shunt sensors measures true Joules and EDP sampled every 50 ms.

### 🎯 Principais Conclusões de Engenharia / Key Findings:

* **🇧🇷 PT-BR:**
  1. **Cold-Start Launch:** No par equivalente de checagem de versão (`hyperfine_cold_start.json`), o PicoClaw inicializa em **$9{,}74\text{ ms}$** de média vs. $37{,}15\text{ ms}$ do OpenClaw (**$3{,}81\times$ mais rápido na média**; mediana **$3{,}46\times$**, $9{,}67\text{ ms}$ vs. $33{,}48\text{ ms}$). Nos workers isomórficos com `--version` explícito (`hyperfine_worker_version.json`), o binário Go inicia em **$3{,}04\text{ ms}$** vs. **$22{,}15\text{ ms}$** no Node.js V8 (**$7{,}29\times$ mais rápido**) e **$49{,}32\text{ ms}$** no Python (**$16{,}22\times$ mais rápido**).
  2. **Eficiência de Memória RAM e Silício (`Peak Physical Footprint`):** O PicoClaw aloca de **$4{,}2\text{ a }45{,}5\text{ MB}$** de pegada física de memória (`proc_peak_phys_mb`, `ri_lifetime_max_phys_footprint`, média global $16{,}05\text{ MB}$, subindo para $45{,}5\text{ MB}$ apenas na busca vetorial W3), enquanto o OpenClaw aloca de **$37{,}5\text{ a }67{,}1\text{ MB}$** (média global $45{,}32\text{ MB}$), reduzindo em **$1{,}45\times\text{ a }8{,}97\times$** o consumo físico de memória DRAM (**$2{,}82\times$ menor na média global**).
  3. **Eficiência de Instruções e Ciclos:** Medições via `libproc` comprovam que o PicoClaw executa $243{,}8\times 10^6$ instruções e $84{,}0\times 10^6$ ciclos, contra $937{,}1\times 10^6$ instruções ($3{,}84\times$ mais) e $396{,}3\times 10^6$ ciclos ($4{,}72\times$ mais) no OpenClaw Minimal.
  4. **Escalabilidade em Loops Longos (W4) e Eficiência em EDP (Dualidade de Regimes):** No ciclo autônomo ReAct de 10 passos sob Regime A (Cold Prefill), o PicoClaw completou a tarefa com $55354{,}8\text{ ms}$ de mediana e $\text{EDP} = 48543{,}57\text{ J}\cdot\text{s}$, alcançando **$92{,}53\%$ menor Energy-Delay Product** e significância estatística robusta frente ao OpenClaw Full ($d = -1{,}0$, $\hat{A}_{12} = 0{,}0$, $p < 10^{-5}$) ao evitar o inchaço de catálogo de 54 ferramentas. Já sob o Regime B (Warm KV-Cache Reuse, sessão unificada), com prefill amortizado, os runtimes equalizados convergem em eficiência mantendo **$>35\%$ menor EDP** frente ao OpenClaw Full.
  5. **Estudo de Ablação (Prompt Bloat) e Módulo Ativo Zero-Copy Tool-RAG Pruner:** A injeção estática de 54 ferramentas corporativas no OpenClaw Full eleva o tempo médio de W1 de $5852{,}6\text{ ms}$ para $20682{,}7\text{ ms}$ e a energia líquida de $94{,}06\text{ J}$ para $329{,}50\text{ J}$ ($3{,}50\times$). O módulo ativo **Zero-Copy Dynamic Tool-RAG Schema Pruner** ($54 \rightarrow \text{Top-}5$ ferramentas via produto interno vetorial em 384D em $< 0{,}35\text{ ms}$) reduz os tokens de prompt de $7.067$ para $893$, eliminando **$>85\%$ da latência e energia** no Regime A e superando até o catálogo estático de 15 ferramentas no Regime B.
  6. **Dinâmica de Execução e Eficiência em W2:** No Workload W2 (3-Tool Chain), sob decodificação gulosa com esquemas de ferramentas harmonizados, tanto PicoClaw quanto OpenClaw Minimal emitem $29{,}0$ tokens de resposta com latências totais equivalentes ($5556{,}1\text{ ms}$ vs. $5557{,}1\text{ ms}$) e consumo energético líquido comparável ($84{,}81\text{ J}$ vs. $85{,}04\text{ J}$, $2{,}92\text{ J/token}$ vs. $2{,}93\text{ J/token}$). O isolamento microarquitetural comprova a eficiência do runtime Go: overhead de orquestração $T_{\text{orch}}$ mediano de apenas **$5{,}58\text{ ms}$** no PicoClaw contra **$20{,}95\text{ ms}$** no OpenClaw Minimal (**$3{,}76\times$ menor atraso de despacho**), além de **$4{,}73\text{ MB}$** de `Peak Physical Footprint` (`proc_peak_phys_mb`) contra **$39{,}67\text{ MB}$** (**$8{,}39\times$ menor alocação física de DRAM em W2**).
  7. **Caracterização de Prefill de Catálogo e Reuso de KV-Cache:** Conforme atestado no estudo de caracterização de 8 catálogos ($0, 5, 10, 15, 25, 40, 54, 100$ ferramentas no llama.cpp / Metal GPU), o inchaço de esquemas corporativos expande o pré-processamento de atenção na GPU Metal ($T_{\text{prefill}}$ cresce de $128{,}1\text{ ms}$ para $4434{,}4\text{ ms}$, $17877{,}3\text{ ms}$ e $39190{,}5\text{ ms}$), exibindo escalabilidade potencial ($T = 0{,}3197 \cdot N^{1{,}2342}$, $R^2 = 0{,}9993$, $\text{AIC}_c = 99{,}25$) e quadrática ($R^2 = 0{,}99999$) compatível com a complexidade de atenção do transformer, enquanto o reuso do KV-cache elimina essa sobrecarga redundante ($5{,}5\times\text{ a }946{,}5\times$ speedup de prefill), confirmando que o gargalo de catálogos volumosos reside na atenção neural e não no despacho do orquestrador.
  8. **Dualidade de Regimes Operacionais e Réplica Inter-Sessão ($n=30$) com Bun Nativo:** O repositório avalia dois regimes completos ($n=30$ cada, 660 ensaios por campanha) e uma réplica independente inter-sessão ($n=30$ por bloco, incluindo o runtime **Bun v1.4.4 / JavaScriptCore**):
     * *Regime A (`cache_prompt=false`):* O prefill frio na GPU Metal domina $>75\%$ do tempo total de execução e satura a potência do encapsulamento em $\approx 16\text{ W}$, provocando quase-paridade ponta a ponta entre os runtimes.
     * *Regime B (`cache_prompt=true`):* Com o prefill amortizado pelo reuso do KV-cache no `llama-server` (protocolo isolado por bloco determinando taxa verificada de `Cache Hit` de **$99{,}9\%$ a $100{,}0\%$** em W1–W3 e **$97{,}6\%$ a $99{,}3\%$** em W4), a latência global despenca para patamares sub-segundo em W2 (redução de **$>20\times$** no catálogo de 54 ferramentas). Sob esse amortecimento de prefill, a parcela relativa de sobrecarga de orquestração ($\Phi_{\text{orch}} = T_{\text{orch}} / T_{\text{task}}$) situa-se entre **$0{,}37\%$ e $4{,}65\%$**, permanecendo a latência ponta a ponta de Go, Python, Node-Minimal e Bun dentro de $-1{,}5\%$ a $+5{,}8\%$ do baseline neural direto (menor que a deriva térmica inter-sessão de $\sim 3\%\text{--}10\%$ em W1, W2 e W4, enquanto no W3 a busca vetorial BLAS/SIMD supera o loop escalar do Go em $5{,}6\%\text{--}5{,}8\%$ entre sessões).
  9. **Deconvolução de Energia por Processo (Resultado Negativo Validado do XNU) e Estimativa Analítico-Empírica de Largura de Banda UMA LPDDR5X:** Medições físicas diretas no trilho `CPU Power` do Apple SMC com GPU ociosa isolam o custo marginal de despacho ($1{,}252\text{ mJ/op}$ no Go, $1{,}000\text{ mJ/op}$ no Python, $0{,}196\text{ mJ/op}$ no Node Minimal em W2). A validação cruzada estabelece um **Resultado Negativo Formal para `ri_billed_energy`** do kernel Darwin XNU ($r = -0{,}0510, p = 0{,}580, \text{OLS } R^2 = -0{,}676$ contra a média, corroborando Fahad et al., 2019), enquanto valida como regressores físicos reais de energia da CPU o tempo de execução (`t_exec_ms`, $R^2 = 0{,}949$), instruções aposentadas (`proc_instructions`, $R^2 = 0{,}955$) e ciclos (`proc_cycles`, $R^2 = 0{,}945$). Usando diretamente a energia do trilho `CPU Power` do SMC, a fração de energia de orquestração no Regime B ($\Phi_{\text{energy, orch}}$) em W2/W3 é de apenas **$0{,}04\% / 1{,}42\%$** no Go, **$0{,}03\% / 0{,}34\%$** no Python, **$0{,}01\% / 0{,}49\%$** no Node Minimal e **$0{,}01\% / 0{,}30\%$** no Node Full. Na decodificação neural na GPU Metal, a **Estimativa Analítico-Empírica de Largura de Banda de Memória ($\text{Model Weights} \div \text{ITL}$)** registra **mediana global de $97{,}0\text{ GB/s}$ ($80{,}8\%$ de $120\text{ GB/s}$) e média de $95{,}9\text{ GB/s}$ ($79{,}9\%$ no Regime A) a $106{,}7\text{ GB/s}$ ($88{,}9\%$ no Regime B; média global $104{,}0\text{ GB/s}$ / $86{,}7\%$)**, consistente com o teto prático de Roofline em UMA ($\approx 86\text{--}88\%$, Imamura, 2026; Benazir & Lin, 2025).

* **🇺🇸 EN-US:**
  1. **Cold-Start Launch:** In the equivalent version-check pair (`hyperfine_cold_start.json`), PicoClaw cold-starts in **$9.74\text{ ms}$** mean vs. $37.15\text{ ms}$ for OpenClaw (**$3.81\times$ faster mean**; median **$3.46\times$**, $9.67\text{ ms}$ vs. $33.48\text{ ms}$). Across the isomorphic workers with explicit `--version` handling (`hyperfine_worker_version.json`), compiled Go starts in **$3.04\text{ ms}$** vs. **$22.15\text{ ms}$** for Node.js V8 (**$7.29\times$ faster**) and **$49.32\text{ ms}$** for Python (**$16.22\times$ faster**).
  2. **RAM & Silicon Efficiency (`Peak Physical Footprint`):** PicoClaw allocates between **$4.2\text{ and }45.5\text{ MB}$** of peak physical memory (`proc_peak_phys_mb`, `ri_lifetime_max_phys_footprint`, global mean $16.05\text{ MB}$, rising to $45.5\text{ MB}$ only in W3 vector search), whereas OpenClaw demands **$37.5\text{ to }67.1\text{ MB}$** (global mean $45.32\text{ MB}$), delivering a **$1.45\times\text{ to }8.97\times$** reduction in physical DRAM footprint (**$2.82\times$ leaner overall**).
  3. **Instruction & Cycle Efficiency:** Darwin `libproc` counters reveal PicoClaw retires $243.8\times 10^6$ instructions and $84.0\times 10^6$ cycles, compared to $937.1\times 10^6$ instructions ($3.84\times$ higher) and $396.3\times 10^6$ cycles ($4.72\times$ higher) in OpenClaw Minimal.
  4. **Long ReAct Loops Scalability (W4) & EDP Efficiency (Dual-Regime Dynamics):** In the 10-turn autonomous ReAct loop under Regime A (Cold Prefill), PicoClaw finished with $55354.8\text{ ms}$ median and $\text{EDP} = 48543.57\text{ J}\cdot\text{s}$, achieving **$92.53\%$ lower Energy-Delay Product** with significant effect sizes over OpenClaw Full ($d = -1.0$, $\hat{A}_{12} = 0.0$, $p < 10^{-5}$) by avoiding 54-tool catalog prompt bloat. Conversely, under Regime B (Warm KV-Cache Reuse, unified session) with amortized prefill, equalized arms exhibit close EDP parity while remaining **$>35\%$ lower in EDP** compared to OpenClaw Full.
  5. **Ablation Findings (Prompt Bloat) & Active Zero-Copy Tool-RAG Pruner:** Static schema injection of 54 corporate tools in OpenClaw Full increases W1 mean latency from $5852.6\text{ ms}$ to $20682.7\text{ ms}$ and mean net energy from $94.06\text{ J}$ to $329.50\text{ J}$ ($3.50\times$). Our active **Zero-Copy Dynamic Tool-RAG Schema Pruner** ($54 \rightarrow \text{Top-}5$ tools via 384-D cosine similarity in $<0.35\text{ ms}$) shrinks W1 prompt tokens from $7,067$ to $893$, eliminating **$>85\%$ of latency and energy** in Regime A and outperforming even the static 15-tool catalog in Regime B.
  6. **W2 Execution Dynamics & Efficiency:** In Workload W2 (3-Tool Chain), under greedy decoding with equalized tool descriptors, both PicoClaw and OpenClaw Minimal emit $29.0$ tokens with identical task latency ($5556.1\text{ ms}$ vs. $5557.1\text{ ms}$) and net energy ($84.81\text{ J}$ vs. $85.04\text{ J}$, $2.92\text{ J/token}$ vs. $2.93\text{ J/token}$). Microarchitectural isolation confirms compiled Go maintains $3.76\times$ lower orchestrator delay ($T_{\text{orch}} = 5.58\text{ ms}$ vs. $20.95\text{ ms}$) and $8.39\times$ lower physical DRAM footprint in W2 ($4.73\text{ MB}$ vs. $39.67\text{ MB}$ `proc_peak_phys_mb`).
  7. **Schema Prefill Characterization & KV-Cache Reuse:** Across 8 catalog sizes ($0, 5, 10, 15, 25, 40, 54, 100$ tools on llama.cpp / Metal GPU), enterprise schema injection escalates GPU prefill duration ($T_{\text{prefill}}$ rises from $128.1\text{ ms}$ to $4434.4\text{ ms}$, $17877.3\text{ ms}$, and $39190.5\text{ ms}$), exhibiting power-law ($T = 0.3197 \cdot N^{1.2342}$, $R^2 = 0.9993$, $\text{AIC}_c = 99.25$) and quadratic ($R^2 = 0.99999$) scaling compatible with transformer attention complexity, while KV-cache activation avoids redundant attention computation ($5.5\times\text{ to }946.5\times$ prefill speedup), confirming that enterprise schema bloat bottlenecks agent execution via transformer attention costs rather than host orchestrator delay.
  8. **Operational Dual-Regime Trade-offs & Inter-Session Replication ($n=30$) with Native Bun:** The testbed characterizes two full campaigns ($n=30$ each, 660 physical trials per regime) plus an independent inter-session replication ($n=30$ per block, including native **Bun v1.4.4 / JavaScriptCore**):
     * *Regime A (`cache_prompt=false`):* Cold attention prefill on the Metal GPU accounts for $>75\%$ of total execution duration and saturates package power at $\approx 16\text{ W}$, producing near-parity in wall-clock duration between host runtimes.
     * *Regime B (`cache_prompt=true`):* When prompt prefill is amortized via block-isolated KV-cache retention in `llama-server` (verified `Cache Hit` rates of **$99.9\%$ to $100.0\%$** across W1–W3 and **$97.6\%$ to $99.3\%$** in W4), overall task duration drops to sub-second levels in W2 (a **$>20\times$** latency reduction for the 54-tool catalog under block-isolated caching). Under amortized prefill, orchestrator overhead share ($\Phi_{\text{orch}} = T_{\text{orch}} / T_{\text{task}}$) spans **$0.37\%$ to $4.65\%$**, while end-to-end latency for Go, Python, Node-Minimal, and Bun remains within $-1.5\%$ to $+5.8\%$ of the direct neural baseline (smaller than the $\sim 3\%\text{--}10\%$ cross-session thermal/clock drift in W1, W2, and W4, whereas in W3 vectorized BLAS/SIMD consistently outperforms scalar Go loops by $5.6\%\text{--}5.8\%$ across sessions).
  9. **Per-Process Energy Deconvolution (Validated XNU Negative Result) & Analytical-Empirical UMA Bandwidth Estimation:** Direct physical measurements on the Apple SMC `CPU Power` rail with GPU idle isolate marginal tool dispatch cost ($1.252\text{ mJ/op}$ in Go, $1.000\text{ mJ/op}$ in Python, $0.196\text{ mJ/op}$ in Node Minimal in W2). Cross-validation establishes a formal **Negative Result for Darwin XNU `ri_billed_energy`** ($r = -0.0510, p = 0.580, \text{OLS } R^2 = -0.676$ vs. the mean, corroborating Fahad et al., 2019), while validating execution time (`t_exec_ms`, $R^2 = 0.949$), retired instructions (`proc_instructions`, $R^2 = 0.955$), and core cycles (`proc_cycles`, $R^2 = 0.945$) as accurate physical CPU energy proxies. Using direct SMC `CPU Power` rail Joules, Regime B orchestrator energy share ($\Phi_{\text{energy, orch}}$) across W2/W3 is merely **$0.04\% / 1.42\%$** in Go, **$0.03\% / 0.34\%$** in Python, **$0.01\% / 0.49\%$** in Node Minimal, and **$0.01\% / 0.30\%$** in Node Full. During Metal GPU neural decoding, our **Analytical & Empirical Memory Bandwidth Estimation ($\text{Model Weights} \div \text{ITL}$)** yields a **global median of $97.0\text{ GB/s}$ ($80.8\%$ of $120\text{ GB/s}$) and a mean ranging from $95.9\text{ GB/s}$ ($79.9\%$ in Regime A) to $106.7\text{ GB/s}$ ($88.9\%$ in Regime B; global mean $104.0\text{ GB/s}$ / $86.7\%$)**, aligning with the practical Roofline UMA ceiling ($\approx 86\text{--}88\%$, Imamura, 2026; Benazir & Lin, 2025).

### 📐 Regras Práticas de Decisão Arquitetural / Empirical Architectural Decision Rules

* **🇧🇷 PT-BR:**
  1. **Disparo Efêmero em CLI / Cold-Start:** Para utilitários de linha de comando efêmeros ou gatilhos curtos em edge, binários nativos compilados (Go Mach-O) reduzem a latência média de inicialização em **$3{,}81\times$** ($9{,}74\text{ ms}$ vs. $37{,}15\text{ ms}$ no Node.js V8; mediana **$3{,}46\times$**, $9{,}67\text{ ms}$ vs. $33{,}48\text{ ms}$ em `hyperfine_cold_start.json`) e em **$7{,}29\times$** nos workers isomórficos ($3{,}04\text{ ms}$ vs. $22{,}15\text{ ms}$ no Node.js e $49{,}32\text{ ms}$ no Python em `hyperfine_worker_version.json`), eliminando o bootstrap do interpretador.
  2. **Borda com Memória Compartilhada Limitada (UMA / Multi-Agente):** Em nós embarcados e SoCs de memória unificada onde GPU e CPU compartilham o mesmo barramento de DRAM, Go nativo reduz a pegada física de memória de pico (`proc_peak_phys_mb`, `ri_lifetime_max_phys_footprint`) em **$2{,}82\times$** na média global ($16{,}05\text{ MB}$ vs. $45{,}32\text{ MB}$ no Node.js V8; variando de $4{,}2\text{--}45{,}5\text{ MB}$ no Go vs. $37{,}5\text{--}67{,}1\text{ MB}$ no Node.js V8, ou **$1{,}45\times\text{ a }8{,}97\times$** entre workloads). Isso preserva capacidade física crítica de DRAM para tabelas de páginas do KV-Cache e pesos neurais.
  3. **Daemons Persistentes com Cache Quente e Esquemas Compactos ($\le 15$ ferramentas):** Com retenção de prefixo de KV-cache ativa ($\text{Cache Hit} \ge 97{,}6\%$), Go, Python, Node.js e Bun diferem em menos de $-1{,}5\%$ a $+5{,}8\%$ do baseline neural direto ($\Phi_{\text{orch}} \in [0{,}37\%, 4{,}65\%]$, $\Phi_{\text{energy, orch}} \in [0{,}01\%, 1{,}42\%]$). Como a deriva inter-sessão ($\sim 3\%\text{--}10\%$) supera essas diferenças em W1, W2 e W4, a escolha da linguagem pode priorizar maturidade de ecossistema e restrições de RAM no host.
  4. **Grandes Catálogos Corporativos ($\ge 50$ ferramentas):** O gargalo dominante decorre do pré-processamento de atenção super-linear na GPU ($\alpha \approx 1{,}23$) e não da linguagem do host. A mitigação mandatória exige isolamento determinístico de slot de KV-cache (redução de $>20\times$ no tempo de execução) ou ativação do módulo **Zero-Copy Dynamic Tool-RAG Schema Pruner** ($54 \rightarrow \text{Top-}5$ ferramentas em $<0{,}35\text{ ms}$, reduzindo latência e energia em $>85\%$).

* **🇺🇸 EN-US:**
  1. **Ephemeral CLI / Cold-Start Invocation:** For short-lived CLI utilities, serverless functions, or bursty edge triggers, native compiled binaries (Go Mach-O) reduce mean startup latency by **$3.81\times$** ($9.74\text{ ms}$ vs. $37.15\text{ ms}$ in Node.js V8; median **$3.46\times$**, $9.67\text{ ms}$ vs. $33.48\text{ ms}$ in `hyperfine_cold_start.json`) and isomorphic worker startup by **$7.29\times$** ($3.04\text{ ms}$ vs. $22.15\text{ ms}$ in Node.js and $49.32\text{ ms}$ in Python in `hyperfine_worker_version.json`), eliminating runtime interpreter bootstrap overhead.
  2. **Memory-Constrained Unified Memory (UMA) / Multi-Agent Edge:** On embedded edge nodes and unified memory SoCs where CPU and GPU share physical DRAM, Go native reduces peak physical DRAM allocation (`proc_peak_phys_mb`, `ri_lifetime_max_phys_footprint`) by **$2.82\times$** on global average ($16.05\text{ MB}$ vs. $45.32\text{ MB}$ in Node.js V8; ranging from $4.2\text{--}45.5\text{ MB}$ in Go vs. $37.5\text{--}67.1\text{ MB}$ in Node.js V8, or **$1.45\times\text{ to }8.97\times$** across workloads). This safeguards vital physical DRAM capacity for KV-cache page tables and model weights.
  3. **Persistent Daemons with Warm KV-Cache and Compact Schemas ($\le 15$ tools):** When running persistent services with verified prefix caching ($\text{Cache Hit} \ge 97.6\%$) and lean schemas, compiled Go, Python, Node.js, and Bun differ by less than $-1.5\%$ to $+5.8\%$ from the direct neural baseline ($\Phi_{\text{orch}} \in [0.37\%, 4.65\%]$, $\Phi_{\text{energy, orch}} \in [0.01\%, 1.42\%]$). Because independent inter-session drift ($\sim 3\%\text{--}10\%$) exceeds these intra-session differences in W1, W2, and W4, runtime selection can be driven primarily by library ecosystem maturity and host memory constraints.
  4. **Large Enterprise Tool Catalogs ($\ge 50$ tools):** The primary performance bottleneck shifts entirely to super-linear attention prefill on the GPU ($\alpha \approx 1.23$) rather than host orchestration. Mitigating this bottleneck strictly requires deterministic KV-cache slot isolation (yielding $>20\times$ latency reduction) or enabling our built-in **Zero-Copy Dynamic Tool-RAG Schema Pruner** ($54 \rightarrow \text{Top-}5$ tools in $<0.35\text{ ms}$, eliminating $>85\%$ of prefill latency and energy).

---

## 🛠️ Guia Didático e Provas de Execução / Beginner's Walkthrough

Para visualizar a analogia didática do "Carro e os Dois Motoristas", o mini tutorial de 3 minutos e todos os **9 passos com exemplos ilustrativos da estrutura de saída no Apple Silicon M4**, consulte o guia dedicado:

👉 **[Acessar o Guia Didático e Logs em `tutorial/README.md`](tutorial/README.md)**

| Etapa / Step | Descrição Técnica Comprovada no Terminal |
| :---: | :--- |
| **Passo 1** | Servidor `llama-server` Metal GPU alocado na DRAM UMA e healthcheck `ok`. |
| **Passo 2** | Inspeção física dos datasets determinísticos em `data/workload_data/`. |
| **Passo 3** | Execução ao vivo dos traces W1 a W4 com cálculo de $\Delta\text{RSS}$ e latência. |
| **Passo 4** | Medição estatística de cold-start via `hyperfine` com vantagem de $3{,}81\times$ na média ($3{,}46\times$ na mediana, e $7{,}29\times$ nos workers isomórficos) para o Go. |
| **Passo 5** | Verificação de integridade criptográfica SHA-256 de todos os arquivos rastreados em `data/manifest_sha256.json` (`make verify` / `python scripts/verify_manifest.py`). |
| **Passo 6** | Modo Dry-Run portátil de validação completa do pipeline (`make dry-run`). |
| **Passo 7** | Leitura dos shunts elétricos do chip M4 via Apple SMC (`powermetrics -i 50`). |
| **Passo 8** | Protocolo de quiescência operacional do macOS (`caffeinate -dims`). |
| **Passo 9** | Campanha de reuso de KV-cache (Regime B) com taxa de retenção determinística $\ge 97{,}6\%$ via `scripts/run_warm_cache_campaign.py`. |

---

## 🔬 Ameaças à Validade / Threats to Validity

Em conformidade com a literatura de engenharia de software experimental e avaliação de desempenho (Jain, 1991; Lilja, 2000):

### 1. Validade Interna (*Internal Validity*)
* **Estocasticidade do Modelo Neural:** Variações probabilísticas na geração de texto poderiam alterar a quantidade de tokens gerados e mascarar o desempenho do runtime. **Mitigação:** Fixou-se decodificação gulosa determinística (`temperature = 0.0`, `seed = 42`) no `llama.cpp`, garantindo respostas idênticas token a token.
* **Ruído do Sistema Operacional e Throttling:** Tarefas em segundo plano do macOS (Spotlight, Time Machine, repouso de tela) poderiam contaminar as medições de I/O e latência. **Mitigação:** Aplicou-se suspensão de indexação (`sudo mdutil -a -i off`), isolamento em loopback de rede local e bloqueio persistente de repouso via `/usr/bin/caffeinate -dims`.

### 2. Validade Externa (*External Validity*)
* **Generalização do Modelo Neural:** Os experimentos foram conduzidos com o Meta Llama-3.2-3B-Instruct quantizado em 4 bits (GGUF Q4_K_M). Embora este modelo represente a fronteira de eficiência para agentes em dispositivos locais (*edge computing*), modelos de 8B ou 70B imporiam maior tempo de prefill, tornando o percentual relativo de overhead do orquestrador ($T_{\text{orch}}$) menor em relação ao tempo neural total.
* **Diversidade de Hardware:** Os resultados refletem a microarquitetura Apple Silicon M4 com memória unificada (UMA). Em servidores x86 convencionais com GPU dedicada acoplada via barramento PCIe, a transferência de tensores adiciona latência de socket que não ocorre no Apple Silicon.

### 3. Validade de Construto (*Construct Validity*)
* **🇧🇷 PT-BR:**
  * **Isolamento de Métricas de Latência:** Medir apenas a latência total ponta a ponta não separaria a lentidão da GPU da sobrecarga do agente. **Mitigação:** Decompôs-se algebricamente a latência ($T_{\text{task}} = T_{\text{orch}} + T_{\text{neural}} + T_{\text{dispatch}}$) com resolução de microssegundos e incorporou-se a linha de base neural direta (*Neural Baseline*) sem agentes.
  * **Granularidade Física dos Sensores Analógicos de Potência:** Em arquiteturas SoC com memória unificada (Apple Silicon M4), os sensores analógicos de shunt gerenciados pelo SMC medem o consumo agregado nos trilhos de hardware (clusters de CPU, Metal GPU e ANE) no nível do pacote SoC, e não por processo POSIX individual (Barroso & Hölzle, 2007; You et al., 2023). Isolar Joules analógicos exclusivos para um único processo durante a execução concorrente de CPU e GPU é fisicamente inobservável no nível de shunt. **Mitigação:** Seguindo a metodologia consagrada de benchmarking energético para sistemas de aprendizado de máquina (Georgiou et al., 2022; You et al., 2023), nosso arcabouço resolve essa limitação arquitetural por meio de telemetria em duas camadas: (i) energia total do pacote do sistema ($E_{\text{total}}$ e energia líquida sobre a linha de base quiescente) integrada via regra trapezoidal composta a partir do `powermetrics` em intervalos de 50 ms, e (ii) atribuição microarquitetural por processo (`ri_instructions`, `ri_cycles`, `ri_billed_energy` e `ri_lifetime_max_phys_footprint`) coletada diretamente do kernel Darwin XNU via `libproc` (`proc_pid_rusage` com `RUSAGE_INFO_V4`). Em ambientes não-privilegiados, os campos elétricos são estritamente marcados como indisponíveis (`N/A`), preservando o princípio inviolável de zero estimativas sintéticas.
* **🇺🇸 EN-US:**
  * **Latency Metric Isolation:** Measuring only end-to-end task latency cannot disentangle GPU inference duration from agent runtime overhead. **Mitigation:** Latency is algebraically decomposed ($T_{\text{task}} = T_{\text{orch}} + T_{\text{neural}} + T_{\text{dispatch}}$) with microsecond precision, benchmarked against a zero-overhead direct *Neural Baseline*.
  * **Physical Granularity of Analog Power Sensors:** In unified-memory SoC architectures (Apple Silicon M4), physical electrical shunt sensors managed by the SMC instrument aggregate hardware power rails (CPU, GPU, ANE) at the package level rather than individual POSIX processes (Barroso & Hölzle, 2007; You et al., 2023). Isolating exclusive analog Joules for a single process during concurrent CPU--GPU execution is physically unobservable at the shunt layer. **Mitigation:** Following established energy-benchmarking methodology for machine learning systems (Georgiou et al., 2022; You et al., 2023), our harness resolves this architectural constraint via two-layer telemetry: (i) system-wide package energy ($E_{\text{total}}$ and net active energy above quiescent baseline) integrated via the composite trapezoidal rule from `powermetrics` at 50 ms resolution, and (ii) per-process microarchitectural attribution (`ri_instructions`, `ri_cycles`, `ri_billed_energy`, `ri_lifetime_max_phys_footprint`) polled from the Darwin XNU kernel via `libproc` (`proc_pid_rusage` with `RUSAGE_INFO_V4`). When running unprivileged, electrical energy fields safely report unavailable (`N/A`), upholding the strict zero-synthetic-proxy empirical protocol.

---

## 🔐 Permissões de Kernel, Sistema Operacional e Níveis de Privilégio / OS Kernel Permissions

Seguindo o **Princípio do Menor Privilégio (*Principle of Least Privilege*)**:

| Componente / Comando | Nível de Privilégio | Subsistema do Kernel / SO Acessado | Finalidade Metodológica |
| :--- | :---: | :--- | :--- |
| **`powermetrics`** | **Superusuário (`sudo`)** | **Apple SMC (*System Management Controller*)** | Leitura dos shunts físicos de corrente/tensão do chip M4 (mW). Acesso restrito pelo kernel XNU para prevenir ataques de canal lateral (*Platypus*). |
| **`mdutil -a -i off / on`** | **Superusuário (`sudo`)** | **APFS Filesystem Metadata & Daemons `mds`** | Desativação temporária da indexação do Spotlight para anular ruído de I/O no Workload W2. |
| **Darwin `libproc` (`proc_pid_rusage`)** | **Usuário Padrão (Sem Root)** | **Syscall Darwin XNU (`/usr/lib/libproc.dylib`)** | Coleta de contadores de hardware (`ri_instructions`, `ri_cycles`, RSS) via Python `ctypes` sem exigir privilégios de administrador. |
| **`caffeinate -dims`** | **Usuário Padrão (Sem Root)** | **IOKit Power Management Assertion** | Prevenção de repouso de sistema, display e disco durante a execução das baterias de testes. |
| **`llama-server` (Metal GPU)** | **Usuário Padrão (Sem Root)** | **Apple Metal Framework & Driver IOGPU** | Execução de tensores e compute shaders na GPU integrada dentro do espaço de endereçamento da UMA. |
| **Orquestradores (Go / Node.js)** | **Usuário Padrão (Sem Root)** | **POSIX Processes & Loopback TCP (`127.0.0.1`)** | Execução padronizada dos agentes em espaço de usuário comum. |

---

## 📁 Estrutura do Repositório / Directory Structure

```text
.
├── Makefile                                   <- Automação completa (make setup, test, benchmark, reproduce-figures)
├── CITATION.cff                               <- Metadados acadêmicos para citação e Zenodo DOI
├── LICENSE                                    <- Licença MIT para código-fonte
├── DATA_LICENSE                               <- Licença Creative Commons CC-BY 4.0 para dados e figuras
├── references.bib                             <- Base bibliográfica formal BibTeX (21 referências primárias verificadas)
├── reproduce_linux_gold.sh                    <- Script de reprodução física automatizada em Linux x86_64
├── windows_gold.ps1                           <- Script PowerShell de reprodução no Windows 11
├── launch_sentinel_intel_win.ps1              <- Script PowerShell de reprodução no Windows Intel HD Graphics 4600
├── AUDIT_REPORT_FINAL.md                      <- Relatório final dinâmico de auditoria (inventário real dos 35 .jsonl)
├── audit_export/                              <- Artefatos consolidados da auditoria quad-plataforma
│   ├── AUDIT_REPORT_FINAL.md                  <- Espelho do relatório final de auditoria
│   ├── Systems_Replication_Report.md          <- Relatório consolidado de replicação de sistemas (100% inglês)
│   ├── audit_summary_metrics.json             <- Métricas consolidadas em formato JSON estruturado
│   ├── quad_platform_consolidated_summary.csv <- Sumário estatístico comparativo quad-plataforma
│   ├── anomaly_and_cache_diagnostics.csv      <- Diagnóstico de dependência serial, drift e telemetria térmica
│   ├── figures/                               <- Figuras consolidadas em 300 DPI (Figuras 1 a 6)
│   └── tables/                                <- Tabelas consolidadas em Markdown e LaTeX (Tabelas 1 a 8)
├── audit_export_quad_platform.zip             <- Pacote zip autocontido da auditoria quad-plataforma
├── audit_txt_chunks/                          <- Arquivos de auditoria em texto fatiados (.txt <= 150 KB)
├── tutorial/                                  <- Guia didático passo a passo e logs ilustrativos
│   └── README.md                              <- Tutorial prático bilíngue com passos 1 a 9 e traces ilustrativos
├── adapters/
│   └── windows_intel_graphics/                <- Adaptadores e workers user-mode para Intel HD Graphics 4600 (W2/W5)
├── W5_langchain_real_world/                   <- Workload corporativo W5 (agent.py, evaluator.py, SQLite)
├── benchmark/                                 <- Harness de execução, adaptadores e orquestradores
│   ├── adapters/                              <- Implementação do padrão Strategy/Adapter
│   │   ├── base.py                            <- Interface abstrata AgentOrchestratorAdapter
│   │   ├── picoclaw_adapter.py                <- Adaptador PicoClaw Go nativo
│   │   ├── openclaw_adapter.py                <- Adaptador OpenClaw Node.js (Minimal e Full Ablation)
│   │   ├── bun_minimal_adapter.py             <- Adaptador BunMinimal para extensibilidade multi-runtime
│   │   ├── python_native_adapter.py           <- Adaptador PythonNative (referência CPython 3.12/3.14)
│   │   └── neural_baseline_adapter.py         <- Adaptador de linha de base neural direta
│   ├── windows_x86_64_telemetry_adapter.py    <- Telemetria Win32 QueryProcessCycleTime e PSAPI
│   ├── picoclaw_orch.go                       <- Orquestrador Go nativo (compilado Mach-O ARM64 / ELF / PE)
│   ├── openclaw_orch.mjs                      <- Orquestrador Node.js/TypeScript V8
│   ├── python_orch.py                         <- Orquestrador Python 3.12/3.14 + NumPy
│   ├── telemetry.py                           <- Coletor de telemetria Apple SMC, libproc e Linux RAPL
│   ├── run_unified_benchmark.py               <- Executor mestre com randomized block e modo dry-run
│   ├── analyze_results.py                     <- Análise estatística (Mediana, IQR, Cliff's d, A12, Holm-Bonferroni)
│   └── generate_charts.py                     <- Gerador de figuras da campanha M4
├── scripts/                                   <- Scripts utilitários e de campanha
│   ├── reproduce_quad_platform_analysis.py    <- Pipeline mestre quad-plataforma (estatística, Tabelas 1–8, Figuras 1–6, relatórios)
│   ├── generate_audit_txt_chunks.py           <- Gerador dos chunks textuais leves (<= 150 KB) em audit_txt_chunks/
│   ├── run_linux_x86_64_master_campaign.py    <- Harness de execução física para Linux x86_64 (RAPL/NVML/PMU)
│   ├── run_windows_x86_64_master_campaign.py  <- Harness de execução física para Windows 11 (Win32/NVML)
│   ├── run_prefill_ablation.py                <- Caracterização de prefill e ajuste polinomial (Metal GPU)
│   ├── run_warm_cache_campaign.py             <- Campanha do Regime B com isolamento de blocos (KV-cache ativo)
│   ├── run_w2_resample.py                     <- Script auditável de reamostragem focada de W2 com backup
│   ├── run_inter_session_replication.py       <- Validação de replicação inter-sessão física independente
│   ├── run_uma_energy_and_bandwidth_attribution.py <- Deconvolução SMC/libproc e telemetria de banda UMA
│   ├── verify_manifest.py                     <- Validador criptográfico SHA-256 (todos os arquivos rastreados + 35 .jsonl)
│   ├── check_quiescence.sh                    <- Auditoria de quiescência operacional
│   └── legacy/                                <- Scripts exploratórios arquivados
├── tests/                                     <- Suíte de testes automatizados (51 testes em pytest)
│   ├── test_adapters_and_failfast.py          <- Validação dos adaptadores e fail-fast
│   ├── test_artifact_consistency.py           <- Consistência numérica cruzada JSON/CSV/LaTeX
│   ├── test_dataset_generator.py              <- Validação de integridade dos datasets determinísticos
│   ├── test_statistical_engine.py             <- Validação matemática de Cliff's d, A12, Bootstrap e Holm
│   ├── test_telemetry_parser.py               <- Validação de parsing SMC, RAPL e libproc
│   └── test_windows_intel_graphics_adapter.py <- Validação de isolamento e esquema do adaptador Intel iGPU
├── figures/                                   <- 6 figuras científicas quad-plataforma em 300 DPI (100% inglês)
├── results/                                   <- Resultados experimentais estruturados
│   ├── publication_campaign/                  <- Dados brutos macOS Apple Silicon M4 (7 arquivos .jsonl)
│   │   ├── raw_trials.jsonl                   <- Regime A Cold Prefill (825 linhas: 750 medições + 75 warmups, W1–W5)
│   │   ├── warm_cache_trials.jsonl            <- Regime B Warm KV-Cache (825 linhas: 750 medições + 75 warmups, W1–W5)
│   │   ├── inter_session_trials.jsonl         <- Sessão 2 de replicação inter-sessão (825 linhas, W1–W5)
│   │   ├── kv_cache_thrashing_trials.jsonl    <- Ablação KV-Cache Thrashing T1/T2/T3 (90 linhas)
│   │   ├── tool_rag_mitigation_trials.jsonl   <- Ablação Tool-RAG 54->Top-5 (1.056 linhas, W1–W4)
│   │   ├── prefill_ablation.jsonl             <- Ablação de catálogos 0..100 ferramentas (528 linhas)
│   │   ├── uma_energy_bandwidth_trials.jsonl  <- Deconvolução SMC/libproc e banda UMA (120 linhas)
│   │   ├── campaign_metadata.json             <- Metadados completos do ambiente e flags de hardware
│   │   ├── summary_statistics.json            <- Estatísticas sumárias e EDP
│   │   ├── statistical_tests.json             <- Testes Mann-Whitney U, Cliff's Delta e Vargha-Delaney
│   │   └── tables/                            <- Tabelas LaTeX (.tex) e CSV (.csv) da campanha M4
│   ├── quad_platform_tables/                  <- Tabelas LaTeX quad-plataforma (.tex: Tabelas 1, 6, 7 e 8)
│   └── exploratory_campaigns/                 <- Campanhas exploratórias históricas preservadas
├── data/                                      <- Datasets brutos (28 .jsonl: 2 macOS + 26 x86_64), workloads e manifesto SHA-256
│   ├── mcp_live_transport_trials.jsonl        <- macOS M4 MCP Live Transport (135 linhas, W2)
│   ├── external_framework_langchain_trials.jsonl <- macOS M4 LangChain Core externo (144 linhas, W1–W4)
│   ├── linux_x86_64_session1/raw/             <- Linux x86_64 NVIDIA Sessão 1 (5 .jsonl: raw, warm, kv, mcp_live_transport, tool_rag)
│   ├── linux_x86_64_session2/raw/             <- Linux x86_64 NVIDIA Sessão 2 (5 .jsonl: raw, warm, kv, mcp_live_transport, tool_rag)
│   ├── windows_x86_64_session1/raw/           <- Windows 11 NVIDIA Sessão 1 (5 .jsonl: raw, warm, kv, mcp_live_transport, tool_rag)
│   ├── windows_x86_64_session2/raw/           <- Windows 11 NVIDIA Sessão 2 (5 .jsonl: raw, warm, kv, mcp_live_transport, tool_rag)
│   ├── windows_intel_graphics_session1/raw/   <- Windows Intel iGPU Sessão 1 (3 .jsonl: raw, warm, tool_rag)
│   ├── windows_intel_graphics_session2/raw/   <- Windows Intel iGPU Sessão 2 (3 .jsonl: raw, warm, tool_rag)
│   ├── workload_data/                         <- 50 mock files, 750 logs JSONL, RAG chunks e pesos 384d
│   └── manifest_sha256.json                   <- Manifesto criptográfico SHA-256 dos arquivos rastreados
├── docs/                                      <- Documentação técnica complementar (PT/EN)
├── reports/                                   <- Relatórios acadêmicos (.docx / .pdf)
└── tools/                                     <- Toolchain embarcada portátil (llama_cpp, hyperfine, uv)
```

---

## ⚡ Guia Rápido de Reprodução / Quickstart Reproduction

### 1. Verificação Rápida para Avaliadores (Sem Sudo / Multi-OS) / Fast Verification (No Sudo / Cross-Platform)
Para avaliadores testando o repositório em ambientes isolados (ex: Linux x86_64, Windows ou macOS sem modelo GGUF ou privilégios de superusuário), execute o pipeline simulado de ponta a ponta em menos de 10 segundos:

```bash
# Executa simulação determinística portátil, testes estatísticos e renderização gráfica (< 5s)
make dry-run
```

### 2. Modelo de Segurança e Execução Completa nas 4 Plataformas Físicas / Security Model & Quad-Platform Physical Runs
> [!IMPORTANT]
> **Privilégios e Segurança:** Os agentes avaliados (`PicoClaw` e `OpenClaw`) e o servidor neural (`llama-server`) **sempre executam estritamente em espaço de usuário comum** (`euid != 0`). A exigência de `sudo` restringe-se exclusivamente à amostragem física de sensores de hardware bloqueada pelo kernel (Apple SMC `powermetrics` no macOS, Intel RAPL e NVIDIA NVML no Linux).

#### 🍎 Apple Silicon M4 (macOS Darwin ARM64)
```bash
# 1. Configurar o ambiente isolado automaticamente (Python venv, Node.js e ferramentas)
make setup

# 2. Executar a suíte de testes automatizados (pytest e ruff linter)
make test

# 3. Execução em espaço de usuário comum (Sem Sudo / Degradação Graciosa)
make benchmark

# 4. Execução física com telemetria elétrica completa do Apple SMC (Requer Sudo)
make benchmark-full-smc

# 5. Regenerar todas as 6 figuras científicas em 300 DPI
make reproduce-figures
```

#### 🐧 Linux x86_64 (Ubuntu 24.04/26.04 LTS com NVIDIA GPU)
```bash
# Execução da campanha completa com telemetria Intel RAPL e NVIDIA NVML (Requer Sudo)
sudo bash reproduce_linux_gold.sh

# Ou execução direta via script mestre em Python
python scripts/run_linux_x86_64_master_campaign.py --ngl 16 --reps 30
```

#### 🪟 Windows 11 x86_64 (PowerShell 7+ / Prompt de Administrador com NVIDIA dGPU)
```powershell
# Execução da campanha padrão ouro com telemetria Win32 QueryProcessCycleTime e NVML
.\windows_gold.ps1 -Reps 30 -Ngl 16

# Ou execução direta via script mestre em Python
python scripts\run_windows_x86_64_master_campaign.py --ngl 16 --reps 30
```

#### 💻 Windows 10/11 x86_64 (Intel HD Graphics 4600 iGPU UMA)
```powershell
# Execução da campanha automatizada com sentinela e telemetria Win32 PSAPI em user-mode
powershell -ExecutionPolicy Bypass -File .\launch_sentinel_intel_win.ps1
```

#### 📊 Pipeline Mestre de Consolidação Quad-Plataforma e Verificação
```bash
# 1. Recalcula todas as estatísticas a partir dos 35 arquivos .jsonl, gera Tabelas 1–8,
#    renderiza as 6 figuras em 300 DPI, atualiza os relatórios e empacota audit_export_quad_platform.zip
python scripts/reproduce_quad_platform_analysis.py

# 2. Exporta os chunks textuais leves (<= 150 KB) em audit_txt_chunks/
python scripts/generate_audit_txt_chunks.py

# 3. Executa os 51 testes automatizados e valida o manifesto criptográfico SHA-256
pytest -q
python scripts/verify_manifest.py
```

---

## 🔄 Continuous Integration (CI) & Reproducibility

Artifact consistency, protocol invariants, and multi-platform telemetry backends are automatically validated on every push and pull request via a Continuous Integration (CI) pipeline using GitHub Actions (`.github/workflows/ci.yml`). The matrix tests against:
* **Ubuntu Linux (`ubuntu-latest`)**
* **Microsoft Windows (`windows-latest`)**
* **Apple macOS (`macos-latest`)**

The pipeline executes `ruff check`, `pytest -q tests/`, the fast reviewer dry-run integration test, and the cryptographic manifest verification to guarantee zero-drift reproducibility and strict adherence to empirical Zero-Mock guidelines.

---

## 🧠 Decisões Metodológicas e Arquitetura dos Scripts / Methodological Rationale & Code Architecture

### Por que cada decisão metodológica foi adotada / Why Each Methodological Choice Matters
1. **Isolamento de Slots KV-Cache (`T1`, `T2`, `T3`):** Separa evicção descontrolada (*thrashing*, `T2`) da alocação isolada por bloco (`T3`), isolando o custo de recomputação quadrática de prefill do custo intrínseco do runtime orquestrador (Kwon et al., 2023).
2. **Moving Block Bootstrap ($b=3$) e Tamanho Amostral Efetivo ($n_{\text{eff}}$):** Execuções em cache quente (Regime B) podem exibir autocorrelação serial lag-1 ($|r_1| > 2/\sqrt{n}$) devido à retenção de páginas de memória pelo SO e drenagem de sockets loopback. O Moving Block Bootstrap (Künsch, 1989) preserva a dependência temporal de curto alcance nos intervalos de confiança de 95% sem assumir independência i.i.d. estrita.
3. **TOST de Contrastes Inter-Sessão ($\Delta T_{\text{orch}}$) em Blocos com SESOI Fixo:** Testes de hipótese nula tradicionais não provam equivalência. O procedimento *Two One-Sided Tests* via Moving Block Bootstrap ($b=3$, $B=5{,}000$; Künsch, 1989; Schuirmann, 1987; Lakens, 2017) avalia se os contrastes $\Delta T_{\text{orch}} = T_{\text{orch}}(\text{Runtime}) - T_{\text{orch}}(\text{PicoClaw})$ replicam entre sessões independentes dentro de uma margem pré-especificada e independente dos dados ($\Delta_{\text{SESOI}} = \pm 5{,}0\text{ ms}$), com IC 90% matematicamente alinhado a $\alpha = 0{,}05$ e decisão padronizada em 3 estados (`Equivalent`, `Different`, `Inconclusive`).
4. **Segregação Cross-ISA de Contadores PMU:** Contagens brutas de instruções retiradas diferem estruturalmente entre ARM64 (RISC) e x86_64 (CISC) por densidade de ISA e expansão de micro-ops (Weaver et al., 2013). As contagens são segregadas por ISA e interpretadas por razões intra-nó; no Windows (onde `CR4.PCE` restringe contadores PMU em user-mode), utilizam-se ciclos de CPU diretos via Win32 `QueryProcessCycleTime` sem extrapolações sintéticas de IPC.

### Arquitetura dos Scripts Principais / Core Script Architecture
- **`scripts/reproduce_quad_platform_analysis.py`:** Pipeline central sem hardcode que ingere os 35 arquivos `.jsonl` brutos, calcula diagnósticos de estacionariedade/drift ($r_1$, $n_{\text{eff}}$, Holm-Bonferroni), consolida estatísticas (Mann-Whitney $U$, Kruskal-Wallis, Cliff's $\delta$, Vargha-Delaney $A_{12}$, TOST), exporta Tabelas 1–8 (`.md` e `.tex`), renderiza as 6 figuras em 300 DPI, gera dinamicamente `Systems_Replication_Report.md` e `AUDIT_REPORT_FINAL.md`, e empacota `audit_export_quad_platform.zip`.
- **`scripts/verify_manifest.py`:** Calcula digests SHA-256 em blocos de 64 KB para todos os arquivos rastreados em `data/manifest_sha256.json`, validando a integridade dos dados brutos, código e saídas (`--update` recalcula o manifesto após execuções físicas).
- **`benchmark/adapters/` & `adapters/windows_intel_graphics/`:** Implementações do padrão Strategy/Adapter (`AgentOrchestratorAdapter`) desacoplando cada runtime (Go, Node.js, CPython, Bun, LangChain) e cada backend de telemetria nativa (Apple SMC/`libproc`, Linux RAPL/NVML/`perf`, Windows MSR/NVML/Win32 PSAPI) do harness experimental.
- **`scripts/generate_audit_txt_chunks.py`:** Fatia relatórios, tabelas Markdown e diagnósticos CSV em arquivos `.txt` leves ($\le 150\text{ KB}$) em `audit_txt_chunks/` com cabeçalhos de rastreabilidade.

---

## 🔐 Inventário Criptográfico dos 35 Datasets Empíricos / Cryptographic SHA-256 Manifest

Todos os **35 arquivos `.jsonl` brutos** contêm registros medidos diretamente no hardware físico nas 4 plataformas (Apple M4, Linux x86_64, Windows 11 NVIDIA e Windows Intel iGPU) em execuções limpas (*from-scratch*). Para evitar divergências de manutenção manual, o inventário completo com paths exatos, contagens de linhas/trials medidos/warmups e hashes SHA-256 é gerado dinamicamente em:
- [`AUDIT_REPORT_FINAL.md`](AUDIT_REPORT_FINAL.md) (Seção 3)
- [`audit_export/Systems_Replication_Report.md`](audit_export/Systems_Replication_Report.md) (Seção 6)
- [`data/manifest_sha256.json`](data/manifest_sha256.json)

A integridade de todos os arquivos rastreados (incluindo os 35 datasets `.jsonl` brutos das 4 plataformas) pode ser verificada a qualquer momento com:
```bash
python scripts/verify_manifest.py
```

---

## 💖 Apoio à Pesquisa / Support the Research (Pix)

<p align="center">
  <img src="figures/pix_qr_code.png" alt="Chave Pix QR Code" width="220"/>
</p>

### 🇧🇷 Apoie a Pesquisa Científica Aberta (Pix)
Se esta suíte de testes, os dados empíricos quad-plataforma e as ferramentas abertas foram úteis para a sua pesquisa, dissertação, benchmark de hardware ou desenvolvimento de engenharia, você pode apoiar a infraestrutura computacional e publicações abertas do projeto via **Pix**:

* **Chave Pix (E-mail):** `rafael.paniccia@aluno.ufabc.edu.br`
* **Favorecido:** Rafael Paniccia Cassetta
* **Instituição:** Universidade Federal do ABC (UFABC)
* **Finalidade:** Manutenção de servidores de teste, infraestrutura de telemetria de hardware e publicação científica *open-access*.

### 🇺🇸 Support Independent Open-Access Systems Research
If this benchmark framework, empirical quad-platform telemetry, or reproducible analysis helped your research or engineering workflows, you can support our academic infrastructure and open-access publications via Brazilian Pix transfer using the QR code above or key `rafael.paniccia@aluno.ufabc.edu.br`.

---

## 📚 Fundamentação Teórica e Referências / References

As decisões metodológicas, modelos estatísticos e formulações de hardware estão ancorados na literatura científica revisada por pares contida no arquivo [`references.bib`](references.bib):

1. **Avaliação de Desempenho de Sistemas:**
   * Jain, R. (1991). *The Art of Computer Systems Performance Analysis*. John Wiley & Sons.
   * Lilja, D. J. (2000). *Measuring Computer Performance: A Practitioner's Guide*. Cambridge University Press.
2. **Estatística Não-Paramétrica e Correções de Hipóteses Múltiplas:**
   * Mann, H. B., & Whitney, D. R. (1947). *On a Test of Whether one of Two Random Variables is Stochastically Larger than the Other*. Annals of Mathematical Statistics, 18(1), 50–60.
   * Cliff, N. (1993). *Dominance statistics: Ordinal analyses to answer ordinal questions*. Psychological Bulletin, 114(3), 494–509.
   * Vargha, A., & Delaney, H. D. (2000). *A Critique and Improvement of the CL Common Language Effect Size Statistics*. Journal of Educational and Behavioral Statistics, 25(2), 101–132.
   * Holm, S. (1979). *A Simple Sequentially Rejective Multiple Test Procedure*. Scandinavian Journal of Statistics, 6(2), 65–70.
   * Efron, B. (1979). *Bootstrap Methods: Another Look at the Jackknife*. The Annals of Statistics, 7(1), 1–26.
3. **Eficiência Energética e Arquitetura de Computadores:**
   * Horowitz, M., Indermaur, T., & Gonzalez, R. (1994). *Low-power digital design*. IEEE Symposium on Low Power Electronics, 8–11.
   * Barroso, L. A., & Hölzle, U. (2007). *The Case for Energy-Proportional Computing*. IEEE Computer, 40(12), 33–37.
   * Pereira, R., et al. (2021). *Ranking programming languages by energy efficiency*. Science of Computer Programming, 205, 102609.
4. **Agentes Autônomos de IA e Inferência Local:**
   * Yao, S., et al. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR 2023.
   * Schick, T., et al. (2023). *Toolformer: Language Models Can Teach Themselves to Use Tools*. NeurIPS 2023.
   * Lewis, P., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS 2020.
   * Reddi, V. J., et al. (2020). *MLPerf Inference Benchmark*. IEEE Micro, 40(3), 8–16.

---

## 🤝 Agradecimentos / Acknowledgments

* **Universidade Federal do ABC (UFABC):** Ao Programa de Pós-Graduação em Engenharia da Informação / Ciência da Computação.
* **Universidade Federal do ABC (UFABC):** Ao Centro de Engenharia, Modelagem e Ciências Sociais Aplicadas (CECS) pelo apoio institucional e infraestrutura computacional.
* **Telemetry Frameworks & Open Source:** The authors acknowledge the use of Apple Silicon and Intel RAPL telemetry frameworks for microarchitectural data acquisition. We also thank the open-source community for the foundational tools that enabled this cross-platform validation.
