# Guia Prático Introdutório Passo a Passo
## Como Entender, Executar e Explicar o Projeto Sem Complicações Técnicas
**Projeto:** PicoClaw (Go) vs. OpenClaw (Node.js/TypeScript) no Apple Silicon M4  
**Autor:** Rafael Paniccia Cassetta (RA: 21202520618) — UFABC  

---

### 1. A Analogia Central: O Carro e os Dois Motoristas

Para entender este projeto em 30 segundos, imagine a seguinte situação:
* **O Motor do Carro:** É a Inteligência Artificial da Meta (**Llama-3.2 de 3 bilhões de parâmetros**). Esse motor gera o texto e pensa nas respostas.
* **O Servidor:** É o **`llama.cpp`**, que liga esse motor diretamente na placa de vídeo ultrarrápida do Mac mini M4 (a GPU Metal).
* **Os Motoristas:** São os dois **Agentes de IA** competindo para ver quem dirige melhor o carro:
  1. **OpenClaw:** Feito em **Node.js / TypeScript**. É como um motorista que carrega uma mochila pesada com 54 ferramentas diferentes, manuais gigantescos e precisa de um tradutor simultâneo (a máquina virtual V8 do JavaScript) para conversar com o carro. Ele é famoso e tem muitos recursos, mas é pesado e gasta muita energia e memória.
  2. **PicoClaw:** Feito em **Go (Golang)** pela Sipeed. É como um atleta minimalista. Ele fala direto a língua nativa do processador do Mac (código ARM64 puro), não precisa de tradutor e só carrega o que vai usar.

**A Pergunta de Pesquisa:** Se o motor de IA é exatamente o mesmo para os dois, qual motorista faz a viagem mais rápida, gasta menos memória RAM e consome menos bateria do Mac?

---

### 2. O Que Significa Cada Ferramenta que Usamos?

| Ferramenta | O que ela é na prática? | Para que serviu no nosso teste? |
| :--- | :--- | :--- |
| **PicoClaw** | O agente leve feito em Go. | O competidor rápido e compacto. |
| **OpenClaw** | O agente pesado feito em Node.js. | O competidor modular e expansível. |
| **llama-server** | O programa que liga a IA na placa de vídeo. | Garante que os dois agentes conversem com a mesma IA local. |
| **hyperfine** | Um cronômetro de precisão atômica. | Cronometrou 30 vezes seguidas o tempo exato para abrir cada agente. |
| **powermetrics** | Sensores de energia oficiais do chip M4. | Mediu quantos Watts de energia a CPU e a GPU gastaram a cada 0,1 segundo. |
| **caffeinate** | Um comando que "dá café" para o Mac. | Garante que o Mac mini nunca durma ou desligue a tela durante os testes. |
| **mdutil** | O controle de buscas do Spotlight do Mac. | Pausou as buscas em disco para o Mac não ficar lento durante as medições. |

---

### 3. As 4 Tarefas que Demos para os Agentes Resolverem

Criamos 4 níveis de dificuldade (chamados de Tiers W1 a W4):
1. **W1 (Fácil — Reflexão Simples):** O agente só precisa responder uma pergunta teórica sobre o chip M4 em duas frases. Não usa nenhuma ferramenta externa.
2. **W2 (Médio — Cadeia de 3 Ferramentas):** O agente precisa:
   * Listar 50 arquivos numa pasta (`list_dir`).
   * Filtrar um arquivo de log de 750 linhas procurando palavras específicas (`grep_logs`).
   * Calcular média e desvio padrão dos dados encontrados (`calc_stats`).
3. **W3 (Pesado — Busca em Memória RAG com 10.000 Documentos):** O agente recebe uma pergunta e precisa varrer matematicamente 10.000 textos usando vetores de 384 dimensões para achar os 5 mais parecidos.
4. **W4 (Estresse Máximo — Loop Autônomo ReAct de 10 Rodadas):** O agente entra em um ciclo de 10 voltas seguidas pensando, chamando ferramentas, lendo resultados e pensando de novo.

---

### 4. Passo a Passo: Como Rodar Tudo na Sua Máquina (Copiar e Colar)

Abra o aplicativo **Terminal** no seu Mac e siga estes passos:

#### Passo 1: Entrar na pasta do projeto
```bash
cd /Users/rafael/.gemini/antigravity/scratch/picoclaw-vs-openclaw-benchmark
```

#### Passo 2: Rodar o instalador automático (se estiver em uma máquina nova)
```bash
./benchmark/setup_environment.sh
```
*Ele baixa sozinho o Go, Node.js, Python, llama.cpp e o modelo de IA. Você não precisa instalar nada manualmente.*

#### Passo 3: Executar a bateria de testes reais ao vivo
```bash
python3 benchmark/run_live_campaign.py campaign_run_6 ./campaign_run_6
```
*Você verá na tela cada rodada acontecendo na hora, mostrando os milissegundos e o consumo de memória RAM.*

#### Passo 4: Ver os gráficos gerados
Abra a pasta `figures/` ou `screenshots/` para ver as figuras prontas em alta resolução:
```bash
open figures/fig8_three_campaigns_reproducibility.png
open screenshots/print_screen_03_powermetrics.png
```

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
