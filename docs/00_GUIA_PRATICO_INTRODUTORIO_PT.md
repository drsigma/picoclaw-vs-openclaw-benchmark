# Guia Prático Introdutório Passo a Passo
## Como Entender, Usar os Datasets, Executar e Explicar o Projeto Sem Complicações Técnicas
**Projeto:** PicoClaw (Go) vs. OpenClaw (Node.js/TypeScript) no Apple Silicon M4  
**Autor:** Rafael Paniccia Cassetta (RA: 21202520618) — UFABC  

---

### 1. A Analogia Central: O Carro e os Dois Motoristas

Para entender este projeto em 30 segundos, imagine a seguinte situação:
* **O Motor do Carro:** É a Inteligência Artificial da Meta (**Llama-3.2 de 3 bilhões de parâmetros**). Esse motor gera o texto e pensa nas respostas.
* **O Suporte do Motor:** É o **`llama.cpp`**, que liga esse motor diretamente na placa de vídeo ultrarrápida do Mac mini M4 (a GPU Metal de 10 núcleos).
* **Os Dois Motoristas (Agentes de IA):**
  1. **OpenClaw:** Feito em **Node.js / TypeScript**. É como um motorista que carrega uma mochila pesada com 54 ferramentas diferentes, manuais gigantescos e precisa de um tradutor simultâneo (a máquina virtual V8 do JavaScript) para conversar com o carro. Ele é famoso e tem muitos recursos, mas é pesado e consome muita memória RAM e energia.
  2. **PicoClaw:** Feito em **Go (Golang)** pela Sipeed. É como um atleta minimalista. Ele fala direto a língua nativa do processador do Mac (código de máquina ARM64 puro), não precisa de tradutor e só carrega o que vai usar.

**A Pergunta de Pesquisa:** Se o motor de IA é exatamente o mesmo para os dois, qual motorista faz a viagem mais rápida, gasta menos memória RAM e consome menos energia da máquina?

---

### 2. O Que Significa Cada Ferramenta que Usamos?

| Ferramenta | O que ela é na prática? | Para que serviu no nosso teste? |
| :--- | :--- | :--- |
| **PicoClaw** | O agente leve feito em Go (binário nativo ARM64). | O competidor rápido, estático e compacto. |
| **OpenClaw** | O agente modular corporativo feito em Node.js/TypeScript. | O competidor flexível e modular, porém pesado. |
| **llama-server** | O programa que liga a IA na placa de vídeo (Metal GPU). | Garante que os dois agentes conversem com a mesma IA local em `127.0.0.1:8080`. |
| **hyperfine** | Um cronômetro de precisão atômica para o terminal. | Cronometrou 30 vezes seguidas o tempo exato para abrir cada agente (cold start). |
| **powermetrics** | Sensores de energia oficiais do chip M4 (SMC). | Mediu quantos Watts de energia a CPU e a GPU gastaram a cada 0,1 segundo. |
| **caffeinate** | Um comando que "dá café" para o Mac não dormir. | Garante que o Mac mini nunca durma ou desligue a tela durante as horas de testes. |
| **mdutil** | O controle de buscas do Spotlight do Mac. | Pausou as buscas em disco para o Mac não ter jitter ou lentidão durante as medições. |

---

### 3. Os Datasets em `data/workload_data/`: Para que servem e como são usados?

Nos testes reais, os agentes não apenas "conversam", eles precisam processar dados reais do sistema operacional. Para isso, criamos datasets determinísticos padronizados dentro da pasta [`data/workload_data/`](../data/workload_data/):

1. **`mock_files/` (50 arquivos sintéticos):**
   * **Usado no Teste W2 e W4:** O agente recebe a missão de listar o diretório (`list_dir`), contar a quantidade de arquivos, verificar permissões e inspecionar nomes de arquivos.
2. **`system_logs.jsonl` (750 linhas de eventos de sistema estruturados em JSON):**
   * **Usado no Teste W2 e W4:** O agente usa a ferramenta `grep_logs` para varrer os registros em busca de falhas severas (`CRITICAL` ou `ERROR`) e depois chama a ferramenta `calc_stats` para calcular a média e o desvio padrão dos tempos de resposta registrados nos logs.
3. **`rag_chunks_10k.json` (10.000 fragmentos de documentos) e `embedding_head_100k.npz` (matriz de projeção de 384 dimensões):**
   * **Usado no Teste W3 (Vector RAG):** O agente carrega esses 10.000 textos na memória RAM e realiza uma busca vetorial baseada em similaridade de cosseno ponderada para encontrar os 5 fragmentos mais relevantes para a consulta do usuário.

> **Como verificar os datasets no terminal:**
> ```bash
> ls -lh data/workload_data/
> head -n 5 data/workload_data/system_logs.jsonl
> ```
> Se precisar recriá-los do zero com dados novos e semente determinística:
> ```bash
> ./tools/.venv/bin/python benchmark/generate_datasets.py
> ```

---

### 4. Passo a Passo Visual com Fotos: Como Rodar Tudo na Sua Máquina

#### Passo 1: Inicialização do Servidor Neural Metal GPU
Iniciamos o `llama-server` na porta 8080 carregando o Llama-3.2-3B diretamente na GPU Metal:
```bash
./tools/llama_cpp/llama-b11887/llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```
![Passo 1: Servidor Neural llama.cpp Metal GPU](../screenshots/print_screen_01_llama_server.png)

#### Passo 2: Verificação dos Datasets de Carga
Inspecionamos os arquivos de entrada em `data/workload_data/`:
```bash
ls -lh data/workload_data/
```
![Passo 2: Verificação dos Datasets de Carga](../screenshots/print_screen_07_datasets_workload.png)

#### Passo 3: Executar a Bateria de Testes Físicos ao Vivo
Executamos o orquestrador de benchmark para rodar os workloads W1 a W4 em tempo real:
```bash
./tools/.venv/bin/python benchmark/run_live_campaign.py campaign_run_6 ./campaign_run_6
```
![Passo 3: Execução Física em Tempo Real](../screenshots/print_screen_04_live_execution.png)

#### Passo 4: Medir o Tempo de Abertura (Cold Start) com Hyperfine
Cronometramos a latência de inicialização de ambos os agentes:
```bash
./tools/hyperfine/hyperfine --warmup 5 --runs 30 \
  "./tools/picoclaw/picoclaw --version" \
  "./tools/node/bin/node ./benchmark/openclaw_orch.mjs --version"
```
![Passo 4: Medição de Cold-Start](../screenshots/print_screen_02_hyperfine.png)

#### Passo 5: Validar a Taxa de Poisson (Assertividade $\ge 90{,}3\%$)
Rodamos o motor estatístico de Poisson para verificar a conformidade com os intervalos de Garwood:
```bash
./tools/.venv/bin/python benchmark/poisson_sampling_validation.py
```
![Passo 5: Motor Estatístico de Poisson](../screenshots/print_screen_05_poisson_engine.png)

#### Passo 6: Monitorar Sensores de Energia e Impedir o Mac de Dormir
Ativamos o modo anti-sono com `caffeinate` e monitoramos os sensores do chip Apple M4:
```bash
/usr/bin/caffeinate -dims &
sudo powermetrics -i 100 -n 10 --samplers cpu_power,gpu_power
```
![Passo 6: Telemetria de Hardware](../screenshots/print_screen_03_powermetrics.png)

#### Passo 7: Visualizar os Gráficos Comparativos de Reprodutibilidade
Abrimos os gráficos de alta resolução comprovando variabilidade $< 2{,}5\%$ entre 5 campanhas físicas:
```bash
open figures/fig8_three_campaigns_reproducibility.png
```
![Passo 7: Reprodutibilidade Multi-Campanhas](../figures/fig8_three_campaigns_reproducibility.png)

---

### 5. Como Entender os Resultados sem Ficar Confuso

Quando alguém olhar os gráficos, explique assim:
1. **Abertura (Cold Start):** O PicoClaw abre em **9,6 milissegundos**, enquanto o OpenClaw demora **225 milissegundos**. O PicoClaw é **23 vezes mais rápido**.
2. **Memória RAM:** O PicoClaw consome apenas **14 a 34 MB** de memória RAM. O OpenClaw gasta **166 a 448 MB**. O OpenClaw gasta **13 vezes mais memória**.
3. **Velocidade de Ferramentas:** O PicoClaw executa **326 ferramentas por segundo**, enquanto o OpenClaw executa **64 ferramentas por segundo** (o PicoClaw é **5 vezes mais rápido**).
4. **Energia do Chip:** Na hora que a IA está gerando o texto, a placa de vídeo do Mac M4 consome sozinha **12,6 Watts** (de um total de 16,4 Watts). Como a placa de vídeo gasta quase tudo, quando os textos são iguais a energia fica parecida. Mas se usarmos o OpenClaw como ele vem de fábrica (com 54 ferramentas no prompt), ele faz a placa de vídeo trabalhar por 57 segundos e gasta 500 Joules extras!

---

### 6. As 3 Frases de Ouro para a Apresentação
* *"Isolamos o tempo da IA do tempo do agente: o Go gasta menos de 1 milissegundo de atraso, enquanto o Node.js gasta dezenas a centenas de milissegundos."*
* *"O teste foi executado 5 vezes na máquina física real e provou que a variabilidade entre sessões é menor que 2,5% (estatisticamente invariante)."*
* *"Para rodar em computadores do dia a dia e dispositivos pequenos sem travar a máquina, o PicoClaw em Go é a escolha correta de engenharia."*
