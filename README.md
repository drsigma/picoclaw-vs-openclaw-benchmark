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

## 🚀 Mini Tutorial Passo a Passo / Step-by-Step Mini Tutorial

### 🇧🇷 Versão em Português: Como Entender e Executar em 3 Minutos

#### 1. A Analogia Central (O Carro e os Dois Motoristas)
* **O Motor:** É o modelo de IA da Meta (**Llama-3.2-3B**). Ele pensa e gera as palavras.
* **O Suporte do Motor:** É o **`llama.cpp`**, que liga o modelo diretamente na GPU Metal de 10 núcleos do Mac mini M4.
* **Os Dois Motoristas (Agentes):**
  * **OpenClaw (Node.js):** Carrega uma mochila pesada com 54 ferramentas e precisa de um tradutor simultâneo (a máquina virtual V8). Rico em recursos, porém consome muita RAM e energia.
  * **PicoClaw (Go):** Um atleta minimalista. Fala o código binário nativo ARM64 do Mac, não precisa de tradutor e só carrega o que vai usar.
* **A Pergunta:** Quando ambos usam exatamente a mesma IA, qual agente é mais rápido, gasta menos RAM e consome menos energia da máquina?

#### 2. Como Reproduzir os Testes na Sua Máquina
```bash
# 1. Clonar e entrar no repositório
git clone git@github.com:drsigma/picoclaw-vs-openclaw-benchmark.git
cd picoclaw-vs-openclaw-benchmark

# 2. Configurar o ambiente em 1 clique (provisiona Python, Node.js e ferramentas embarcadas)
./tools/setup_environment.sh

# 3. Verificar integridade criptográfica SHA-256 de todos os arquivos
./tools/.venv/bin/python -c '
import json, hashlib, os
m = json.load(open("data/manifest_sha256.json"))
ok = sum(1 for p, meta in m.items() if os.path.exists(p) and hashlib.sha256(open(p, "rb").read()).hexdigest() == meta["sha256"])
print(f"Verificação Concluída: {ok}/{len(m)} arquivos íntegros (0 falhas).")
'

# 4. Executar o motor estatístico de Poisson (Assertividade >= 90%)
./tools/.venv/bin/python benchmark/poisson_sampling_validation.py

# 5. Executar uma nova bateria física completa na GPU Metal
./tools/.venv/bin/python benchmark/run_live_campaign.py campaign_run_6 ./campaign_run_6

# 6. Visualizar o gráfico comparativo das 5 campanhas
open figures/fig8_three_campaigns_reproducibility.png
```

---

### 🇺🇸 English Version: How to Understand and Run in 3 Minutes

#### 1. Core Metaphor (The Engine and the Two Drivers)
* **The Engine:** Meta's local **Llama-3.2-3B** model generating token logits.
* **The Engine Mount:** **`llama.cpp`** running bare-metal on the 10-core Apple Metal GPU.
* **The Two Drivers (Agent Orchestrators):**
  * **OpenClaw (Node.js):** Carries 54 tool schemas and requires the Google V8 JIT interpreter. Highly modular but incurs dynamic typing and GC pause overhead.
  * **PicoClaw (Go):** Pure compiled ARM64 assembly with zero interpreter overhead and static typing.
* **The Research Question:** Under identical neural serving, which runtime architecture achieves higher throughput, lower latency, and reduced energy-delay product?

#### 2. How to Replicate Locally
```bash
# 1. Clone and enter repository
git clone git@github.com:drsigma/picoclaw-vs-openclaw-benchmark.git
cd picoclaw-vs-openclaw-benchmark

# 2. Automated 1-click testbed setup (provisions Python, Node.js, and embedded tools)
./tools/setup_environment.sh

# 3. Validate SHA-256 cryptographic signatures
./tools/.venv/bin/python -c '
import json, hashlib, os
m = json.load(open("data/manifest_sha256.json"))
ok = sum(1 for p, meta in m.items() if os.path.exists(p) and hashlib.sha256(open(p, "rb").read()).hexdigest() == meta["sha256"])
print(f"Verified {ok}/{len(m)} files matching SHA-256 signatures.")
'

# 4. Run Poisson validation engine
./tools/.venv/bin/python benchmark/poisson_sampling_validation.py

# 5. Open multi-campaign reproducibility chart
open figures/fig8_three_campaigns_reproducibility.png
```

---

## 📖 Glossário Bilíngue de Termos / Bilingual Technical Glossary

| Termo / Technical Term | Definição em Português (PT-BR) | Formal Definition in English (EN-US) |
| :--- | :--- | :--- |
| **PicoClaw** | Agente de IA minimalista desenvolvido pela Sipeed compilado em Go nativo Mach-O ARM64. | Ultra-lightweight edge AI agent framework written in Go, compiled to native Mach-O ARM64. |
| **OpenClaw** | Orquestrador corporativo em TypeScript/Node.js com validação TypeBox e banco SQLite. | Extensible AI agent runtime executing on Node.js/V8 with TypeBox schema parsing and SQLite. |
| **UMA (Unified Memory)** | Arquitetura de Memória Unificada da Apple compartilhada a 120 GB/s entre CPU e Metal GPU. | Unified Memory Architecture on Apple Silicon sharing 120 GB/s LPDDR5X DRAM across CPU and GPU. |
| **Cold Start ($T_{\text{cold}}$)** | Tempo desde a chamada `execve()` até o processo carregar módulos e emitir a primeira saída. | Time elapsed from `execve()` process spawn until first output token or CLI help emission. |
| **RSS (Resident Set Size)** | Quantidade física real de memória DRAM ocupada pelo processo na memória principal. | Actual physical DRAM allocated to the process page table, excluding swapped or virtual memory. |
| **TTFT (Time-to-First-Token)** | Latência desde o envio do prompt até o modelo neural emitir o primeiro token decodificado. | Latency from prompt ingestion until the neural serving engine emits its initial response token. |
| **ITL (Inter-Token Latency)** | Tempo médio em milissegundos entre emissões sucessivas de tokens autoregressivos. | Mean duration (ms) between consecutive auto-regressive token generation steps. |
| **$T_{\text{orch}}$** | Sobrecarga pura de computação do agente de software ($T_{\text{task}} - T_{\text{neural}}$). | Net orchestrator runtime latency isolating agent overhead from neural forward inference. |
| **EDP (Energy-Delay Product)** | Métrica que pondera energia e tempo ao quadrado ($E \times T$), penalizando lentidão. | Performance-energy trade-off metric ($E \times T$) heavily penalizing slow system latencies. |
| **Garwood Exact CI** | Método exato via distribuição $\chi^2$ (Garwood, 1936) para intervalos de confiança de Poisson. | Exact confidence interval for Poisson event rates based on the Chi-Square distribution. |
| **Overdispersion Test** | Teste de Cameron & Trivedi (1990) que confirma se $\text{Variância} = \text{Média}$ no processo Poisson. | Cameron & Trivedi (1990) regression test verifying absence of overdispersion ($\text{Var} = \text{Mean}$). |
| **caffeinate** | Utilitário do macOS que impede suspensão de tela, disco e repouso ocioso da CPU. | Native macOS daemon preventing idle CPU sleep, display power-down, and disk spin-down. |

---

## 📊 Principais Resultados Empíricos / Key Benchmark Findings

| Dimensão Avaliada / Metric | PicoClaw (Go 1.23.2) | OpenClaw (Node.js 26.12.1) | Vantagem / Ratio | Significância Estatística |
| :--- | :---: | :---: | :---: | :---: |
| **Inicialização a Frio ($T_{\text{cold}}$)** | **$9{,}63 \pm 0{,}22\text{ ms}$** | $225{,}55 \pm 16{,}06\text{ ms}$ | **$23{,}42\times$ mais rápido** | $t = 30{,}12, \; p < 10^{-23}$ |
| **Memória RAM Ociosa (Idle RSS)** | **$14{,}02 \pm 0{,}13\text{ MB}$** | $166{,}10 \pm 0{,}50\text{ MB}$ | **$11{,}85\times$ menos RAM** | $t = 59{,}44, \; p < 10^{-35}$ |
| **Pico de RAM (W4 10-Turn ReAct)** | **$33{,}83 \pm 0{,}34\text{ MB}$** | $448{,}33 \pm 3{,}95\text{ MB}$ | **$13{,}25\times$ menos RAM** | $t = 61{,}20, \; p < 10^{-47}$ |
| **Instruções de Hardware Aposentadas** | **$155{,}84\text{ M}$** | $4.650{,}08\text{ M}$ | **$29{,}84\times$ menos instruções** | $t = 82{,}15, \; p < 10^{-40}$ |
| **Vazão de Ferramentas ($R_{\text{tool}}$)** | **$326{,}39\text{ ops/s}$** | $64{,}30\text{ ops/s}$ | **$5{,}08\times$ maior vazão** | $z = 19{,}92, \; p < 10^{-15}$ |
| **Energy-Delay Product (EDP - W1)** | **$31{,}62\text{ J}\cdot\text{s}$** | $41{,}48\text{ J}\cdot\text{s}$ | **$24{,}4\%\text{ menor EDP}$** | $t = 11{,}45, \; p < 10^{-13}$ |
| **Tamanho do Prompt de Fábrica (CLI)** | **$4.657\text{ tokens}$** | $16.369\text{ tokens}$ | **$3{,}51\times$ menor prompt** | Estoura limite de 4.096 |

---

## 🎯 Amostragem de Poisson e Assertividade ($\ge 90\%$ a $93{,}8\%$)

Em estrita conformidade com a teoria clássica de filas e sistemas (Raj Jain, 1991), o acionamento de ferramentas foi modelado como um **Processo Pontual de Poisson**:
* **Tier W2 ($K = 300$ eventos, $n = 100$ repetições):** Assertividade de **$90{,}33\%$** (erro relativo $d \le 9{,}67\%$, $\text{IC}_{90\%}: [296{,}03, 359{,}13]\text{ ops/s}$).
* **Tier W4 ($K = 1.000$ eventos, $n = 100$ repetições):** Assertividade de **$93{,}75\%$** (erro relativo $d \le 6{,}25\%$, $\text{IC}_{95\%}: [209{,}70, 237{,}61]\text{ ops/s}$).
* **Teste de Sobredispersão:** Estatística $z = 0{,}00, \; p = 1{,}00$, confirmando equidispersão estrita ($\text{Var} = \text{Média}$).

![Poisson Assertiveness](figures/fig7_poisson_assertiveness.png)

---

## 🔬 Validação Cruzada das 5 Campanhas Físicas (Reprodutibilidade 100%)

Conduzimos **5 campanhas físicas independentes** na máquina real com repouso suprimido via `caffeinate -dims`:
* **[Campanha 1 (Baseline)](campaign_run_1):** 480 testes fatoriais paramétricos + calibração de sensores SMC de potência.
* **[Campanha 2 (Live Run 1)](campaign_run_2):** Bateria física independente ao vivo na GPU Metal.
* **[Campanha 3 (Live Run 2)](campaign_run_3):** Segunda repetição física ao vivo.
* **[Campanha 4 (Live Run 3)](campaign_run_4):** Terceira repetição física ao vivo.
* **[Campanha 5 (Live Run 4)](campaign_run_5):** Quarta repetição física ao vivo ($K=300$ eventos de Poisson).

O relatório comparativo consolidado está disponível em:
* [Relatório Comparativo em Português](campaign_comparison/CAMPAIGN_COMPARISON.md)
* [Cross-Campaign Report in English](campaign_comparison/CAMPAIGN_COMPARISON_EN.md)

![Multi-Campaign Reproducibility](figures/fig8_three_campaigns_reproducibility.png)

---

## ⚖️ Conclusão Metodológica com Prós e Contras / Conclusion & Trade-Offs

### 🇧🇷 Conclusão e Análise de Engenharia (Português)

Os experimentos físicos demonstram conclusivamente que a arquitetura do orquestrador de software **não é um detalhe de implementação secundário**, mas sim um fator determinante na responsividade, viabilidade térmica e consumo de recursos no Apple Silicon M4.

#### 1. PicoClaw (Go 1.23.2 — Binário Nativo Mach-O ARM64)
* **✅ Prós (Vantagens):**
  * **Inicialização Instantânea ($23{,}4\times$ mais rápido):** Média de apenas **$9{,}63\text{ ms}$** contra $225{,}55\text{ ms}$ do Node.js. Excelente para invocação sob demanda e funções serverless locais.
  * **Pegada de Memória Mínima ($13\times$ menos RAM):** Consome apenas **$14\text{ MB}$ em repouso e $33{,}8\text{ MB}$ em pico (W4)**. Não sobrecarrega a DRAM unificada nem disputa o barramento UMA com a GPU Metal.
  * **Alta Vazão de Ferramentas ($5\times$ superior):** Atinge **$326\text{ ops/s}$**, serializando estruturas e despachando chamadas em microssegundos com zero overhead de tipagem dinâmica.
  * **Eficiência no Energy-Delay Product (EDP):** Vantagem de **$24{,}4\%$ no W1** ($31{,}62\text{ J}\cdot\text{s}$ vs. $41{,}48\text{ J}\cdot\text{s}$), penalizando severamente atrasos de computação.
  * **Imunidade a Pausas GC:** Coletor concorrente tri-color não-geracional mantém latência determinística sem pausas perceptíveis.
* **❌ Contras (Limitações):**
  * **Ecossistema Menor de Extensões:** Menor disponibilidade de bibliotecas de terceiros se comparado à amplitude do ecossistema NPM.
  * **Rigidez de Compilação:** Novas ferramentas exigem tipagem estática e compilação do binário (não permite carregar módulos JavaScript avulsos em tempo de execução).
  * **Foco em Edge/Embarcados:** Projetado pela Sipeed para dispositivos compactos, possuindo menos integrações nativas de interface gráfica de fábrica.

#### 2. OpenClaw (Node.js v26.12.1 / TypeScript — Runtime Google V8)
* **✅ Prós (Vantagens):**
  * **Ecossistema Gigantesco (NPM):** Acesso a centenas de milhares de bibliotecas prontas para banco de dados, integrações de APIs e provedores de nuvem.
  * **Flexibilidade e Dinamismo:** Esquemas de ferramentas flexíveis validados em tempo real com TypeBox sem necessidade de recompilação.
  * **Arquitetura Rica para Desktop:** Suporte nativo a SQLite (`node:sqlite`), gateways REST/WebSocket e ecossistema de automação corporativa maduro.
* **❌ Contras (Limitações):**
  * **Consumo de Memória Massivo ($166\text{ a }448\text{ MB}$):** Ocupa até $13\times$ mais memória DRAM física, aumentando a pressão no barramento UMA de 120 GB/s.
  * **Lentidão de Cold-Start ($225\text{ ms}$):** O custo de inicialização da V8 e varredura de árvores profundas em `node_modules` penaliza execuções efêmeras.
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

## 📸 Registros Visuais do Terminal (Screenshots)

Na pasta [`screenshots/`](screenshots/) estão registradas as evidências em tempo real no Apple Silicon M4:
1. [`print_screen_01_llama_server.png`](screenshots/print_screen_01_llama_server.png): Servidor Metal GPU alocado na DRAM, carregamento em 347 ms e healthcheck `{"status":"ok"}`.
2. [`print_screen_02_hyperfine.png`](screenshots/print_screen_02_hyperfine.png): Medição estatística de cold-start comprovando vantagem de $23{,}4\times$ do PicoClaw.
3. [`print_screen_03_powermetrics.png`](screenshots/print_screen_03_powermetrics.png): Leituras dos sensores de corrente/tensão do chip Apple M4 via SMC (`powermetrics`).
4. [`print_screen_04_live_execution.png`](screenshots/print_screen_04_live_execution.png): Execução física em tempo real dos workloads W1 a W4.
5. [`print_screen_05_poisson_engine.png`](screenshots/print_screen_05_poisson_engine.png): Motor analítico de Poisson com intervalos exatos de Garwood e assertividade $\ge 90\%$.
6. [`print_screen_06_caffeinate_quiescence.png`](screenshots/print_screen_06_caffeinate_quiescence.png): Quiescência do sistema operacional via `caffeinate -dims` e pausa do Spotlight.

---

## 📂 Estrutura de Pastas e Documentação Bilíngue

```text
picoclaw-vs-openclaw-benchmark/
├── README.md                                  <- Este documento mestre com mini tutorial e glossário
├── docs/                                      <- Documentação acadêmica formal (100% Bilíngue)
│   ├── 00_GUIA_PRATICO_INTRODUTORIO_PT.md     <- Guia Prático Introdutório (Português)
│   ├── 00_PRACTICAL_INTRODUCTORY_GUIDE_EN.md  <- Practical Introductory Guide (English)
│   ├── 01_GLOSSARIO_PT.md                     <- Glossário Técnico Completo (Português)
│   ├── 02_GLOSSARY_EN.md                      <- Formal Technical Glossary (English)
│   ├── 03_METODOLOGIA_ESTATISTICA_POISSON.md  <- Provas do modelo de Poisson e assertividade (PT)
│   ├── 03_POISSON_STATISTICAL_METHODOLOGY_EN.md <- Poisson statistical proofs & sizing (EN)
│   ├── 04_HARDWARE_TELEMETRY_TERMINAL_OUTPUTS.md <- Telemetria de terminal e registradores PMC (PT)
│   ├── 04_HARDWARE_TELEMETRY_TERMINAL_OUTPUTS_EN.md <- Terminal telemetry & PMC registers (EN)
│   ├── 05_GUIA_REPRODUCAO_PASSO_A_PASSO.md    <- Guia passo a passo de reprodução local (PT)
│   ├── 05_STEP_BY_STEP_REPRODUCTION_GUIDE_EN.md <- Step-by-step reproduction guide (EN)
│   ├── 06_ACADEMIC_DEFENSE_FAQ.md             <- Perguntas e Respostas da Banca Examinadora (PT)
│   ├── 06_ACADEMIC_DEFENSE_FAQ_EN.md          <- Academic Defense FAQ & Qualis A Reviewers (EN)
│   ├── 07_PRINTS_PASSO_A_PASSO.md             <- Demonstração detalhada de cada screenshot (PT)
│   ├── 07_STEP_BY_STEP_SCREENSHOTS_EN.md      <- Detailed demonstration of each screenshot (EN)
│   ├── 08_REGISTRO_DE_AJUSTES_E_DESVIOS.md    <- Registro dos 9 ajustes metodológicos globais (PT)
│   ├── 08_ADJUSTMENTS_AND_CORRECTIVE_ACTIONS_EN.md <- Formal record of 9 adjustments (EN)
│   ├── 09_EQUALIZED_TEST_CONDITIONS_GUARANTEE_PT.md <- Prova formal de condições equalizadas (PT)
│   └── 09_EQUALIZED_TEST_CONDITIONS_GUARANTEE_EN.md <- Formal guarantee of equalized conditions (EN)
├── tools/                                     <- Ferramentas embarcadas e provisionador automático
│   ├── setup_environment.sh                   <- Script de inicialização automática em 1 clique
│   ├── picoclaw/                              <- Binário oficial Sipeed PicoClaw (Mach-O ARM64)
│   ├── llama_cpp/                             <- Servidor llama-server com Metal GPU shaders
│   ├── hyperfine/                             <- Binário hyperfine para medição de cold start
│   ├── uv/                                    <- Instalador Astral uv standalone
│   ├── openclaw-package.json                  <- Metadados oficiais de runtime do OpenClaw
│   └── node/                                  <- Runtime Node.js provisionado (darwin-arm64)
├── screenshots/                               <- Capturas reais das ferramentas no terminal
├── campaign_run_1/                            <- Campanha 1: Baseline 480 testes + telemetria SMC
├── campaign_run_2/                            <- Campanha 2: Segunda bateria física na GPU Metal
├── campaign_run_3/                            <- Campanha 3: Terceira bateria física na GPU Metal
├── campaign_run_4/                            <- Campanha 4: Quarta bateria física na GPU Metal
├── campaign_run_5/                            <- Campanha 5: Quinta bateria física ($K=300$ Poisson)
├── campaign_comparison/                       <- Relatórios e gráficos comparativos das 5 campanhas
├── benchmark/                                 <- Orquestradores Go e Node.js e scripts de automação
├── data/                                      <- Dados brutos JSONL, powermetrics e manifest SHA-256
│   ├── workload_data/                         <- Datasets determinísticos (50 mocks, log JSONL e RAG)
│   └── manifest_sha256.json                   <- Assinatura criptográfica SHA-256 de todos os arquivos
├── figures/                                   <- Figuras científicas em 300 DPI (Figuras 1 a 8)
└── reports/                                   <- Relatórios acadêmicos formatados (.docx e .pdf)
```

---

## 🔒 Integridade Criptográfica e Conformidade Metodológica

Em estrita observância às diretrizes da UFABC e de avaliação de sistemas (Raj Jain, 1991):
1. **Manifesto SHA-256:** Todos os 80 arquivos do repositório possuem assinaturas calculadas em [`data/manifest_sha256.json`](data/manifest_sha256.json).
2. **Garantia de Condições Idênticas:** Nenhum ajuste oportunista foi aplicado em rodadas isoladas. Os 9 ajustes descritos em [`docs/08_REGISTRO_DE_AJUSTES_E_DESVIOS.md`](docs/08_REGISTRO_DE_AJUSTES_E_DESVIOS.md) foram aplicados uniformemente a todas as 5 campanhas físicas.
3. **Supervisão do Autor:** Todos os testes físicos, medições e interpretações estatísticas foram realizados e supervisionados pelo pesquisador **Rafael Paniccia Cassetta (RA: 21202520618)**.

---

## 📚 Referências Bibliográficas

1. **Jain, R. (1991).** *The Art of Computer Systems Performance Analysis: Techniques for Experimental Design, Measurement, Simulation, and Modeling.* John Wiley & Sons.
2. **Lilja, D. J. (2000).** *Measuring Computer Performance: A Practitioner's Guide.* Cambridge University Press.
3. **Garwood, F. (1936).** *Fiducial Limits for the Poisson Distribution.* Biometrika, 28(3/4), 437–442.
4. **Cameron, A. C., & Trivedi, P. K. (1990).** *Regression-based tests for overdispersion in the Poisson model.* Journal of Econometrics, 46(3), 347–364.
5. **Sipeed. (2026).** *PicoClaw: Ultra-lightweight Edge AI Agent Framework (v0.3.1).* Mach-O ARM64 binary distribution.
6. **Steinberger, P., & OpenClaw Foundation. (2026).** *OpenClaw Autonomous Personal Assistant (v2026.10.7).* NPM package distribution.
