# Guia Completo de Reprodução Passo a Passo (Reprodutibilidade 100%)
## Como Clonar, Executar os Testes e Recriar Todos os Gráficos Localmente
**Público-Alvo:** Revisores de Periódicos Acadêmicos (*SoftwareX* / *IEEE*), Membros de Bancas e Pesquisadores  
**Requisitos de Sistema:**
* **Reprodução Completa com Telemetria Física:** macOS 14.0+ em Apple Silicon (M1/M2/M3/M4) com pelo menos 16 GB de Memória Unificada (UMA).
* **Reprodução Simulado-Portátil (Qualquer Máquina):** Qualquer distribuição Linux (Ubuntu, Debian, Fedora, Arch), Windows (via WSL2) ou macOS Intel/Apple Silicon, sem exigir sudo, GPU ou modelo neural local.

---

### Modo Rápido: Reprodução em Qualquer Máquina (Linux, Windows WSL, macOS)

Para revisores que desejam validar a lógica do framework, a consistência numérica e a geração de gráficos em qualquer arquitetura em menos de 10 segundos:

```bash
# 1. Clonar o repositório
git clone https://github.com/drsigma/picoclaw-vs-openclaw-benchmark.git
cd picoclaw-vs-openclaw-benchmark

# 2. Configurar o ambiente (Python venv e dependências)
make setup

# 3. Executar a suíte de testes unitários e linter
make test

# 4. Executar a campanha simulada de ponta a ponta (Sem Sudo / Multi-OS)
make simulate-campaign

# 5. Regenerar todas as figuras científicas em 300 DPI
make reproduce-figures
```

---

### Passo a Passo Detalhado para Execução Física no Apple Silicon

#### Passo 1: Obter o Repositório e Verificar a Integridade dos Arquivos
```bash
git clone https://github.com/drsigma/picoclaw-vs-openclaw-benchmark.git
cd picoclaw-vs-openclaw-benchmark
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

#### Passo 2: Inicializar o Ambiente e Datasets
```bash
# 1. Provisionar o ambiente isolado
make setup

# 2. Gerar os datasets determinísticos das cargas W1–W4 (se necessário regenerar)
./tools/.venv/bin/python ./benchmark/generate_datasets.py
```

---

#### Passo 3: Inicializar o Servidor Neural Local `llama.cpp`
Em uma janela de terminal, inicie o servidor Metal GPU:
```bash
./tools/llama_cpp/llama-b11887/llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```

Em outra janela, teste se o endpoint de saúde responde:
```bash
curl -s http://127.0.0.1:8080/health
# Deve retornar: {"status":"ok"}
```

---

#### Passo 4: Executar a Campanha de Benchmark Mestre
* **Modo Padrão em Espaço de Usuário (Sem Sudo):**
  ```bash
  make benchmark
  ```
* **Modo Completo com Telemetria Elétrica Apple SMC (Requer Sudo):**
  ```bash
  make benchmark-full-smc
  ```

---

#### Passo 5: Validação Estatística de Poisson e Intervalos de Garwood
```bash
./tools/.venv/bin/python ./benchmark/poisson_sampling_validation.py
```
Esse script calcula os intervalos exatos de Garwood (1936), processa os eventos de Poisson e plota `figures/fig7_poisson_assertiveness.png`.

---

#### Passo 6: Regenerar Todas as Figuras e Tabelas
```bash
make reproduce-figures
./tools/.venv/bin/python ./benchmark/analyze_results.py
```
Todas as tabelas consolidadas estarão em `results/publication_campaign/tables/` e as figuras em `figures/`.
