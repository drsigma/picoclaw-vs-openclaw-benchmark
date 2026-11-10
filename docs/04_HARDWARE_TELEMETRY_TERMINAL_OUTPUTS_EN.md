# Hardware Telemetry and Raw Terminal Evidence (English)
## Terminal Session Logs, Hardware Counters, and Benchmarking Output on Apple M4
**Test Environment:** Apple Mac mini (M4, Mac16,10, 10 CPU cores [4P+6E], 10 Metal GPU cores, 24 GB UMA)  
**Operating System:** macOS 26.6.2 (Darwin 25.6.0, Build 25G83)  

---

### 1. Neural Engine Initialization & GPU Memory Shaders (`llama.cpp b11887`)

The local inference engine was initialized with full Apple Metal GPU compute shader acceleration (`-ngl 99`):

```bash
$ ./tools/llama_cpp/llama-b11887/llama-server \
    -m ./models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
    -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```

**Captured Terminal Stream:**
```text
llama_model_loader: loaded meta data with 31 key-value pairs and 291 tensors from Llama-3.2-3B-Instruct-Q4_K_M.gguf
llama_model_loader: - type q4_K: 193 tensors | model size: 1.92 GiB (5.14 BPW) | params: 3.21 B
ggml_metal_init: allocating Metal GPU memory pipeline on Apple M4 SoC
ggml_metal_init: found device: Apple M4 (10 GPU compute cores)
ggml_metal_init: default allocation size = 1024.00 MiB | max allocation = 18432.00 MiB
0.04.621.431 I system_info: n_threads = 4 / 10 | MTL : EMBED_LIBRARY = 1 | CPU : NEON = 1 | ACCELERATE = 1
0.05.315.493 I common_perf_print:        load time =     347.47 ms
0.05.315.494 I common_perf_print: prompt eval time =     195.06 ms / 10 tokens (51.27 tokens/s)
0.05.315.495 I common_perf_print:        eval time =     496.49 ms / 23 runs   (46.32 tokens/s)
srv    init: HTTP server listening at http://127.0.0.1:8080 (health: OK)
```

---

### 2. Cold-Start Latency Benchmarks via `hyperfine v2.0.0` ($n = 30$)

Evaluating CLI process bootstrap from `execve()` to prompt readiness:

```bash
$ ./tools/hyperfine/hyperfine --runs 30 \
    "./tools/picoclaw_bin/picoclaw agent --help" \
    "./tools/openclaw_npm/node_modules/.bin/openclaw agent --help"
```

**Benchmark Output:**
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

### 3. Apple M4 SMC Hardware Telemetry via `/usr/bin/powermetrics` (100 ms)

Direct physical current/voltage rail measurements from Apple's System Management Controller:

#### 3.1. Idle Baseline:
```text
*** Sampled system activity (Mon Oct 25 20:11:04 2026) [Idle Baseline] ***
CPU Power: 1430 mW | P-Cluster HW active freq: 4349 MHz | E-Cluster: 1980 MHz
GPU Power:   28 mW | GPU HW active freq:  741 MHz (Residency: 9.63% active)
ANE Power:    0 mW
Combined Power (CPU + GPU + ANE): 1458 mW (~1.46 W baseline idle)
```

#### 3.2. PicoClaw v0.3.1 Under Active Workload (W2 Tool Chain + Metal GPU):
```text
*** Sampled system activity (Mon Oct 25 20:11:15 2026) [PicoClaw W2 Tool Chain + Metal GPU] ***
CPU Power:  3765 mW (Peak: 4710 mW) | P-Cluster active freq: 4300 MHz
GPU Power: 12672 mW (Peak: 12672 mW) | GPU HW active freq: 1578 MHz (100.0% residency)
ANE Power:     0 mW (kernels dispatched strictly to Metal GPU Shaders)
Combined Power (CPU + GPU + ANE): 16437 mW (~16.44 W active load, Peak: 16865 mW)
```

#### 3.3. OpenClaw v2026.10.7 Under Active Workload (W2 Tool Chain + Metal GPU):
```text
*** Sampled system activity (Mon Oct 25 20:11:28 2026) [OpenClaw W2 Tool Chain + Metal GPU] ***
CPU Power:  3803 mW (Peak: 4319 mW) | P-Cluster active freq: 4304 MHz
GPU Power: 12659 mW (Peak: 12659 mW) | GPU HW active freq: 1578 MHz (100.0% residency)
Combined Power (CPU + GPU + ANE): 16463 mW (~16.46 W active load, Peak: 16463 mW)
```

---

### 4. Darwin Kernel Performance Monitoring Counters (`RUSAGE_INFO_V4`)

Hardware PMC registers captured via Darwin's `proc_pid_rusage()` API:

* **PicoClaw (Go):** Peak RSS: `20.14 MB`, Phys Footprint: `10.73 MB`, Instructions: `88,904,539`, Cycles: `26,632,895`.
* **OpenClaw (Node.js):** Peak RSS: `164.55 MB`, Phys Footprint: `115.56 MB`, Instructions: `4,725,436,930`, Cycles: `1,628,251,877`.
