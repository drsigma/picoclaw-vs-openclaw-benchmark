# Tecnologias, Bibliotecas e Ferramentas Utilizadas
## Justificativa Metodológica, Arquitetura de Software e Decisões de Engenharia
**Projeto:** Avaliação de Desempenho PicoClaw (Go) vs. OpenClaw (Node.js) no Apple Silicon M4  
**Autor:** Rafael Paniccia Cassetta (RA: 21202520618) — UFABC  
**Disciplina:** CCM313-EEI203 — Análise de Desempenho de Redes e Sistemas (2026.3)  

---

## 1. Por que Python para a Suíte de Benchmark e Automação?

Uma pergunta central na engenharia de testes de desempenho é: **se os agentes competidores foram escritos em Go e Node.js/TypeScript, por que toda a infraestrutura de testes, automação, coleta de telemetria, validação estatística e geração de relatórios foi implementada em Python?**

As razões metodológicas e arquiteturais são estritas:

1. **Separação Rígida entre Objeto de Teste e Harness de Medição:**
   * Na metodologia de avaliação de sistemas (Raj Jain, 1991), o instrumento de medição (*Test Harness*) não pode sofrer interferência das bibliotecas do próprio sistema sob teste.
   * Se usássemos Node.js para medir o OpenClaw, o orquestrador de teste disputaria o mesmo motor V8, o mesmo *garbage collector* e o mesmo *event loop* com o agente, contaminando as leituras de latência e consumo de memória RAM.
   * Se usássemos Go para medir o PicoClaw, introduziríamos viés de instrumentação interna.
   * Python atua como um **observador externo e neutro**, disparando os processos como filhos de sistema operacional independentes, capturando PID, medindo RSS e lendo sensores de hardware sem compartilhar memória ou *threads* com os competidores.

2. **Maturidade Científica e Validação Estatística Acadêmica:**
   * O ecossistema Python conta com a **SciPy** e o **NumPy**, as bibliotecas de computação científica mais rigorosas e extensivamente auditadas do mundo acadêmico.
   * Cálculos de limites fiduciais exatos de Poisson (Garwood, 1936), testes de superdispersão de Cameron & Trivedi (1990) e análise de variância ANOVA One-Way exigem quantis analíticos da distribuição Qui-Quadrado ($\chi^2$) e da distribuição $F$, implementados com estabilidade de ponto flutuante de 64 bits na SciPy. Bash ou JavaScript puro não possuem suporte nativo a essas operações matemáticas sem bibliotecas instáveis de terceiros.

3. **Orquestração Multiprocesso e Controle de Daemons:**
   * Python oferece a biblioteca padrão `subprocess`, permitindo lançar o servidor neural Metal GPU (`llama-server`) em segundo plano, monitorar seu *healthcheck* HTTP via `urllib`, disparar o utilitário anti-repouso `caffeinate`, executar os agentes com *timeouts* determinísticos e capturar *exit codes* de forma portável e robusta.

4. **Pipelines de Publicação Científica Integrada (Gráficos e Relatórios):**
   * Com o mesmo conjunto de dados brutos coletados em formato JSONL, o Python constrói tanto as figuras em 300 DPI compatíveis com publicações IEEE/ACM (`matplotlib`) quanto o documento acadêmico oficial no formato Word ABNT (`python-docx`), garantindo rastreabilidade criptográfica direta entre medição física e relatório final.

---

## 2. Bibliotecas Python: Nomes Específicos, Versões e Justificativas

Todas as bibliotecas Python estão fixadas e provisionadas no ambiente virtual isolado [`tools/.venv`](../tools/).

| Biblioteca | Versão | Função Primária no Projeto | Por que foi escolhida? |
| :--- | :---: | :--- | :--- |
| **`scipy`** | `1.15.2` | Motor de inferência estatística, quantis Qui-Quadrado, intervalos de Garwood e ANOVA. | **Rigor Matemático Estrito:** Fornece as funções analíticas `scipy.stats.chi2.ppf` e `scipy.stats.poisson` necessárias para calcular os limites fiduciais exatos da distribuição de Poisson (Garwood, 1936), o teste de dispersão de Cameron & Trivedi e a ANOVA One-Way (`scipy.stats.f_oneway`) entre as 5 campanhas físicas, eliminando qualquer aproximação empírica grosseira. |
| **`numpy`** | `2.2.3` | Álgebra linear de alta performance, manipulação matricial e cálculo de similaridade vetorial. | **Desempenho Vetorial no Workload W3 (RAG):** Carrega a matriz de projeção densa de 98.688 parâmetros (`embedding_head_100k.npz`) e executa a normalização L2 e produtos escalares (similaridade de cosseno) sobre 10.000 fragmentos de documentos utilizando instruções SIMD vetorizadas do Apple Silicon M4. |
| **`matplotlib`** | `3.10.1` | Renderização gráfica vetorial e raster em 300 DPI das Figuras 1 a 8. | **Qualidade de Publicação Científica:** Suporta formatação tipográfica matemática completa via KaTeX/mathtext, barras de erro empíricas assimétricas, geração de gráficos em 300 DPI para relatórios impressos e paleta de cores acessível para daltônicos (*colorblind-safe*). |
| **`python-docx`** | `1.1.2` | Geração programática do Relatório de Teste de Sistemas (`reports/*.docx`). | **Conformidade com Normas da UFABC e ABNT:** Constrói relatórios acadêmicos estruturados com paginação formal, tabelas alinhadas, legendas automáticas e metadados institucionais diretamente a partir dos logs de medição, sem depender do aplicativo Microsoft Word instalado na máquina. |
| **`dulwich`** | `0.22.8` | Cliente Git em Python puro para versionamento, commits e push SSH. | **Independência dos Stubs do Xcode macOS:** No macOS, `/usr/bin/git` é um *wrapper* da Apple que tenta abrir uma janela gráfica solicitando o download de 15 GB do Xcode Command Line Tools. O `dulwich` opera 100% em espaço de usuário Python, lê e grava a base Git diretamente e autentica via chaves SSH Ed25519 sem exigir nenhuma ferramenta gráfica externa. |

### Módulos Nativos da Biblioteca Padrão do Python (Zero Dependências Adicionais)
* **`subprocess`:** Gerenciamento dos processos de baixo nível dos agentes, captura de *stdout*/*stderr* e medição síncrona com *warmup*.
* **`urllib.request` e `urllib.error`:** Comunicação cliente HTTP REST para envio das mensagens no formato OpenAI ChatCompletions (`/v1/chat/completions`) para o servidor `llama.cpp` local.
* **`hashlib`:** Geração determinística dos hashes SHA-256 para indexação de integridade de todos os 215 arquivos no [`data/manifest_sha256.json`](../data/manifest_sha256.json).
* **`json` e `csv`:** Leitura e escrita estruturada dos traces de telemetria em formato JSON Lines (`consolidated_trials.jsonl`) e exportações de tabelas comparativas.
* **`time` (`time.perf_counter_ns`):** Medição de latência com resolução nanométrica baseada no registrador de ciclo do hardware do macOS.
* **`pathlib` e `os.path`:** Garantia de caminhos portáteis relativos à raiz do repositório, permitindo execução idêntica em qualquer diretório.

---

## 3. Ferramentas de Sistema, Compiladores e Motores de Execução

| Ferramenta | Versão / Build | O que é? | Por que foi escolhida? |
| :--- | :---: | :--- | :--- |
| **Go (Golang)** | `1.23.2` | Compilador estático para código de máquina nativo ARM64 (PicoClaw). | **Arquitetura Minimalista Nativa:** Produz executáveis no formato nativo Mach-O ARM64 de ~57 MB sem necessidade de máquina virtual intermediária. O modelo de concorrência com *goroutines* leves (~2 KB por pilha) e o coletor de lixo tri-color concorrente eliminam pausas longas de GC (*Stop-The-World* $< 1\text{ ms}$), atingindo cold start de $9{,}63\text{ ms}$ e consumo de apenas $14\text{ MB}$ de RAM. |
| **Node.js / TypeScript** | `v26.12.1` | Ambiente de execução JavaScript/TypeScript sobre a Google V8 (OpenClaw). | **Representante Corporativo Padrão:** É o ecossistema dominante na indústria para criação de agentes autônomos de IA corporativos. A Google V8 oferece compilação JIT multinível (Sparkplug, Maglev, Turbofan), validação dinâmica de esquemas via TypeBox e persistência nativa em SQLite (`node:sqlite`), permitindo analisar o custo real de memória ($166\text{ a }448\text{ MB}$) e atraso de inicialização ($225\text{ ms}$) em sistemas empresariais. |
| **llama.cpp** | `build b11887 (Metal)` | Servidor de inferência neural local em C++ com aceleração por GPU Metal. | **Aceleração Direta Bare-Metal:** Executa modelos de linguagem diretamente nos 10 núcleos da GPU Metal do Apple Silicon M4 usando *shaders* otimizados em Metal Shading Language, sem sobrecargas de CUDA ou PyTorch. Possibilita decodificação estritamente determinística com temperatura $0{,}0$ e semente fixa ($42$), garantindo que ambos os agentes recebam respostas idênticas token a token. |
| **hyperfine** | `1.19.0` | Cronômetro estatístico para linha de comando desenvolvido em Rust. | **Medição Precisa de Inicialização (Cold Start):** Executa fases automáticas de aquecimento (*warmup*), detecta variações de cache de disco e executa 30 iterações sucessivas calculando média, desvio padrão e intervalos de confiança estatísticos, eliminando viés humano ou erros de amostragem no *cold start*. |
| **powermetrics** | Nativo Apple macOS | Utilitário de telemetria de sensores de hardware do Apple Silicon. | **Acesso Direto ao Hardware via SMC:** É a ferramenta autorizada pela Apple que lê diretamente os registradores de corrente e tensão do *System Management Controller* (SMC), fornecendo leituras de consumo elétrico real em miliwatts (mW) para CPU, GPU e memória DRAM a cada 100 ms. Bibliotecas de software genéricas são incapazes de medir essa potência física real. |
| **caffeinate** | Nativo Apple macOS | Comando do sistema para controle de gerenciamento de energia. | **Quiescência e Prevenção de Throttling:** Executado com as flags `-dims` (Display, Idle, Machine, System), impede que o Mac mini M4 entre em modo de economia de energia, desligue a tela ou sofra limitação térmica de CPU durante testes prolongados de várias horas. |
| **mdutil** | Nativo Apple macOS | Utilitário de controle de indexação do Spotlight do macOS. | **Eliminação de Ruído de Disco (Jitter):** Usado para pausar a indexação em segundo plano dos processos `mds` e `mdworker` durante os testes, garantindo que o I/O de disco medido no workload W2 reflita exclusivamente a leitura dos arquivos do teste e não buscas do sistema operacional. |
| **Astral uv** | `v0.5.x` | Gerenciador de ambientes virtuais e dependências em Rust. | **Provisionamento Portátil e Imediato:** Baixa, compila e instala os pacotes Python no ambiente virtual isolado `tools/.venv` em menos de 3 segundos, dispensando modificações no sistema global do Mac. |

---

## 4. Relação entre os Datasets e as Bibliotecas nos Workloads

1. **Workload W1 (Reflexão Simples):**
   * Não consome datasets em disco. A biblioteca `urllib` envia o prompt de reflexão arquitetural do chip M4 e mede o tempo até o primeiro token e a latência de orquestração do runtime.
2. **Workload W2 (Cadeia de 3 Ferramentas):**
   * O orquestrador usa `os` e `json` para acessar `data/workload_data/mock_files/` (`list_dir`), filtrar `data/workload_data/system_logs.jsonl` com expressões regulares (`grep_logs`) e calcular agregações numéricas (`calc_stats`).
3. **Workload W3 (Vector RAG em Memória):**
   * O orquestrador utiliza a biblioteca **`numpy`** para carregar os pesos pré-calculados em `data/workload_data/embedding_head_100k.npz`, projetar vetores de 384 dimensões e executar busca de similaridade de cosseno sobre os 10.000 textos de `data/workload_data/rag_chunks_10k.json`.
4. **Workload W4 (Loop Autônomo ReAct de 10 Passos):**
   * Executa um ciclo interativo contínuo alternando entre as ferramentas dos workloads W2 e W3, registrando o aumento progressivo de consumo de memória RAM (RSS) ao longo dos 10 passos.

---

## 5. Conclusão Metodológica

A escolha de cada componente técnico respondeu estritamente aos critérios de **reprodutibilidade**, **rigor estatístico** e **não-intrusividade**. A combinação de binários nativos especializados (Go, C++ Metal, Rust) com um harness de orquestração e análise em Python garante que qualquer pesquisador independente consiga replicar integralmente os resultados sem ambiguidades.
