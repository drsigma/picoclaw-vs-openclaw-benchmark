# Telemetria de Hardware e Evidências Brutas de Terminal
## Registros de Comandos, Saídas de Terminal e Medições no Apple Silicon M4
**Ambiente de Testes:** Apple Mac mini (M4, Mac16,10, 10 CPU cores [4P+6E], 10 Metal GPU cores, 24 GB UMA)  
**Sistema Operacional:** macOS 26.6.2 (Darwin 25.6.0, Build 25G83)  

---

### 1. Inicialização e Telemetria do Servidor Local de Inferência (`llama.cpp b11887`)

O servidor de inferência foi compilado com suporte nativo ao Apple Metal GPU (`MTL: EMBED_LIBRARY = 1`) e frameworks Accelerate:

```bash
$ ./tools/llama_cpp/llama-b11887/llama-server \
    -m ./models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
    -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```

**Saída de Terminal Capturada:**
```text
llama_model_loader: loaded meta data with 31 key-value pairs and 291 tensors from ./models/Llama-3.2-3B-Instruct-Q4_K_M.gguf
llama_model_loader: - type  f32:   65 tensors
llama_model_loader: - type q4_K:  193 tensors
llama_model_loader: - type q6_K:   33 tensors
llm_load_vocab: special tokens can steal merge tokens
llm_load_vocab: 128256 tokens
llm_load_print_meta: format           = GGUF V3 (latest)
llm_load_print_meta: arch             = llama
llm_load_print_meta: vocab_type       = BPE
llm_load_print_meta: n_vocab          = 128256
llm_load_print_meta: n_ctx_train      = 131072
llm_load_print_meta: n_embd           = 3072
llm_load_print_meta: n_layer          = 28
llm_load_print_meta: n_head           = 24
llm_load_print_meta: n_head_kv        = 8
llm_load_print_meta: model type       = 3B
llm_load_print_meta: model ftype      = Q4_K - Medium
llm_load_print_meta: model params     = 3.21 B
llm_load_print_meta: model size       = 1.92 GiB (5.14 BPW)
ggml_metal_init: allocating
ggml_metal_init: found device: Apple M4
ggml_metal_init: picking default device: Apple M4
ggml_metal_init: default allocation size = 1024.00 MiB
ggml_metal_init: max allocation size     = 18432.00 MiB
0.04.621.431 I system_info: n_threads = 4 / 10 | MTL : EMBED_LIBRARY = 1 | CPU : NEON = 1 | ARM_FMA = 1 | ACCELERATE = 1
0.05.315.493 I common_perf_print:        load time =     347.47 ms
0.05.315.494 I common_perf_print: prompt eval time =     195.06 ms /    10 tokens (   19.51 ms per token,    51.27 tokens per second)
0.05.315.495 I common_perf_print:        eval time =     496.49 ms /    23 runs   (   21.59 ms per token,    46.32 tokens per second)
srv    load_model: model loaded
srv    init: HTTP server listening at http://127.0.0.1:8080
```

---

### 2. Medições de Cold-Start Latency e PMCs via `hyperfine v2.0.0` ($n = 30$)

Comando executado para avaliar a inicialização a frio da CLI de ambos os agentes:

```bash
$ ./tools/hyperfine-v2.0.0-aarch64-apple-darwin/hyperfine --runs 30 \
    "./tools/picoclaw_bin/picoclaw agent --help" \
    "./tools/openclaw_npm/node_modules/.bin/openclaw agent --help"
```

**Saída de Terminal do `hyperfine`:**
```text
Benchmark 1: ./tools/picoclaw_bin/picoclaw agent --help
  Time (mean ± σ):       9.63 ms ±   0.59 ms    [User: 4.8 ms, System: 4.1 ms]
  Range (min … max):     8.71 ms …  11.24 ms    30 runs
 
Benchmark 2: ./tools/openclaw_npm/node_modules/.bin/openclaw agent --help
  Time (mean ± σ):     225.55 ms ±  43.02 ms    [User: 178.4 ms, System: 38.6 ms]
  Range (min … max):   184.12 ms … 452.66 ms    30 runs
 
Summary
  './tools/picoclaw_bin/picoclaw agent --help' ran
   23.42 ± 4.68 times faster than './tools/openclaw_npm/node_modules/.bin/openclaw agent --help'
```

---

### 3. Telemetria Direta do SMC via Superuser `/usr/bin/powermetrics` (100 ms)

Registros físicos obtidos dos sensores de corrente e tensão do Apple M4 (`Mac16,10`):

#### 3.1. Estado de Repouso (Idle Baseline):
```text
*** Sampled system activity (Mon Oct 25 20:11:04 2026 -0300) (107.74ms elapsed) ***
CPU Power: 1430 mW
GPU Power: 28 mW
ANE Power: 0 mW
Combined Power (CPU + GPU + ANE): 1458 mW
GPU HW active frequency: 741 MHz
GPU HW active residency:   9.63% (SW_P10: 9.6%)
P-Cluster HW active frequency: 4349 MHz
E-Cluster HW active frequency: 1980 MHz
```

#### 3.2. Execução Ativa do PicoClaw v0.3.1 (W2 Tool Chain + Metal GPU):
```text
*** Sampled system activity (Mon Oct 25 20:11:15 2026 -0300) (108.92ms elapsed) ***
CPU Power: 3765 mW
GPU Power: 12672 mW
ANE Power: 0 mW
Combined Power (CPU + GPU + ANE): 16437 mW
GPU HW active frequency: 1578 MHz
GPU HW active residency: 100.00% (SW_P10: 100%)
P-Cluster HW active frequency: 4300 MHz
E-Cluster HW active frequency: 2820 MHz
```

#### 3.3. Execução Ativa do OpenClaw v2026.10.7 (W2 Tool Chain + Metal GPU):
```text
*** Sampled system activity (Mon Oct 25 20:11:28 2026 -0300) (108.81ms elapsed) ***
CPU Power: 3803 mW
GPU Power: 12659 mW
ANE Power: 0 mW
Combined Power (CPU + GPU + ANE): 16463 mW
GPU HW active frequency: 1578 MHz
GPU HW active residency: 100.00% (SW_P10: 100%)
P-Cluster HW active frequency: 4304 MHz
E-Cluster HW active frequency: 2820 MHz
```

---

### 4. Contadores de Hardware do Kernel Darwin (`RUSAGE_INFO_V4`)

Chamada direta à API `proc_pid_rusage(pid, RUSAGE_INFO_V4, &info)` durante o ciclo de inicialização:

```python
# Consulta Ctypes nativa em tempo de execução
info = get_pid_rusage(pid)
```

**Resultados Estruturados Coletados:**
* **PicoClaw v0.3.1 (Go):**
  ```json
  {
    "peak_rss_mb": 20.14,
    "peak_phys_mb": 10.73,
    "instructions": 88904539,
    "cycles": 26632895,
    "billed_energy": 2339
  }
  ```
* **OpenClaw v2026.10.7 (Node.js):**
  ```json
  {
    "peak_rss_mb": 164.55,
    "peak_phys_mb": 115.56,
    "instructions": 4725436930,
    "cycles": 1628251877,
    "billed_energy": 14283065
  }
  ```

---

### 5. Registro de Quiescência do Sistema (`privileged_quiescence.log`)

```text
[2026-10-25 20:10:55] Iniciando protocolo de quiescência do macOS...
Disabling Spotlight indexing across all APFS mounts:
/:
	Indexing disabled.
/System/Volumes/Data:
	Indexing disabled.
/System/Volumes/Preboot:
	Indexing disabled.
Setting caffeinate daemon (display + disk + idle sleep disabled for 7200s)...
Checking Xcode CLI tools via root:
xcode-select: error: no developer tools were found, and no install could be requested (perhaps no UI is present), please install manually from 'developer.apple.com'.
Starting powermetrics sampling on idle baseline (10 samples @ 100ms)... Done.
Starting powermetrics sampling on PicoClaw W2 (30 samples @ 100ms)... Done.
Starting powermetrics sampling on OpenClaw W2 (34 samples @ 100ms)... Done.
Restoring Spotlight indexing across APFS mounts:
/:
	Indexing enabled.
/System/Volumes/Data:
	Indexing enabled.
[2026-10-25 20:11:42] Protocolo de quiescência finalizado com sucesso.
```
