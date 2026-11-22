# QUAD-PLATFORM MICROARCHITECTURAL SYSTEMS REPLICATION REPORT
## Empirical Systems Evaluation: macOS ARM64 (Apple M4) vs. Linux x86_64 vs. Windows 11 x86_64 (NVIDIA) vs. Windows 10/11 x86_64 (Intel Graphics)

**Document Classification:** Systems Replication Report  
**Target Standard:** SoftwareX / Elsevier Artifact Verification and Systems Benchmarking Guidelines  
**Date of Audit:** 2026-11-21  
**Repository Branch:** `main`  
**Evaluation Summary:** Campanha Final - Empirical measurement and quad-platform verification across 4 distinct physical environments.  

---

## 1. EXECUTIVE SUMMARY & CONSOLIDATED METRICS

This conformance report documents the physical execution, microarchitectural instrumentation, and statistical consolidation of the **PicoClaw vs. OpenClaw** benchmark suite across **four distinct physical hardware platforms**:
1. **Platform 1 (Reference Architecture):** Apple Silicon Mac Mini M4 (Darwin 26.6.2, ARM64, 10-core SoC [4 Performance + 6 Efficiency], 24 GB Unified LPDDR5X Memory at 120 GB/s on-die bandwidth, Metal 3, Apple SMC `powermetrics` telemetry).
2. **Platform 2:** Dell G15 5520 under Ubuntu 26.04 LTS (Kernel Linux 7.0.0-43-generic x86_64, Intel Core i5-12500H [16 logical threads], 30.5 GiB DDR5-4800, discrete NVIDIA GeForce RTX 3050 Laptop GPU 4GB VRAM, Intel RAPL MSR + NVIDIA NVML + `perf_event_open`).
3. **Platform 3:** Dell G15 5520 under Microsoft Windows 11 64-bit (Build 26200 x86_64, Intel Core i5-12500H [16 logical threads], 31.7 GiB DDR5-4800, discrete NVIDIA GeForce RTX 3050 Laptop GPU 4GB VRAM, Intel MSR RAPL + NVML DLL + Win32 PSAPI + WDDM).
4. **Platform 4:** MSI Z97 XPOWER AC under Microsoft Windows 10 Pro 64-bit (Build 19045 x86_64, Intel Core i7-4790K @ 4.00GHz [4 cores / 8 threads], 15.88 GiB Shared DDR3-1600 System RAM, integrated Intel HD Graphics 4600 iGPU UMA, Win32 PSAPI process telemetry in unprivileged user-mode).

> **Nota Metodológica Obrigatória sobre Offload e Regime B (Dell G15 Linux/Windows & Intel iGPU):**  
> A inferência foi realizada em regime híbrido (`-ngl 16`, correspondendo a ~3.0 GiB na VRAM de 4 GB no Dell G15; e abertura UMA em memória DDR3 no Intel iGPU), acarretando saturação de barramento PCIe/RAM. Os ganhos absolutos em cache quente (Regime B) nas arquiteturas x86 são limitados por esse offload parcial e não são diretamente comensuráveis com o M4 de memória unificada.  
> *(English: Inference was conducted in a hybrid regime (-ngl 16, corresponding to ~3.0 GiB within the 4 GB VRAM ceiling on Dell G15; and host UMA DDR3 aperture on Intel iGPU), entailing PCIe/RAM bandwidth saturation. Absolute gains in warm cache (Regime B) on x86 architectures are constrained by this partial offload and are not directly commensurable with the unified memory M4.)*

> **Authorship and Execution Node Declaration:** Git author `drsgima` (author of the Windows testbed commits) is the principal author operating the dedicated Windows physical testbed nodes.

### Key Empirical Findings (Workload W2 -- Standard 15-Tool Chain):
- **Client Middleware Dispatch Latency ($T_{\text{orch}}$):**
  * **macOS ARM64 (M4):** PicoClaw Go achieved a median latency of **5.53 ms** vs. OpenClaw Full at **24.55 ms** (**4.44x speedup**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
  * **Linux x86_64:** PicoClaw Go achieved a median latency of **6.66 ms** vs. OpenClaw Full at **35.99 ms** (**5.40x speedup**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
  * **Windows 11 NVIDIA:** PicoClaw Go achieved a median latency of **13.11 ms** vs. OpenClaw Full at **48.55 ms** (**3.70x speedup**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
  * **Windows Intel iGPU:** PicoClaw Go achieved a median latency of **14.03 ms** vs. OpenClaw Full at **68.89 ms** (**4.91x speedup**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
- **Resident Physical Memory Footprint (Peak RSS):**
  * **macOS ARM64 (M4):** PicoClaw Go stabilized at **5.09 MB** vs. OpenClaw Full at **37.71 MB** (**7.41x memory reduction**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
  * **Linux x86_64:** PicoClaw Go stabilized at **9.70 MB** vs. OpenClaw Full at **86.67 MB** (**8.94x memory reduction**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
  * **Windows 11 NVIDIA:** PicoClaw Go stabilized at **10.20 MB** vs. OpenClaw Full at **72.93 MB** (**7.15x memory reduction**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
  * **Windows Intel iGPU:** PicoClaw Go stabilized at **8.19 MB** vs. OpenClaw Full at **54.76 MB** (**6.69x memory reduction**; Cliff's $\delta = 1.00$, Mann-Whitney $p < 0.0001$).
- **Instruction bloat and Hardware PMC Telemetry:**
  * **macOS ARM64 (Apple PMU):** OpenClaw Full executed **791.7M instructions**, compared to **62.3M** in PicoClaw (**12.71x instruction elimination ratio**).
  * **Linux x86_64 (`perf_event_open`):** OpenClaw Full executed **771.5M instructions**, compared to **32.7M** in PicoClaw (**23.63x instruction elimination ratio**).
  * **Windows Platforms (NVIDIA and Intel iGPU):** Hardware instruction counters are restricted in user-mode by the OS kernel (marked `N/A*`); CPU cycles tracked empirically via `QueryProcessCycleTime` confirm **528.1M cycles** in OpenClaw Full vs. **45.8M** in PicoClaw (**11.54x cycle overhead**).

---

## 2. HARDWARE THROTTLING & IDLE POWER DECOMPOSITION

### 2.1. Análise de Registradores NVML e Diagnóstico de Throttling no Linux e Windows
A inspeção detalhada dos registros brutos JSONL ao longo de todos os trials no Linux e Windows documenta o comportamento térmico e de potência:
- **Comportamento Cumulativo Estacionário no Linux (`cpu_pkg_throttle_events`):** Os eventos registrados no Linux em `cpu_pkg_throttle_events` refletem comportamento cumulativo estacionário decorrente da leitura acumuladora do registrador MSR da CPU Intel (`IA32_PACKAGE_THERM_STATUS`), mantendo estabilidade térmica ao longo dos trials sem degradação progressiva de throughput.
- **Limites Estritos de TDP no Windows (`gpu_sw_power_cap`):** Os registros de `gpu_sw_power_cap` (máscara `0x8`) no Windows 11 NVIDIA operaram exclusivamente para mitigar limites estritos de TDP móvel (teto de 75W da GPU móvel) durante rajadas curtas de multiplicação matricial no prefill de contexto, não correspondendo a throttling térmico.
- **Ausência de Throttling Térmico de Hardware:** O registrador booleano da NVML `gpu_thermal_throttle_active_end` permaneceu `False` em 100% dos trials com dGPU no Linux e Windows. A temperatura da GPU permaneceu entre 50.0°C e 74.0°C, estritamente abaixo do limiar de 87.0°C exigido para acionamento de `HW_THERMAL_SLOWDOWN` (máscara `0x40`) ou `SW_THERMAL_SLOWDOWN` (máscara `0x20`).

### 2.2. Explicit Idle Power ($P_{\text{idle}}$) Telemetry and Duration Integration
Idle power baselines were empirically characterized during dedicated quiescence intervals prior to benchmark execution:
- **macOS ARM64 (Apple M4):** $P_{\text{idle}} = 1.20\text{ W}$ (Apple SMC SoC Package, quiescent range 1.00 W -- 1.46 W).
- **Linux x86_64 (Ubuntu 26.04):**
  * Session 1: $P_{\text{idle}} = 19.71\text{ W}$ (Intel CPU Package RAPL: 14.74 W, discrete NVIDIA GPU NVML: 4.98 W).
  * Session 2: $P_{\text{idle}} = 20.08\text{ W}$ (Intel CPU Package RAPL: 15.10 W, discrete NVIDIA GPU NVML: 4.98 W).
- **Windows 11 x86_64 (NVIDIA):**
  * Session 1: $P_{\text{idle}} = 24.13\text{ W}$ (Intel CPU Package RAPL MSR: 15.20 W, discrete NVIDIA GPU NVML: 8.93 W).
  * Session 2: $P_{\text{idle}} = 21.96\text{ W}$ (Intel CPU Package RAPL MSR: 15.20 W, discrete NVIDIA GPU NVML: 6.76 W).
- **Windows 10/11 x86_64 (Intel Graphics):**
  * Session 1 & 2: $P_{\text{idle}} = 28.50\text{ W}$ (Intel Core i7-4790K host package baseline). Note: dynamic host package energy marked N/A** due to unprivileged user-mode execution without kernel MSR RAPL driver.

> **Explanation of Apparent $P_{\text{idle}}$ Duration Scaling in Linux:**
> The telemetry harness computes net dynamic energy by subtracting $P_{\text{idle}} \times \text{trial\_wall\_s}$ from gross energy across the complete trial lifecycle (which includes subprocess initialization, loopback socket binding, and process teardown). In short-duration workloads (W1--W2), $\text{trial\_wall\_s} > T_{\text{task}}$ due to fixed subprocess overhead. Dividing $(E_{\text{total}} - E_{\text{net}})$ by $T_{\text{task}}$ yields an apparent variation from ~24.9 W (W1) to ~20.1 W (W4), which is entirely an artifact of lifecycle duration mismatch rather than sensor drift.

---

## 3. STATISTICAL SERIAL DEPENDENCE & DRIFT ANALYSIS

Following recommendations from systems benchmarking literature (Kalibera & Jones 2013; Maricq et al. 2018; Goldsman & Schmeiser 1997), serial dependence and temporal drift were evaluated across all experimental cells:

### 3.1. Autocorrelation ($r_1$), Effective Sample Size ($n_{\text{eff}}$), and Moving Block Bootstrap
- **Regime A (Cold Prefill):** In cold prefill across all platforms, serial autocorrelation remained strictly within white-noise boundaries ($|r_1| < 2/\sqrt{30} \approx 0.365$). On macOS ARM64, $r_1 \in [-0.246, +0.142]$; on Linux x86_64, $r_1 \in [-0.348, +0.233]$; on Windows 11, $r_1 \in [-0.184, +0.174]$. This confirms that cold cache evictions effectively eliminated context leakage.
- **Regime B (Warm Cache):** In warm cache, serial autocorrelation emerged across a minority of cells:
  * On macOS ARM64, negative autocorrelation ($r_1 \in [-0.518, -0.829]$) was observed across W1--W3. This negative autocorrelation is attributed to alternating coupling between telemetry harness dispatch cadence, loopback TCP socket buffer drainage, and server thread wake-up scheduling, rather than cache residuals.
  * On Windows 11, positive autocorrelation ($r_1 \in [+0.390, +0.732]$) was observed, reflecting memory page retention dynamics in the Windows Standby List.
  * For all cells exhibiting $|r_1| > 0.365$, effective sample sizes $n_{\text{eff}} = n(1 - r_1)/(1 + r_1)$ were computed, and 95% Confidence Intervals were derived via **Moving Block Bootstrap (MBB, block size $b=3$)** to preserve short-range serial dependence structure.
- **Interpretação de $n_{\text{eff}}$ e Robustez Estatística:** Os valores de $U$ e de $\delta$ de Cliff refletem $n=30$. A métrica $n_{\text{eff}}$ é documentada exclusivamente como diagnóstico de saúde da dependência serial e não altera os contrastes robustos de efeitos grandes observados. *(Test statistics $U$ and Cliff's $\delta$ reflect $n=30$; $n_{\text{eff}}$ is documented exclusivamente as a health diagnostic of serial correlation without altering the observed large effect magnitudes).*

### 3.2. Linear Regression Drift Test with Holm-Bonferroni Family-Wise Error Control
The exploratory comparison was conducted via ordinary least squares linear regression of task latency against trial order (rep $1 \dots 30$):
- Across all experimental cells, **over 95% of cells exhibited zero statistically significant drift** after Holm-Bonferroni correction ($p_{\text{adj}} \ge 0.05$).
- In the rare cases where drift occurred (e.g. W4 long-context prefill), slope magnitudes represented less than $0.09\%$ of total task duration per repetition, driven by minor cumulative memory allocation and subtle thermal equilibrium adjustments rather than systemic instability.

---

## 4. SCIENTIFIC REVISION OF EMPIRICAL TABLES

### 4.1. Table 5: Tool-RAG Schema Pruning Analysis
- **Token Reduction:** Tool-RAG dynamic pruning reduces active prompt tokens from 7,091 tokens (unmitigated 54-tool catalog) to **917 tokens** (retrieved Top-5 schema), representing an **$-87.1\%$ token reduction**.
- **Regime Separation:** In Regime A (Cold Prefill), dynamic schema pruning eliminates quadratic attention overhead, providing substantial speedup (up to 9.96x on Intel Graphics and 7.43x on macOS M4). In Regime B (Warm KV Cache), prefix KV reuse amortizes tool schema attention, confirming that Tool-RAG's primary microarchitectural value is cold prefill mitigation.

### 4.2. Table 4: KV-Cache Thrashing & Slot Isolation
- The column `Thrashing Overhead` was renamed to `Full-to-Minimal Catalog Ratio` to accurately reflect architectural schema scaling.
- Actual cache eviction penalties were quantified directly as the ratio of uncontrolled thrashing to isolated retention ($T_2/T_3$):
  * **macOS ARM64:** Minimal catalog cache penalty $= 7.15\text{x}$; Full catalog cache penalty $= 20.24\text{x}$.
  * **Linux x86_64:** Minimal catalog cache penalty $= 1.96\text{x}$; Full catalog cache penalty $= 2.63\text{x}$.
  * **Windows 11:** Minimal catalog cache penalty $= 1.99\text{x}$; Full catalog cache penalty $= 2.35\text{x}$.

### 4.3. Table 3: Cache Invariance Clarification
- Empirical measurements indicate that **cache invariance applies strictly to absolute orchestrator latency $T_{\text{orch}}$ (ms)** ($|\Delta T_{\text{orch}}| < 0.5\text{ ms}$ between cold prefill and warm cache).
- The relative overhead fraction $\Phi_{\text{orch}} = T_{\text{orch}} / T_{\text{task}}$ increases under warm cache because neural inference latency $T_{\text{neural}}$ decreases by up to 10x.

### 4.4. Table 7: Multi-Platform Dual-Session Replication
- Complete dual-session replication across platforms demonstrated cross-session median divergence below $2.0\%$ across all tested agent runtimes, with formal two one-sided equivalence tests (TOST) confirming statistical equivalence within $\pm 15\%$.

### 4.5. Table 8: Enterprise LangChain Workload (W5)
- Consolidated telemetry and LLM-as-a-judge quality scores (1–5) across platforms confirm that PicoClaw maintains deterministic task success while eliminating 75–85% of Node.js resident memory bloat.

---

## 5. FORMAL LITERATURE CITATIONS

This experimental protocol and microarchitectural interpretation are formally aligned with systems and benchmarking literature:
1. **Kalibera, T. & Jones, R. (2013):** *Rigorous Benchmarking in Reasonable Time*, ACM ISMM '13, pp. 63--74. DOI: `10.1145/2464157.2464160`
2. **Maricq, A. et al. (2018):** *Taming Performance Variability*, USENIX OSDI '18, pp. 409--425. ISBN: `978-1-939133-08-3`
3. **Goldsman, D. & Schmeiser, B. W. (1997):** *Methods for Estimating the Variance of the Sample Mean*, ACM TOMACS, 7(3):389--418. DOI: `10.1145/259207.259235`
4. **Kwon, W. et al. (2023):** *Efficient Memory Management for Large Language Model Serving with PagedAttention*, ACM SOSP '23, pp. 611--626. DOI: `10.1145/3600006.3613165`

---

## 6. CRYPTOGRAPHIC MANIFEST AUDIT & TRIAL INVENTORY

Every empirical `.jsonl` trial record was audited for schema validity, null values, and SHA-256 integrity:

| Platform | Session Identifier | Dataset Role | Measured Trials | Warmup Trials | Full SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (Apple Silicon M4) | publication_campaign (Campanha Final) | `raw` | 750 | 75 | `9f624bd429c810fbbaa2c952b18ea718b17d42b7b8667d6419c561ec7f60ed01` |
| macOS ARM64 (Apple Silicon M4) | publication_campaign (Campanha Final) | `warm` | 750 | 75 | `bd2854fd866a1d1b963ef7cfe8e659e6c68b59794c1cf6c3ac4f38952f79dea6` |
| macOS ARM64 (Apple Silicon M4) | publication_campaign (Campanha Final) | `kv` | 90 | 0 | `48532324bcb7ad5c0d072c80571480e308dfdf48029312cded4677f47bbd3081` |
| macOS ARM64 (Apple Silicon M4) | publication_campaign (Campanha Final) | `mcp` | 135 | 0 | `03e8d3bd247e29c498e87a727daaa41d47e4d3b6005713d25a0a33301d3232c4` |
| macOS ARM64 (Apple Silicon M4) | publication_campaign (Campanha Final) | `rag` | 960 | 96 | `3631f7843cef17e9a6c53fd2fc0970164c10ec090433d1f034e4d3238e35dc22` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_1 | `raw` | 720 | 72 | `d1638d0828368255c04d2036fa406a3eaf2493cf84c7fa5420e9c0657e7c7163` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_1 | `warm` | 720 | 72 | `57b161cddcdea65fc9ad41c8d1057f9211e20d9c25a024249191dda4a36a3986` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_1 | `kv` | 180 | 4 | `8b7412a2d4e4057d4989ae51393dfd494ebfcd47c8a34bf07c9fe7af9d89d077` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_1 | `mcp` | 270 | 27 | `7c564aea727a8b5e96b5b84e04ddb2ba4ea3229881a459992c037258b76c3162` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_1 | `rag` | 480 | 48 | `4aa33319210e6b10e648df12f1da1d290a3ed8d2c4d34a4af7f9568ca159ece9` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_2 | `raw` | 720 | 72 | `b93043922cb156324ef7593568747634c7a65471eaaecadc45020719395e037a` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_2 | `warm` | 720 | 72 | `fa6889e7dcc500624f333c7e050edb13541a4cd7baacb2859cb708ff75f6f663` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_2 | `kv` | 180 | 4 | `548ac456d8996e18d4682b46f40f7fa2f69ef85e505e8ebb65dd94b9d67e4c0f` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_2 | `mcp` | 270 | 27 | `5df9cbfe446f82bead1459ae491db087f4e75c829c0ed7969e35aa1e216b62cd` |
| Ubuntu 26.04 LTS (Linux 7.0 x86_64) | clean_run_linux_session_2 | `rag` | 480 | 48 | `077b0c75beb580df9fb8ef61c6d367c27d88a431720aa694219407e0ff077669` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session1 | `raw` | 900 | 90 | `264db96648f43c8301a936cd9e8a26895a8c79d284b5a78dd62021a1b4006cf9` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session1 | `warm` | 900 | 90 | `3091e23b550627a6b34b692f50566cf99f12ab3ac3fda820dbd2e66a953de019` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session1 | `kv` | 180 | 4 | `5ab229460ef19505cd721cf795d7569337212a81fdd3652aa3275a4fb0f8de79` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session1 | `mcp` | 270 | 27 | `9888d6edfabe937e2b0e85845314479b361013ba0fed24220ce58bf206abffab` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session1 | `rag` | 600 | 60 | `449bc5204c6f1cd222002eeebd95a3ebbdc45915002a188eb4fa4a7a3b1848f9` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session2 | `raw` | 900 | 90 | `f42f751681083f82787947c10244fecdd24c21ba6e123abd3752870d30568297` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session2 | `warm` | 900 | 90 | `d2df5802ed7c48e3064da8d5eabd27e9f494756bffdb4ad1429560c5286eb891` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session2 | `kv` | 180 | 4 | `f4ac5017ceae16ff4c28b936b988d5f76f96f225e81de1d627970ccb5ce28786` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session2 | `mcp` | 270 | 27 | `d9b1e3500af1b210405a7c87de1c6d442ccba36a41e355a99bba68ab16d12e36` |
| Microsoft Windows 11 (x86_64 build 26200) | windows_x86_64_session2 | `rag` | 600 | 60 | `ad45f15cb9bea1c483692b6e4dcf39062c709b4f2f2fad1267316692ac616e62` |
| Microsoft Windows 10/11 (Intel HD Graphics 4600 / UMA Architecture) | windows_intel_graphics_session1 | `raw` | 300 | 30 | `e6993e9edeb9964f2109972da4444e6bca4d9952260961eebf1a3286d2a71d80` |
| Microsoft Windows 10/11 (Intel HD Graphics 4600 / UMA Architecture) | windows_intel_graphics_session1 | `warm` | 300 | 30 | `081809a8c7b44808fb0cfe41d4bdf7a08d77e68f8e16dfcf1f678ecfe5b4f7ab` |
| Microsoft Windows 10/11 (Intel HD Graphics 4600 / UMA Architecture) | windows_intel_graphics_session1 | `rag` | 120 | 12 | `b4501867f7a7642c18f31130f0f35e926e9aeb3e19d8a028ce32acf28afff669` |
| Microsoft Windows 10/11 (Intel HD Graphics 4600 / UMA Architecture) | windows_intel_graphics_session2 | `raw` | 300 | 30 | `920d68b0197e3039021a1ca327b41807c2cd7b60ed1b606371f6d30e65854a33` |
| Microsoft Windows 10/11 (Intel HD Graphics 4600 / UMA Architecture) | windows_intel_graphics_session2 | `warm` | 300 | 30 | `d922a01b5dd42bd5ce8b4b9248bf6a4cb636a45384c025d9bffcb010f021e22c` |
| Microsoft Windows 10/11 (Intel HD Graphics 4600 / UMA Architecture) | windows_intel_graphics_session2 | `rag` | 120 | 12 | `34736fbad16b3fb5d499c14805a4e4700d21337ed7a57090bad8b98811a04157` |

---

## 7. EMPIRICAL SUMMARY & CONCLUDING OBSERVATIONS

The quad-platform measurement campaign demonstrates that:
1. **Architectural Invariance:** The Node.js V8 runtime client middleware bottleneck persists across all four operating systems and processor architectures.
2. **Statistical Robustness:** Moving block bootstrap confidence intervals and TOST equivalence tests establish cross-session replication across all evaluated platforms.
3. **Microarchitectural Grounding:** Hardware instruction bloat and memory footprint scaling are verified through direct PMU counters on ARM64 and x86_64.
4. **Methodological Transparency:** All raw datasets, statistical consolidation scripts, and configuration manifests are documented for independent quad-platform replication.
