# Practical Introductory Step-by-Step Guide
## How to Understand, Use Workload Datasets, Reproduce, and Explain the Project Without Technical Friction
**Project:** PicoClaw (Go) vs. OpenClaw (Node.js/TypeScript) on Apple Silicon M4  
**Author:** Rafael Paniccia Cassetta (Student ID: 21202520618) — UFABC  

---

### 1. The Core Metaphor: The Car and the Two Drivers

To grasp this entire research project in 30 seconds, imagine a car:
* **The Car Engine:** This is the local Artificial Intelligence model from Meta (**Llama-3.2 with 3 billion parameters**). It does all the thinking, reads sentences, and generates words.
* **The Engine Mount / Server:** This is **`llama.cpp`**, which connects the AI brain directly to the ultra-fast 10-core Metal GPU inside the Apple Mac mini M4.
* **The Two Drivers (AI Agent Orchestrators):**
  1. **OpenClaw (Node.js / TypeScript):** A driver carrying a giant backpack filled with 54 different tools, massive instruction manuals, and needing a live interpreter (the Google V8 JavaScript engine) to translate every thought into computer code. It is rich in features and plugins, but it is heavy and consumes significant memory and energy.
  2. **PicoClaw (Go / Golang by Sipeed):** A minimalist athlete. It speaks the native machine language of Apple's processor (pure ARM64 assembly) directly, needs no interpreter, and carries only the tools required for the task.

**The Central Research Question:** When both drivers use the exact same AI engine, which driver runs faster, wastes less RAM, and drains less electrical energy?

---

### 2. Plain-English Breakdown of Every Tool Used

| Tool Name | What is it in plain English? | What did it do in our benchmark? |
| :--- | :--- | :--- |
| **PicoClaw** | Ultra-lightweight AI agent written in Go (native ARM64 binary). | The fast, bare-metal native contender. |
| **OpenClaw** | Popular AI agent written in Node.js/TypeScript. | The modular, plugin-heavy desktop contender. |
| **llama-server** | High-performance C++ local AI server. | Runs Llama-3.2 on the Apple M4 GPU over localhost (`127.0.0.1:8080`). |
| **hyperfine** | High-precision statistical CLI stopwatch. | Measured the exact launch time (cold start) 30 times in a row. |
| **powermetrics** | Apple's built-in hardware power sensor tool. | Sampled real wattage (mW) of CPU and GPU every 100 milliseconds. |
| **caffeinate** | macOS built-in anti-sleep command. | Keeps the Mac mini awake, preventing screen and system sleep. |
| **mdutil** | macOS Spotlight indexing control. | Paused background disk searches to keep timings jitter-free. |

---

### 3. The Datasets in `data/workload_data/`: Purpose and Utilization

In physical trials, agents do not merely chat in isolation; they execute deterministic, grounded file and data manipulation tasks. These workloads consume standardized datasets in [`data/workload_data/`](../data/workload_data/):

1. **`mock_files/` (50 synthetic files):**
   * **Used in Workload W2 and W4:** The agent is instructed to invoke `list_dir` to inspect disk files, count entries, and parse filesystem metadata.
2. **`system_logs.jsonl` (750 structured JSON system log records):**
   * **Used in Workload W2 and W4:** The agent invokes `grep_logs` to filter severe error records (`CRITICAL`/`ERROR`) and subsequently calls `calc_stats` to compute rolling latency averages and standard deviations.
3. **`rag_chunks_10k.json` (10,000 document text chunks) & `embedding_head_100k.npz` (384-dimensional dense projection matrix):**
   * **Used in Workload W3 (Vector RAG):** The agent loads these 10,000 document chunks into memory and computes cosine similarity against query embeddings to rank and retrieve the top-5 relevant chunks.

> **How to inspect datasets via terminal:**
> ```bash
> ls -lh data/workload_data/
> head -n 5 data/workload_data/system_logs.jsonl
> ```
> To deterministically regenerate them from scratch:
> ```bash
> ./tools/.venv/bin/python benchmark/generate_datasets.py
> ```

---

### 4. Step-by-Step Visual Guide with Real Terminal Screenshots

#### Step 1: Launch Local Metal GPU Neural Server (`llama-server`)
Launch `llama-server` on port 8080 loading Llama-3.2-3B directly onto the Apple Metal GPU:
```bash
./tools/llama_cpp/llama-b11887/llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```
![Step 1: llama.cpp Metal GPU Neural Server](../screenshots/print_screen_01_llama_server.png)

#### Step 2: Inspect Workload Datasets
Verify the deterministic input files in `data/workload_data/`:
```bash
ls -lh data/workload_data/
```
![Step 2: Inspecting Workload Datasets](../screenshots/print_screen_07_datasets_workload.png)

#### Step 3: Run Live Physical Campaign
Execute the orchestrator runner across workloads W1 through W4 in real time:
```bash
./tools/.venv/bin/python benchmark/run_live_campaign.py campaign_run_6 ./campaign_run_6
```
![Step 3: Live Campaign Execution](../screenshots/print_screen_04_live_execution.png)

#### Step 4: Measure Cold-Start Launch Latency with Hyperfine
Benchmark process startup times across 30 warmed-up trials:
```bash
./tools/hyperfine/hyperfine --warmup 5 --runs 30 \
  "./tools/picoclaw/picoclaw --version" \
  "./tools/node/bin/node ./benchmark/openclaw_orch.mjs --version"
```
![Step 4: Hyperfine Cold Start Benchmark](../screenshots/print_screen_02_hyperfine.png)

#### Step 5: Validate Poisson Statistical Engine (Assertiveness $\ge 90.3\%$)
Execute the Poisson engine to confirm Garwood fiducial interval coverage:
```bash
./tools/.venv/bin/python benchmark/poisson_sampling_validation.py
```
![Step 5: Poisson Sampling Validation](../screenshots/print_screen_05_poisson_engine.png)

#### Step 6: Power Telemetry & System Quiescence Protocol
Prevent OS sleep via `caffeinate` and sample hardware sensors via `powermetrics`:
```bash
/usr/bin/caffeinate -dims &
sudo powermetrics -i 100 -n 10 --samplers cpu_power,gpu_power
```
![Step 6: Power Telemetry & Quiescence](../screenshots/print_screen_03_powermetrics.png)

#### Step 7: Inspect Multi-Campaign Reproducibility Figures
Open the publication-ready figures proving $< 2.5\%$ cross-campaign variability:
```bash
open figures/fig8_three_campaigns_reproducibility.png
```
![Step 7: Multi-Campaign Reproducibility](../figures/fig8_three_campaigns_reproducibility.png)

---

### 5. How to Interpret Results Without Confusion

1. **Cold Start Launch:** PicoClaw opens in **9.6 ms**, while OpenClaw takes **225 ms**. PicoClaw is **23 times faster**.
2. **RAM Footprint:** PicoClaw consumes only **14 to 34 MB** of RAM. OpenClaw takes **166 to 448 MB**. OpenClaw uses **13 times more memory**.
3. **Tool Throughput:** PicoClaw serializes and dispatches **326 tools per second**, while OpenClaw reaches **64 tools per second** under identical workload conditions.
4. **Hardware Energy:** When the model generates tokens, the 10-core Metal GPU draws **12.6 Watts** (of 16.4 W total SoC power). Because the GPU dominates power consumption, equalized prompts produce similar energy totals. However, running unmodified stock OpenClaw (54 tool schemas) forces 57 seconds of continuous GPU execution, dissipating over 500 extra Joules!

---

### 6. The 3 Key Takeaways for Examination Presentations
* *"We algebraically separated neural inference from orchestrator runtime latency: Go incurs less than 1 ms overhead, whereas Node.js incurs tens to hundreds of milliseconds."*
* *"Testing was physically reproduced 5 times on the bare-metal machine, proving cross-campaign variance is under 2.5% (strictly invariant)."*
* *"For edge deployment and background assistant agents, PicoClaw in Go is the superior engineering architecture."*
