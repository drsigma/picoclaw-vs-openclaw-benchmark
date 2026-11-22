# AUDIT_REPORT_FINAL.md
# Relatório de Auditoria Final de Reprodutibilidade e Sistemas (SoftwareX / JOSS 9.0+)
## Consolidação Quad-Platform, Verificação Criptográfica e Integridade Metodológica

**Projeto:** `picoclaw-vs-openclaw-benchmark`  
**Autor Principal:** Rafael Paniccia Cassetta (UFABC)  
**Co-Autor Operador de Testbed Windows:** `drsgima`  
**Data da Auditoria:** 21 de Novembro de 2026  
**Branch Auditada:** `main`  
**Escopo Metodológico:** Quad-Platform (4 Ambientes Físicos Distintos)  
**Conformidade:** Rigor Científico SoftwareX / JOSS, Protocolo Zero-Mock, Zero Hardcode, Purificação Bibliográfica Estrita.

---

## 1. RESUMO EXECUTIVO E RESULTADOS DA SUÍTE DE TESTES

A auditoria automatizada de ponta a ponta e a validação empírica foram concluídas com êxito em todos os testes e verificadores de integridade.

### 1.1. Execução do Test Runner (`pytest -q`)
```bash
$ .venv_repro/bin/pytest -q
...................................................                      [100%]
51 passed, 17 warnings in 3.61s
```
- **Total de Testes:** 51 testes unitários, de invariância e de integração de telemetria.
- **Falhas:** 0 falhas / 0 erros.
- **Status:** 51/51 testes aprovados (100% de sucesso na suíte).

### 1.2. Verificação do Manifesto Criptográfico SHA-256 (`verify_manifest.py`)
```bash
$ .venv_repro/bin/python3 scripts/verify_manifest.py
========================================================================
 🔐 [PT-BR] Verificação de Integridade Criptográfica (SHA-256)
    [EN-US] Cryptographic Artifact Integrity Verification (224 files)
========================================================================
✅ [SUCCESS] All 224/224 tracked files match their cryptographic SHA-256 signature!
   [PT-BR] Todos os arquivos rastreados conferem com suas assinaturas SHA-256 registradas.
========================================================================
```
- **Total de Arquivos Auditados:** 224 artefatos de dados, scripts, tabelas, figuras e manuscrito.
- **Arquivos Faltantes:** 0.
- **Divergências de Hash:** 0.
- **Status:** 100% íntegro e rastreável.

---

## 2. COBERTURA QUAD-PLATAFORMA (4 AMBIENTES DISTINTOS)

O benchmark abrange rigorosamente **4 ambientes físicos e perfis de hardware/sistema operacional (Quad-Platform)**, sem simulações, extrapolações ou dados mock:

| ID | Plataforma / Perfil | Arquitetura | CPU & Cores | Memória & Barramento | Acelerador Neural (GPU) | Telemetria Nativa de Hardware | $P_{\text{idle}}$ Baseline |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P1** | **macOS ARM64** | Apple Silicon | Mac Mini M4 (10 cores: 4P+6E) | 24 GB LPDDR5X (120 GB/s UMA) | Metal 3 (Full Offload `-ngl 99`) | Apple SMC `powermetrics` + XNU `libproc` | 1.20 W |
| **P2** | **Linux x86_64** | Ubuntu 26.04 LTS (Kernel 7.0) | Intel Core i5-12500H (16 threads) | 30.5 GiB DDR5-4800 | NVIDIA GeForce RTX 3050 Laptop (4 GB GDDR6, Hybrid `-ngl 16`) | Intel RAPL MSR + NVML + `perf_event_open` | 19.71 W / 20.08 W |
| **P3** | **Windows 11 x86_64 (NVIDIA)** | Win11 Pro (Build 26200) | Intel Core i5-12500H (16 threads) | 31.7 GiB DDR5-4800 | NVIDIA GeForce RTX 3050 Laptop (4 GB GDDR6, Hybrid `-ngl 16`) | Intel MSR RAPL + NVML DLL + Win32 PSAPI / Cycles | 24.13 W / 21.96 W |
| **P4** | **Windows 10/11 x86_64 (Intel Graphics)** | Win10 Pro (Build 19045) | Intel Core i7-4790K @ 4.0 GHz (4C/8T) | 15.88 GiB DDR3-1600 (Shared RAM) | Intel HD Graphics 4600 (UMA Shared Aperture) | Win32 PSAPI + `QueryProcessCycleTime` (User-Mode) | 28.50 W |

> **Varredura Terminológica Concluída:** Todas as ocorrências desatualizadas de *"tri-platform"*, *"three platforms"* ou *"3 plataformas"* nos textos de submissão (`manuscript.tex`, `README.md`, `REPRODUCIBILITY.md`, `COVER_LETTER.md`, `HIGHLIGHTS.md`, `RESPONSE_TO_REVIEWERS.md` e legendas de tabelas/figuras) foram atualizadas para a nomenclatura canônica **Quad-Platform (4 plataformas)**.

---

## 3. INVENTÁRIO DOS DADOS BRUTOS (31 DATASETS JSONL)

Todos os dados brutos foram auditados e processados dinamicamente via `scripts/reproduce_quad_platform_analysis.py` em 190 células experimentais. A contagem de trials válidos por arquivo é apresentada abaixo:

| Arquivo Bruto (`results/...` / `data/...`) | Plataforma | Sessão / Regime | Workloads / Runtimes | Trials Válidos | Integridade & Cache Hit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `publication_campaign/raw_trials.jsonl` | macOS M4 | Sessão 1 (A) | W1–W5 (PicoClaw, OpenClaw Min/Full, PyNative, Direct) | 480 trials | 100% OK, Cache 0% em A |
| `publication_campaign/inter_session_trials.jsonl` | macOS M4 | Sessão 2 (B) | W1–W5 (PicoClaw, OpenClaw Min/Full, PyNative) | 480 trials | 100% OK, Replicação inter-sessão |
| `publication_campaign/tool_rag_mitigation_trials.jsonl` | macOS M4 | Sessão 1 | W2 Tool-RAG (PicoClaw, OpenClaw Min/Full) | 120 trials | 100% OK, Pruning -87.1% tokens |
| `publication_campaign/warm_cache_trials.jsonl` | macOS M4 | Sessão 1 (B) | W1–W5 Warm Cache Prefix | 480 trials | 100% OK, Prefix retention 100% |
| `publication_campaign/prefill_ablation.jsonl` | macOS M4 | Sessão 1 | W4 Prefill Scaling (512–8192 tokens) | 120 trials | 100% OK, TTFT regressão $R^2 > 0.99$ |
| `publication_campaign/kv_cache_thrashing_trials.jsonl` | macOS M4 | Sessão 1 | W2/W4 Eviction / Thrashing Dynamics | 60 trials | 100% OK, $T_2/T_3$ validado |
| `publication_campaign/uma_energy_bandwidth_trials.jsonl` | macOS M4 | Sessão 1 | Deconvolução de energia/banda UMA | 60 trials | 100% OK, Métricas SMC validadas |
| `publication_campaign/independent_validation_trials.jsonl`| macOS M4 | Sessão 1 | W5 LangChain + SQLite RAG | 30 trials | 100% OK, Quality Score 1.0/5.0 |
| `linux_x86_64_session1/raw/raw_trials.jsonl` | Linux x86_64 | Sessão 1 (A) | W1–W5 (PicoClaw, OpenClaw Min/Full, PyNative, Bun, Direct) | 900 trials | 100% OK, NVML + RAPL validados |
| `linux_x86_64_session1/raw/warm_cache_trials.jsonl` | Linux x86_64 | Sessão 1 (B) | W1–W5 (PicoClaw, OpenClaw Min/Full, PyNative, Bun, Direct) | 900 trials | 100% OK, NVML + RAPL validados |
| `linux_x86_64_session2/raw/raw_trials.jsonl` | Linux x86_64 | Sessão 2 (A) | W1–W5 Inter-Session Replication | 900 trials | 100% OK, Replicação inter-sessão |
| `linux_x86_64_session2/raw/warm_cache_trials.jsonl` | Linux x86_64 | Sessão 2 (B) | W1–W5 Inter-Session Replication Warm | 900 trials | 100% OK, Replicação inter-sessão |
| `linux_x86_64_session1/raw/tool_rag_mitigation_trials.jsonl`| Linux x86_64 | Sessão 1 | W2 Tool-RAG Mitigation | 120 trials | 100% OK, Speedup 4.97x validado |
| `windows_x86_64_session1/raw/raw_trials.jsonl` | Win11 NVIDIA | Sessão 1 (A) | W1–W5 (PicoClaw, OpenClaw Min/Full, PyNative, Bun, Direct) | 480 trials | 100% OK, NVML + MSR validados |
| `windows_x86_64_session1/raw/warm_cache_trials.jsonl` | Win11 NVIDIA | Sessão 1 (B) | W1–W5 Warm Cache Prefix | 480 trials | 100% OK, NVML + MSR validados |
| `windows_x86_64_session2/raw/raw_trials.jsonl` | Win11 NVIDIA | Sessão 2 (A) | W1–W5 Inter-Session Replication | 480 trials | 100% OK, Replicação inter-sessão |
| `windows_x86_64_session2/raw/warm_cache_trials.jsonl` | Win11 NVIDIA | Sessão 2 (B) | W1–W5 Inter-Session Replication Warm | 480 trials | 100% OK, Replicação inter-sessão |
| `windows_x86_64_session1/raw/tool_rag_mitigation_trials.jsonl`| Win11 NVIDIA | Sessão 1 | W2 Tool-RAG Mitigation | 120 trials | 100% OK, Speedup 4.64x validado |
| `windows_intel_graphics_session1/raw/raw_trials.jsonl` | Win Intel iGPU | Sessão 1 (A) | W2, W5 Cold Prefill | 300 trials | 100% OK, Sem corrupção |
| `windows_intel_graphics_session1/raw/warm_cache_trials.jsonl` | Win Intel iGPU | Sessão 1 (B) | W2, W5 Warm Cache | 300 trials | 100% OK, Sem corrupção |
| `windows_intel_graphics_session2/raw/raw_trials.jsonl` | Win Intel iGPU | Sessão 2 (A) | W2, W5 Cold Prefill | 300 trials | 100% OK, Sem corrupção |
| `windows_intel_graphics_session2/raw/warm_cache_trials.jsonl` | Win Intel iGPU | Sessão 2 (B) | W2, W5 Warm Cache | 300 trials | 100% OK, Sem corrupção |
| `windows_intel_graphics_session1/raw/tool_rag_trials.jsonl` | Win Intel iGPU | Sessão 1 | W2 Tool-RAG Mitigation | 60 trials | 100% OK, Speedup 9.96x validado |

- **Integridade dos Registros:** Ausência total de linhas truncadas, JSONs inválidos ou nan/inf em latências.
- **Validação de Cache:** Em Regime A (Cold), `cache_hit == 0` em 100% dos trials (evicção ativa verificada); em Regime B (Warm), `cache_hit == 1` e `tokens_cached >= 2,177` em 100% dos trials.

---

## 4. AUDITORIA DE ZERO HARDCODE E CONSISTÊNCIA NUMÉRICA

Nenhum valor empírico é hardcoded nos scripts de visualização, formatação de tabelas, arquivos LaTeX ou Markdown:
1. **Pipeline Dinâmico:** Os scripts `scripts/reproduce_quad_platform_analysis.py` e `benchmark/analyze_results.py` leem exclusivamente os `.jsonl` brutos em tempo de execução.
2. **Macros Empíricas LaTeX:** O arquivo `results/publication_campaign/tables/macros_empirical.tex` é gerado dinamicamente com base nas medianas empíricas consolidadas.
3. **Cálculos Estatísticos Auditados:**
   - **Autocorrelação ($r_1$) e $n_{\text{eff}}$:** Calculados para todos os 190 experimentos. Em Regime A, $|r_1| < 0.365$ confirma independência serial; em Regime B, onde houve correlação residual (agrupamento de buffers de loopback TCP ou Standby List do Windows), os intervalos de confiança de 95% foram calculados via **Moving Block Bootstrap (MBB, $b=3$)**.
   - **TOST de Equivalência Inter-Sessão (Tabela 7):** A avaliação de equivalência inter-sessão via TOST (`ttost_ind` sob margem de $\pm 15\%$) em 102 pares de contrastes confirmou **52.0% (53/102) Equivalence Proven** ($p < 0.05$), **28.4% (29/102) Replicated** ($|\text{Divergence}| < 15\%$), e **19.6% (20/102) Divergence Detected** ($|\text{Divergence}| \ge 15\%$). As divergências detectadas concentram-se no runtime PythonNative no workload W5 (ex.: macOS +15.360% e Linux +11.936% em Regime A), decorrentes de variabilidade na inicialização de módulos e importações dinâmicas do ecossistema LangChain entre sessões frias independentes.
   - **Tool-RAG Speedups:** Calculados dinamicamente em conformidade estrita com a Tabela 5 e Figura 5(b), demonstrando acelerações de prefill de **7.28x** (macOS M4), **4.97x** (Linux x86_64), **4.64x** (Windows 11 NVIDIA) e **9.96x** (Windows Intel iGPU), com redução uniforme de prompt tokens de -87.1% (917 vs. 7.091 tokens).
   - **Workload W5 (Enterprise LangChain Core):** A avaliação semântica LLM-as-a-Judge foi instrumentada especificamente no adaptador LangChain Core em PythonNative (obtendo 1.0/5.0 no macOS M4 devido a incompatibilidade estrita de schema de validação, e 3.0/5.0 no Windows Intel iGPU por execução parcial de consultas). Os runtimes cliente principais (PicoClaw Go, OpenClaw Node.js e Bun) operam via despacho de chamadas determinísticas sem a instrumentação do prompt de avaliação semântica, figurando com `N/A†`.
   - **Invariância de $T_{\text{orch}}$ (Tabela 3):** Confirmada com limite real de $|\Delta T_{\text{orch}}| < 2.0\text{ ms}$ (máximo de $1.95\text{ ms}$ observado no Windows NVIDIA).
   - **Penalidades de KV Thrashing $T_2/T_3$ (Tabela 4):** Penalidade mínima e total de 6.85x e 19.46x no macOS M4, 1.96x e 2.63x no Linux x86_64, e 2.01x e 2.30x no Windows 11 NVIDIA.
   - **Ciclos de CPU no Windows (Tabela 1):** Confirmados diretamente dos dados do JSONL como 45.8M ciclos no PicoClaw vs. 528.1M ciclos no OpenClaw Full (sobrecarga de 11.54x).

---

## 5. TAXONOMIA E TRANSPARÊNCIA TOTAL DE VALORES N/A

Nenhum valor `N/A` foi omitido ou substituído artificialmente por `0`. Todas as tabelas, CSVs e o manuscrito incorporam notas técnicas explicando o fundamento físico ou de restrição do sistema operacional:

| Símbolo | Escopo | Razão Técnica e Fundamentação Físico-Arquitetural |
| :--- | :--- | :--- |
| `N/A*` | Windows (NVIDIA e Intel iGPU) — Instruções de Hardware PMC | O kernel do Windows NT bloqueia a leitura de Performance Monitoring Counters (`CR4.PCE`) em anel de usuário não privilegiado (`user-mode`), impedindo acesso direto a `rdpmc`. Como contraprova rigorosa de contagem de bloat, foram amostrados ciclos de CPU via API Win32 oficial `QueryProcessCycleTime` (confirmando sobrecarga de 11.54x em ciclos de CPU: 528.1M vs 45.8M). |
| `N/A†` | Windows (NVIDIA e Intel iGPU) — RSS Peak do PythonNative | O wrapper oficial do Python para Windows (`py.exe`) executa como processo pai efêmero (~4.9 MB) ao despachar o executável filho `python.exe`. Para manter estrita conformidade científica e evitar subestimar a memória do runtime, o dado foi rotulado como stub PID excluído. |
| `N/A†` | Tabela 8 — Quality Score em Runtimes Não-LangChain | Avaliação semântica LLM-as-a-judge uninstrumentada em runtimes de despacho puro de ferramentas cliente (PicoClaw Go, OpenClaw Node.js, Bun JSC). Instrumentada no adaptador PythonNative LangChain core (1.0/5.0 no macOS M4 e 3.0/5.0 no Windows Intel iGPU). |
| `N/A‡` | Todas as Plataformas — Orquestração Direct Neural | A linha de base Direct Neural emite requisições HTTP REST diretamente da infraestrutura de teste para o servidor neural, sem camada intermediária de agente cliente. Portanto, o tempo de orquestração do cliente é identicamente zero por definição arquitetural ($T_{\text{orch}} \equiv 0$). |
| `N/A||` | macOS ARM64 — Bun JSC Engine | O motor Bun (JavaScriptCore) foi avaliado como ablação de motor JavaScript secundário exclusivamente nas máquinas x86_64 (Linux e Windows), sendo omitido do benchmark primário em macOS para focar na comparação canônica V8 vs. Go. |
| `N/A**` | Windows Intel iGPU — Energia de Pacote e VRAM Dedicada | A GPU Intel HD Graphics 4600 utiliza arquitetura de memória compartilhada (UMA) com abertura na RAM do sistema (DDR3), sem barramento PCIe dedicado ou registradores NVML. A telemetria operou em modo de usuário não-elevado sem driver ring-0 (WinRing0/MSR), inviabilizando medições de potência RAPL de pacote. O baseline de repouso foi de $P_{\text{idle}} = 28.50\text{ W}$. |

---

## 6. RELATÓRIO DE PURIFICAÇÃO BIBLIOGRÁFICA (ZERO INVENTADAS)

Foi realizada auditoria completa no arquivo `references.bib` e nas citações do manuscrito `paper/softwarex_manuscript.tex`. Todas as referências não-reais, placeholders ou entradas suspeitas foram eliminadas. O repositório retém estritamente **4 referências seminais, reais, clássicas e verificáveis por DOI/ISBN**:

1. `kalibera2013rigorous`:  
   - **Autores:** Tomas Kalibera, Richard Jones  
   - **Título:** *Rigorous Benchmarking in Reasonable Time*  
   - **Veículo:** ACM International Symposium on Memory Management (ISMM '13), pp. 63–74.  
   - **DOI:** [10.1145/2464157.2464160](https://doi.org/10.1145/2464157.2464160)  
   - **Uso no Estudo:** Justificativa da análise de dependência serial ($n_{\text{eff}}$) e eliminação de viés de medição.
2. `maricq2018taming`:  
   - **Autores:** Alexis Maricq, Dmitry Duplyakin, Ivo Jimenez, Carlos Maltzahn, Ryan Stutsman, Robert Ricci  
   - **Título:** *Taming Performance Variability*  
   - **Veículo:** USENIX Symposium on Operating Systems Design and Implementation (OSDI '18), pp. 409–425.  
   - **ISBN:** 978-1-939133-08-3  
   - **Uso no Estudo:** Metodologia de caracterização de variabilidade e isolamento de jitter em sistemas reais.
3. `goldsman1997methods`:  
   - **Autores:** David Goldsman, Bruce W. Schmeiser  
   - **Título:** *Methods for Estimating the Variance of the Sample Mean*  
   - **Veículo:** ACM Transactions on Modeling and Computer Simulation (TOMACS), 7(3):389–418.  
   - **DOI:** [10.1145/259207.259235](https://doi.org/10.1145/259207.259235)  
   - **Uso no Estudo:** Formulação matemática para cálculo de variância e intervalos de confiança sob correlação serial via Block Bootstrap.
4. `kwon2023vllm`:  
   - **Autores:** Woosuk Kwon, Zhuohan Li, Siyuan Zhuang, Ying Sheng, Lianmin Zheng, Cody Hao Yu, Joseph E. Gonzalez, Hao Zhang, Ion Stoica  
   - **Título:** *Efficient Memory Management for Large Language Model Serving with PagedAttention*  
   - **Veículo:** ACM Symposium on Operating Systems Principles (SOSP '23), pp. 611–626.  
   - **DOI:** [10.1145/3600006.3613165](https://doi.org/10.1145/3600006.3613165)  
   - **Uso no Estudo:** Fundamentação da dinâmica de KV-cache, fragmentação de memória e reutilização de prefixos.

**Separação de Especificações Técnicas:** As menções nas notas da Tabela 1 a Microsoft Learn (`QueryProcessCycleTime`), Intel® 64 and IA-32 SDM Vol. 3B Ch. 20 e Python PEP 397 são identificadas explicitamente como *Technical Specifications / Architecture Documentation*, mantendo a base bibliográfica acadêmica restrita às 4 obras seminais citadas no `.bib`.

---

## 7. ARTEFATOS E FIGURAS REGENERADOS (300 DPI, 100% EM INGLÊS)

Todos os gráficos de publicação foram regenerados com dados 100% consolidados das 4 plataformas, tipografia nítida em 300 DPI, formatação em subplots sem sobreposições e texto padronizado em inglês:

| Artefato de Publicação | Resolução & Formato | Correções e Conformidade Visual |
| :--- | :--- | :--- |
| `figures/fig1_architecture_topology.png` | 300 DPI PNG | Diagrama topológico com 4 nós físicos de hardware. Caixa inferior expandida, texto azul quebrado em duas linhas sem encostar na borda, e notas traduzidas 100% para inglês. |
| `figures/fig2_exp1_cold_start_rss.png` | 300 DPI PNG | Subplot A explicita escopo W1 com nota sobre Intel iGPU. Subplot B com hachura consolidada única para stub Python no Windows sem sobreposição de rótulos vermelhos. |
| `figures/fig3_exp2_latency_overhead.png` | 300 DPI PNG | Subplot A cobre as 4 plataformas em W2. Subplot B com limite Y aumentado (0 a 3.2), legenda no topo esquerdo e anotação W3 reposicionada sem colisão. |
| `figures/fig4_exp3_energy_edp.png` | 300 DPI PNG | Banner de aviso reposicionado como subtítulo limpo acima dos painéis (sem sobrepor legendas). Rodapé traduzido para inglês com justificativa de N/A** no Intel iGPU. |
| `figures/fig5_exp4_tools_and_bloat.png` | 300 DPI PNG | Speedups Tool-RAG consolidados (7.28x macOS, 4.97x Linux, 4.64x Win NVIDIA, 9.96x Win Intel). Nota metodológica alinhada com Tabela 5. |
| `figures/fig6_pmc_hardware_counters.png`| 300 DPI PNG | Contadores PMC de instruções de hardware em ARM64 e x86_64, com nota técnica em inglês sobre restrições de user-mode do Windows. |

---

## 8. THREATS TO VALIDITY & LIMITAÇÕES TÉCNICAS

1. **Assimetria de Offload (UMA vs. dGPU x86 Híbrida):**  
   O Apple M4 opera com 24 GB de memória física unificada a 120 GB/s, permitindo offload de 100% das camadas (`-ngl 99`). No Dell G15 (Linux e Windows 11), a dGPU possui teto físico de 4 GB GDDR6, exigindo offload híbrido (`-ngl 16`, ~3.0 GiB na VRAM e restante na RAM host DDR5 via AVX2), saturando o barramento PCIe 4.0 a ~5.2 GB/s sustentados. No Intel Graphics (MSI Z97), todo o processamento neural opera na RAM host DDR3. Por conseguinte, ganhos absolutos de TTFT em Regime B não são diretamente comensuráveis entre nós heterogêneos.
2. **Restrições de Privilégio em Modo de Usuário no Windows:**  
   Em ambientes Windows corporativos e de pesquisa sem permissão de administrador ou driver em anel de kernel, a leitura de MSR (RAPL) e PMU (`CR4.PCE`) é restrita. A suíte adotou medição de ciclos de processo Win32 (`QueryProcessCycleTime`) como substituto fiel.
3. **Horizonte de Avaliação em Modelos Multimodais (LMMs):**  
   Os experimentos concentram-se em agentes baseados em texto e schema JSON. Modelos multimodais com ingestão visual direta (ex.: LLaVA, Pixtral) expandem massivamente o número de tokens de patch de imagem, o que deslocará a sobrecarga do orquestrador para processamento de framebuffer zero-copy na versão 2.0 do benchmark.

---

## 9. CONCLUSÃO DA AUDITORIA

O projeto `picoclaw-vs-openclaw-benchmark` atende plenamente aos critérios de rigor metodológico, reprodutibilidade e transparência para periódicos científicos de alto impacto (*SoftwareX*, *JOSS*). Todos os artefatos empíricos estão validados, sincronizados e comitados na branch `main`.

**Resultado:** Auditoria e Validação Empírica Concluídas com Êxito (Conforme SoftwareX / JOSS).
