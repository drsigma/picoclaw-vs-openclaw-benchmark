# Guia Completo de Reprodução Passo a Passo (Reprodutibilidade 100%)
## Como Clonar, Executar os Testes e Recriar Todos os Gráficos Localmente
**Público-Alvo:** Revisores de Periódicos Acadêmicos, Membros de Bancas de Defesa e Pesquisadores  
**Requisitos Mínimos:** macOS 14.0+ em Apple Silicon (M1/M2/M3/M4) com pelo menos 16 GB de Memória Unificada.

---

### Passo 1: Obter o Repositório e Verificar a Integridade dos Arquivos

Navegue até a raiz do repositório:
```bash
cd /Users/rafael/.gemini/antigravity/scratch/picoclaw-vs-openclaw-benchmark
```

Verifique a integridade criptográfica de todos os binários, dados e relatórios contra o manifesto SHA-256:
```bash
python3 -c '
import json, hashlib, os
manifest = json.load(open("data/manifest_sha256.json"))
ok, fail = 0, 0
for rel_path, meta in manifest.items():
    if os.path.exists(rel_path):
        h = hashlib.sha256(open(rel_path, "rb").read()).hexdigest()
        if h == meta["sha256"]:
            ok += 1
        else:
            print(f"[FAIL] {rel_path}: mismatch!")
            fail += 1
print(f"Verificação concluída: {ok} arquivos íntegros, {fail} falhas.")
'
```

---

### Passo 2: Inicializar o Ambiente Python e Compilar os Orquestradores

O projeto é 100% autossuficiente e não requer ferramentas do Xcode instaladas no sistema:

```bash
# 1. Ativar o interpretador CPython 3.12.3 independente
VENV_PYTHON="../picoclaw_vs_openclaw/.venv/bin/python"

# 2. Compilar o orquestrador estático Go ARM64 (caso queira recompilar do fonte)
CGO_ENABLED=0 ../picoclaw_vs_openclaw/tools/go/bin/go build \
    -o ./benchmark/picoclaw_orch \
    ./benchmark/picoclaw_orch.go

# 3. Gerar os datasets determinísticos das cargas W1–W4 (50 configs, logs JSONL e projeção RAG 100k)
$VENV_PYTHON ./benchmark/generate_datasets.py
```

---

### Passo 3: Inicializar o Servidor Neural Local `llama.cpp`

Abra uma janela de terminal e inicie o servidor Metal GPU:
```bash
../picoclaw_vs_openclaw/tools/llama_cpp/llama-b11887/llama-server \
  -m ../picoclaw_vs_openclaw/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```

Em outra janela, teste se o endpoint de saúde responde:
```bash
curl -s http://127.0.0.1:8080/health
# Deve retornar: {"status":"ok"}
```

---

### Passo 4: Executar a Campanha de Validação Estatística de Poisson ($\ge 90\%$ de Assertividade)

Execute o motor analítico de Poisson:
```bash
$VENV_PYTHON ./benchmark/poisson_sampling_validation.py
```

Esse script executa as seguintes etapas automaticamente:
1. Calcula os limiares amostrais teóricos ($K \ge 271$ eventos para $90\%$ de assertividade; $K \ge 1.537$ para $95\%$).
2. Processa as amostras empíricas com $n = 100$ repetições ($K = 300$ eventos no W2 e $K = 1.000$ eventos no W4).
3. Calcula os Intervalos de Confiança Exatos de Garwood (1936) via Qui-Quadrado.
4. Gera o arquivo de dados consolidado em `data/poisson_results.json`.
5. Plota o gráfico científico em alta resolução em `figures/fig7_poisson_assertiveness.png`.

---

### Passo 5: Executar os 480 Testes da Matriz Fatorial Completa (Opcional)

Para reproduzir a bateria inteira de 480 testes fatoriais (16 tratamentos $\times$ 30 repetições):
```bash
$VENV_PYTHON ./benchmark/run_all_experiments.py
```
*Duração estimada: aproximadamente 25 a 35 minutos no Mac mini M4.*  
Os dados consolidados serão salvos em `data/results_all.json`.

---

### Passo 6: Regenerar Todas as Figuras e Relatórios Finais em Word e PDF

Para recriar todas as figuras científicas (Figuras 1 a 6) e compilar os documentos em `.docx` e `.pdf`:
```bash
# 1. Regenerar os 6 gráficos originais em 300 DPI
$VENV_PYTHON ./benchmark/generate_charts.py

# 2. Compilar os relatórios formais da disciplina (System Testing Report e Revised Work Plan)
$VENV_PYTHON ./benchmark/build_reports.py

# 3. Compilar o Guia Rápido e Defesa
$VENV_PYTHON ./benchmark/build_layperson_guide.py
```

Todos os relatórios gerados estarão prontos para submissão na pasta `reports/`.
