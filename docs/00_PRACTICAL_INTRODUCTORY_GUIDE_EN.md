# Practical Introductory Step-by-Step Guide
## How to Understand, Reproduce, and Explain the Project Without Technical Friction
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
| **PicoClaw** | Ultra-lightweight AI agent written in Go. | The fast, bare-metal native contender. |
| **OpenClaw** | Popular AI agent written in Node.js/TypeScript. | The modular, plugin-heavy desktop contender. |
| **llama-server** | High-performance C++ local AI server. | Runs Llama-3.2 on the Apple M4 GPU over localhost (127.0.0.1:8080). |
| **hyperfine** | High-precision statistical CLI stopwatch. | Measured the exact launch time (cold start) 30 times in a row. |
| **powermetrics** | Apple's built-in hardware power sensor tool. | Sampled real wattage (mW) of CPU and GPU every 100 milliseconds. |
| **caffeinate** | macOS built-in anti-sleep command. | Keeps the Mac mini awake, preventing screen and system sleep. |
| **mdutil** | macOS Spotlight indexing control. | Paused background disk searches to keep timings jitter-free. |

---

### 3. The 4 Benchmark Tasks Executed by the Agents

We established 4 standardized workload difficulty tiers (Tiers W1 to W4):
1. **W1 (Easy — Simple Reflection):** The agent answers a short architectural question about Apple Silicon M4 in two sentences. No external tools are called.
2. **W2 (Medium — 3-Step Tool Chain):** The agent must:
   * List 50 mock files in a folder (`list_dir`).
   * Filter a 750-line log file searching for error keywords (`grep_logs`).
   * Compute mean, variance, and standard deviation over 500 data points (`calc_stats`).
3. **W3 (Heavy — Vector RAG Memory Search over 10,000 Documents):** The agent receives a query and performs a 384-dimensional cosine similarity search across 10,000 chunked documents using a 98,688-parameter dense projection head.
4. **W4 (Stress Test — 10-Turn Autonomous ReAct Loop):** The agent enters a 10-cycle autonomous loop observing, executing tools, inspecting results, and deciding the next action.

---

### 4. Step-by-Step: How to Run Everything on Your Machine

Open the **Terminal** application on your Mac and run:

#### Step 1: Navigate to repository root
```bash
cd /Users/rafael/.gemini/antigravity/scratch/picoclaw-vs-openclaw-benchmark
```

#### Step 2: Run automated setup (if on a fresh host)
```bash
./benchmark/setup_environment.sh
```
*Automatically provisions isolated Go, Node.js, Python, llama.cpp, and the model weights. No manual dependencies required.*

#### Step 3: Run live physical campaign
```bash
python3 benchmark/run_live_campaign.py campaign_run_6 ./campaign_run_6
```

#### Step 4: Inspect generated charts
Open `figures/` or `screenshots/` to inspect high-resolution outputs:
```bash
open figures/fig8_three_campaigns_reproducibility.png
open screenshots/print_screen_03_powermetrics.png
```

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
