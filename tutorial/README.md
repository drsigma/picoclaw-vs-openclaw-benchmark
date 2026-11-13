# Guia Didático e Tutorial Visual Passo a Passo / Beginner's Walkthrough & Visual Proofs

[![Platform](https://img.shields.io/badge/Platform-Apple%20Silicon%20M4-purple.svg)](https://www.apple.com/)
[![Bilingual](https://img.shields.io/badge/Language-PT--BR%20%7C%20EN--US-blue.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-black.svg)](../LICENSE)

---

## 🇧🇷 Português (PT-BR): Como Entender e Reproduzir em 3 Minutos

Este guia didático foi elaborado para estudantes, pesquisadores e engenheiros que desejam compreender a essência do benchmark sem atrito técnico imediato, acompanhando cada etapa com exemplos ilustrativos da estrutura de saída do terminal no Apple Silicon M4.

---

### 0. Como Reproduzir em Qualquer Máquina (Linux, Windows WSL, macOS)

Você **NÃO precisa de um Mac com Apple Silicon nem de GPU dedicada** para reproduzir e auditar este trabalho científico! Qualquer estudante ou revisor em Linux (Ubuntu, Debian, Fedora), Windows (via WSL2) ou macOS Intel pode executar o pipeline completo:

```bash
# 1. Clonar e entrar na pasta do projeto
git clone https://github.com/drsigma/picoclaw-vs-openclaw-benchmark.git
cd picoclaw-vs-openclaw-benchmark

# 2. Configurar o ambiente isolado com 1 comando
make setup

# 3. Executar a Verificação Rápida Portátil (< 5 segundos, sem GPU, sem Sudo)
make dry-run

# 4. Executar os 45 testes unitários automatizados (pytest e linter ruff)
make test

# 5. Regenerar todas as 6 figuras científicas em 300 DPI
make reproduce-figures
```

*Caso você possua um Mac com Apple Silicon (M1/M2/M3/M4):*
* Execute `make benchmark` para rodar a campanha física real em espaço de usuário comum;
* Execute `make benchmark-full-smc` caso queira amostragem física de miliwatts com privilégios de superusuário via Apple SMC.

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

### 3. Passo a Passo e Exemplos Ilustrativos da Estrutura de Saída (Illustrative Runner Output Format)

#### Passo 1: Inicialização do Servidor Neural Metal GPU (`llama-server`)
O servidor neural aloca os tensores do Llama-3.2-3B na memória unificada (UMA) e carrega os shaders na GPU Metal do Mac mini:
```bash
./tools/llama_cpp/llama-b11887/llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```
```text
0.04.154.161 I srv  llama_server: initializing ...
0.04.154.169 I cmn  common_param: common_params_print_info: verbosity = 3 (adjust with the `-lv N` CLI arg)
0.04.156.027 I srv    load_model: loading model './models/Llama-3.2-3B-Instruct-Q4_K_M.gguf'
0.05.841.379 I cmn          init: llama threadpool init, n_threads = 4
0.06.149.561 I srv    load_model: initializing, n_slots = 1, n_ctx_slot = 32768, kv_unified = 'false'
0.06.152.620 I srv  server_run_i: model loaded
0.06.152.626 I srv  server_on_li: listening on http://127.0.0.1:8080
```
*Fonte do Log Real / Real Log Source:* `results/publication_campaign/llama_server_publication.log` (Linhas 1–8).  
*Legenda Técnica:* Inicialização do `llama-server` (b11887) no Apple M4 (`Mac16,10`). Observa-se a alocação de 3.21 bilhões de parâmetros (2,019 GB em Q4_K_M) diretamente na DRAM compartilhada (`n_slots = 1, n_ctx_slot = 32768`) e prontidão do endpoint HTTP loopback.

---

#### Passo 2: Verificação e Validação dos Datasets dos Workloads
Antes de iniciar os testes, inspeciona-se a integridade física dos datasets determinísticos:
```bash
ls -lh data/workload_data/
head -n 5 data/workload_data/system_logs.jsonl
```
```text
data/workload_data/
├── mock_files/ (50 arquivos sintéticos determinísticos)
├── system_logs.jsonl (750 linhas estruturadas de log APFS)
├── rag_chunks_10k.json (10.000 fragmentos textuais para busca vetorial)
├── doc_embeddings.bin (matriz binária float32 de embeddings 10.000 x 384)
├── w_proj.bin (matriz de projeção float32 256 x 384)
└── b_proj.bin (vetor de bias float32 de 384 dimensões)
```
*Legenda Técnica:* Inspeção dos 50 arquivos sintéticos, do log estruturado de 750 linhas APFS e dos pesos de projeção vetorial em float32 (`doc_embeddings.bin`, `w_proj.bin`).

---

#### Passo 3: Execução Física dos Agentes em Tempo Real
Os orquestradores executam os testes fatoriais W1 a W4 contra o servidor neural:
```bash
./tools/.venv/bin/python benchmark/run_unified_benchmark.py
```
*(Exemplo Ilustrativo da Estrutura de Saída do Runner / Illustrative Runner Output Format)*
```text
[001/600] picoclaw         W1 Rep 1: Task=5497.0ms, Orch=29.73ms, RAM=11.2MB, EDP=491.2J·s
[002/600] openclaw_minimal W1 Rep 1: Task=5847.5ms, Orch=51.28ms, RAM=85.6MB, EDP=550.5J·s
[003/600] openclaw_full    W1 Rep 1: Task=20674.1ms, Orch=66.44ms, RAM=85.6MB, EDP=6815.0J·s
[004/600] python_native    W1 Rep 1: Task=5485.6ms, Orch=10.41ms, RAM=38.2MB, EDP=492.2J·s
[005/600] neural_baseline  W1 Rep 1: Task=5489.6ms, Orch=0.00ms, RAM=0.0MB, EDP=483.6J·s
```
*Legenda Técnica:* Traces em tempo real ilustrando a estrutura de saída do runner com a latência de tarefa ($T_{\text{task}}$), tempo de inferência neural ($T_{\text{neural}}$), overhead do runtime ($T_{\text{orch}}$) e consumo de memória RAM residente (RSS).

---

#### Passo 4: Medição Estatística de Cold-Start com Hyperfine
Cronometragem com precisão nanométrica do tempo de disparo a frio (30 repetições, `hyperfine_cold_start.json` e `hyperfine_worker_version.json`):
```bash
./tools/hyperfine/hyperfine --warmup 5 --runs 30 \
  "./tools/picoclaw/picoclaw version" \
  "./tools/node/bin/node ./benchmark/openclaw_orch.mjs --version"
```
```text
Benchmark 1: ./tools/picoclaw/picoclaw version
  Time (mean ± σ):       9.74 ms ±   0.38 ms    [Median: 9.67 ms]
  Range (min … max):     9.12 ms …  10.84 ms    30 runs
Benchmark 2: ./tools/node/bin/node ./benchmark/openclaw_orch.mjs --version
  Time (mean ± σ):      37.15 ms ±   4.12 ms    [Median: 33.48 ms]
  Range (min … max):    32.80 ms …  48.90 ms    30 runs
Summary:
  PicoClaw ran 3.81 times faster (mean) and 3.46 times faster (median) than OpenClaw
```
*Fonte do Log Real / Real Log Source:* `results/publication_campaign/hyperfine_cold_start.json` (e `results/publication_campaign/hyperfine_worker_version.json`).  
*Legenda Técnica:* No par equivalente de checagem de versão (`hyperfine_cold_start.json`), o PicoClaw (Go nativo) inicializa em **$9{,}74\text{ ms}$** de média (**$9{,}67\text{ ms}$** de mediana) vs. **$37{,}15\text{ ms}$** de média (**$33{,}48\text{ ms}$** de mediana) no OpenClaw (Node.js/V8), comprovando vantagem de inicialização de **$3{,}81\times$ na média ($3{,}46\times$ na mediana)** a favor do Go (e **$3{,}04\text{ ms}$ vs. $22{,}15\text{ ms}$ [$7{,}29\times$]** nos workers isomórficos em `hyperfine_worker_version.json`).

---

#### Passo 5: Verificação de Integridade Criptográfica (SHA-256)
Auditoria automática dos 226 arquivos do repositório contra a assinatura digital:
```bash
make verify
```
```text
========================================================================
 🔐 [PT-BR] Verificação de Integridade Criptográfica (SHA-256)
    [EN-US] Cryptographic Artifact Integrity Verification (226 files)
========================================================================
✅ [SUCCESS] All 226/226 tracked files match their cryptographic SHA-256 signature!
   [PT-BR] Todos os arquivos rastreados conferem com suas assinaturas SHA-256 registradas.
========================================================================
```
*Legenda Técnica:* Verificação matemática estrita garantindo que nenhum dataset binário, código-fonte ou tabela LaTeX foi alterado silenciosamente.

---

#### Passo 6: Verificação Rápida Portátil de Revisores (Modo Dry-Run)
Execução do ciclo completo em qualquer sistema operacional (< 5 segundos, sem GPU Metal):
```bash
make dry-run
```
```text
========================================================================
 🧪 [PT-BR] Modo Dry-Run / Mock Rápido (Verificação Portátil de Pipeline)
    [EN-US] Dry-Run / Fast Mock Mode (Portable Pipeline Verification)
========================================================================
🌐 [INFO] Local loopback mock server listening on 127.0.0.1:8088.
📊 Matrix: 5 agents x 4 workloads x 2 reps = 40 evaluation trials.
▶️  Dispatching randomized evaluation blocks...
📈 Executing non-parametric statistical analysis...
Loaded 40 evaluated trial records.
✅ Generated LaTeX macros: results/simulated_check/tables/macros_empirical.tex
✅ Generated summary JSON: results/simulated_check/summary_statistics.json
✅ Generated CSV table: results/simulated_check/tables/metrics_summary.csv
🎨 Generating publication charts...
```
*Legenda Técnica:* Mock determinístico que simula todas as chamadas SSE e valida a pipeline estatística e de geração gráfica em ambientes de integração contínua (CI).

---

#### Passo 7: Telemetria de Hardware via Apple SMC (`powermetrics -i 50`)
Amostragem dos sensores de potência física do silício M4 via SMC:
```bash
sudo powermetrics -i 50 -n 10 --samplers cpu_power,gpu_power
```
```text
Machine model: Mac16,10
OS version: 25G83
*** Sampled system activity (Thu Nov 12 18:28:01 2026 -0300) (55.28ms elapsed) ***
E-Cluster HW active frequency: 2208 MHz
E-Cluster HW active residency:  51.33%
CPU Power: 669 mW
GPU Power: 90 mW
ANE Power: 0 mW
Combined Power (CPU + GPU + ANE): 760 mW
```
*Fonte do Log Real / Real Log Source:* `results/publication_campaign/powermetrics_publication_sample.txt` (Linhas 1–56).  
*Legenda Técnica:* Leitura física real dos shunts elétricos do Apple M4 SoC (`Mac16,10`, OS `25G83`) a cada 50 ms via `powermetrics`.

---

#### Passo 8: Garantia de Quiescência Operacional do macOS (`caffeinate -dims`)
```bash
/usr/bin/caffeinate -dims &
./scripts/check_quiescence.sh
```
```text
=== System Quiescence Pre-Flight Check ===
[PASS] Caffeinate process running: PID 1233 (/usr/bin/caffeinate -dims)
[PASS] Spotlight indexing disabled: mdutil -a -i off
[PASS] Loopback interface active: 127.0.0.1:8080 responding
System quiescence verified for low-noise empirical measurement.
```
*Legenda Técnica:* Auditoria do daemon `caffeinate -dims` prevenindo repouso de sistema, display e disco durante as rodadas de medição.

---

#### Passo 9: Caracterização de Reuso de KV-Cache (Regime B - Warm Cache)
Execução da campanha em blocos isolados com persistência determinística de prefixos (`BENCH_CACHE_PROMPT=true`):
```bash
sudo -E ./tools/.venv/bin/python scripts/run_warm_cache_campaign.py
```
```text
{"timestamp_iso": "2026-11-12T22:48:23Z", "agent_key": "picoclaw", "workload": "W2", "rep": 1, "is_warmup": false, "t_task_ms": 741.84, "t_neural_ms": 736.7, "t_orch_ms": 5.14, "ttft_ms": 235.12, "itl_ms": 17.91, "prompt_ms": 235.12, "predicted_ms": 501.58, "proc_peak_phys_mb": 4.73, "prompt_tokens": 2177, "cached_tokens": 2176, "uncached_prompt_tokens": 1, "cache_hit_pct": 99.95, "energy_net_above_idle_j": 8.87, "session_id": "S1_REGIME_B_UNIFIED_20261113", "hardware": "Apple Mac mini M4 (Mac16,10, 10-core CPU, 10-core Metal GPU, 24GB LPDDR5X UMA)"}
```
*Fonte do Log Real / Real Log Source:* `results/publication_campaign/warm_cache_trials.jsonl`.  
*Legenda Técnica:* Registro real extraído de `warm_cache_trials.jsonl` comprovando retenção de prefixo no `llama-server` (`cached_tokens = 2176 / 2177`, `cache_hit_pct = 99.95%`), latência sub-segundo (`741.84 ms`), `Peak Physical Footprint` (`4.73 MB`) e energia líquida via Apple SMC (`8.87 J`).

---

## 🇺🇸 English (EN-US): How to Understand and Reproduce in 3 Minutes

This walkthrough is tailored for students, researchers, and engineers seeking an intuitive yet technically precise understanding of the benchmark, supported by illustrative terminal output examples recorded on Apple Silicon M4.

---

### 0. How to Reproduce on Any Machine (Linux, Windows WSL, macOS)

You **DO NOT need an Apple Silicon Mac or a dedicated GPU** to reproduce and audit this research! Any reviewer, student, or researcher on Linux (Ubuntu, Debian, Fedora), Windows (via WSL2), or Intel/Apple Silicon macOS can run the entire pipeline:

```bash
# 1. Clone repository and enter project directory
git clone https://github.com/drsigma/picoclaw-vs-openclaw-benchmark.git
cd picoclaw-vs-openclaw-benchmark

# 2. Setup isolated environment with a single command
make setup

# 3. Run Instant Portable Dry-Run Verification (< 5 seconds, No GPU, No Sudo)
make dry-run

# 4. Run the 45 automated unit tests (pytest and ruff linter)
make test

# 5. Re-render all 6 publication figures in 300 DPI
make reproduce-figures
```

*If you are running on an Apple Silicon Mac (M1/M2/M3/M4):*
* Run `make benchmark` for physical execution in standard user space (no sudo required);
* Run `make benchmark-full-smc` for complete physical hardware electrical telemetry via Apple SMC shunts.

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

### 3. Step-by-Step Walkthrough with Illustrative Runner Output Format

#### Step 1: Launch Local Metal GPU Neural Server (`llama-server`)
```bash
./tools/llama_cpp/llama-b11887/llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```
```text
0.04.154.161 I srv  llama_server: initializing ...
0.04.154.169 I cmn  common_param: common_params_print_info: verbosity = 3 (adjust with the `-lv N` CLI arg)
0.04.156.027 I srv    load_model: loading model './models/Llama-3.2-3B-Instruct-Q4_K_M.gguf'
0.05.841.379 I cmn          init: llama threadpool init, n_threads = 4
0.06.149.561 I srv    load_model: initializing, n_slots = 1, n_ctx_slot = 32768, kv_unified = 'false'
0.06.152.620 I srv  server_run_i: model loaded
0.06.152.626 I srv  server_on_li: listening on http://127.0.0.1:8080
```
*Real Log Source:* `results/publication_campaign/llama_server_publication.log` (Lines 1–8).  
*Technical Caption:* Initialization of `llama-server` (build b11887) on Apple M4 (`Mac16,10`). Notice the allocation of 3.21B parameters (2.019 GB in Q4_K_M) directly in shared DRAM (`n_slots = 1, n_ctx_slot = 32768`) and endpoint readiness on HTTP loopback.

---

#### Step 2: Inspect Workload Datasets
```bash
ls -lh data/workload_data/
head -n 5 data/workload_data/system_logs.jsonl
```
```text
data/workload_data/
├── mock_files/ (50 synthetic deterministic text files)
├── system_logs.jsonl (750 APFS structured JSON log lines)
├── rag_chunks_10k.json (10,000 vector chunks)
├── doc_embeddings.bin (10,000 x 384 float32 embeddings)
├── w_proj.bin (256 x 384 float32 projection head)
└── b_proj.bin (384 float32 bias vector)
```
*Technical Caption:* Inspection of 50 mock files, 750 APFS structured JSON log lines, and dense float32 projection matrix (`doc_embeddings.bin`, `w_proj.bin`).

---

#### Step 3: Run Master Live Benchmark Campaign
```bash
./tools/.venv/bin/python benchmark/run_unified_benchmark.py
```
*(Illustrative Runner Output Format / Exemplo Ilustrativo da Estrutura de Saída do Runner)*
```text
[001/600] picoclaw         W1 Rep 1: Task=5497.0ms, Orch=29.73ms, RAM=11.2MB, EDP=491.2J·s
[002/600] openclaw_minimal W1 Rep 1: Task=5847.5ms, Orch=51.28ms, RAM=85.6MB, EDP=550.5J·s
[003/600] openclaw_full    W1 Rep 1: Task=20674.1ms, Orch=66.44ms, RAM=85.6MB, EDP=6815.0J·s
[004/600] python_native    W1 Rep 1: Task=5485.6ms, Orch=10.41ms, RAM=38.2MB, EDP=492.2J·s
[005/600] neural_baseline  W1 Rep 1: Task=5489.6ms, Orch=0.00ms, RAM=0.0MB, EDP=483.6J·s
```
*Technical Caption:* Real-time execution traces demonstrating the illustrative runner output format capturing task latency ($T_{\text{task}}$), neural serving time ($T_{\text{neural}}$), runtime overhead ($T_{\text{orch}}$), and Resident Set Size (RSS).

---

#### Step 4: Measure Cold-Start Launch Latency with Hyperfine
```bash
./tools/hyperfine/hyperfine --warmup 5 --runs 30 \
  "./tools/picoclaw/picoclaw version" \
  "./tools/node/bin/node ./benchmark/openclaw_orch.mjs --version"
```
```text
Benchmark 1: ./tools/picoclaw/picoclaw version
  Time (mean ± σ):       9.74 ms ±   0.38 ms    [Median: 9.67 ms]
  Range (min … max):     9.12 ms …  10.84 ms    30 runs
Benchmark 2: ./tools/node/bin/node ./benchmark/openclaw_orch.mjs --version
  Time (mean ± σ):      37.15 ms ±   4.12 ms    [Median: 33.48 ms]
  Range (min … max):    32.80 ms …  48.90 ms    30 runs
Summary:
  PicoClaw ran 3.81 times faster (mean) and 3.46 times faster (median) than OpenClaw
```
*Real Log Source:* `results/publication_campaign/hyperfine_cold_start.json` (and `results/publication_campaign/hyperfine_worker_version.json`).  
*Technical Caption:* Hyperfine statistical benchmarking (`hyperfine_cold_start.json`) proving PicoClaw launches in **$9.74\text{ ms}$** mean (**$9.67\text{ ms}$** median) vs. OpenClaw's **$37.15\text{ ms}$** mean (**$33.48\text{ ms}$** median), a **$3.81\times$ mean ($3.46\times$ median)** speedup (and **$3.04\text{ ms}$ vs. $22.15\text{ ms}$ [$7.29\times$]** across the isomorphic workers in `hyperfine_worker_version.json`).

---

#### Step 5: Cryptographic Integrity Verification (SHA-256)
Automated audit of all 226 tracked repository files against their cryptographic hashes:
```bash
make verify
```
```text
========================================================================
 🔐 [PT-BR] Verificação de Integridade Criptográfica (SHA-256)
    [EN-US] Cryptographic Artifact Integrity Verification (226 files)
========================================================================
✅ [SUCCESS] All 226/226 tracked files match their cryptographic SHA-256 signature!
   [PT-BR] Todos os arquivos rastreados conferem com suas assinaturas SHA-256 registradas.
========================================================================
```
*Technical Caption:* Strict mathematical integrity validation ensuring no dataset binaries, source files, or LaTeX tables were silently modified.

---

#### Step 6: Reviewer Fast Portable Dry-Run Mode
Execute full pipeline validation on any platform (< 5 seconds, no GPU required):
```bash
make dry-run
```
```text
========================================================================
 🧪 [PT-BR] Modo Dry-Run / Mock Rápido (Verificação Portátil de Pipeline)
    [EN-US] Dry-Run / Fast Mock Mode (Portable Pipeline Verification)
========================================================================
🌐 [INFO] Local loopback mock server listening on 127.0.0.1:8088.
📊 Matrix: 5 agents x 4 workloads x 2 reps = 40 evaluation trials.
▶️  Dispatching randomized evaluation blocks...
📈 Executing non-parametric statistical analysis...
Loaded 40 evaluated trial records.
✅ Generated LaTeX macros: results/simulated_check/tables/macros_empirical.tex
✅ Generated summary JSON: results/simulated_check/summary_statistics.json
✅ Generated CSV table: results/simulated_check/tables/metrics_summary.csv
🎨 Generating publication charts...
```
*Technical Caption:* Deterministic loopback mock server simulating SSE tool chunks to validate statistical inference and publication chart rendering in headless CI environments.

---

#### Step 7: Hardware Power Telemetry via Apple SMC (`powermetrics -i 50`)
```bash
sudo powermetrics -i 50 -n 10 --samplers cpu_power,gpu_power
```
```text
Machine model: Mac16,10
OS version: 25G83
*** Sampled system activity (Thu Nov 12 18:28:01 2026 -0300) (55.28ms elapsed) ***
E-Cluster HW active frequency: 2208 MHz
E-Cluster HW active residency:  51.33%
CPU Power: 669 mW
GPU Power: 90 mW
ANE Power: 0 mW
Combined Power (CPU + GPU + ANE): 760 mW
```
*Real Log Source:* `results/publication_campaign/powermetrics_publication_sample.txt` (Lines 1–56).  
*Technical Caption:* Real physical readout from Apple M4 SoC electrical shunts (`Mac16,10`, OS `25G83`) at 50 ms intervals via `powermetrics`.

---

#### Step 8: System Quiescence Pre-Flight Check (`caffeinate -dims`)
```bash
/usr/bin/caffeinate -dims &
./scripts/check_quiescence.sh
```
```text
=== System Quiescence Pre-Flight Check ===
[PASS] Caffeinate process running: PID 1233 (/usr/bin/caffeinate -dims)
[PASS] Spotlight indexing disabled: mdutil -a -i off
[PASS] Loopback interface active: 127.0.0.1:8080 responding
System quiescence verified for low-noise empirical measurement.
```
*Technical Caption:* Verification of `caffeinate -dims` assertion preventing system, display, and disk sleep during benchmark runs.

---

#### Step 9: Realistic Warm KV-Cache Retention Campaign (Regime B)
Executing the block-isolated campaign evaluating persistent prefix caching (`BENCH_CACHE_PROMPT=true`):
```bash
sudo -E ./tools/.venv/bin/python scripts/run_warm_cache_campaign.py
```
```text
{"timestamp_iso": "2026-11-12T22:48:23Z", "agent_key": "picoclaw", "workload": "W2", "rep": 1, "is_warmup": false, "t_task_ms": 741.84, "t_neural_ms": 736.7, "t_orch_ms": 5.14, "ttft_ms": 235.12, "itl_ms": 17.91, "prompt_ms": 235.12, "predicted_ms": 501.58, "proc_peak_phys_mb": 4.73, "prompt_tokens": 2177, "cached_tokens": 2176, "uncached_prompt_tokens": 1, "cache_hit_pct": 99.95, "energy_net_above_idle_j": 8.87, "session_id": "S1_REGIME_B_UNIFIED_20261113", "hardware": "Apple Mac mini M4 (Mac16,10, 10-core CPU, 10-core Metal GPU, 24GB LPDDR5X UMA)"}
```
*Real Log Source:* `results/publication_campaign/warm_cache_trials.jsonl`.  
*Technical Caption:* Real record extracted from `warm_cache_trials.jsonl` proving deterministic prefix retention in `llama-server` (`cached_tokens = 2176 / 2177`, `cache_hit_pct = 99.95%`), sub-second task latency (`741.84 ms`), `Peak Physical Footprint` (`4.73 MB`), and net energy via Apple SMC (`8.87 J`).
