# Step-by-Step Visual Telemetry Records (Screenshots)
## Terminal Evidences and Measurement Displays on Apple Silicon M4
**Author:** Rafael Paniccia Cassetta (ID: 21202520618)  
**Institution:** Federal University of ABC (UFABC)  
**Course:** CCM313-EEI203 — Computer Networks and Systems Performance Evaluation (2026.3)  

---

### 1. Launch of Local Neural Inference Server `llama.cpp` (Metal GPU)

The local inference engine was configured to map the Meta Llama-3.2-3B-Instruct model directly onto the 24 GB Unified Memory Architecture (UMA) of the Apple M4 chip, offloading 100% of tensor layers to the Metal GPU (`-ngl 99`).

![Screenshot 1 - llama-server Metal GPU](../screenshots/print_screen_01_llama_server.png)

* **Key telemetry points shown:**
  * Device allocation: `Apple M4 (10 GPU compute cores)`.
  * Model DRAM loading time: `347.47 ms`.
  * Prompt evaluation throughput: `195.06 ms / 10 tokens` (`51.27 tokens/s`).
  * Autoregressive token generation throughput: `21.59 ms per token` (`46.32 tokens/s`).
  * Loopback health check (`curl http://127.0.0.1:8080/health` $\implies$ `{"status":"ok"}`).

---

### 2. Cold Start Startup Latency Measurement via `hyperfine v2.0.0`

Compares process initialization speed from `execve()` between PicoClaw's compiled Go ARM64 binary and OpenClaw's dynamic Node.js/V8 runtime executing `agent --help` over $n = 30$ statistical repetitions.

![Screenshot 2 - hyperfine Cold Start](../screenshots/print_screen_02_hyperfine.png)

* **Key telemetry points shown:**
  * **PicoClaw (Go):** mean of **$9.63 \pm 0.59\text{ ms}$**.
  * **OpenClaw (Node.js):** mean of **$225.55 \pm 43.02\text{ ms}$**.
  * **Finding:** PicoClaw is **$23.42 \pm 4.68$ times faster** in cold start startup, eliminating JIT warm-up and module graph resolution latency.

---

### 3. Apple M4 SMC Hardware Power Telemetry (`/usr/bin/powermetrics`)

Real-time 100 ms telemetry sampling from Apple System Management Controller (SMC) current and voltage shunts for CPU, Metal GPU, and Neural Engine (ANE) power rails.

![Screenshot 3 - powermetrics Apple M4 SMC](../screenshots/print_screen_03_powermetrics.png)

* **Key telemetry points shown:**
  * **Idle Baseline:** Combined SoC power of **$1,458\text{ mW}$ ($1.46\text{ W}$)**, with Metal GPU consuming only $28\text{ mW}$ and E-cores running at $1,980\text{ MHz}$.
  * **PicoClaw under W2 Load:** Metal GPU reaches $100.0\%$ active residency at maximum frequency of $1,578\text{ MHz}$, drawing **$12,672\text{ mW}$ ($12.67\text{ W}$)**, while CPU draws $3,765\text{ mW}$, yielding **$16,437\text{ mW}$ ($16.44\text{ W}$)** total package power.
  * **OpenClaw under W2 Load:** GPU draws **$12,659\text{ mW}$** and CPU draws $3,803\text{ mW}$, totaling **$16,463\text{ mW}$ ($16.46\text{ W}$)**.
  * **ANE Power = 0 mW:** Confirms empirically that `llama.cpp` executes 100% of tensor operations on the Metal GPU without offloading to the Neural Engine.

---

### 4. Real Live Physical Campaign Execution (`run_live_campaign.py`)

Shows real-time physical workload evaluations dispatching live prompt reflection (W1), tool calling chains (W2), vector RAG (W3), and multi-turn ReAct loops (W4) against the hardware.

![Screenshot 4 - Live Physical Execution](../screenshots/print_screen_04_live_execution.png)

* **Key telemetry points shown:**
  * Real-time metrics: Task completion time ($T_{\text{task}}$), neural inference latency ($T_{\text{neural}}$), pure agent orchestration overhead ($T_{\text{orch}}$), and physical resident memory footprint (`RAM MB`).
  * PicoClaw maintains $T_{\text{orch}} < 1\text{ ms}$ in W1 with RAM at $\sim 11\text{ MB}$, whereas OpenClaw consumes $85\text{ to }88\text{ MB}$ of RAM and higher orchestration overhead.

---

### 5. Poisson High-Assertiveness Statistical Engine ($\ge 90\%$)

Demonstrates the calculation of theoretical event bounds $K$, Garwood (1936) exact confidence intervals, and the Cameron & Trivedi (1990) overdispersion test.

![Screenshot 5 - Poisson Statistical Engine](../screenshots/print_screen_05_poisson_engine.png)

* **Key telemetry points shown:**
  * Theoretical threshold for $90\%$ assertiveness: $K \ge 271$ events ($Z = 1.6449$).
  * W2 Evaluation with $K = 300$ events: PicoClaw achieves **$326.39\text{ ops/s}$** with **$90.33\%$ assertiveness**.
  * W4 Evaluation with $K = 1,000$ events: PicoClaw achieves **$223.32\text{ ops/s}$** with **$93.75\%$ assertiveness**.
  * Overdispersion test: $z = 0.00, \; p = 1.00$, confirming strict Poisson equidispersion.

---

### 6. Host OS Quiescence and Sleep Prevention Protocol (`caffeinate` & `mdutil`)

Demonstrates system-level sleep suppression and Spotlight index suspension preventing background I/O interference during measurements.

![Screenshot 6 - OS Quiescence and Caffeinate](../screenshots/print_screen_06_caffeinate_quiescence.png)

* **Key telemetry points shown:**
  * The background daemon `/usr/bin/caffeinate -dims` actively preventing display, disk, idle CPU, and system sleep.
  * Spotlight index suspension across `/`, `/System/Volumes/Data`, and `/System/Volumes/Preboot` via `mdutil -a -i off`, and subsequent restoration with `mdutil -a -i on` after testing.
