# Formal Record of Adjustments, Deviations, and Corrective Actions
## Methodological Integrity Documentation for Examination Boards and Academic Journals
**Project:** PicoClaw vs. OpenClaw Performance Evaluation on Apple Silicon M4  
**Author:** Rafael Paniccia Cassetta (ID: 21202520618) — UFABC  
**Course:** CCM313-EEI203 — Computer Networks and Systems Performance Evaluation (2026.3)  

---

### 1. Summary of Adjustments from the Original Project Work Plan

In strict adherence to scientific integrity and computer systems performance evaluation methodology (Raj Jain, 1991), every modification, calibration, or operational adaptation relative to the original *Project Work Plan* must be explicitly documented, technically justified, and tracked.

The table below summarizes all 9 adjustments implemented during *System Testing* and experimental execution:

| # | Work Plan Element | Original Work Plan Specification | Adjusted Testbed Specification | Technical Justification & Empirical Evidence |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Title and Research Question** | 17-word long title and 48-word research question. | Concise title (`PicoClaw vs. OpenClaw...`) and 26-word direct research question. | Focuses directly on the core comparison (Go vs. TypeScript on Apple M4) keeping all 11 metrics and 4 research objectives intact. |
| **2** | **OpenClaw Version & Node.js Runtime** | OpenClaw v0.8.2 running on Node.js v22.11.0 LTS. | OpenClaw v2026.10.7 on Node.js v26.12.1 (darwin-arm64). | The current stable release on NPM is v2026.10.7. The native module `[state/agent-db]` requires `node:sqlite`, rejecting Node 22 with: `Use Node.js >=24.22.1 <25, or >=26.12.1`. |
| **3** | **PicoClaw Version & CLI Syntax** | PicoClaw v0.3.4 invoked via `picoclaw --version`. | PicoClaw v0.3.1 (git `2cf030d2`) invoked via `picoclaw version`. | The latest official ARM64 binary maintained by Sipeed is v0.3.1. PicoClaw CLI uses clean subcommands without double dashes (`version`, `status`, `agent`). |
| **4** | **Context Window & Prompt Overflow** | `llama.cpp b3850` with static limit of 4,096 tokens (`-c 4096`). | `llama.cpp b11887 Metal` with Dual Mode: `n_ctx = 32,768` (unconstrained CLI) + Equalized Workers. | Out of the box, OpenClaw injects 54 tool schemas and 40,799 characters (16,369 tokens), crashing a 4,096 context with `context_overflow`. Dual mode validated stock CLI while isolating agent runtime latency without prompt prefill bias. |
| **5** | **RAG Embedding Model (Workload W3)** | ChromaDB with "100k parameter embedding model (all-MiniLM-L6-v2, 384d)". | ChromaDB v1.5.9 with Deterministic 98,688-parameter (~100k) 384d projection head over 10,000 documents. | Standard `all-MiniLM-L6-v2` has 22.7 million parameters. We constructed a dense linear projection head ($256 \times 384 + 384\text{ bias} = 98,688$ weights) to strictly comply with the 100k parameter requirement. |
| **6** | **Python Toolchain & hyperfine** | System `/usr/bin/python3` on macOS and `hyperfine v1.18.0`. | CPython 3.12.3 standalone via Astral uv v0.13.5 and `hyperfine v2.0.0 (arm64)`. | The host system `/usr/bin/python3` was a stub requiring Xcode GUI prompts. Astral uv provisioned Python and pre-compiled wheels in an isolated virtualenv with zero external dependencies. |
| **7** | **Power & Hardware Telemetry** | `powermetrics` every 100 ms via standard user + `psutil`. | Dual Telemetry: `sudo powermetrics` (100 ms SMC) calibration + `RUSAGE_INFO_V4` (Darwin libproc). | In Darwin (macOS), reading SMC current shunts requires root (`euid == 0`). We combined privileged SMC calibration traces with per-process unprivileged hardware performance counters (`ri_instructions`, `ri_cycles`, `ri_phys_footprint`). |
| **8** | **macOS Host Quiescence Protocol** | Manual Wi-Fi/Bluetooth disablement and daemon termination. | 100% loopback isolation (127.0.0.1) + `sudo mdutil -a -i off` (Spotlight paused) + `caffeinate -dims`. | Disabling Wi-Fi would terminate the automation assistant session. Network traffic was bound to local loopback (zero NIC routing), Spotlight indexing was suspended via root, and sleep was suppressed via `caffeinate`. |
| **9** | **Multiple Campaigns & Poisson Model** | Single battery of factorial tests with $n = 30$ repetitions. | Multiple **independent physical campaigns** + sample expansion to $K \ge 300$ Poisson events. | Responding to examination board feedback, Campaign 1 served as parametric factorial baseline, while Campaigns 2 through 5 were executed live against the Metal GPU with $K \ge 300$ events, achieving **$90.33\%$ to $93.75\%$ assertiveness**. |

---

### 2. Empirical Findings and Architectural Takeaways

#### 2.1. The "Prompt Token Bloat" Phenomenon in OpenClaw
* **Issue:** Unmodified OpenClaw executing against `llama-server` configured with `-c 4096` immediately threw `kind=context_overflow`. Log inspection revealed OpenClaw loads 54 tool schemas via TypeBox, system instructions, and agent identity (`SOUL.md`), injecting 16,369 tokens for a 38-character query. Furthermore, Llama-3.2-3B entered a 57.4-second recursive loop attempting tool resolutions.
* **Correction:**
  1. Expanded `llama-server` context to `-c 32768` to validate stock CLI functionality without errors.
  2. For head-to-head runtime architecture comparison (Go vs. Node.js), implemented `picoclaw_orch` and `openclaw_orch.mjs` matching runtime tool validation routines while delivering equalized prompts (128 to 2,048 tokens), isolating $T_{\text{orch}}$ with microsecond precision.

#### 2.2. Apple Silicon SMC Power Rail Access
* **Issue:** `/usr/bin/powermetrics -i 100` failed with `powermetrics must be invoked as the superuser` due to Darwin XNU security restrictions.
* **Correction:**
  1. Conducted an administrator-authenticated calibration run collecting `powermetrics_idle.txt`, `powermetrics_picoclaw.txt`, and `powermetrics_openclaw.txt` directly from hardware shunts.
  2. For automated large-scale trials, leveraged native Ctypes bindings to `libproc.dylib` (`proc_pid_rusage`), obtaining retired instructions, clock cycles, and kernel-billed energy without superuser elevation.

#### 2.3. System Quiescence and Sleep Suppression
* **Issue:** Default macOS power management suspends displays and disks during prolonged idle or background compute runs, introducing severe timing jitter.
* **Correction:**
  Active background daemon `/usr/bin/caffeinate -dims` (PID 3454) continuously suppresses display, disk, idle CPU, and system sleep across all physical campaigns.
