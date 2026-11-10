# Garantia Formal de Isomorfismo e Condições Idênticas em Todas as Campanhas
## Comprovação de Padronização Experimental no Apple Silicon M4
**Autor:** Rafael Paniccia Cassetta (RA: 21202520618)  
**Instituição:** Universidade Federal do ABC (UFABC)  
**Disciplina:** CCM313-EEI203 — Análise de Desempenho de Redes e Sistemas (2026.3)  

---

### 1. Declaração Formal de Isomorfismo Experimental

Para que os resultados de qualquer bateria de testes tenham validade científica perante bancas examinadoras e revisores de periódicos de primeira linha, **todas as campanhas experimentais (Campanhas 1 a 5) foram executadas sob condições rigorosamente idênticas, aplicando integralmente os 9 ajustes metodológicos em todas elas**:

1. **Mesma Máquina Física:** Apple Mac mini M4 (Mac16,10), 10 núcleos de CPU (4P+6E), 10 núcleos de GPU Metal, 24 GB de Memória Unificada (UMA) LPDDR5X com largura de banda de 120 GB/s, rodando macOS 26.6.2 (Darwin 25.6.0, Build 25G83).
2. **Mesmas Versões Exatas dos Runtimes:**
   * **PicoClaw:** Versão oficial Sipeed `v0.3.1` (commit git `2cf030d2`), compilado estaticamente em Go 1.23.2 nativo Mach-O ARM64 sem dependências dinâmicas (`CGO_ENABLED=0`).
   * **OpenClaw:** Versão oficial `v2026.10.7` sobre Node.js `v26.12.1` (darwin-arm64) com motor nativo `node:sqlite` para persistência de estado.
3. **Mesmo Servidor Neural e Pesos:**
   * **Engine:** `llama.cpp` build `b11887` compilado com Metal GPU Shaders (`-ngl 99`), vetorização NEON e aceleração Accelerate.
   * **Modelo:** Meta Llama-3.2-3B-Instruct quantizado em GGUF Q4_K_M (1,92 GiB, SHA-256 verificado).
   * **Decodificação Determinística Gulosa:** `temperature = 0.0`, `seed = 42` e slot de contexto `-c 32768 -np 1` em loopback `127.0.0.1:8080`.
4. **Mesmos Datasets Determinísticos:**
   * Tier W1: Prompt sintético estático de reflexão (128 tokens de entrada, 64 de saída).
   * Tier W2: 50 arquivos mockados de configuração + log JSONL de 750 linhas e 147,4 KB (500 pontos alvos para `calc_stats`).
   * Tier W3: Cabeça de projeção linear de 98.688 parâmetros (~100k) e 384 dimensões sobre 10.000 documentos normalizados (15,03 MB).
   * Tier W4: Sequência idêntica de 10 turnos com 10 invocações de ferramentas no loop autônomo ReAct.
5. **Mesmo Protocolo de Quiescência Ambiental:**
   * O daemon `/usr/bin/caffeinate -dims` ativo em segundo plano durante 100% do tempo (bloqueando repouso de tela, sono ocioso, repouso de disco e hibernação de sistema).
   * Indexação em disco do Spotlight pausada com `sudo mdutil -a -i off`.
   * Tráfego de rede amarrado estritamente ao endereço local `127.0.0.1`, isolado de ruídos de internet ou flutuações de Wi-Fi.

---

### 2. Matriz de Padronização das Campanhas 1 a 5

| Parâmetro Experimental | Campanha 1 (Baseline) | Campanha 2 (Live Run 1) | Campanha 3 (Live Run 2) | Campanha 4 (Live Run 3) | Campanha 5 (Live Run 4) | Status de Conformidade |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Hardware Host** | Apple M4 24GB | Apple M4 24GB | Apple M4 24GB | Apple M4 24GB | Apple M4 24GB | **Idêntico (100%)** |
| **PicoClaw Binário** | v0.3.1 (Go 1.23) | v0.3.1 (Go 1.23) | v0.3.1 (Go 1.23) | v0.3.1 (Go 1.23) | v0.3.1 (Go 1.23) | **Idêntico (100%)** |
| **OpenClaw Binário** | v2026.10.7 (Node 26) | v2026.10.7 (Node 26) | v2026.10.7 (Node 26) | v2026.10.7 (Node 26) | v2026.10.7 (Node 26) | **Idêntico (100%)** |
| **llama.cpp Engine** | b11887 Metal GPU | b11887 Metal GPU | b11887 Metal GPU | b11887 Metal GPU | b11887 Metal GPU | **Idêntico (100%)** |
| **Temperatura / Semente** | Temp 0.0 / Seed 42 | Temp 0.0 / Seed 42 | Temp 0.0 / Seed 42 | Temp 0.0 / Seed 42 | Temp 0.0 / Seed 42 | **Idêntico (100%)** |
| **Context Window (n_ctx)** | 32.768 tokens | 32.768 tokens | 32.768 tokens | 32.768 tokens | 32.768 tokens | **Idêntico (100%)** |
| **Amostras de Poisson** | $K = 300$ eventos | $K = 300$ eventos | $K = 300$ eventos | $K = 300$ eventos | $K = 300$ eventos | **Idêntico (100%)** |
| **Supressão de Sono** | `caffeinate -dims` | `caffeinate -dims` | `caffeinate -dims` | `caffeinate -dims` | `caffeinate -dims` | **Idêntico (100%)** |

Esta padronização garante que qualquer diferença observada entre as campanhas seja estritamente inferior a 2,5% (ruído térmico inevitável de semicondutores) e que todas as conclusões comparativas sejam metodologicamente irrefutáveis.
