# Registro Histórico das Campanhas Exploratórias / Changelog of Exploratory Campaigns

---

## 🇧🇷 Português (PT-BR)

Este documento registra formalmente a evolução metodológica e as calibrações empíricas ocorridas entre as campanhas experimentais 1 a 5 no Apple Silicon M4. Em conformidade com as diretrizes de avaliação de desempenho computacional (Jain, 1991), todas as fases preliminares e ajustes são documentados de forma transparente para assegurar a rastreabilidade científica total.

### Evolução Metodológica por Campanha

#### Campanha 1 (`campaign_run_1`) — Calibração Inicial e Shunts do Apple SMC
* **Objetivo:** Estabelecer a primeira linha de base fatorial (480 ensaios) e coletar dados físicos de consumo energético diretamente dos shunts analógicos do Apple System Management Controller (SMC).
* **Artefatos:** `summary_campaign_run_1.json`, `powermetrics_idle.txt`, `powermetrics_picoclaw.txt`, `powermetrics_openclaw.txt`, `privileged_quiescence.log`.
* **Achados e Desvios:**
  1. Identificação de que o utilitário nativo `/usr/bin/powermetrics` exige elevação de privilégios (`sudo`) para acessar registradores de miliwatts do SoC M4.
  2. Diagnóstico do fenômeno de *Prompt Token Bloat* na CLI oficial do OpenClaw: o carregamento estático de 54 ferramentas corporativas gerou 16.369 tokens de entrada para perguntas triviais, causando estouro de contexto em janelas de 4k tokens e prefill de 57 segundos na GPU.
  3. No Workload W4 (loop autônomo ReAct), a formulação inicial permitia gerações livres de respostas verbais longas, estendendo a latência para ~22 a 23 segundos por rodada.

#### Campanhas 2 a 4 (`campaign_run_2`, `campaign_run_3`, `campaign_run_4`) — Baterias Físicas Padronizadas
* **Objetivo:** Executar rodadas físicas independentes e sequenciais na GPU Metal (`llama-server`, Metal compute shaders) com os 9 ajustes metodológicos já consolidados.
* **Artefatos:** `raw_trials.jsonl` e `summary_campaign_run_*.json` em cada pasta.
* **Ajustes Aplicados:**
  1. Equalização do Workload W4: prompt estruturado estritamente delimitado a 10 passos sequenciais de raciocínio e execução, estabilizando a latência em ~10,8s (PicoClaw Go) e ~12,6s (OpenClaw Node.js).
  2. Integração da biblioteca de kernel Darwin `libproc` (`proc_pid_rusage`) para leitura de contadores de hardware (`ri_instructions`, `ri_cycles`, RSS) sem necessidade de privilégios de root para os processos dos agentes.
  3. Quiescência térmica e operacional ativa via `/usr/bin/caffeinate -dims`.
* **Resultados:** Coeficiente de variação inter-campanhas inferior a $2{,}5\%$ para os workloads W1 a W3, demonstrando alta estabilidade do ambiente bare-metal.

#### Campanha 5 (`campaign_run_5`) — Validação do Processo Pontual de Poisson
* **Objetivo:** Submeter a bancada a uma bateria de estresse de alta intensidade com $K = 300$ chamadas de ferramentas sob distribuição de Poisson.
* **Artefatos:** `raw_trials.jsonl`, `summary_campaign_run_5.json`.
* **Resultados:** Assertividade empírica entre $90{,}33\%$ e $93{,}84\%$ dentro dos intervalos fiduciais analíticos exatos de Garwood (1936), com teste de Cameron & Trivedi confirmando equidispersão estocástica ($t = 0{,}412 < 1{,}96$).

---

## 🇺🇸 English (EN-US)

This document formally records the methodological evolution and empirical calibrations across experimental campaigns 1 through 5 conducted on Apple Silicon M4. Adhering to computer systems performance evaluation standards (Jain, 1991), all exploratory phases and engineering refinements are preserved to guarantee complete scientific provenance.

### Chronological Methodological Evolution

#### Campaign 1 (`campaign_run_1`) — Initial Baseline & Apple SMC Shunt Calibration
* **Objective:** Establish the first full factorial baseline matrix (480 observations) and capture physical electrical dissipation directly from Apple System Management Controller (SMC) analog shunt sensors.
* **Stored Artifacts:** `summary_campaign_run_1.json`, `powermetrics_idle.txt`, `powermetrics_picoclaw.txt`, `powermetrics_openclaw.txt`, `privileged_quiescence.log`.
* **Key Observations and Deviations:**
  1. Identified that native macOS `/usr/bin/powermetrics` requires superuser escalation (`sudo`) to read SoC milliwatt registers.
  2. Discovered OpenClaw's stock CLI *Prompt Token Bloat*: bundling 54 enterprise schemas injected 16,369 prompt tokens for trivial queries, triggering context overflow in standard 4k windows and 57-second GPU prefill delays.
  3. Workload W4 (autonomous ReAct loop) initially permitted unconstrained natural language verbiage, inflating execution latency to ~22–23 seconds per trial.

#### Campaigns 2 through 4 (`campaign_run_2`, `campaign_run_3`, `campaign_run_4`) — Standardized Physical Replicates
* **Objective:** Execute sequential, independent hardware test runs against local Metal GPU compute shaders under unified, calibrated conditions.
* **Stored Artifacts:** `raw_trials.jsonl` and `summary_campaign_run_*.json` per run.
* **Applied Refinements:**
  1. Equalized Workload W4: structured prompt constrained to 10 discrete ReAct cycles, stabilizing latency at ~10.8s (PicoClaw Go) and ~12.6s (OpenClaw Node.js).
  2. Integrated Darwin XNU kernel ABI `libproc` (`proc_pid_rusage` with `rusage_info_v4`) to capture low-level hardware performance counters without root escalation.
  3. Thermal and operational quiescence enforced via `/usr/bin/caffeinate -dims`.
* **Outcomes:** Cross-campaign coefficient of variation under $2.5\%$ across W1–W3, confirming high reproducibility on Apple Silicon bare metal.

#### Campaign 5 (`campaign_run_5`) — Poisson Point Process Verification
* **Objective:** Execute high-intensity Poisson stress testing with $K = 300$ discrete tool invocations.
* **Stored Artifacts:** `raw_trials.jsonl`, `summary_campaign_run_5.json`.
* **Outcomes:** Empirical assertiveness reached $90.33\%$ to $93.84\%$ within exact Garwood (1936) fiducial bounds, with Cameron & Trivedi auxiliary regression confirming Poisson equidispersion ($t = 0.412 < 1.96$).
