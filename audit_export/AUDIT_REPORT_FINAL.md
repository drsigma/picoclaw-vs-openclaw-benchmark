# AUDIT_REPORT_FINAL.md
# Relatório de Auditoria Final de Reprodutibilidade e Sistemas (Quad-Platform)
## Consolidação Multi-Plataforma, Verificação Criptográfica e Consistência Empírica

**Projeto:** `picoclaw-vs-openclaw-benchmark`  
**Autor Principal:** Rafael Paniccia Cassetta (UFABC)  
**Operador do Testbed Windows:** `drsgima`  
**Data da Consolidação:** 2026-11-22  
**Branch Auditada:** `main`  
**Escopo Empírico:** Quad-Platform (4 ambientes físicos distintos, 35 arquivos `.jsonl` em disco, 190 células experimentais).  

---

## 1. VERIFICAÇÃO AUTOMATIZADA DE TESTES E INTEGRIDADE

- **Suíte de Testes (`pytest -q`):** `57/57 tests passed` (saída completa salva em `audit_export/pytest_output.txt`) (testes unitários, invariância de protocolo, alinhamento IC 90% <-> TOST e segregação de W5).
- **Manifesto Criptográfico (`scripts/verify_manifest.py`):** Todos os `277/277` arquivos rastreados em `data/manifest_sha256.json` conferem com suas assinaturas SHA-256 em disco (0 arquivos ausentes, 0 divergências de hash).
- **Pacote de Revisão e Exportação Modular (`audit_export_quad_platform.zip`):** Contém `references.bib`, `scripts/reproduce_quad_platform_analysis.py`, `scripts/verify_manifest.py`, `data/manifest_sha256.json`, `audit_export/pytest_output.txt`, `audit_export/REVIEW_PACKAGE_README.md` (instruções de acesso aos 35 `.jsonl`), todas as 6 figuras (300 DPI), todas as 8 tabelas (`.md`/`.tex`) e sumários CSV/JSON, acompanhados dos chunks textuais leves em `audit_txt_chunks/` (<= 150 KB por arquivo).

---

## 2. COBERTURA QUAD-PLATAFORMA (4 AMBIENTES FÍSICOS)

| ID | Plataforma / Perfil | Arquitetura | CPU & Threads | Memória & Barramento | Acelerador Neural (GPU) | Telemetria Nativa | $P_{\text{idle}}$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P1** | **macOS ARM64** | Apple Silicon M4 | 10 cores (4P+6E) | 24 GB LPDDR5X (120 GB/s UMA) | Metal 3 (`-ngl 99`, offload integral) | Apple SMC `powermetrics` + XNU `libproc` | 1.20 W |
| **P2** | **Linux x86_64** | Ubuntu 26.04 LTS (Kernel 7.0) | Intel Core i5-12500H (16T) | 30.5 GiB DDR5-4800 | NVIDIA RTX 3050 Laptop (4 GB, híbrido `-ngl 16`) | Intel RAPL MSR + NVML + `perf_event_open` | 19.71 W / 20.08 W |
| **P3** | **Windows 11 NVIDIA** | Win11 Pro (Build 26200) | Intel Core i5-12500H (16T) | 31.7 GiB DDR5-4800 | NVIDIA RTX 3050 Laptop (4 GB, híbrido `-ngl 16`) | Intel MSR RAPL + NVML DLL + Win32 PSAPI / Cycles | 24.13 W / 21.96 W |
| **P4** | **Windows Intel iGPU** | Win10 Pro (Build 19045) | Intel Core i7-4790K (4C/8T) | 15.88 GiB DDR3-1600 (Shared RAM) | Intel HD Graphics 4600 (UMA Shared Aperture) | Win32 PSAPI + `QueryProcessCycleTime` (user-mode) | 28.50 W |

> **Verificação Terminológica:** Confirmada a presença de **4/4 plataformas** nos dados brutos, tabelas, figuras e documentação principal, com nomenclatura atualizada para **quad-platform**.

---

## 3. INVENTÁRIO DE ARQUIVOS E HASHES SHA-256 (35 ARQUIVOS `.jsonl`)

Tabela gerada dinamicamente por varredura direta dos arquivos `.jsonl` em disco, idêntica à Seção 6 de `audit_export/Systems_Replication_Report.md`:

| Relative Path | Platform | Session Identifier | Role | Workloads | Total Lines | Measured Trials | Warmup Trials | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | :--- |
| `results/publication_campaign/raw_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `raw` | W1, W2, W3, W4, W5 | 825 | 750 | 75 | `9f624bd429c810fbbaa2c952b18ea718b17d42b7b8667d6419c561ec7f60ed01` |
| `results/publication_campaign/warm_cache_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `warm` | W1, W2, W3, W4, W5 | 825 | 750 | 75 | `bd2854fd866a1d1b963ef7cfe8e659e6c68b59794c1cf6c3ac4f38952f79dea6` |
| `results/publication_campaign/kv_cache_thrashing_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `kv` | W2 | 90 | 90 | 0 | `48532324bcb7ad5c0d072c80571480e308dfdf48029312cded4677f47bbd3081` |
| `data/mcp_live_transport_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `mcp` | W2 | 135 | 135 | 0 | `03e8d3bd247e29c498e87a727daaa41d47e4d3b6005713d25a0a33301d3232c4` |
| `results/publication_campaign/tool_rag_mitigation_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `rag` | W1, W2, W3, W4 | 1056 | 960 | 96 | `3631f7843cef17e9a6c53fd2fc0970164c10ec090433d1f034e4d3238e35dc22` |
| `results/publication_campaign/prefill_ablation.jsonl` | macOS (M4) | `darwin_m4_session1` | `prefill` | 8 conditions | 528 | 480 | 48 | `ce1a12908ef22c0c40b1ff42c3a17a0914779234d9e81e003c7cf2d1b2ee9f5f` |
| `results/publication_campaign/uma_energy_bandwidth_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `uma` | W2, W3 | 120 | 120 | 0 | `960dbbe9c568134175a5c049a3e5f936bcebeb69c93777c4dc7037c6a58a31e3` |
| `data/external_framework_langchain_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `langchain` | W1, W2, W3, W4 | 144 | 120 | 24 | `2fe416fbf8b74ca4dcd18bfb7bb58f69044fa31b8c5fb60a9f3f3658ea458365` |
| `results/publication_campaign/inter_session_trials.jsonl` | macOS (M4) | `darwin_m4_session2` | `warm` | W1, W2, W3, W4, W5 | 825 | 750 | 75 | `ca99fe1748f8e4c171f4a180e258c183797aae3291f7e0d3e44433c77e106ba0` |
| `data/linux_x86_64_session1/raw/raw_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `65f27603213370acfc317357c2c8a01f2abb664858c443b1ae27941d9d9d54a5` |
| `data/linux_x86_64_session1/raw/warm_cache_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `c7388d9d64c9b765ff29e4c91d7e5406b02764cc7cac48d6c7a06d0fd0962d67` |
| `data/linux_x86_64_session1/raw/kv_cache_thrashing_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `kv` | W2 | 184 | 180 | 4 | `b5217cdfae6f7ef23ee994b2555e5050150da3ba6303fa250550d1534b6ec559` |
| `data/linux_x86_64_session1/raw/mcp_live_transport_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `mcp` | W2 | 297 | 270 | 27 | `e8ba4fcbc7403346fb946e524571fe6bf69722eee7d58a560eaceccd1dd7c5f8` |
| `data/linux_x86_64_session1/raw/tool_rag_mitigation_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `ac3c0f22fba876213b9ebe3f6e49edaa5e0c71446827ad6a9139bddf14650b32` |
| `data/linux_x86_64_session2/raw/raw_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `43df3c3249528937871d9728bb4437107696117be1ec3af8f171f457a810957b` |
| `data/linux_x86_64_session2/raw/warm_cache_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `3767a65018317e9e3e93efb0b595e6bc64150b2a454cce7d7baba473f9d379da` |
| `data/linux_x86_64_session2/raw/kv_cache_thrashing_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `kv` | W2 | 184 | 180 | 4 | `c67bfcd561c8ef224a44221a37494c4886d3598eaff1a18f4788977fcf20a328` |
| `data/linux_x86_64_session2/raw/mcp_live_transport_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `mcp` | W2 | 297 | 270 | 27 | `907a8e21bc41eedc92f3fec78b2e9dc46fd2fd31e80a9e6073426570b5c655e9` |
| `data/linux_x86_64_session2/raw/tool_rag_mitigation_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `65434ed3546fbb07f6fcabadeafe64762f4a774c7faab56ee7c3c552dd2d4598` |
| `data/windows_x86_64_session1/raw/raw_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `264db96648f43c8301a936cd9e8a26895a8c79d284b5a78dd62021a1b4006cf9` |
| `data/windows_x86_64_session1/raw/warm_cache_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `3091e23b550627a6b34b692f50566cf99f12ab3ac3fda820dbd2e66a953de019` |
| `data/windows_x86_64_session1/raw/kv_cache_thrashing_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `kv` | W2 | 184 | 180 | 4 | `5ab229460ef19505cd721cf795d7569337212a81fdd3652aa3275a4fb0f8de79` |
| `data/windows_x86_64_session1/raw/mcp_live_transport_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `mcp` | W2 | 297 | 270 | 27 | `9888d6edfabe937e2b0e85845314479b361013ba0fed24220ce58bf206abffab` |
| `data/windows_x86_64_session1/raw/tool_rag_mitigation_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `449bc5204c6f1cd222002eeebd95a3ebbdc45915002a188eb4fa4a7a3b1848f9` |
| `data/windows_x86_64_session2/raw/raw_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `f42f751681083f82787947c10244fecdd24c21ba6e123abd3752870d30568297` |
| `data/windows_x86_64_session2/raw/warm_cache_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `d2df5802ed7c48e3064da8d5eabd27e9f494756bffdb4ad1429560c5286eb891` |
| `data/windows_x86_64_session2/raw/kv_cache_thrashing_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `kv` | W2 | 184 | 180 | 4 | `f4ac5017ceae16ff4c28b936b988d5f76f96f225e81de1d627970ccb5ce28786` |
| `data/windows_x86_64_session2/raw/mcp_live_transport_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `mcp` | W2 | 297 | 270 | 27 | `d9b1e3500af1b210405a7c87de1c6d442ccba36a41e355a99bba68ab16d12e36` |
| `data/windows_x86_64_session2/raw/tool_rag_mitigation_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `ad45f15cb9bea1c483692b6e4dcf39062c709b4f2f2fad1267316692ac616e62` |
| `data/windows_intel_graphics_session1/raw/raw_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session1` | `raw` | W2, W5 | 330 | 300 | 30 | `e6993e9edeb9964f2109972da4444e6bca4d9952260961eebf1a3286d2a71d80` |
| `data/windows_intel_graphics_session1/raw/warm_cache_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session1` | `warm` | W2, W5 | 330 | 300 | 30 | `081809a8c7b44808fb0cfe41d4bdf7a08d77e68f8e16dfcf1f678ecfe5b4f7ab` |
| `data/windows_intel_graphics_session1/raw/tool_rag_mitigation_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session1` | `rag` | W2 | 132 | 120 | 12 | `b4501867f7a7642c18f31130f0f35e926e9aeb3e19d8a028ce32acf28afff669` |
| `data/windows_intel_graphics_session2/raw/raw_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session2` | `raw` | W2, W5 | 330 | 300 | 30 | `920d68b0197e3039021a1ca327b41807c2cd7b60ed1b606371f6d30e65854a33` |
| `data/windows_intel_graphics_session2/raw/warm_cache_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session2` | `warm` | W2, W5 | 330 | 300 | 30 | `d922a01b5dd42bd5ce8b4b9248bf6a4cb636a45384c025d9bffcb010f021e22c` |
| `data/windows_intel_graphics_session2/raw/tool_rag_mitigation_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session2` | `rag` | W2 | 132 | 120 | 12 | `34736fbad16b3fb5d499c14805a4e4700d21337ed7a57090bad8b98811a04157` |
| **TOTAL (35 files)** | **4 Platforms** | **All Sessions** | **All** | **W1--W5 + Ablations** | **18,616** | **16,995** | **1,621** | **SHA-256 Computed** |

---

## 4. GERAÇÃO DINÂMICA A PARTIR DOS JSONL BRUTOS

Todos os números reportados nos documentos, tabelas e gráficos derivam de `scripts/reproduce_quad_platform_analysis.py` sobre os `.jsonl` listados na Seção 3:

- **Autocorrelação Serial em Ambos os Regimes e Ajuste na Tabela 2 (M4):** Dependência serial ($|r_1| > 2/\sqrt{30} \approx 0.365$) ocorreu em **20/95** células no **Regime A (Cold)** e em **27/95** células no **Regime B (Warm)** (total **47/190**). Na Tabela 2 (excluindo `python_native` W5 por M1), o ajuste de variância de Mann-Whitney por $n_{\text{eff}}$ para células com $r_1 > 0$ mantém **91/146** contrastes significativos após Holm-Bonferroni (vs. **99/146** no teste padrão; **8** contrastes marcados `(NS*)` perdem significância sob correção de $r_1$, todos no Linux x86_64).
- **Estacionariedade e Drift Temporal (M7):** Em 190 células analisadas via regressão linear com correção Holm-Bonferroni, **188/190 (98.9%)** não apresentaram drift significativo ($p_{\text{adj}} \ge 0.05$) e **2/190** foram significativas. O pior caso de inclinação entre células válidas (excluindo `python_native` W5) foi **0.599%/rep** (`Windows Intel iGPU`, `Regime B (Warm Cache)`, `neural_baseline`, `W5`, $p_{\text{adj}}=1$); incluindo o braço segregado W5, o máximo bruto foi **1.376%/rep** em `Windows 11` `Regime B (Warm Cache)` `python_native` `W5` ($p_{\text{adj}}=1$).
- **Throttling por Delta Intra-Trial (M8):** No Linux x86_64, `cpu_pkg_throttle_events` mede o delta intra-trial (`end - start` entre threads lógicos), com incrementos positivos em **884/900** trials do Regime A (máx. **120,948**/trial) e **768/900** do Regime B, documentando throttling real de CPU móvel sob offload híbrido `-ngl 16`; nas GPUs discretas (Linux e Windows 11 NVIDIA), `gpu_thermal_throttle_active_end` registrou **0** eventos e `gpu_sw_power_cap` (`0x04`) registrou **0** eventos no Windows NVIDIA.
- **Replicação Inter-Sessão e TOST em Blocos com SESOI Fixo (Tabela 7; M2--M5):** Nos **95 pares válidos** (**7 pares confundidos de `python_native` W5 excluídos por M1**) avaliados via Moving Block Bootstrap ($b=3$, $B=5{,}000$; Künsch 1989) com **SESOI fixo pré-especificado $\Delta_{\text{SESOI}} = \pm 5.0\text{ ms}$** e **IC 90%** alinhado a $\alpha = 0.05$ (Schuirmann 1987; Lakens 2017): **76 (80.0%)** `Equivalent`, **0 (0.0%)** `Different`, e **19 (20.0%)** `Inconclusive`.
- **Tool-RAG Schema Pruning (Tabela 5 e Figura 5b; M6):** Redução de $-87.1\%$ em tokens de prompt (7.091 para 917 tokens). Acelerações em Regime A (`OpenClaw Tool-RAG`) vs. **54-Tool Full**: **7.28x** (macOS M4, baseline interno), **5.16x** (Linux x86_64), **4.64x** (Windows 11 NVIDIA) e **9.96x** (Windows Intel iGPU); e vs. **15-Tool Minimal**: **2.10x**, **1.79x**, **1.71x** e **2.35x**, respectivamente (nos 3 nós x86_64 os braços podados referenciam os baselines da campanha principal do mesmo nó).
- **KV-Cache Thrashing $T_2/T_3$ (Tabela 4):** Penalidades medidas (Minimal / Full): **6.85x / 19.46x** no macOS M4, **1.48x / 2.63x** no Linux x86_64, e **2.01x / 2.30x** no Windows 11 NVIDIA. (Sub-experimento não executado no Intel iGPU, dedicado a W2/W5.)
- **Invariância de $T_{\text{orch}}$ (Tabela 3):** Limite empírico observado de $|\Delta T_{\text{orch}}| < 2.0\text{ ms}$ (máximo de **$1.95\text{ ms}$** em PicoClaw (Go) on Windows 11 NVIDIA).
- **Ciclos de CPU no Windows (Tabela 1 e Figura 6c/d):** No Windows 11 NVIDIA: **45.8M** ciclos no PicoClaw vs. **528.1M** no OpenClaw Full (**11.54x**). No Windows Intel iGPU: **87.8M** ciclos no PicoClaw vs. **1446.1M** no OpenClaw Full (**16.47x**).
- **Workload W5 — Auditoria de Tokens, Segregação de `python_native` (M1) e Desescopo do Protótipo LLM-as-a-Judge (E3):** Todos os 4 ambientes incluídos com auditoria de `prompt_tokens`, `completion_tokens`, `tool_calls` e `finish_reason` em `audit_export/w5_token_and_schema_audit.csv`. Como `python_native` (LangChain Core) apresentou falha de validação de schema / prompt truncado (`1,287/26` tokens vs. `2,007–6,921/33–38` nos orquestradores comparáveis; TTFT `50.0 ms` vs. `4,939.5 ms` no macOS Regime A; anomalia de `1,416.3 ms` de $T_{\text{orch}}$ no Linux Warm), foi **excluído das Tabelas 2 e 7** e **segregado na Parte B da Tabela 8** (`¶`). **Não houve avaliação comparativa de qualidade de saída entre runtimes:** o protótipo `W5_langchain_real_world/evaluator.py` (usando o mesmo `Meta-Llama-3.2-3B-Instruct Q4_K_M` local em `temperature=0.0`, `max_tokens=150`, rubrica de 1--5 pontos para 3 problemas de orçamento/SLA/compliance com fallback heurístico — sujeito a *same-family / self-evaluation bias*, Zheng et al. 2023) rodou apenas em `python_native` W5 ($N=30$ saídas/regime no macOS e Intel iGPU), onde `1.0/5.0` no macOS (`30/30`, `evaluation_reasoning = "Empty output"`) reflete falha de validação de schema com saída vazia e `3.0/5.0` no Intel iGPU (`30/30`) reflete detecção parcial de 1 problema sem cruzamento documento-banco.

---

## 5. TAXONOMIA DE VALORES `N/A`

Nenhum valor `N/A` foi substituído por `0`. Todos os símbolos estão definidos nas notas das Tabelas 1 e 8:

| Símbolo | Escopo | Justificativa Físico-Arquitetural |
| :--- | :--- | :--- |
| `N/A*` | Windows (NVIDIA e Intel iGPU) — Hardware Instructions | O kernel do Windows NT bloqueia leitura de contadores PMU (`CR4.PCE`) em user-mode sem driver privilegiado. Ciclos de CPU são medidos diretamente via Win32 `QueryProcessCycleTime` (11.54x no NVIDIA; 16.47x no Intel iGPU). |
| `N/A†` | Tabela 8 — `quality_score` (Protótipo Desescopado — E3) | Não houve avaliação comparativa de qualidade entre runtimes. O protótipo `evaluator.py` (`Llama-3.2-3B-Instruct`, rubrica 1--5 pontos, $N=30$/regime, risco explícito de *same-family bias*) rodou apenas em `python_native` W5 (`1.0/5.0` = `Empty output` por falha de schema no macOS; `3.0/5.0` no Intel iGPU) e não foi instrumentado nos runtimes comparáveis (`N/A†`). |
| `N/A‡` | Todas as Plataformas — `neural_baseline` (RSS, Instr/Cycles) | A linha de base neural envia chamadas HTTP diretamente ao `llama-server` sem processo orquestrador cliente ($T_{\text{orch}} \equiv 0$). |
| `N/A§` | Tabelas 1, 8 e Figura 2(b) — `python_native` no Windows (RSS e Cycles) | A invocação via wrapper `py.exe` (PEP 397) captura o PID pai efêmero (~4.9 MB) em vez do processo filho `python.exe`; os dados do stub são excluídos uniformemente em todo o pacote. |
| `N/A||` | macOS ARM64 — Bun JSC Engine | Motor secundário adicionado após o congelamento da campanha primária Cold/Warm no Apple M4; avaliado nas plataformas x86_64 (Linux e Windows), com medições suplementares Warm Session 2 no macOS preservadas em `inter_session_trials.jsonl`. |
| `N/A**` | Windows Intel iGPU — Energia de Pacote e EDP | Intel HD Graphics 4600 opera sobre memória DDR3 compartilhada (UMA) sem sensores NVML dedicados ou driver MSR RAPL em anel zero no modo de usuário ($P_{\text{idle}} = 28.50\text{ W}$). |
| `¶` | Tabela 8 Parte B — `python_native` em W5 (Segregado) | Falha de validação de schema / prompt truncado (`1,287/26` tokens vs. `2,007–6,921/33–38`; TTFT `50 ms` no macOS); excluído de comparações de desempenho/energia/TOST (Tabelas 2 e 7) por M1. |

---

## 6. AUDITORIA BIBLIOGRÁFICA (`references.bib`)

Todas as entradas em `references.bib` foram conferidas contra publicações primárias (21 referências primárias ativas com DOIs/ISBNs/arXiv IDs conferidos):
- **Corrigida:** `maricq2018taming` (nomes reais dos autores conferidos no OSDI '18: *Aleksander Maricq* e *Ryan Stutsman*).
- **Removida/Substituída:** entrada anterior `goldsman1997methods` continha DOI incorreto (`10.1145/259207.259235`, pertencente a outro artigo do TOMACS); substituída pela referência seminal do Moving Block Bootstrap (`kuensch1989jackknife`, DOI: `10.1214/aos/1176347265`).
- **Referências metodológicas adicionadas:** `hoefler2015scientific`, `schuirmann1987comparison`, `lakens2017equivalence` (DOI: `10.1177/1948550617697177`), `mann1947test`, `kruskal1952use`, `holm1979simple`, `cliff1993dominance`, `vargha2000critique`, `weaver2013nondeterminism`, `yao2023react`, `zheng2023judging`, `reddi2020mlperf`, `you2023zeus`, `barroso2007case`, `fahad2019comparative`, `williams2009roofline`, `smith2016software` (além das existentes `kalibera2013rigorous` e `kwon2023vllm`).
- **Especificações Técnicas Separadas:** Documentação de fabricantes e PEPs (Microsoft Learn `QueryProcessCycleTime` / Win32 PSAPI, Intel 64 and IA-32 SDM Vol. 3B Ch. 20, Python PEP 397) são rotuladas explicitamente como documentação técnica nas notas das tabelas.

---

## 7. FIGURAS REGENERADAS (300 DPI, EM INGLÊS) E HASHES SHA-256

| Arquivo | Descrição | SHA-256 |
| :--- | :--- | :--- |
| `figures/fig1_architecture_topology.png` | Quad-platform hardware topology diagram (4 physical nodes, English labels, dynamic dataset count, wrapped sensor boundary notes). | `f9a1bcb1a54ff2aeee6a99407effc742dca7bc31a692cae2f97d48a1fdc16dcb` |
| `figures/fig2_exp1_cold_start_rss.png` | Panel (a) W1 cold latency with numerical labels and Intel iGPU/Bun scope note; Panel (b) W2 Peak RSS across 4 platforms with unified N/A§ (Win Stub) hatched block. | `47a036c7ddcc1068da100170c050a4fef3730fada580acbe3001dee4bda7ea8b` |
| `figures/fig3_exp2_latency_overhead.png` | Panel (a) W2 client T_orch across 4 platforms with numerical labels; Panel (b) W1--W4 Phi_orch with non-overlapping W3 Ranking Inversion callout. | `15082798b8d7601f3a9a358a99cf355bc55ed9577c9597fb3f56a1941c0522f1` |
| `figures/fig4_exp3_energy_edp.png` | Panel (a) W2 net dynamic energy (J & Watts); Panel (b) W2 EDP with uncapped Y-axis (>=6,600 J·s) and numerical bar labels; clean top notice and English Intel iGPU N/A** note. | `7a7eb616b580dff400f54942d57bbb51ba21c2fe1a4cea12ccf9c28970fae2b6` |
| `figures/fig5_exp4_tools_and_bloat.png` | Panel (a) Linux W1--W4 context bloat latency with bar labels; Panel (b) Quad-platform Tool-RAG Cold speedups (7.28x macOS, 5.16x Linux, 4.64x Win NVIDIA, 9.96x Win Intel). | `9eabf3b4d538c0930c8674cd2b2aad66efdbff0da77d845c8d0088ea0787791f` |
| `figures/fig6_pmc_hardware_counters.png` | 2x2 quad-platform microarchitectural figure: (a) macOS ARM64 instructions, (b) Linux x86_64 instructions, (c) Windows NVIDIA & Intel iGPU CPU cycles, (d) 4-platform relative bloat ratios. | `993d02190119dced683fd666955b47f47bed7f2cddc9760fbd594a91740e79e7` |

---

## 8. LIMITAÇÕES E THREATS TO VALIDITY

1. **Assimetria de Offload e Memória (UMA vs. Híbrido PCIe vs. DDR3):** Apple M4 executa offload integral em memória unificada (`-ngl 99`, 120 GB/s). Dell G15 (Linux e Windows 11) opera sob offload híbrido (`-ngl 16`) limitado pela VRAM de 4 GB GDDR6 com streaming PCIe (~5.2 GB/s). Intel HD Graphics 4600 opera sobre RAM DDR3 compartilhada. Contrastes absolutos de latência neural em Regime B são restritos a comparações intra-nó.
2. **Restrições de Privilégio em Modo de Usuário no Windows:** Ausência de acesso ring-0 impede leitura direta de `INST_RETIRED.ANY` (`CR4.PCE`) e RAPL MSR no Intel iGPU; ciclos de processo Win32 (`QueryProcessCycleTime`) são utilizados sem extrapolações sintéticas de IPC.
3. **Escopo Desigual no Windows Intel iGPU — Restrito a W2, W5 e Tool-RAG (E8):** Sobre memória DDR3-1600 compartilhada, os tempos medidos em Regime A (Cold Prefill) variaram de **53.5 s/trial** (`picoclaw` / `openclaw_minimal` W2) até **226.7 s/trial** (`openclaw_full` W2 com 54 ferramentas), com os braços comparáveis de W5 entre **50.1 s e 56.9 s/trial**. Executar toda a matriz W1--W4 (especialmente W4 com 10 turnos, excedendo 8--15 minutos/trial em prefill frio), KV-Thrashing (Tabela 4) e MCP Transport (Tabela 6) em duas sessões de 30 repetições demandaria execução contínua por múltiplos dias, introduzindo drift térmico e interferência do SO. Restringir o nó Intel iGPU a W2, W5 e Tool-RAG captura o overhead de middleware ($T_{\text{orch}}$, RSS, ciclos) e a poda de schema em memória compartilhada dentro de janelas estacionárias viáveis.
4. **Escopo Desigual de Bun JSC — Avaliado Apenas em x86_64 na Matriz Consolidada (E8):** Bun (`bun_minimal`, JavaScriptCore) foi adicionado como ablação secundária de motor JS após o congelamento da campanha primária Cold/Warm no Apple M4 (`raw_trials.jsonl`, `warm_cache_trials.jsonl`). Por isso, Bun aparece nos regimes Cold e Warm dos 3 nós x86_64 (Linux, Windows 11 NVIDIA e Windows Intel iGPU) e como `N/A||` nas tabelas consolidadas do macOS (medições suplementares de Bun Warm Session 2 no macOS permanecem arquivadas em `results/publication_campaign/inter_session_trials.jsonl`, sem síntese artificial de Regime A).
5. **Segregação de `python_native` em W5 (M1) e Desescopo do Protótipo LLM-as-a-Judge (E3):** Falha de validação de schema e truncamento de prompt (`1,287/26` tokens) no LangChain Core tornam `python_native` W5 não comparável aos demais orquestradores (excluído das Tabelas 2 e 7; segregado na Parte B da Tabela 8). O avaliador protótipo `evaluator.py` consultou o mesmo `Llama-3.2-3B-Instruct` local (risco de *same-family bias*) somente em `python_native` W5 ($N=30$/regime); nenhuma afirmação comparativa de qualidade de saída entre runtimes é sustentada.
6. **Throttling Térmico/PL de CPU no Linux x86_64 (M8):** Sob offload híbrido `-ngl 16` (AVX2 + RTX 3050), o pacote Intel Core i5-12500H apresentou deltas intra-trial positivos de `cpu_pkg_throttle_events`, elevando a autocorrelação serial $r_1$ (compensada via ajuste de variância na Tabela 2 e Moving Block Bootstrap na Tabela 7).

---

## 9. RESUMO DO ESTADO DE CONSOLIDAÇÃO

Os artefatos empíricos, tabelas Markdown/LaTeX, figuras em 300 DPI, saída salva de `pytest -q`, instruções de acesso aos 35 `.jsonl`, chunks textuais de auditoria e manifesto SHA-256 foram regenerados dinamicamente a partir dos arquivos brutos em disco.
