# Guia Didático e Tutorial Visual Passo a Passo / Beginner's Walkthrough & Visual Proofs

[![Platform](https://img.shields.io/badge/Platform-Apple%20Silicon%20M4-purple.svg)](https://www.apple.com/)
[![Bilingual](https://img.shields.io/badge/Language-PT--BR%20%7C%20EN--US-blue.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-black.svg)](../LICENSE)

---

## 🇧🇷 Português (PT-BR): Como Entender e Reproduzir em 3 Minutos

Este guia didático foi elaborado para estudantes, pesquisadores e engenheiros que desejam compreender a essência do benchmark sem atrito técnico imediato, acompanhando cada etapa com os registros visuais autênticos do terminal no Apple Silicon M4.

---

### 1. A Analogia Central: O Carro e os Dois Motoristas

Para compreender este experimento em 30 segundos, imagine um veículo de corrida:
* **O Motor do Carro:** É o modelo de Inteligência Artificial da Meta (**Llama-3.2 de 3 bilhões de parâmetros**). Ele processa a linguagem e gera as palavras.
* **O Suporte do Motor:** É o **`llama.cpp`**, que conecta esse motor diretamente à placa de vídeo Metal de 10 núcleos do Mac mini M4.
* **Os Dois Motoristas (Orquestradores de Agentes):**
  1. **OpenClaw (Node.js / TypeScript):** Carrega uma mochila pesada contendo 54 esquemas de ferramentas corporativas e necessita de um tradutor simultâneo (a máquina virtual Google V8) para se comunicar com o processador. É flexível e modular, mas consome muita memória RAM e energia térmica.
  2. **PicoClaw (Go):** Um atleta minimalista compilado estaticamente. Fala a linguagem nativa ARM64 do Mac mini, não necessita de interpretador e consome memória mínima.

**A Pergunta de Pesquisa:** Sob o mesmo motor neural local idêntico, qual motorista completa a tarefa com menor latência, menor consumo de memória RAM e maior eficiência energética?

---

### 2. O Papel dos Datasets em `data/workload_data/`

Para que as medições não se limitassem a diálogos puramente sintéticos, os agentes realizam operações reais de computação sobre arquivos em disco:
* **`mock_files/` (50 arquivos):** Consumido nos testes **W2** e **W4**. O agente executa a ferramenta `list_dir` para inspecionar, contar e ler metadados de arquivos.
* **`system_logs.jsonl` (750 registros JSON):** Consumido nos testes **W2** e **W4**. O agente usa a ferramenta `grep_logs` para buscar erros graves (`CRITICAL`/`ERROR`) e depois a ferramenta `calc_stats` para calcular médias e desvios de latência do barramento UMA.
* **`rag_chunks_10k.json` e `embedding_head_100k.npz`:** Consumidos no teste **W3 (Vector RAG)**. O agente carrega esses documentos em memória e calcula similaridade de cosseno ponderada de 384 dimensões para ranquear os textos semanticamente mais próximos.

---

### 3. Passo a Passo Visual com Evidências de Terminal

#### Passo 1: Inicialização do Servidor Neural Metal GPU (`llama-server`)
O servidor neural aloca os tensores do Llama-3.2-3B na memória unificada (UMA) e carrega os shaders na GPU Metal do Mac mini:
```bash
./tools/llama_cpp/llama-b11887/llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```
![Passo 1: Servidor Neural llama.cpp Metal GPU](assets/screenshots/step01_llama_metal_server.png)
*Legenda Técnica:* Inicialização do `llama-server` (b11887) no Apple M4 (`Mac16,10`). Observa-se a alocação de 3.21 bilhões de parâmetros (1,92 GiB em Q4_K_M) diretamente na DRAM compartilhada e prontidão do endpoint HTTP loopback em 347 ms.

---

#### Passo 2: Verificação e Validação dos Datasets dos Workloads
Antes de iniciar os testes, inspeciona-se a integridade física dos datasets determinísticos:
```bash
ls -lh data/workload_data/
head -n 5 data/workload_data/system_logs.jsonl
```
![Passo 2: Verificação dos Datasets de Carga](assets/screenshots/step07_workload_datasets.png)
*Legenda Técnica:* Inspeção dos 50 arquivos sintéticos, do log estruturado de 750 linhas APFS e dos pesos de projeção vetorial em float32 (`embedding_head_100k.npz`).

---

#### Passo 3: Execução Física dos Agentes em Tempo Real
Os orquestradores executam os testes fatoriais W1 a W4 contra o servidor neural:
```bash
./tools/.venv/bin/python benchmark/run_unified_benchmark.py
```
![Passo 3: Execução Física em Tempo Real](assets/screenshots/step04_live_execution.png)
*Legenda Técnica:* Traces em tempo real mostrando a latência de tarefa ($T_{\text{task}}$), tempo de inferência neural ($T_{\text{neural}}$), overhead do runtime ($T_{\text{orch}}$) e consumo de memória RAM residente (RSS).

---

#### Passo 4: Medição Estatística de Cold-Start com Hyperfine
Cronometragem com precisão nanométrica do tempo de disparo a frio (30 repetições):
```bash
./tools/hyperfine/hyperfine --warmup 5 --runs 30 \
  "./tools/picoclaw/picoclaw --version" \
  "./tools/node/bin/node ./benchmark/openclaw_orch.mjs --version"
```
![Passo 4: Medição de Cold-Start com Hyperfine](assets/screenshots/step02_hyperfine_coldstart.png)
*Legenda Técnica:* PicoClaw (Go nativo) inicializa em **$9{,}63\text{ ms}$**, enquanto OpenClaw (Node.js/V8) exige **$225{,}55\text{ ms}$**, comprovando vantagem de inicialização de **$23{,}4\times$** a favor do Go.

---

#### Passo 5: Validação Estatística de Poisson e Intervalos de Garwood
Validação da distribuição estocástica de chegadas de ferramentas ($K=300$):
```bash
./tools/.venv/bin/python benchmark/poisson_sampling_validation.py
```
![Passo 5: Motor Estatístico de Poisson](assets/screenshots/step05_poisson_engine.png)
*Legenda Técnica:* Cálculo dos limites fiduciais exatos de Garwood (1936) via distribuição Qui-Quadrado ($\chi^2$), alcançando assertividade nominal $\ge 90{,}33\%$ e aceitação da hipótese de equidispersão de Cameron & Trivedi ($t < 1{,}96$).

---

#### Passo 6: Telemetria de Hardware e Modo Anti-Sono (Caffeinate)
Amostragem dos sensores de potência física do silício M4 via SMC:
```bash
/usr/bin/caffeinate -dims &
sudo powermetrics -i 100 -n 10 --samplers cpu_power,gpu_power
```
![Passo 6: Telemetria de Hardware via powermetrics](assets/screenshots/step03_powermetrics_telemetry.png)
*Legenda Técnica:* Leitura em tempo real dos shunts elétricos do Apple M4 SoC revelando dissipação de **12,6 W na GPU Metal** e **2,8 W na CPU** sob carga de geração de tokens.

---

#### Passo 7: Garantia de Quiescência Operacional do macOS
```bash
./scripts/check_quiescence.sh
```
![Passo 7: Verificação de Quiescência](assets/screenshots/step06_caffeinate_quiescence.png)
*Legenda Técnica:* Auditoria do daemon `caffeinate -dims` prevenindo repouso de sistema, display e disco durante as rodadas de medição.

---

## 🇺🇸 English (EN-US): How to Understand and Reproduce in 3 Minutes

This walkthrough is tailored for students, researchers, and engineers seeking an intuitive yet technically precise understanding of the benchmark, supported by authentic terminal screenshots recorded on Apple Silicon M4.

---

### 1. The Core Metaphor: The Car and the Two Drivers

To grasp this research benchmark in 30 seconds, imagine a racecar:
* **The Engine:** Meta's local **Llama-3.2 (3-billion parameter)** model generating tokens and reasoning.
* **The Engine Mount:** **`llama.cpp`**, connecting the neural weights directly to Apple Silicon M4's 10-core Metal GPU.
* **The Two Drivers (Agent Orchestrators):**
  1. **OpenClaw (Node.js / TypeScript):** A driver carrying an enterprise backpack filled with 54 tool schemas, requiring Google V8's live JIT interpreter to talk to the hardware. Highly flexible, but incurs elevated RAM and thermal dissipation.
  2. **PicoClaw (Go):** A compiled minimalist athlete speaking native Mach-O ARM64 machine code with zero interpreter overhead.

**The Research Question:** Under an identical local neural serving baseline, which runtime architecture achieves lower latency, reduced RAM footprint, and superior energy efficiency?

---

### 2. Workload Datasets in `data/workload_data/`

To ground evaluation in realistic operating system activity beyond conversational queries, agents process deterministic datasets:
* **`mock_files/` (50 files):** Evaluated in **W2** and **W4**. The agent calls `list_dir` to inspect disk files, parse attributes, and verify permissions.
* **`system_logs.jsonl` (750 JSON records):** Evaluated in **W2** and **W4**. The agent calls `grep_logs` to filter severe error entries and invokes `calc_stats` to compute rolling latency metrics.
* **`rag_chunks_10k.json` & `embedding_head_100k.npz`:** Evaluated in **W3 (Vector RAG)**. The agent performs in-memory 384-dimensional cosine similarity ranking across 10,000 document text chunks.

---

### 3. Step-by-Step Visual Walkthrough with Terminal Proofs

#### Step 1: Launch Local Metal GPU Neural Server (`llama-server`)
```bash
./tools/llama_cpp/llama-b11887/llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```
![Step 1: llama.cpp Metal GPU Neural Server](assets/screenshots/step01_llama_metal_server.png)
*Technical Caption:* Initialization of `llama-server` (build b11887) on Apple M4 (`Mac16,10`), allocating 3.21B parameters (1.92 GiB in Q4_K_M) across Unified Memory Architecture (UMA) in 347 ms.

---

#### Step 2: Inspect Workload Datasets
```bash
ls -lh data/workload_data/
head -n 5 data/workload_data/system_logs.jsonl
```
![Step 2: Inspecting Workload Datasets](assets/screenshots/step07_workload_datasets.png)
*Technical Caption:* Inspection of 50 mock files, 750 APFS structured JSON log lines, and dense float32 projection matrix (`embedding_head_100k.npz`).

---

#### Step 3: Run Master Live Benchmark Campaign
```bash
./tools/.venv/bin/python benchmark/run_unified_benchmark.py
```
![Step 3: Live Benchmark Execution](assets/screenshots/step04_live_execution.png)
*Technical Caption:* Real-time execution traces capturing task latency ($T_{\text{task}}$), neural serving time ($T_{\text{neural}}$), runtime overhead ($T_{\text{orch}}$), and Resident Set Size (RSS).

---

#### Step 4: Measure Cold-Start Launch Latency with Hyperfine
```bash
./tools/hyperfine/hyperfine --warmup 5 --runs 30 \
  "./tools/picoclaw/picoclaw --version" \
  "./tools/node/bin/node ./benchmark/openclaw_orch.mjs --version"
```
![Step 4: Hyperfine Cold Start Benchmark](assets/screenshots/step02_hyperfine_coldstart.png)
*Technical Caption:* Hyperfine statistical benchmarking proving PicoClaw launches in **$9.63\text{ ms}$** vs. OpenClaw's **$225.55\text{ ms}$** ($23.4\times$ speedup).

---

#### Step 5: Poisson Sampling Engine & Garwood Fiducial Intervals
```bash
./tools/.venv/bin/python benchmark/poisson_sampling_validation.py
```
![Step 5: Poisson Sampling Validation](assets/screenshots/step05_poisson_engine.png)
*Technical Caption:* Exact Garwood (1936) Chi-Square fiducial limits confirming $\ge 90.33\%$ Poisson empirical assertiveness and Cameron & Trivedi equidispersion ($t < 1.96$).

---

#### Step 6: Power Telemetry & System Quiescence Protocol
```bash
/usr/bin/caffeinate -dims &
sudo powermetrics -i 100 -n 10 --samplers cpu_power,gpu_power
```
![Step 6: Hardware Power Telemetry via powermetrics](assets/screenshots/step03_powermetrics_telemetry.png)
*Technical Caption:* Real-time Apple M4 SoC power rail telemetry sampling via SMC, indicating **12.6 W Metal GPU** and **2.8 W CPU** power draw during token generation.

---

#### Step 7: System Quiescence Pre-Flight Check
```bash
./scripts/check_quiescence.sh
```
![Step 7: Pre-Flight Quiescence Check](assets/screenshots/step06_caffeinate_quiescence.png)
*Technical Caption:* Verification of `caffeinate -dims` assertion preventing system, display, and disk sleep during benchmark runs.
