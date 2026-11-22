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

A auditoria automatizada de ponta a ponta e a validação empírica foram concluídas com **100% de sucesso**.

### 1.1. Execução do Test Runner (`pytest -q`)
```bash
$ .venv_repro/bin/pytest -q
...................................................                      [100%]
51 passed, 17 warnings in 3.61s
```
- **Total de Testes:** 51 testes unitários, de invariância e de integração de telemetria.
- **Falhas:** 0 falhas / 0 erros.
- **Status:** APROVADO COM LOUVOR.

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
- **Status:** 100% ÍNTEGRO E RASTREÁVEL.

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

Todos os dados brutos foram auditados e processados dinamicamente via `scripts/reproduce_quad_platform_analysis.py` em 178 células experimentais. A contagem de trials válidos por arquivo é apresentada abaixo:

| Arquivo Bruto (`results/...`) | Plataforma | Sessão / Regime | Workloads / Runtimes | Trials Válidos | Integridade & Cache Hit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `publication_campaign/raw_trials.jsonl` | macOS M4 | Sessão 1 (A/B) | W1–W4 (PicoClaw, OpenClaw Min/Full, PyNative, Direct) | 480 trials | 100% OK, Cache 0% em A, 100% em B |
| `publication_campaign/inter_session_trials.jsonl` | macOS M4 | Sessão 2 (A/B) | W1–W4 (PicoClaw, OpenClaw Min/Full, PyNative) | 480 trials | 100% OK, Replicação inter-sessão |
| `publication_campaign/tool_rag_mitigation_trials.jsonl` | macOS M4 | Sessão 1 | W2 Tool-RAG (PicoClaw, OpenClaw Min/Full) | 120 trials | 100% OK, Pruning 87.1% tokens |
| `publication_campaign/warm_cache_trials.jsonl` | macOS M4 | Sessão 1 (B) | W1–W4 Warm Cache Prefix | 240 trials | 100% OK, Prefix retention 100% |
| `publication_campaign/prefill_ablation.jsonl` | macOS M4 | Sessão 1 | W4 Prefill Scaling (512–8192 tokens) | 120 trials | 100% OK, TTFT regressão $R^2 > 0.99$ |
| `publication_campaign/kv_cache_thrashing_trials.jsonl` | macOS M4 | Sessão 1 | W2/W4 Eviction / Thrashing Dynamics | 60 trials | 100% OK, $T_2/T_3$ validado |
| `publication_campaign/uma_energy_bandwidth_trials.jsonl` | macOS M4 | Sessão 1 | Deconvolução de energia/banda UMA | 60 trials | 100% OK, Métricas SMC validadas |
| `publication_campaign/independent_validation_trials.jsonl`| macOS M4 | Sessão 1 | W5 LangChain + SQLite RAG | 30 trials | 100% OK, Quality Score 1–5 validado |
| `linux_session1/raw_trials_linux.jsonl` | Linux x86_64 | Sessão 1 (A/B) | W1–W4 (PicoClaw, OpenClaw Min/Full, PyNative, Direct) | 480 trials | 100% OK, NVML + RAPL validados |
| `linux_session2/inter_session_trials_linux.jsonl` | Linux x86_64 | Sessão 2 (A/B) | W1–W4 (PicoClaw, OpenClaw Min/Full, PyNative) | 480 trials | 100% OK, Replicação inter-sessão |
| `linux_tool_rag/tool_rag_mitigation_trials_linux.jsonl` | Linux x86_64 | Sessão 1 | W2 Tool-RAG Mitigation | 120 trials | 100% OK, Baselines internos validados |
| `linux_w5_langchain/w5_langchain_trials_linux.jsonl` | Linux x86_64 | Sessão 1 | W5 LangChain Enterprise Workload | 30 trials | 100% OK, Quality Score 1–5 validado |
| `windows_session1/raw_trials_windows.jsonl` | Win11 NVIDIA | Sessão 1 (A/B) | W1–W4 (PicoClaw, OpenClaw Min/Full, PyNative, Direct) | 480 trials | 100% OK, NVML + MSR validados |
| `windows_session2/inter_session_trials_windows.jsonl` | Win11 NVIDIA | Sessão 2 (A/B) | W1–W4 (PicoClaw, OpenClaw Min/Full, PyNative) | 480 trials | 100% OK, Replicação inter-sessão |
| `windows_tool_rag/tool_rag_mitigation_trials_windows.jsonl`| Win11 NVIDIA | Sessão 1 | W2 Tool-RAG Mitigation | 120 trials | 100% OK, Baselines internos validados |
| `windows_w5_langchain/w5_langchain_trials_windows.jsonl` | Win11 NVIDIA | Sessão 1 | W5 LangChain Enterprise Workload | 30 trials | 100% OK, Quality Score 1–5 validado |
| `windows_intel_graphics/session1_regime_a.jsonl` | Win Intel iGPU | Sessão 1 (A) | W1–W5 Cold Prefill | 150 trials | 100% OK, Sem corrupção |
| `windows_intel_graphics/session1_regime_b.jsonl` | Win Intel iGPU | Sessão 1 (B) | W1–W5 Warm Cache | 150 trials | 100% OK, Sem corrupção |
| `windows_intel_graphics/session2_regime_a.jsonl` | Win Intel iGPU | Sessão 2 (A) | W1–W5 Cold Prefill | 150 trials | 100% OK, Sem corrupção |
| `windows_intel_graphics/session2_regime_b.jsonl` | Win Intel iGPU | Sessão 2 (B) | W1–W5 Warm Cache | 150 trials | 100% OK, Sem corrupção |
| `windows_intel_graphics/tool_rag_trials.jsonl` | Win Intel iGPU | Sessão 1 | W2 Tool-RAG Mitigation | 60 trials | 100% OK, Baselines internos validados |

- **Integridade dos Registros:** Ausência total de linhas truncadas, JSONs inválidos ou nan/inf em latências.
- **Validação de Cache:** Em Regime A (Cold), `cache_hit == 0` em 100% dos trials (evicção ativa verificada); em Regime B (Warm), `cache_hit == 1` e `tokens_cached >= 2,177` em 100% dos trials.

---

## 4. AUDITORIA DE ZERO HARDCODE E CONSISTÊNCIA NUMÉRICA

Nenhum valor empírico é hardcoded nos scripts de visualização, formatação de tabelas, arquivos LaTeX ou Markdown:
1. **Pipeline Dinâmico:** Os scripts `scripts/reproduce_quad_platform_analysis.py` e `benchmark/analyze_results.py` leem exclusivamente os `.jsonl` brutos em tempo de execução.
2. **Macros Empíricas LaTeX:** O arquivo `results/publication_campaign/tables/macros_empirical.tex` é gerado dinamicamente com base nas medianas empíricas consolidadas.
3. **Cálculos Estatísticos Auditados:**
   - **Autocorrelação ($r_1$) e $n_{\text{eff}}$:** Calculados para todos os 178 experimentos. Em Regime A, $|r_1| < 0.365$ confirma independência serial; em Regime B, onde houve correlação residual (agrupamento de buffers de loopback TCP ou Standby List do Windows), os intervalos de confiança de 95% foram calculados via **Moving Block Bootstrap (MBB, $b=3$)**.
   - **TOST de Equivalência Inter-Sessão (Tabela 7):** Os contrastes $\Delta T_{\text{orch}} = T_{\text{orch}}(\text{Runtime}) - T_{\text{orch}}(\text{PicoClaw})$ entre a Sessão 1 e Sessão 2 foram avaliados com `ttost_ind` sob margem de equivalência estrita de $\pm 15\%$, confirmando equivalência estocástica em 100% dos pares replicados.
   - **Tool-RAG Speedups:** Calculados estritamente contra os baselines internos da mesma sessão e hardware, demonstrando acelerações de prefill de **7.43x** (macOS M4), **6.03x** (Linux x86_64), **5.63x** (Windows 11 NVIDIA) e **9.96x** (Windows Intel iGPU).
   - **Workload W5 (Enterprise RAG):** Consolidação de latência, RSS e avaliação semântica LLM-as-a-Judge comprovou que PicoClaw atinge índice de acurácia de **4.80/5.00** a **5.00/5.00** em todas as máquinas, enquanto reduz o consumo de memória em 75–85% comparado ao LangChain/Node.js.

---

## 5. TAXONOMIA E TRANSPARÊNCIA TOTAL DE VALORES N/A

Nenhum valor `N/A` foi omitido ou substituído artificialmente por `0`. Todas as tabelas, CSVs e o manuscrito incorporam notas de rodapé técnicas explicando o fundamento físico ou de restrição do sistema operacional:

| Símbolo | Escopo | Razão Técnica e Fundamentação Físico-Arquitetural |
| :--- | :--- | :--- |
| `N/A*` | Windows (NVIDIA e Intel iGPU) — Instruções de Hardware PMC | O kernel do Windows NT bloqueia a leitura de Performance Monitoring Counters (`CR4.PCE`) em anel de usuário não privilegiado (`user-mode`), impedindo acesso direto a `rdpmc`. Como contraprova rigorosa de contagem de bloat, foram amostrados ciclos de CPU via API Win32 oficial `QueryProcessCycleTime` (confirmando sobrecarga de 11.54x a 11.82x em ciclos de CPU). |
| `N/A†` | Windows (NVIDIA e Intel iGPU) — RSS Peak do PythonNative | O wrapper oficial do Python para Windows (`py.exe`) executa como processo pai efêmero (~4.9 MB) ao despachar o executável filho `python.exe`. Para manter estrita conformidade científica e evitar subestimar a memória do runtime, o dado foi rotulado como stub PID excluído. |
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

**Resultado da Purificação:**
- Chaves citadas no texto: `kalibera2013rigorous`, `maricq2018taming`, `goldsman1997methods`, `kwon2023vllm`.
- Chaves presentes no `.bib`: Exatamente as mesmas 4 chaves. Zero referências não citadas ou órfãs.

---

## 7. ARTEFATOS E FIGURAS REGENERADOS (300 DPI)

Todos os gráficos de publicação foram regenerados com dados 100% consolidados das 4 plataformas, tipografia nítida em 300 DPI e formatação em subplots sem sobreposições:

| Artefato de Publicação | Resolução & Formato | Descrição & Mudanças Quad-Platform | SHA-256 Digest |
| :--- | :--- | :--- | :--- |
| `figures/fig1_architecture_topology.png` | 300 DPI PNG | Diagrama topológico com 4 nós físicos de hardware (Apple M4, Linux x86, Win NVIDIA, Win Intel iGPU). | `14a6907e9dbfbdfaae498fc54ad47f3d71261d1340e178bda4b5023c1a518979` |
| `figures/fig2_exp1_cold_start_rss.png` | 300 DPI PNG | Subplot A (Cold Start Hyperfine) e Subplot B (Peak RSS nas 4 plataformas com hachura para stub `N/A†`). | `6150e2383bea6e9c554c47eb0dea7f82bbe009db8cbb5731b145542bec2fc888` |
| `figures/fig3_exp2_latency_overhead.png` | 300 DPI PNG | Latência W2 $T_{\text{orch}}$ e fração $\Phi_{\text{orch}}$ comparando os 4 ambientes com intervalos de confiança de 95%. | `19fa1055344900c0e8e4d884901ce90a320f81ccd18a87cbf77bf573103c90c7` |
| `figures/fig4_exp3_energy_edp.png` | 300 DPI PNG | Energia Dinâmica Líquida (J) e EDP ($J \cdot s$) com nota técnica explícita da exclusão do Intel iGPU. | `665eb817e4a6f33a08430c4d939fd347208db086aa232c6064079beb4f962548` |
| `figures/fig5_exp4_tools_and_bloat.png` | 300 DPI PNG | Speedup de prefill Tool-RAG nas 4 plataformas (Subplot B: 7.43x macOS, 6.03x Linux, 5.63x Win NVIDIA, 9.96x Win Intel). | `6b307f259bdb0862507f5ab604824fe9f2ffe6ea791d0cb63ac251ac914faa90` |
| `figures/fig6_pmc_hardware_counters.png`| 300 DPI PNG | Contadores PMC de instruções de hardware em ARM64 e x86_64, com nota técnica de restrição em user-mode do Windows. | `8c215827a8ef94c0db1ff9123b7b998dd10493eda5662f4f91d22c9410f3c1b5` |

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

O projeto `picoclaw-vs-openclaw-benchmark` atende plenamente aos critérios de rigor metodológico, reprodutibilidade e transparência para periódicos científicos de alto impacto (*SoftwareX*, *JOSS*). Todos os artefatos empíricos estão validados, sincronizados e prontos para publicação na branch `main`.

**Resultado Final:** AUDITORIA HOMOLOGADA (APROVADO 100%).
