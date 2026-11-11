# Glossário Técnico e Metodológico (Português)
## Avaliação de Desempenho: PicoClaw (Go) vs. OpenClaw (Node.js/TypeScript) no Apple Silicon M4
**Autor:** Rafael Paniccia Cassetta (RA: 21202520618)  
**Instituição:** Universidade Federal do ABC (UFABC)  
**Disciplina:** CCM313-EEI203 — Análise de Desempenho de Redes e Sistemas (2026.3)  

---

### 1. Métricas de Desempenho Avaliadas

| Símbolo | Métrica | Unidade | Tipo | Definição Formal e Metodológica |
| :--- | :--- | :---: | :---: | :--- |
| $T_{\text{task}}$ | **Latência de Conclusão de Tarefa** | ms | Direta | Intervalo de tempo total decorrido entre o envio do prompt pelo cliente e a recepção completa do último token de saída, medido via relógio monotônico POSIX de nanossegundos (`CLOCK_MONOTONIC_RAW`). |
| $T_{\text{orch}}$ | **Sobrecarga Pura de Orquestração** | ms | Derivada | Latência exclusiva introduzida pelo runtime do agente (serialização JSON, validação de esquemas TypeBox/Go, despacho IPC, coleta de lixo), isolada matematicamente subtraindo a latência da inferência neural: $T_{\text{orch}} = T_{\text{task}} - T_{\text{neural}}$. |
| $\Phi_{\text{orch}}$ | **Fração de Sobrecarga de Orquestração** | % | Derivada | Proporção percentual da latência total da tarefa que é consumida exclusivamente pelo orquestrador: $\Phi_{\text{orch}} = \left(\frac{T_{\text{orch}}}{T_{\text{task}}}\right) \times 100\%$. |
| $\text{TTFT}$ | **Tempo até o Primeiro Token** (*Time to First Token*) | ms | Direta | Latência transcorrida desde o despacho da requisição HTTP até o recebimento do primeiro chunk SSE (*Server-Sent Events*) com conteúdo gerado pelo modelo, refletindo a duração do pré-preenchimento do contexto (*context prefill*). |
| $\text{ITL}$ | **Latência Entre Tokens** (*Inter-Token Latency*) | ms/tok | Direta | Intervalo médio de tempo decorrido entre a emissão de chunks consecutivos de tokens durante a fase de decodificação auto-regressiva: $\text{ITL} = \frac{T_{\text{task}} - \text{TTFT}}{N_{\text{out}} - 1}$. |
| $T_{\text{cold}}$ | **Latência de Inicialização a Frio** (*Cold Start*) | ms | Direta | Duração medida do ciclo de vida completo do processo desde a chamada de sistema `execve()` até o encerramento do processo ou prontidão do socket IPC, avaliada via `hyperfine v2.0.0` com $n = 30$ repetições. |
| $\text{RSS}$ | **Tamanho do Conjunto Residente** (*Resident Set Size*) | MB | Direta | Quantidade de páginas de memória física alocadas na memória principal (DRAM) ocupadas pelo processo em tempo de execução, consultada via estrutura `RUSAGE_INFO_V4` (`ri_resident_size`) do kernel Darwin XNU. |
| $\text{PhysFootprint}$ | **Pegada de Memória Física Real** (*Physical Footprint*) | MB | Direta | Métrica rigorosa do kernel do macOS (`ri_phys_footprint`) que quantifica a memória física de fato retida pelo processo, descontando páginas purgadas, bibliotecas compartilhadas e mapeamentos de arquivos somente-leitura. |
| $\alpha_{\text{mem}}$ | **Fator de Amplificação de Memória** | adimensional | Derivada | Razão de expansão entre a memória máxima consumida sob carga de trabalho e o estado de repouso: $\alpha_{\text{mem}} = \frac{\text{RSS}_{\text{peak}}}{\text{RSS}_{\text{idle}}}$. |
| $R_{\text{tool}}$ | **Vazão de Despacho de Ferramentas** | ops/s | Derivada | Taxa de execução e serialização de chamadas de funções/ferramentas (*tool calling*) por segundo: $R_{\text{tool}} = \frac{N_{\text{tools}}}{T_{\text{dispatch}} / 1000}$. |
| $\text{PMC}$ | **Contadores de Monitoramento de Hardware** | contagem | Direta | Registradores de hardware do Apple Silicon M4 consultados via syscall do Darwin (`proc_pid_rusage`), reportando instruções de CPU aposentadas (`ri_instructions`) e ciclos de clock executados (`ri_cycles`). |
| $E_{\text{pkg}}$ | **Energia Consumida pelo Pacote do SoC** | Joules (J) | Direta/Int. | Integral numérica da potência combinada (CPU + GPU + ANE) reportada a cada 100 ms pelo Apple System Management Controller (SMC) via `/usr/bin/powermetrics`: $E_{\text{pkg}} = \sum P(t) \cdot \Delta t$. |
| $\text{EDP}$ | **Produto Energia-Atraso** (*Energy-Delay Product*) | $\text{J}\cdot\text{s}$ | Derivada | Indicador de mérito de eficiência computacional que penaliza sistemas lentos que demandam alta energia: $\text{EDP} = E_{\text{pkg}} \times \left(\frac{T_{\text{task}}}{1000}\right)$. |

---

### 2. Ferramentas, Runtimes e Bibliotecas do Sistema

* **PicoClaw v0.3.1 (Sipeed):** Orquestrador de agentes de IA ultraleve de borda, compilado estaticamente em linguagem Go 1.23.2 para binário nativo Mach-O ARM64. Utiliza goroutines concorrentes de baixo overhead (2 KB por pilha inicial) e o coletor de lixo não-geracional tri-color concorrente de Go.
* **OpenClaw v2026.10.7:** Orquestrador modular pessoal e corporativo de agentes de IA construído sobre Node.js e TypeScript. Emprega a máquina virtual Google V8, validação dinâmica de esquemas via TypeBox, orquestração de plugins NPM e persistência de sessões com o motor nativo `node:sqlite`.
* **Node.js v26.12.1 (darwin-arm64):** Ambiente de execução JavaScript construído sobre o motor V8, com suporte a módulos nativos ES, multithreading via libuv e suporte completo às APIs de `node:sqlite` requeridas pelo módulo `[state/agent-db]` do OpenClaw.
* **llama.cpp (build b11887 Metal):** Servidor local de inferência em C++20 acelerado por hardware via Apple Metal GPU Shaders, NEON e bibliotecas Accelerate, oferecendo compatibilidade integral com a API OpenAI em `http://127.0.0.1:8080/v1`.
* **Meta Llama-3.2-3B-Instruct (GGUF Q4_K_M):** Modelo de linguagem neural autorregressivo de 3,21 bilhões de parâmetros quantizado em 4 bits (tamanho em disco: 1,92 GiB), configurado com decodificação determinística gulosa (`temperature = 0.0`, `seed = 42`) para anular variabilidade estocástica.
* **hyperfine v2.0.0 (aarch64-apple-darwin):** Utilitário de benchmarking estatístico de linha de comando com compensação de warm-up, calibração de timers de alta precisão e exportação paramétrica de médias e intervalos de confiança.
* **Darwin libproc (`RUSAGE_INFO_V4`):** Interface binária de programação (ABI) do kernel XNU do macOS acessada via `ctypes` no Python para coletar contadores de desempenho de baixo nível sem necessidade de privilégios de administrador (`root`).
* **powermetrics (Apple macOS SMC Telemetry):** Ferramenta utilitária privilegiada da Apple que lê os sensores físicos de corrente e tensão dos barramentos do SoC M4 (`cpu_power`, `gpu_power`, `ane_power`) a intervalos de amostragem de 100 ms.
* **caffeinate & mdutil:** Utilitários do sistema operacional macOS empregados para garantir estabilidade e quiescência experimental: o `caffeinate -dims` previne o sono e hibernação de tela, disco e CPU, enquanto o `mdutil -a -i off` pausa a indexação do Spotlight.
* **Bibliotecas Científicas do Test Harness Python:** Para detalhes aprofundados sobre a arquitetura e justificativa técnica de cada biblioteca utilizada na suíte de testes (`scipy`, `numpy`, `matplotlib`, `python-docx`, `dulwich`, `uv`), consulte o documento oficial: [`10_TECNOLOGIAS_BIBLIOTECAS_E_FERRAMENTAS_PT.md`](10_TECNOLOGIAS_BIBLIOTECAS_E_FERRAMENTAS_PT.md).
  * **`scipy` (v1.15.2):** Funções analíticas Qui-Quadrado (`chi2.ppf`), limites de Poisson de Garwood, dispersão de Cameron & Trivedi e ANOVA One-Way.
  * **`numpy` (v2.2.3):** Vetorização de matrizes e similaridade de cosseno em 384 dimensões no Workload W3 (Vector RAG).
  * **`matplotlib` (v3.10.1):** Geração das 8 figuras científicas em 300 DPI com notação matemática LaTeX.
  * **`python-docx` (v1.1.2):** Compilação dos relatórios formais nos padrões ABNT/UFABC diretamente dos logs.
  * **`dulwich` (v0.22.8):** Protocolo Git em Python puro, eliminando dependências dos stubs do Xcode CLT no macOS.
  * **`uv` (Astral):** Gerenciador de ambientes em Rust que provisiona o virtualenv `tools/.venv` em segundos.

---

### 3. Conceitos de Arquitetura de Hardware (Apple Silicon M4)

* **Arquitetura de Memória Unificada (UMA - *Unified Memory Architecture*):** Barramento de dados compartilhado de 120 GB/s onde a CPU de 10 núcleos (4 núcleos de desempenho *Firestorm* e 6 núcleos de eficiência *Icestorm*), a GPU Metal de 10 núcleos e o motor neural ANE de 16 núcleos acessam o mesmo espaço físico de 24 GB de DRAM LPDDR5X com zero cópias (*zero-copy*).
* **Contenção no Barramento UMA:** Fenômeno físico onde transferências massivas de tensores da GPU durante a avaliação de prompts do LLM concorrem com alocações intensivas de heap da CPU (como as do garbage collector da V8), elevando a latência de acesso à memória.
* **Núcleos P (*Performance Cores*) e Núcleos E (*Efficiency Cores*):** O Apple M4 aloca o agendador de tarefas e o loop de eventos de I/O prioritariamente nos núcleos de alta velocidade (até 4,4 GHz), transferindo processos ociosos para os núcleos de economia (até 2,8 GHz).
