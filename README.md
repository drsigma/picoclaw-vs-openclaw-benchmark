# PicoClaw vs. OpenClaw: Performance Evaluation of Go and TypeScript AI Agent Architectures on Apple Silicon M4

[![UFABC](https://img.shields.io/badge/Institution-UFABC-blue.svg)](http://www.ufabc.edu.br/)
[![Course](https://img.shields.io/badge/Course-CCM313--EEI203-darkgreen.svg)](https://propg.ufabc.edu.br/)
[![Platform](https://img.shields.io/badge/Platform-Apple%20Silicon%20M4-purple.svg)](https://www.apple.com/)
[![Statistical Rigor](https://img.shields.io/badge/Poisson%20Assertiveness-%E2%89%A5%2090.3%25%20--%2093.8%25-brightgreen.svg)](docs/03_METODOLOGIA_ESTATISTICA_POISSON.md)
[![License](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

**Autor / Author:** Rafael Paniccia Cassetta (RA / Student ID: 21202520618)  
**Programa / Program:** Pós-Graduação em Engenharia da Informação / Ciência da Computação  
**Disciplina / Course:** CCM313-EEI203 — Análise de Desempenho de Redes e Sistemas (2026.3)  
**Instituição / Institution:** Universidade Federal do ABC (UFABC)  
**Repositório GitHub / GitHub Repository:** [https://github.com/drsigma/picoclaw-vs-openclaw-benchmark](https://github.com/drsigma/picoclaw-vs-openclaw-benchmark)

---

## 📌 Resumo Executivo / Executive Summary

### Português (PT-BR)
Este repositório contém a suíte completa de experimentos, código-fonte reproduzível, telemetria de sensores de hardware do Apple Silicon M4 (10-core CPU, 10-core Metal GPU, 24 GB UMA), motor de validação estatística de Poisson e relatórios acadêmicos finais comparando duas arquiteturas contrastantes de orquestração de agentes autônomos de IA:
1. **PicoClaw v0.3.1 (Sipeed):** Binário nativo Mach-O ARM64 compilado estaticamente em Go 1.23.2, com goroutines concorrentes leves e coletor de lixo tri-color não-geracional.
2. **OpenClaw v2026.10.7:** Orquestrador corporativo modular em TypeScript/Node.js v26.12.1 executando sobre a Google V8, com validação dinâmica de esquemas via TypeBox e persistência nativa `node:sqlite`.

Ambos os agentes comunicam-se via loopback (`127.0.0.1:8080`) com a mesma instância neural local alimentada por **llama.cpp (build b11887 Metal GPU)** servindo **Meta Llama-3.2-3B-Instruct (GGUF Q4_K_M)** sob decodificação gulosa determinística (`temperature = 0.0`, `seed = 42`), eliminando estocasticidade neural da avaliação do runtime.

### English (EN-US)
This repository hosts the complete experimental testbed, reproducible codebase, hardware power telemetry on Apple Silicon M4 (10-core CPU, 10-core GPU Metal, 24 GB UMA), Poisson statistical validation engine, and academic reports comparing two contrasting AI agent architectures:
1. **PicoClaw v0.3.1 (Sipeed):** Statically compiled Mach-O ARM64 native Go 1.23.2 binary leveraging concurrent goroutines and lightweight tri-color mark-sweep garbage collection.
2. **OpenClaw v2026.10.7:** Enterprise-grade TypeScript agent orchestrator executing atop Node.js v26.12.1 (Google V8), dynamic TypeBox schema validation, and native `node:sqlite` session state storage.

Both orchestrators interface with a unified local neural server via **llama.cpp (b11887 Metal GPU)** serving **Meta Llama-3.2-3B-Instruct (Q4_K_M)** under greedy deterministic decoding (`temperature = 0.0`, `seed = 42`), strictly isolating agent orchestrator performance from neural inference variance.

---

## ❓ Pergunta de Pesquisa / Research Question

### 🇧🇷 Português (PT-BR)
> **"Qual arquitetura de orquestrador de IA — Go nativo (PicoClaw) ou Node.js (OpenClaw) — entrega menor latência, menor consumo de memória RAM e maior eficiência energética no Apple Silicon M4 sob o mesmo modelo neural local?"**

### 🇺🇸 English (EN-US)
> **"Which AI agent architecture — native Go (PicoClaw) or Node.js (OpenClaw) — delivers lower latency, minimal RAM footprint, and higher energy efficiency on Apple Silicon M4 under an identical local neural model?"**

---

## 🚀 Mini Tutorial Passo a Passo com Fotos e Datasets / Step-by-Step Mini Tutorial

### 🇧🇷 Versão em Português: Como Entender, Usar os Datasets e Executar em 3 Minutos

#### 1. A Analogia Central (O Carro e os Dois Motoristas)
* **O Motor:** É o modelo de IA da Meta (**Llama-3.2-3B**). Ele pensa e gera as palavras.
* **O Suporte do Motor:** É o **`llama.cpp`**, que liga o modelo diretamente na GPU Metal de 10 núcleos do Mac mini M4.
* **Os Dois Motoristas (Agentes):**
  * **OpenClaw (Node.js):** Carrega uma mochila pesada com 54 ferramentas e precisa de um tradutor simultâneo (a máquina virtual V8). Rico em recursos, porém consome muita RAM e energia.
  * **PicoClaw (Go):** Um atleta minimalista. Fala o código binário nativo ARM64 do Mac, não precisa de tradutor e só carrega o que vai usar.
* **A Pergunta:** Quando ambos usam exatamente a mesma IA, qual agente é mais rápido, gasta menos RAM e consome menos energia da máquina?

#### 2. Os Datasets em `data/workload_data/`: Para que servem e como são usados?
Para que o teste não seja apenas "conversa teórica", os agentes precisam executar tarefas reais de computação. Os dados para essas tarefas ficam na pasta [`data/workload_data/`](data/workload_data/):
* **`mock_files/` (50 arquivos sintéticos):** Utilizado nos testes **W2** e **W4**. O agente usa a ferramenta `list_dir` para inspecionar, contar e ler metadados desses arquivos em disco.
* **`system_logs.jsonl` (750 linhas de log JSON):** Utilizado nos testes **W2** e **W4**. O agente usa a ferramenta `grep_logs` para buscar erros graves (`CRITICAL`/`ERROR`) e depois a ferramenta `calc_stats` para calcular médias e desvios de latência.
* **`rag_chunks_10k.json` (10.000 fragmentos de texto) e `embedding_head_100k.npz` (matriz de projeção de 384 dimensões):** Utilizados no teste **W3 (Vector RAG)**. O agente carrega esses 10.000 documentos em memória e calcula similaridade de cosseno ponderada para encontrar os 5 textos mais relevantes para a consulta do usuário.

> **Nota de Execução:** Se você quiser inspecionar ou recriar esses dados do zero, execute:
> ```bash
> ./tools/.venv/bin/python benchmark/generate_datasets.py
> ```

#### 3. Passo a Passo Visual de Execução

##### Passo 1: Inicialização do Servidor Neural Metal GPU (`llama-server`)
O servidor neural carrega o modelo Llama-3.2-3B na memória unificada (UMA) e aloca os pesos na GPU Metal do Mac mini:
```bash
./tools/llama_cpp/llama-b11887/llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```
![Passo 1: Servidor Neural llama.cpp Metal GPU](screenshots/print_screen_01_llama_server.png)

##### Passo 2: Verificação e Inspeção dos Datasets dos Workloads
Antes de rodar os agentes, inspecionamos os arquivos de entrada em `data/workload_data/`:
```bash
ls -lh data/workload_data/
head -n 5 data/workload_data/system_logs.jsonl
```
![Passo 2: Verificação dos Datasets de Carga](screenshots/print_screen_07_datasets_workload.png)

##### Passo 3: Execução Física dos Agentes nos Workloads W1 a W4
Os orquestradores executam as chamadas em tempo real contra o servidor local e os datasets:
```bash
# Executa a bateria de testes ao vivo
./tools/.venv/bin/python benchmark/run_live_campaign.py campaign_run_6 ./campaign_run_6
```
![Passo 3: Execução Física em Tempo Real](screenshots/print_screen_04_live_execution.png)

##### Passo 4: Medição Estatística de Cold-Start com Hyperfine
Cronometramos o tempo exato que cada agente leva para iniciar do zero usando 30 repetições com aquecimento:
```bash
./tools/hyperfine/hyperfine --warmup 5 --runs 30 \
  "./tools/picoclaw/picoclaw --version" \
  "./tools/node/bin/node ./benchmark/openclaw_orch.mjs --version"
```
![Passo 4: Medição de Cold-Start](screenshots/print_screen_02_hyperfine.png)

##### Passo 5: Validação Estatística de Poisson (Assertividade $\ge 90{,}3\%$)
Validamos a taxa de chegada de requisições de ferramentas sob distribuição de Poisson com intervalos exatos de Garwood:
```bash
./tools/.venv/bin/python benchmark/poisson_sampling_validation.py
```
![Passo 5: Motor Estatístico de Poisson](screenshots/print_screen_05_poisson_engine.png)

##### Passo 6: Monitoramento de Energia e Modo Anti-Sono
Garantimos quiescência do sistema e lemos a potência física (mW) consumida por CPU, GPU e memória:
```bash
# Mantém o Mac acordado durante todo o experimento
/usr/bin/caffeinate -dims &
# Amostra a telemetria do chip M4 a cada 100ms
sudo powermetrics -i 100 -n 10 --samplers cpu_power,gpu_power
```
![Passo 6: Telemetria de Hardware e Modo Anti-Sono](screenshots/print_screen_03_powermetrics.png)

##### Passo 7: Análise dos Gráficos de Reprodutibilidade
Abrimos os gráficos consolidados de todas as 5 campanhas físicas:
```bash
open figures/fig8_three_campaigns_reproducibility.png
```
![Passo 7: Reprodutibilidade Multi-Campanhas](figures/fig8_three_campaigns_reproducibility.png)

---

### 🇺🇸 English Version: How to Understand, Use Datasets, and Run in 3 Minutes

#### 1. Core Metaphor (The Engine and the Two Drivers)
* **The Engine:** Meta's local **Llama-3.2-3B** model generating token logits.
* **The Engine Mount:** **`llama.cpp`** running bare-metal on the 10-core Apple Metal GPU.
* **The Two Drivers (Agent Orchestrators):**
  * **OpenClaw (Node.js):** Carries 54 tool schemas and requires the Google V8 JIT interpreter. Highly modular but incurs dynamic typing and GC pause overhead.
  * **PicoClaw (Go):** Pure compiled ARM64 assembly with zero interpreter overhead and static typing.
* **The Research Question:** Under identical neural serving, which runtime architecture achieves higher throughput, lower latency, and reduced energy-delay product?

#### 2. The Datasets in `data/workload_data/`: Purpose and Utilization
To ensure realistic, grounded evaluation beyond plain conversational queries, orchestrators interact with deterministic datasets stored in [`data/workload_data/`](data/workload_data/):
* **`mock_files/` (50 synthetic files):** Consumed in **W2** and **W4**. The agent calls `list_dir` to inspect disk files, count entries, and parse metadata.
* **`system_logs.jsonl` (750 structured JSON log records):** Consumed in **W2** and **W4**. The agent calls `grep_logs` to filter severe error events (`CRITICAL`/`ERROR`) and subsequently invokes `calc_stats` to compute rolling latency metrics.
* **`rag_chunks_10k.json` (10,000 document chunks) & `embedding_head_100k.npz` (384-dimensional dense projection matrix):** Consumed in **W3 (Vector RAG)**. The orchestrator embeds candidate documents in RAM and performs cosine similarity search to retrieve the top-5 relevant chunks.

> **Execution Note:** To inspect or regenerate these datasets deterministically:
> ```bash
> ./tools/.venv/bin/python benchmark/generate_datasets.py
> ```

#### 3. Visual Step-by-Step Execution Guide

##### Step 1: Launch Local Metal GPU Neural Server (`llama-server`)
```bash
./tools/llama_cpp/llama-b11887/llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```
![Step 1: llama.cpp Metal GPU Neural Server](screenshots/print_screen_01_llama_server.png)

##### Step 2: Inspect Workload Datasets
Verify the deterministic files that drive W2, W3, and W4:
```bash
ls -lh data/workload_data/
head -n 5 data/workload_data/system_logs.jsonl
```
![Step 2: Inspecting Workload Datasets](screenshots/print_screen_07_datasets_workload.png)

##### Step 3: Execute Live Physical Test Campaign
```bash
./tools/.venv/bin/python benchmark/run_live_campaign.py campaign_run_6 ./campaign_run_6
```
![Step 3: Live Campaign Execution](screenshots/print_screen_04_live_execution.png)

##### Step 4: Measure Cold-Start Launch Latency with Hyperfine
```bash
./tools/hyperfine/hyperfine --warmup 5 --runs 30 \
  "./tools/picoclaw/picoclaw --version" \
  "./tools/node/bin/node ./benchmark/openclaw_orch.mjs --version"
```
![Step 4: Hyperfine Cold Start Benchmark](screenshots/print_screen_02_hyperfine.png)

##### Step 5: Validate Poisson Statistical Engine
```bash
./tools/.venv/bin/python benchmark/poisson_sampling_validation.py
```
![Step 5: Poisson Sampling Validation](screenshots/print_screen_05_poisson_engine.png)

##### Step 6: Power Telemetry & System Quiescence Protocol
```bash
/usr/bin/caffeinate -dims &
sudo powermetrics -i 100 -n 10 --samplers cpu_power,gpu_power
```
![Step 6: Power Telemetry & Quiescence](screenshots/print_screen_03_powermetrics.png)

##### Step 7: Multi-Campaign Statistical Reproducibility Inspection
```bash
open figures/fig8_three_campaigns_reproducibility.png
```
![Step 7: Multi-Campaign Reproducibility](figures/fig8_three_campaigns_reproducibility.png)

---

## 🎯 Conclusão Prática e Trade-Offs / Conclusion & Architectural Trade-Offs

### 🇧🇷 Conclusão e Prós e Contras (Português)

Os ensaios empíricos no Apple Silicon M4 demonstram de forma inequívoca que a arquitetura do orquestrador é o fator determinante de contenção de memória, agilidade de disparo e eficiência térmica.

#### 1. PicoClaw (Go 1.23.2 — Binário Nativo Mach-O ARM64)
* **✅ Prós:**
  * **Cold-Start Instantâneo ($23{,}4\times$ mais rápido):** Inicializa em **$9{,}63\text{ ms}$** vs. $225{,}55\text{ ms}$ do Node.js. Excelente para execuções sob demanda e CLI.
  * **Consumo de Memória Mínimo ($13\times$ menos RAM):** Ocupa apenas **$14\text{ MB}$ em repouso e $33{,}8\text{ MB}$ no loop ReAct de 10 passos**, não competindo pela largura de banda da UMA do Mac.
  * **Vazão Superior de Ferramentas ($5\times$ mais rápido):** Processa **$326\text{ ops/s}$** via serialização estática em Go sem sobrecarga de validação dinâmica.
  * **Menor Produto Energia-Atraso (EDP):** Entrega **$24{,}4\%$ menor EDP em W1** ($31{,}62\text{ J}\cdot\text{s}$ vs. $41{,}48\text{ J}\cdot\text{s}$).
  * **Previsibilidade Operacional:** Coletor de lixo tri-color concorrente não causa pausas perceptíveis (*Stop-The-World* $< 1\text{ ms}$).
* **❌ Contras:**
  * **Ecossistema Menor:** Quantidade menor de conectores prontos se comparado ao ecossistema NPM do JavaScript.
  * **Rigidez de Tipagem:** Adicionar novas ferramentas exige compilar a estrutura em Go, sem flexibilidade de injeção dinâmica de código.
  * **Foco em Dispositivos Edge:** Projetado primariamente para embarcados e serviços de fundo, oferecendo menos integrações diretas com interfaces gráficas.

#### 2. OpenClaw (Node.js v26.12.1 / TypeScript — Google V8 Engine)
* **✅ Prós:**
  * **Ecossistema Massivo:** Acesso imediato a centenas de milhares de pacotes do NPM e integrações com bancos corporativos.
  * **Flexibilidade Dinâmica:** Validação de esquemas em tempo de execução via TypeBox sem necessidade de recompilação binária.
  * **Arquitetura Modular Corporativa:** Persistência de sessão em SQLite embutido e suporte nativo a WebSockets e HTTP.
* **❌ Contras:**
  * **Consumo Elevado de RAM ($166\text{ a }448\text{ MB}$):** Exige $13\times$ mais memória DRAM, disputando barramento com a GPU Metal.
  * **Cold-Start Lento ($225\text{ ms}$):** O tempo de inicialização da máquina virtual V8 e resolução de pacotes introduz atraso perceptível.
  * **Vulnerável ao "Prompt Token Bloat":** De fábrica, injeta 54 ferramentas (16.369 tokens), estourando contextos de 4.096 tokens e forçando 57 segundos extras de decodificação na GPU Metal (> 500 Joules adicionais).
  * **Pressão de GC em Loops Longos:** No loop ReAct (W4), alocações contínuas de objetos na memória jovem acionam coletas de lixo *Mark-Compact*, degradando a fluidez do event loop.

#### 🎯 Veredito Prático de Engenharia:
* **Escolha o PicoClaw (Go):** Se o objetivo for rodar agentes de IA em segundo plano 24/7 no Mac mini, laptops com 16 GB de RAM, ambientes de borda (*Edge computing*), ou quando latência de resposta e contenção de memória forem prioridades absolutas.
* **Escolha o OpenClaw (Node.js):** Se o projeto exigir integrações imediatas com pacotes NPM específicos em servidores dedicados com $\ge 32\text{ GB}$ de RAM, sendo indispensável aplicar uma camada de poda de esquemas (*Tool Pruning*) para conter o inchaço de tokens.

---

### 🇺🇸 Conclusion & Architectural Trade-Offs (English)

Physical empirical trials confirm that agent runtime architecture is a primary driver of performance, memory stability, and energy efficiency on Apple Silicon M4.

#### 1. PicoClaw (Go 1.23.2 — Mach-O ARM64 Native Static Binary)
* **✅ Pros:**
  * **Instantaneous Cold-Start ($23.4\times$ faster):** Launches in **$9.63\text{ ms}$** vs. $225.55\text{ ms}$ for Node.js. Ideal for serverless and on-demand dispatches.
  * **Compact Memory Footprint ($13\times$ less RAM):** Retains only **$14\text{ MB}$ idle and $33.8\text{ MB}$ under peak 10-turn ReAct load**, eliminating UMA bus contention.
  * **High Tool Throughput ($5\times$ higher):** Delivers **$326\text{ ops/s}$** via compiled static serialization without dynamic validation penalty.
  * **Energy-Delay Efficiency:** Achieves **$24.4\%$ lower EDP in W1** ($31.62\text{ J}\cdot\text{s}$ vs. $41.48\text{ J}\cdot\text{s}$).
  * **Deterministic Concurrency:** Non-generational tri-color mark-sweep collector eliminates perceptible GC stop-the-world pauses.
* **❌ Cons:**
  * **Smaller Package Ecosystem:** Smaller library registry compared to NPM.
  * **Static Rigidity:** Adding tools requires static struct definition and binary recompilation.
  * **Edge-Centric Design:** Built primarily for edge and embedded appliances, offering fewer out-of-the-box GUI bridges.

#### 2. OpenClaw (Node.js v26.12.1 / TypeScript — Google V8 Engine)
* **✅ Pros:**
  * **Extensive NPM Ecosystem:** Direct access to hundreds of thousands of established enterprise packages and connectors.
  * **Dynamic Schema Flexibility:** Runtime schema validation via TypeBox without requiring code compilation.
  * **Enterprise Desktop Integration:** Built-in SQLite state management and mature HTTP/WebSocket gateways.
* **❌ Cons:**
  * **Heavy Memory Overhead ($166\text{ to }448\text{ MB}$):** Consumes $13\times$ more DRAM, contending with the Metal GPU for 120 GB/s unified memory bandwidth.
  * **Sluggish Cold-Start ($225\text{ ms}$):** JIT warm-up and deep `node_modules` dependency resolution introduce noticeable startup latency.
  * **Prompt Token Bloat:** Unconstrained stock CLI injects 54 tool schemas (16,369 tokens), crashing 4k context windows and burning >500 extra Joules on prolonged GPU prefill.
  * **Generational GC Pressure:** Multi-turn ReAct loops trigger major *Mark-Compact* GC sweeps, intermittently stalling the `libuv` event loop.

#### 🎯 Practical Engineering Recommendation:
* **Deploy PicoClaw (Go):** For 24/7 background AI assistants, edge appliances, memory-constrained hosts ($\le 16\text{ GB}$ UMA), and ultra-low latency tool orchestration.
* **Deploy OpenClaw (Node.js):** For enterprise workflow servers with $\ge 32\text{ GB}$ DRAM where rapid integration with diverse NPM modules outweighs bare-metal memory and energy efficiency, provided tool schemas are strictly pruned.

---

## 📁 Descrição Detalhada de Todas as Pastas e Diretórios / Exhaustive Directory Breakdown

Abaixo está o detalhamento completo de cada pasta do repositório, sua finalidade técnica e o papel desempenhado na pesquisa:

### 🇧🇷 Detalhamento das Pastas (Português)

| Diretório | O que esta pasta faz e para que serve? |
| :--- | :--- |
| **`benchmark/`** | **Núcleo de Execução e Orquestração dos Testes:** Contém os dois agentes instrumentados (`picoclaw_orch.go` e `openclaw_orch.mjs`), o executor da campanha física em tempo real (`run_live_campaign.py`), o motor estatístico de Poisson (`poisson_sampling_validation.py`), os geradores de gráficos científicos (`generate_charts.py`), relatórios acadêmicos (`build_reports.py`) e datasets determinísticos (`generate_datasets.py`). |
| **`campaign_run_1/`** | **Campanha 1 (Baseline Fatorial Completo):** Armazena os dados brutos de 480 testes fatoriais completos (10 repetições $\times$ 4 workloads $\times$ 2 agentes $\times$ variações de contexto e poda) acompanhados de telemetria completa dos sensores de hardware do chip M4 via `powermetrics`. |
| **`campaign_run_2/`** | **Campanha 2 (Segunda Bateria Física Independente):** Execução independente das rodadas de validação contra o servidor neural na GPU Metal, gerando logs brutos de tempo de execução, uso de memória RSS e vazão de ferramentas para comprovação de invariância. |
| **`campaign_run_3/`** | **Campanha 3 (Terceira Bateria Física Independente):** Terceira replicação física integral, coletando dados de latência e consumo de recursos sob as mesmas condições térmicas e elétricas. |
| **`campaign_run_4/`** | **Campanha 4 (Quarta Bateria Física Independente):** Quarta replicação física para verificação cruzada de reprodutibilidade e garantia de estabilidade temporal. |
| **`campaign_run_5/`** | **Campanha 5 (Quinta Bateria Física com Validação de Poisson):** Execução física de alta intensidade com $K=300$ chamadas de ferramentas, demonstrando assertividade de Poisson entre $90{,}33\%$ e $93{,}84\%$. |
| **`campaign_comparison/`** | **Análise Comparativa Multi-Campanhas:** Reúne os relatórios consolidados (`CAMPAIGN_COMPARISON.md` e `CAMPAIGN_COMPARISON_EN.md`) e os dados estruturados (`multi_campaigns_comparison.json`) que provam matematicamente variabilidade menor que $2{,}5\%$ ($\text{CV} < 2{,}5\%$) e equivalência estatística (ANOVA $p > 0{,}15$). |
| **`data/`** | **Dados Experimentais e Assinaturas Criptográficas:** Guarda os arquivos JSONL consolidados (`consolidated_trials.jsonl`), o log bruto de sensores de energia (`powermetrics_sensors.log`) e o manifesto criptográfico de integridade (`manifest_sha256.json`) contendo o hash SHA-256 de todos os arquivos. |
| **`data/workload_data/`** | **Datasets de Carga Determinística:** Contém os dados consumidos pelos agentes durante a execução: `mock_files/` (50 arquivos para W2/W4), `system_logs.jsonl` (750 linhas de log para W2/W4), `rag_chunks_10k.json` (10.000 textos para W3) e `embedding_head_100k.npz` (matriz de projeção de 384d para busca vetorial). |
| **`docs/`** | **Documentação Acadêmica Bilíngue:** Contém 11 pares de documentos formais (em Português e Inglês), cobrindo metodologia estatística, arquitetura de hardware, guia passo a passo, FAQ para a banca examinadora, registro formal dos 9 ajustes técnicos, prova de condições idênticas e a justificativa arquitetural completa de todas as bibliotecas e ferramentas utilizadas ([`10_TECNOLOGIAS_BIBLIOTECAS_E_FERRAMENTAS_PT.md`](docs/10_TECNOLOGIAS_BIBLIOTECAS_E_FERRAMENTAS_PT.md) / [`10_TECHNOLOGIES_LIBRARIES_AND_TOOLS_EN.md`](docs/10_TECHNOLOGIES_LIBRARIES_AND_TOOLS_EN.md)). |
| **`figures/`** | **Figuras Científicas em Alta Resolução (300 DPI):** Gráficos prontos para publicação científica gerados a partir dos dados reais coletados (Figuras 1 a 8), cobrindo latência, memória RAM, eficiência energética (EDP), vazão de ferramentas, validação de Poisson e reprodutibilidade multi-campanhas. |
| **`reports/`** | **Relatórios Acadêmicos Oficiais:** Documentos finais formatados e submetidos à UFABC nos formatos `.docx` e `.pdf`, incluindo o Relatório de Teste de Sistemas (*System Testing*), o Plano de Trabalho e o Guia Explicativo do Aluno. |
| **`screenshots/`** | **Evidências Visuais do Terminal (Prints Reais):** Sete capturas de tela reais realizadas diretamente no Mac mini M4, comprovando visualmente a execução de cada ferramenta (`llama-server`, `hyperfine`, `powermetrics`, `caffeinate`, etc.) e dos datasets de entrada. |
| **`tools/`** | **Toolchain Portátil e Ferramentas Embarcadas:** Contém o instalador automático `setup_environment.sh`, o binário do Sipeed PicoClaw, o servidor `llama_cpp`, o cronômetro estatístico `hyperfine`, o instalador Python `uv` e os metadados do pacote Node.js do OpenClaw. |

---

### 🇺🇸 Directory Breakdown (English)

| Directory | What does this folder do and what is its purpose? |
| :--- | :--- |
| **`benchmark/`** | **Core Test Execution and Orchestration Engine:** Houses both instrumented agent orchestrators (`picoclaw_orch.go` and `openclaw_orch.mjs`), the live physical runner (`run_live_campaign.py`), the Poisson validation engine (`poisson_sampling_validation.py`), scientific chart builders (`generate_charts.py`), report generators (`build_reports.py`), and dataset generators (`generate_datasets.py`). |
| **`campaign_run_1/`** | **Campaign 1 (Full Factorial Baseline):** Stores raw telemetry from 480 full factorial trials (10 replicates $\times$ 4 workloads $\times$ 2 agents $\times$ context/pruning variations) combined with raw Apple M4 hardware sensor telemetry sampled via `powermetrics`. |
| **`campaign_run_2/`** | **Campaign 2 (Second Independent Physical Run):** Second independent hardware execution run against the live Metal GPU neural server, capturing execution times, RSS memory curves, and tool throughput. |
| **`campaign_run_3/`** | **Campaign 3 (Third Independent Physical Run):** Third full physical replication, recording latency and resource consumption under identical thermal and electrical conditions. |
| **`campaign_run_4/`** | **Campaign 4 (Fourth Independent Physical Run):** Fourth physical replication validating cross-campaign reproducibility and temporal stability. |
| **`campaign_run_5/`** | **Campaign 5 (Fifth Physical Run with Poisson Validation):** High-intensity run featuring $K=300$ tool calls, demonstrating Poisson assertiveness between $90.33\%$ and $93.84\%$. |
| **`campaign_comparison/`** | **Cross-Campaign Comparative Analysis:** Aggregates consolidated reports (`CAMPAIGN_COMPARISON.md` and `CAMPAIGN_COMPARISON_EN.md`) and structured JSON data (`multi_campaigns_comparison.json`) proving cross-run variability below $2.5\%$ ($\text{CV} < 2.5\%$) and statistical equivalence (ANOVA $p > 0.15$). |
| **`data/`** | **Experimental Datasets and Cryptographic Signatures:** Houses consolidated trial logs (`consolidated_trials.jsonl`), raw SMC power logs (`powermetrics_sensors.log`), and the cryptographic integrity manifest (`manifest_sha256.json`) containing SHA-256 signatures for every tracked file. |
| **`data/workload_data/`** | **Deterministic Workload Datasets:** Stores input files consumed by orchestrators during benchmark runs: `mock_files/` (50 files for W2/W4), `system_logs.jsonl` (750 JSON records for W2/W4), `rag_chunks_10k.json` (10,000 texts for W3), and `embedding_head_100k.npz` (384-dimensional dense projection matrix for vector RAG). |
| **`docs/`** | **Bilingual Academic Documentation:** Features 11 paired formal documentation files (Portuguese and English) covering statistical methodology, hardware architecture, step-by-step reproduction, defense examination FAQ, formal record of the 9 corrective adjustments, equalized test conditions guarantee, and the exhaustive justification of all tools and libraries ([`10_TECNOLOGIAS_BIBLIOTECAS_E_FERRAMENTAS_PT.md`](docs/10_TECNOLOGIAS_BIBLIOTECAS_E_FERRAMENTAS_PT.md) / [`10_TECHNOLOGIES_LIBRARIES_AND_TOOLS_EN.md`](docs/10_TECHNOLOGIES_LIBRARIES_AND_TOOLS_EN.md)). |
| **`figures/`** | **Publication-Ready Figures (300 DPI):** High-resolution vector/raster figures (Figures 1 to 8) generated from physical trials, covering latency, RAM footprint, energy-delay product (EDP), tool throughput, Poisson sampling, and multi-campaign reproducibility. |
| **`reports/`** | **Official Academic Reports:** Final documents submitted to UFABC in `.docx` and `.pdf` formats, including the System Testing Report, the Work Plan, and the Plain-English Student Defense Guide. |
| **`screenshots/`** | **Real Terminal Proofs (Screenshots):** Seven authentic terminal captures recorded directly on the Apple Silicon M4 host, visually validating every underlying tool (`llama-server`, `hyperfine`, `powermetrics`, `caffeinate`, etc.) and workload dataset. |
| **`tools/`** | **Self-Contained Embedded Toolchain:** Contains the 1-click installer `setup_environment.sh`, Sipeed PicoClaw binary, `llama_cpp` Metal server, `hyperfine` statistical stopwatch, Astral `uv` installer, and OpenClaw runtime package metadata. |

---

## 📖 Glossário de Termos Técnicos e Acadêmicos / Comprehensive Technical Glossary

| Termo / Term | Definição em Português (PT-BR) | English Definition (EN-US) |
| :--- | :--- | :--- |
| **UMA (Unified Memory Architecture)** | Arquitetura de memória do Apple Silicon onde CPU, GPU e Neural Engine compartilham o mesmo espaço de endereçamento físico e barramento de alta velocidade (120 GB/s no M4), eliminando cópias PCIe mas sujeita a contenção quando múltiplos processos alocam DRAM simultaneamente. | Apple Silicon memory architecture where CPU, GPU, and Neural Engine share a unified physical address space and high-speed memory bus (120 GB/s on M4), avoiding PCIe copies but introducing contention under heavy concurrent allocations. |
| **Cold Start Launch Latency** | Tempo decorrido desde o disparo do processo pelo sistema operacional até a conclusão de sua inicialização e prontidão para receber comandos, medido estatisticamente via `hyperfine`. | Time elapsed from OS process fork/exec until runtime initialization is complete and ready to handle commands, statistically benchmarked via `hyperfine`. |
| **RSS (Resident Set Size)** | Quantidade exata de memória RAM física alocada pelo processo e mapeada na tabela de páginas do sistema operacional (excluindo memória paginada em disco swap). | Exact amount of physical RAM allocated to a process and currently held in the operating system page table (excluding paged-out swap memory). |
| **Google V8 Engine** | Máquina virtual de execução de JavaScript e WebAssembly desenvolvida pelo Google, utilizada pelo Node.js para compilar código dinamicamente (JIT) em linguagem de máquina. | Google's open-source high-performance JavaScript and WebAssembly engine, utilized by Node.js to JIT-compile source code into native machine instructions. |
| **Goroutines & M:N Scheduler** | Threads leves de espaço de usuário gerenciadas pelo runtime de Go sobre uma quantidade $M$ de threads do sistema operacional em $N$ núcleos físicos, com custo de alocação de apenas ~2 KB por pilha. | Lightweight user-space execution threads multiplexed by Go's runtime scheduler over $M$ OS threads across $N$ physical cores, requiring only ~2 KB of stack space upon spawn. |
| **Tri-color Mark-Sweep GC** | Coletor de lixo não-geracional e concorrente do Go que divide ponteiros em cores (branco, cinza e preto), executando coletas em paralelo com a aplicação e com pausas inferiores a 1 milissegundo. | Go's non-generational concurrent garbage collector that colors heap pointers (white, grey, black), running sweeps in parallel with application logic and limiting STW pauses to sub-millisecond durations. |
| **Generational GC (Mark-Compact)** | Coletor de lixo do Node.js (V8) que divide a memória em geração jovem (*New Space*) e velha (*Old Space*), exigindo compactação periódica que pode interromper temporariamente a execução do *event loop*. | V8 garbage collection strategy partitioning heap memory into nursery (New Space) and tenured (Old Space), periodically performing Mark-Compact cycles that pause the `libuv` event loop. |
| **Poisson Assertiveness** | Métrica estatística que avalia se a frequência empírica de eventos por unidade de tempo se enquadra dentro do intervalo de confiança fiducial de Garwood para um processo estocástico de Poisson com confiança $\ge 90\%$. | Statistical compliance metric determining whether empirical event arrivals fall within Garwood's exact fiducial confidence interval for a Poisson stochastic process at $\ge 90\%$ confidence. |
| **Cameron & Trivedi Test** | Teste formal de regressão que avalia se a variância dos dados excede a média (superdispersão ou sobredispersão), confirmando a adequação de um modelo de contagem de Poisson ($t$-stat $< 1{,}96$). | Formal regression-based diagnostic test checking whether sample variance equals sample mean (detecting overdispersion or underdispersion) to confirm Poisson validity ($t$-stat $< 1.96$). |
| **Deterministic Greedy Decoding** | Estratégia de geração neural onde o modelo de linguagem sempre seleciona o token de maior probabilidade absoluta (`temperature = 0.0`), eliminando qualquer variação estocástica entre rodadas. | Language model decoding policy selecting the single most probable token at each step (`temperature = 0.0`), eliminating all stochastic variance between experimental runs. |
| **EDP (Energy-Delay Product)** | Métrica combinada de eficiência de hardware ($E \times D$), obtida multiplicando a energia total dissipada em Joules pelo tempo total de execução em segundos ($\text{J}\cdot\text{s}$), penalizando severamente sistemas lentos. | Hardware efficiency metric calculated as total dissipated energy (Joules) multiplied by total elapsed execution time (seconds) ($\text{J}\cdot\text{s}$), heavily penalizing slow architectures. |
| **Metal Shaders / llama.cpp GPU** | Código especializado compilado em Apple Metal Shading Language que executa tensores e multiplicações de matrizes diretamente nos 10 núcleos da GPU do Mac mini M4. | Specialized compute kernels compiled in Apple Metal Shading Language that execute matrix multiplications and tensor operations directly on the M4 10-core GPU. |
| **Tool Pruning** | Prática de engenharia de software que remove esquemas de ferramentas desnecessárias do prompt inicial do agente, evitando inchaço de contexto (*prompt token bloat*) e consumo excessivo de energia na GPU. | Software engineering technique filtering out unused tool definitions from the agent's system prompt, mitigating token bloat and preventing massive GPU prefill overhead. |
| **ReAct Loop (Reason + Act)** | Paradigma de orquestração autônoma onde o agente de IA alterna continuamente entre raciocínio verbalizado (*Thought*), disparo de ferramenta externa (*Action*) e inspeção de retorno (*Observation*). | Autonomous agent framework where the model iteratively cycles between explicit verbal reasoning (*Thought*), external tool execution (*Action*), and sensory inspection (*Observation*). |
| **Vector RAG (Cosine Similarity)** | Técnica de recuperação de informação onde fragmentos de texto são mapeados em vetores densos e ranqueados calculando o cosseno do ângulo entre a consulta e os documentos armazenados. | Information retrieval paradigm where textual documents are projected into dense vector spaces and ranked based on the cosine angle between query and document vectors. |
| **Powermetrics & Apple SMC** | Ferramenta nativa do macOS para amostragem dos sensores analógicos e digitais integrados no chip Apple Silicon via controlador de gerenciamento do sistema (SMC), medindo consumo real de energia em miliwatts. | Apple's hardware diagnostics utility reading on-die voltage and current sensors via the System Management Controller (SMC), reporting real-time power dissipation in milliwatts. |
| **Caffeinate Quiescence Protocol** | Protocolo operacional que executa `/usr/bin/caffeinate -dims` e suspende a indexação do Spotlight (`mdutil`) para impedir que o sistema operacional entre em repouso térmico ou execute tarefas concorrentes de fundo. | Operational testbed setup running `/usr/bin/caffeinate -dims` and pausing Spotlight (`mdutil`) to prevent OS sleep, thermal throttling, or background disk indexing during empirical trials. |
| **Mach-O ARM64 Binary** | Formato binário nativo executável dos sistemas operacionais da Apple para a arquitetura de processadores ARM de 64 bits (Apple Silicon), sem camadas intermediárias de interpretação. | Apple's native binary executable file format targeting 64-bit ARM architectures (Apple Silicon), executing directly on the processor without intermediate emulation or runtime interpreters. |
| **SciPy & NumPy (Inferência Científica)** | Bibliotecas de computação científica em Python empregadas no *Test Harness* para calcular quantis exatos de Qui-Quadrado ($\chi^2$), intervalos fiduciais de Poisson (Garwood, 1936), regressão de Cameron & Trivedi, ANOVA One-Way e álgebra matricial de projeção vetorial no Workload W3 (RAG). Consulte [`docs/10_TECNOLOGIAS_BIBLIOTECAS_E_FERRAMENTAS_PT.md`](docs/10_TECNOLOGIAS_BIBLIOTECAS_E_FERRAMENTAS_PT.md). | Scientific computing Python libraries powering the test harness to evaluate exact Chi-Square ($\chi^2$) quantiles, Garwood (1936) Poisson fiducial limits, Cameron & Trivedi dispersion tests, One-Way ANOVA, and vector similarity projection in W3 (RAG). See [`docs/10_TECHNOLOGIES_LIBRARIES_AND_TOOLS_EN.md`](docs/10_TECHNOLOGIES_LIBRARIES_AND_TOOLS_EN.md). |
| **Matplotlib & Python-docx (Publicação Acadêmica)** | Bibliotecas responsáveis pela compilação programática de relatórios nos padrões formais da ABNT/UFABC (`python-docx`) e renderização em 300 DPI das figuras científicas com notação matemática LaTeX (`matplotlib`). Consulte [`docs/10_TECNOLOGIAS_BIBLIOTECAS_E_FERRAMENTAS_PT.md`](docs/10_TECNOLOGIAS_BIBLIOTECAS_E_FERRAMENTAS_PT.md). | Python publishing libraries responsible for programmatic compilation of formal ABNT/UFABC academic reports (`python-docx`) and 300-DPI publication figures with LaTeX mathematical notation (`matplotlib`). See [`docs/10_TECHNOLOGIES_LIBRARIES_AND_TOOLS_EN.md`](docs/10_TECHNOLOGIES_LIBRARIES_AND_TOOLS_EN.md). |
| **Dulwich & Astral uv (Portabilidade e Isolamento)** | O `dulwich` é uma implementação pura em Python do protocolo Git para commits e push SSH sem acionar os diálogos gráficos do Xcode CLT no macOS; o `uv` é um gerenciador de pacotes em Rust que provisiona o ambiente virtual isolado em segundos sem poluir o sistema hospedeiro. Consulte [`docs/10_TECNOLOGIAS_BIBLIOTECAS_E_FERRAMENTAS_PT.md`](docs/10_TECNOLOGIAS_BIBLIOTECAS_E_FERRAMENTAS_PT.md). | `dulwich` is a pure-Python Git client implementation enabling commits and SSH pushes without triggering Xcode CLT macOS prompts; `uv` is a Rust-based environment manager provisioning isolated virtual environments in seconds. See [`docs/10_TECHNOLOGIES_LIBRARIES_AND_TOOLS_EN.md`](docs/10_TECHNOLOGIES_LIBRARIES_AND_TOOLS_EN.md). |

---

## 🔒 Integridade Criptográfica e Conformidade Metodológica

Em estrita observância às diretrizes da UFABC e de avaliação de sistemas (Raj Jain, 1991):
1. **Manifesto SHA-256:** Todos os arquivos do repositório possuem assinaturas calculadas em [`data/manifest_sha256.json`](data/manifest_sha256.json).
2. **Garantia de Condições Idênticas:** Nenhum ajuste oportunista foi aplicado em rodadas isoladas. Os 9 ajustes descritos em [`docs/08_REGISTRO_DE_AJUSTES_E_DESVIOS.md`](docs/08_REGISTRO_DE_AJUSTES_E_DESVIOS.md) e [`docs/09_EQUALIZED_TEST_CONDITIONS_GUARANTEE_PT.md`](docs/09_EQUALIZED_TEST_CONDITIONS_GUARANTEE_PT.md) foram aplicados uniformemente a todas as 5 campanhas físicas.
3. **Supervisão do Autor:** Todos os testes físicos, medições e interpretações estatísticas foram realizados e supervisionados pelo pesquisador **Rafael Paniccia Cassetta (RA: 21202520618)**.

---

## 📚 Referências Bibliográficas

1. **Jain, R. (1991).** *The Art of Computer Systems Performance Analysis: Techniques for Experimental Design, Measurement, Simulation, and Modeling.* John Wiley & Sons.
2. **Lilja, D. J. (2000).** *Measuring Computer Performance: A Practitioner's Guide.* Cambridge University Press.
3. **Garwood, F. (1936).** *Fiducial Limits for the Poisson Distribution.* Biometrika, 28(3/4), 437–442.
4. **Cameron, A. C., & Trivedi, P. K. (1990).** *Regression-based tests for overdispersion in the Poisson model.* Journal of Econometrics, 46(3), 347–364.
5. **Sipeed. (2026).** *PicoClaw: Ultra-lightweight Edge AI Agent Framework (v0.3.1).* Mach-O ARM64 binary distribution.
6. **Steinberger, P., & OpenClaw Foundation. (2026).** *OpenClaw Autonomous Personal Assistant (v2026.10.7).* NPM package distribution.
