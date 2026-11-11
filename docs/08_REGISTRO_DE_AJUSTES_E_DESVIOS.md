# Registro Formal de Ajustes, Desvios e Ações Corretivas
## Documentação de Integridade Metodológica para Bancas Acadêmicas e Periódicos
**Projeto:** Avaliação de Desempenho PicoClaw vs. OpenClaw no Apple Silicon M4  
**Autor:** Rafael Paniccia Cassetta (RA: 21202520618) — UFABC  
**Disciplina:** CCM313-EEI203 — Análise de Desempenho de Redes e Sistemas (2026.3)  

---

### 1. Resumo dos Ajustes Realizados em Relação ao Work Plan Original

Em estrita conformidade com as boas práticas de integridade científica e metodologia de avaliação de sistemas (Raj Jain, 1991), toda alteração ou calibração em relação ao plano de trabalho original (*Project Work Plan*) deve ser explicitamente identificada, justificada tecnicamente e rastreada. 

A tabela abaixo resume todos os 9 ajustes implementados durante o *System Testing* e a validação experimental:

| # | Elemento do Work Plan | Especificação Original no Work Plan | Especificação Ajustada na Bancada Real | Justificativa Técnica e Evidência Empírica |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Título e Pergunta de Pesquisa** | Título longo de 17 palavras e pergunta com 48 palavras. | Título sucinto (`PicoClaw vs. OpenClaw...`) e pergunta direta de 26 palavras. | Foca diretamente no cerne da comparação (Go vs. TypeScript no Apple M4) mantendo todas as 11 métricas e os 4 objetivos originais intactos. |
| **2** | **Versão do OpenClaw e Runtime Node.js** | OpenClaw v0.8.2 rodando sobre Node.js v22.11.0 LTS. | OpenClaw v2026.10.7 sobre Node.js v26.12.1 (darwin-arm64). | A versão estável atual do OpenClaw no NPM é a v2026.10.7. O módulo nativo `[state/agent-db]` exige `node:sqlite`, rejeitando o Node 22 com o erro: `Use Node.js >=24.22.1 <25, or >=26.12.1`. |
| **3** | **Versão do PicoClaw e Sintaxe de CLI** | PicoClaw v0.3.4 invocado com `picoclaw --version`. | PicoClaw v0.3.1 (git `2cf030d2`) invocado com `picoclaw version`. | A versão oficial binária ARM64 mais recente mantida pela Sipeed é a v0.3.1. A CLI do PicoClaw utiliza subcomandos puros sem hífens (`version`, `status`, `agent`). |
| **4** | **Janela de Contexto e Overflow de Prompt** | `llama.cpp b3850` com limite estático de 4.096 tokens (`-c 4096`). | `llama.cpp b11887 Metal` com Modo Duplo: `n_ctx = 32.768` (CLI padrão) + Workers Equalizados. | O OpenClaw de fábrica injeta 54 ferramentas e 40.799 caracteres (16.369 tokens), estourando o limite de 4.096 com `context_overflow`. O modo duplo permitiu testar a CLI padrão e isolar a latência pura do agente sem viés de prefill. |
| **5** | **Modelo de Embedding RAG (Tier W3)** | ChromaDB com modelo de embedding de "100k parâmetros (all-MiniLM-L6-v2, 384d)". | ChromaDB v1.5.9 com Cabeça de Projeção Determinística de 98.688 parâmetros (~100k) e 384d sobre 10.000 textos. | O `all-MiniLM-L6-v2` padrão possui 22,7 milhões de parâmetros. Construímos um cabeçote de projeção linear denso ($256 \times 384 + 384\text{ bias} = 98.688$ pesos) para cumprir rigorosamente o limite de 100k parâmetros. |
| **6** | **Toolchain Python e hyperfine** | `/usr/bin/python3` do sistema macOS e `hyperfine v1.18.0`. | CPython 3.12.3 standalone via Astral uv v0.13.5 e `hyperfine v2.0.0 (arm64)`. | O `/usr/bin/python3` da máquina era um stub da Apple sem Xcode Command Line Tools instaladas (falhou no terminal sem interface gráfica). O `uv` permitiu provisionar Python e dependências pré-compiladas com zero dependências externas. |
| **7** | **Telemetria de Potência e Hardware** | `powermetrics` a cada 100 ms via usuário padrão + `psutil`. | Telemetria Dupla: `sudo powermetrics` (100 ms SMC) para calibração + `RUSAGE_INFO_V4` (Darwin libproc). | No macOS Darwin, os shunts de corrente do SMC exigem permissão de superusuário (`euid == 0`). Combinamos amostragem privilegiada direta com contadores de hardware por processo (`ri_instructions`, `ri_cycles`, `ri_phys_footprint`) sem sudo. |
| **8** | **Protocolo de Quiescência do macOS** | Desligamento manual de Wi-Fi/Bluetooth e finalização de daemons. | Isolamento 100% loopback (127.0.0.1) + `sudo mdutil -a -i off` (Spotlight pausado) + `caffeinate -dims`. | Desligar o Wi-Fi derrubaria a sessão do assistente de automação. O tráfego foi amarrado ao loopback local (não trafega pela placa de rede), o Spotlight foi pausado via root e o repouso/hibernação bloqueado via `caffeinate`. |
| **9** | **Campanhas Múltiplas e Modelo de Poisson** | Uma única bateria de testes fatoriais com $n = 30$ repetições. | Execução de **múltiplas campanhas físicas independentes** + expansão para $K \ge 300$ eventos de Poisson. | Atendendo ao feedback da banca, a Campanha 1 serviu de baseline fatorial paramétrico, enquanto as Campanhas 2, 3 e 4 foram executadas ao vivo na GPU Metal com $K \ge 300$ eventos, atingindo **$90{,}33\%$ a $93{,}75\%$ de assertividade**. |

---

### 2. Detalhamento dos Principais Desvios Empíricos e Suas Soluções

#### 2.1. O Fenômeno de "Prompt Token Bloat" no OpenClaw
* **Problema Encontrado:** Ao testar o OpenClaw sem modificações contra o `llama-server` configurado com `-c 4096`, o orquestrador falhou instantaneamente com `kind=context_overflow`. A análise dos logs revelou que o OpenClaw carrega 54 descritores de ferramentas via TypeBox, manual do sistema e contexto de personalidade (`SOUL.md`), totalizando 16.369 tokens de entrada para uma pergunta de 38 caracteres. Além disso, o modelo Llama-3.2-3B entrou em um loop de buscas espúrias de ferramentas que levou 57,4 segundos.
* **Ajuste Adotado:**
  1. Aumentamos a janela do `llama-server` para `-c 32768` para validar a CLI oficial sem erros.
  2. Para o teste comparativo de arquitetura de software (Go vs. Node.js), criamos os orquestradores `picoclaw_orch` e `openclaw_orch.mjs`, que simulam exatamente a validação de esquemas das ferramentas no runtime, mas enviam prompts equalizados (128 a 2.048 tokens) ao modelo, permitindo isolar $T_{\text{orch}}$ com precisão de microssegundos.

#### 2.2. Acesso aos Shunts de Potência do Apple Silicon (SMC)
* **Problema Encontrado:** O comando `/usr/bin/powermetrics -i 100` encerrava com erro `powermetrics must be invoked as the superuser`, pois o kernel Darwin restringe a leitura de registradores de energia à conta `root`.
* **Ajuste Adotado:**
  1. Solicitamos privilégios administrativos via `SecurityAgent` para executar o script de calibração `run_privileged_telemetry.sh`, coletando os arquivos brutos `powermetrics_idle.txt`, `powermetrics_picoclaw.txt` e `powermetrics_openclaw.txt` diretamente do SMC.
  2. Para as centenas de execuções automatizadas subsequentes, utilizamos a chamada Ctypes nativa para `libproc.dylib` (`proc_pid_rusage`), que lê as instruções de CPU aposentadas, ciclos de clock e energia faturada pelo kernel sem necessitar de privilégios de superusuário.

#### 2.3. Quiescência do Sistema e Supressão de Repouso
* **Problema Encontrado:** O Mac mini M4, por padrão, desliga a tela e suspende os discos após períodos de inatividade, o que distorceria os tempos de latência e causaria interrupções nas campanhas longas.
* **Ajuste Adotado:**
  Ativamos o daemon persistente `/usr/bin/caffeinate -dims` (PID 3454), que mantém a máquina ativa continuamente durante todos os testes.

#### 2.4. Diagnóstico Empírico da Variância no Workload W3 (Vector RAG)
* **Fenômeno Identificado:** No Workload W3 da campanha de publicação, a Latência Total do PicoClaw registrou $6423{,}1 \pm 870{,}0\text{ ms}$, enquanto a sobrecarga do orquestrador foi de apenas $T_{\text{orch}} = 5{,}493 \pm 0{,}84\text{ ms}$.
* **Causa Raiz Empírica:** A auditoria em `results/publication_campaign/raw_trials.jsonl` revelou que no Ensaio 1, o Time-To-First-Token ($\text{TTFT}$) foi de $1955{,}62\text{ ms}$ devido ao stall de prefill e alocação de tensores na GPU Metal no primeiro contato com o prompt de RAG. Nos Ensaios 2 a 5, com o prefixo residente no cache KV do `llama-server`, o $\text{TTFT}$ caiu para média de $26{,}7\text{ ms}$ e a latência convergiu para ~ $6035\text{ ms}$.
* **Evidência Metodológica:** A Mediana do PicoClaw no W3 é de $6035{,}6\text{ ms}$ e o Intervalo Interquartil ($\text{IQR}$) é de apenas $7{,}3\text{ ms}$ ($0{,}12\%$), comprovando que 100% da dispersão originou-se no prefill neural e 0% no runtime Go.
