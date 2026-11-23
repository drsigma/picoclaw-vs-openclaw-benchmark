# AUDIT_REPORT_FINAL.md
## Quad-Platform Repository Reproducibility Log & Artifact Inventory

> **Scope Notice:** This document is a technical reproducibility log for the repository artifacts (generated dynamically by `scripts/reproduce_quad_platform_analysis.py`) and is **not part of the manuscript**.

**Repository:** `picoclaw-vs-openclaw-benchmark`  
**Principal Author:** Rafael Paniccia Cassetta (UFABC)  
**Windows Testbed Operator:** `drsgima` (git author `drsgima` on Windows 11 NVIDIA commits; `drsigma` on Windows 10 Intel iGPU commits)  
**Consolidation Date:** 2026-11-22  
**Branch:** `main`  
**Dataset Scope:** Quad-Platform (4 physical hardware/OS profiles, 35 raw `.jsonl` files on disk, 190 experimental cells).  

---

## 1. EXECUTED COMMANDS AND OBSERVED OUTPUTS

The following commands were executed in the repository virtual environment (`.venv_repro`) on branch `main`:

| Command | Observed Output |
| :--- | :--- |
| `python3 scripts/reproduce_quad_platform_analysis.py` | Scanned `35` `.jsonl` files (`18,616` lines, `16,995` measured trials, `1,621` warmups), computed `190` diagnostic cells, generated Tables 1--8 (`.md`/`.tex`), rendered Figures 1--6 (300 DPI), generated reports and `audit_export/REVIEW_PACKAGE_README.md`, and built `audit_export_quad_platform.zip` (exit code 0). |
| `python3 scripts/generate_audit_txt_chunks.py` | Exported 4 lightweight text chunks (`INDEX.txt`, `audit_pt1_report_and_checklist.txt`, `audit_pt2_tables.txt`, `audit_pt3_summary_and_diagnostics.txt`) in `audit_txt_chunks/`, each `<= 150 KB` (exit code 0). |
| `pytest -v` | `59/59 tests passed` (exit code 0; full transcript saved in `audit_export/pytest_output.txt`) (58 passed in test suite; 17 Python 3.14 upstream `DeprecationWarning` notices from langsmith `asyncio.iscoroutinefunction` without functional impact). |
| `python3 scripts/verify_manifest.py` | `287/287` tracked files matched their recorded SHA-256 digests in `data/manifest_sha256.json` (`0` missing, `0` hash mismatches, exit code 0). |

---

## 2. QUAD-PLATFORM HARDWARE COVERAGE (4 PHYSICAL ENVIRONMENTS)

| ID | Platform / Profile | Architecture | CPU & Threads | Memory & Bus | Neural Accelerator (GPU) | Native Telemetry | $P_{\text{idle}}$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P1** | **macOS ARM64** | Apple Silicon M4 | 10 cores (4P+6E) | 24 GB LPDDR5X (120 GB/s UMA) | Metal 3 (`-ngl 99`, full offload) | Apple SMC `powermetrics` + XNU `libproc` | 1.20 W |
| **P2** | **Linux x86_64** | Ubuntu 26.04 LTS (Kernel 7.0) | Intel Core i5-12500H (16T) | 30.5 GiB DDR5-4800 | NVIDIA RTX 3050 Laptop (4 GB, hybrid `-ngl 16`) | Intel RAPL MSR + NVML + `perf_event_open` | 19.71 W / 20.08 W |
| **P3** | **Windows 11 NVIDIA** | Win11 Pro (Build 26200) | Intel Core i5-12500H (16T) | 31.7 GiB DDR5-4800 | NVIDIA RTX 3050 Laptop (4 GB, hybrid `-ngl 16`) | Intel MSR RAPL + NVML DLL + Win32 PSAPI / Cycles | 24.13 W / 21.96 W |
| **P4** | **Windows Intel iGPU** | Win10 Pro (Build 19045) | Intel Core i7-4790K (4C/8T) | 15.88 GiB DDR3-1600 (Shared RAM) | Intel HD Graphics 4600 (UMA Shared Aperture) | Win32 PSAPI + `QueryProcessCycleTime` (user-mode) | 28.50 W |

---

## 3. FILE INVENTORY AND SHA-256 DIGESTS (35 RAW `.jsonl` FILES)

Inventory table computed dynamically from the `.jsonl` files on disk (identical to Section 6 of `audit_export/Systems_Replication_Report.md`):

| Relative Path | Platform | Session Identifier | Role | Workloads | Total Lines | Measured Trials | Warmup Trials | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | :--- |
| `results/publication_campaign/raw_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `raw` | W1, W2, W3, W4, W5 | 825 | 750 | 75 | `9f624bd429c810fbbaa2c952b18ea718b17d42b7b8667d6419c561ec7f60ed01` |
| `results/publication_campaign/warm_cache_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `warm` | W1, W2, W3, W4, W5 | 825 | 750 | 75 | `bd2854fd866a1d1b963ef7cfe8e659e6c68b59794c1cf6c3ac4f38952f79dea6` |
| `results/publication_campaign/kv_cache_thrashing_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `kv` | W2 | 90 | 90 | 0 | `48532324bcb7ad5c0d072c80571480e308dfdf48029312cded4677f47bbd3081` |
| `data/mcp_live_transport_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `mcp` | W2 | 135 | 135 | 0 | `03e8d3bd247e29c498e87a727daaa41d47e4d3b6005713d25a0a33301d3232c4` |
| `results/publication_campaign/tool_rag_mitigation_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `rag` | W1, W2, W3, W4 | 1056 | 960 | 96 | `3631f7843cef17e9a6c53fd2fc0970164c10ec090433d1f034e4d3238e35dc22` |
| `results/publication_campaign/prefill_ablation.jsonl` | macOS (M4) | `darwin_m4_session1` | `prefill` | 8 conditions | 528 | 480 | 48 | `ce1a12908ef22c0c40b1ff42c3a17a0914779234d9e81e003c7cf2d1b2ee9f5f` |
| `results/publication_campaign/uma_energy_bandwidth_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `uma` | W2, W3 | 120 | 120 | 0 | `960dbbe9c568134175a5c049a3e5f936bcebeb69c93777c4dc7037c6a58a31e3` |
| `data/external_framework_langchain_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `langchain` | W1, W2, W3, W4 | 144 | 120 | 24 | `2fe416fbf8b74ca4dcd18bfb7bb58f69044fa31b8c5fb60a9f3f3658ea458365` |
| `results/publication_campaign/inter_session_trials.jsonl` | macOS (M4) | `darwin_m4_session2` | `warm` | W1, W2, W3, W4, W5 | 825 | 750 | 75 | `ca99fe1748f8e4c171f4a180e258c183797aae3291f7e0d3e44433c77e106ba0` |
| `data/linux_x86_64_session1/raw/raw_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `65f27603213370acfc317357c2c8a01f2abb664858c443b1ae27941d9d9d54a5` |
| `data/linux_x86_64_session1/raw/warm_cache_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `c7388d9d64c9b765ff29e4c91d7e5406b02764cc7cac48d6c7a06d0fd0962d67` |
| `data/linux_x86_64_session1/raw/kv_cache_thrashing_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `kv` | W2 | 184 | 180 | 4 | `b5217cdfae6f7ef23ee994b2555e5050150da3ba6303fa250550d1534b6ec559` |
| `data/linux_x86_64_session1/raw/mcp_live_transport_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `mcp` | W2 | 297 | 270 | 27 | `e8ba4fcbc7403346fb946e524571fe6bf69722eee7d58a560eaceccd1dd7c5f8` |
| `data/linux_x86_64_session1/raw/tool_rag_mitigation_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `ac3c0f22fba876213b9ebe3f6e49edaa5e0c71446827ad6a9139bddf14650b32` |
| `data/linux_x86_64_session2/raw/raw_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `43df3c3249528937871d9728bb4437107696117be1ec3af8f171f457a810957b` |
| `data/linux_x86_64_session2/raw/warm_cache_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `3767a65018317e9e3e93efb0b595e6bc64150b2a454cce7d7baba473f9d379da` |
| `data/linux_x86_64_session2/raw/kv_cache_thrashing_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `kv` | W2 | 184 | 180 | 4 | `c67bfcd561c8ef224a44221a37494c4886d3598eaff1a18f4788977fcf20a328` |
| `data/linux_x86_64_session2/raw/mcp_live_transport_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `mcp` | W2 | 297 | 270 | 27 | `907a8e21bc41eedc92f3fec78b2e9dc46fd2fd31e80a9e6073426570b5c655e9` |
| `data/linux_x86_64_session2/raw/tool_rag_mitigation_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `65434ed3546fbb07f6fcabadeafe64762f4a774c7faab56ee7c3c552dd2d4598` |
| `data/windows_x86_64_session1/raw/raw_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `264db96648f43c8301a936cd9e8a26895a8c79d284b5a78dd62021a1b4006cf9` |
| `data/windows_x86_64_session1/raw/warm_cache_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `3091e23b550627a6b34b692f50566cf99f12ab3ac3fda820dbd2e66a953de019` |
| `data/windows_x86_64_session1/raw/kv_cache_thrashing_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `kv` | W2 | 184 | 180 | 4 | `5ab229460ef19505cd721cf795d7569337212a81fdd3652aa3275a4fb0f8de79` |
| `data/windows_x86_64_session1/raw/mcp_live_transport_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `mcp` | W2 | 297 | 270 | 27 | `9888d6edfabe937e2b0e85845314479b361013ba0fed24220ce58bf206abffab` |
| `data/windows_x86_64_session1/raw/tool_rag_mitigation_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `449bc5204c6f1cd222002eeebd95a3ebbdc45915002a188eb4fa4a7a3b1848f9` |
| `data/windows_x86_64_session2/raw/raw_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `f42f751681083f82787947c10244fecdd24c21ba6e123abd3752870d30568297` |
| `data/windows_x86_64_session2/raw/warm_cache_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `d2df5802ed7c48e3064da8d5eabd27e9f494756bffdb4ad1429560c5286eb891` |
| `data/windows_x86_64_session2/raw/kv_cache_thrashing_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `kv` | W2 | 184 | 180 | 4 | `f4ac5017ceae16ff4c28b936b988d5f76f96f225e81de1d627970ccb5ce28786` |
| `data/windows_x86_64_session2/raw/mcp_live_transport_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `mcp` | W2 | 297 | 270 | 27 | `d9b1e3500af1b210405a7c87de1c6d442ccba36a41e355a99bba68ab16d12e36` |
| `data/windows_x86_64_session2/raw/tool_rag_mitigation_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `ad45f15cb9bea1c483692b6e4dcf39062c709b4f2f2fad1267316692ac616e62` |
| `data/windows_intel_graphics_session1/raw/raw_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session1` | `raw` | W2, W5 | 330 | 300 | 30 | `e6993e9edeb9964f2109972da4444e6bca4d9952260961eebf1a3286d2a71d80` |
| `data/windows_intel_graphics_session1/raw/warm_cache_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session1` | `warm` | W2, W5 | 330 | 300 | 30 | `081809a8c7b44808fb0cfe41d4bdf7a08d77e68f8e16dfcf1f678ecfe5b4f7ab` |
| `data/windows_intel_graphics_session1/raw/tool_rag_mitigation_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session1` | `rag` | W2 | 132 | 120 | 12 | `b4501867f7a7642c18f31130f0f35e926e9aeb3e19d8a028ce32acf28afff669` |
| `data/windows_intel_graphics_session2/raw/raw_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session2` | `raw` | W2, W5 | 330 | 300 | 30 | `920d68b0197e3039021a1ca327b41807c2cd7b60ed1b606371f6d30e65854a33` |
| `data/windows_intel_graphics_session2/raw/warm_cache_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session2` | `warm` | W2, W5 | 330 | 300 | 30 | `d922a01b5dd42bd5ce8b4b9248bf6a4cb636a45384c025d9bffcb010f021e22c` |
| `data/windows_intel_graphics_session2/raw/tool_rag_mitigation_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session2` | `rag` | W2 | 132 | 120 | 12 | `34736fbad16b3fb5d499c14805a4e4700d21337ed7a57090bad8b98811a04157` |
| **TOTAL (35 files)** | **4 Platforms** | **All Sessions** | **All** | **W1--W5 + Ablations** | **18,616** | **16,995** | **1,621** | **SHA-256 Computed** |

---

## 4. DYNAMIC GENERATION FROM RAW JSONL DATASETS

All numerical summaries reported across tables, figures, and reports are computed by `scripts/reproduce_quad_platform_analysis.py` from the raw `.jsonl` files listed in Section 3:

- **Detrended Serial Autocorrelation Across Both Regimes & Table 2 Adjustment (Etapa 2 / M4):** Linearly detrending trial order prior to estimating $r_1$ (both raw `autocorr_r1_raw` and detrended `autocorr_r1` exported in `anomaly_and_cache_diagnostics.csv`), lag-1 serial dependence ($|r_1| > 2/\sqrt{30} \approx 0.365$) occurred in **17/95** cells in **Regime A (Cold)** and **24/95** cells in **Regime B (Warm)** (**41/190** overall). In Table 2 (excluding W5 `python_native` per M1), inflating Mann-Whitney $U$ asymptotic variance via $n_{\text{eff}} = n(1-r_1)/(1+r_1)$ for positively autocorrelated cells ($r_1 > 0$; Bayley & Hammersley 1946; Yue & Wang 2004; Zimmerman & Zumbo 1993; Fagerland & Sandvik 2009) retains **93/146** Holm-Bonferroni significant contrasts (vs. **99/146** unadjusted; **6** contrasts marked `(NS*)` lose significance under $r_1$ correction).
- **Stationarity & Temporal Drift (M7):** OLS regression across all 190 experimental cells with Holm-Bonferroni FWER adjustment found **188/190 (98.9%)** non-significant ($p_{\text{adj}} \ge 0.05$) and **2/190** significant. Across valid (non-segregated) cells, the largest observed absolute slope was **0.599%/rep** (`Windows Intel iGPU`, `Regime B (Warm Cache)`, `neural_baseline`, `W5`, $p_{\text{adj}}=1$); including the segregated W5 `python_native` arm, the overall raw maximum was **1.376%/rep** in `Windows 11` `Regime B (Warm Cache)` `python_native` `W5` ($p_{\text{adj}}=1$).
- **Intra-Trial Hardware Throttling Deltas (Etapa 3 / M8):** On Linux x86_64, `cpu_pkg_throttle_events` records genuine intra-trial `end - start` deltas summed across logical threads (non-monotonic across consecutive trials, confirming non-sticky per-trial deltas), totaling **1,652/1,800** non-zero Session 1 primary trials (**9,925,812 events**, **9.93M**: **884/900** in Regime A, max **120,948**/trial; **768/900** in Regime B). Discrete GPUs on Linux and Windows 11 NVIDIA recorded **0** thermal-throttle events (`gpu_thermal_throttle_active_end`) and **0** SW power-cap events (`0x04`); the non-zero NVML bitmask on Windows NVIDIA (**902/1800** trials) corresponds exclusively to `0x01` (`nvmlClocksThrottleReasonGpuIdle`).
- **Inter-Session Contrast Equivalence (Three-State MBB TOST + Holm-Bonferroni & $b \in \{2,3,5\}$ Sensitivity, Table 7; Etapa 2):** Across **95 valid pairs** (**7 schema-failed W5 `python_native` pairs excluded per M1**) evaluated via Moving Block Bootstrap ($b=3$, $B=10,000$; Künsch 1989) against a fixed SESOI of $\pm 5.0\text{ ms}$ with order-statistic 90% CIs and Holm-Bonferroni FWER adjustment ($p_{\text{TOST, adj}}$; Schuirmann 1987; Lakens 2017): **72 (75.8%)** `Equivalent`, **23 (24.2%)** `Inconclusive`, and **0 (0.0%)** `Different` (identical Holm-adjusted decisions across $b \in \{2, 3, 5\}$, exported in `audit_export/tost_block_sensitivity.csv`).
- **Workload-Dependent Runtime Ranking & W3 Inversion (C3):** Compiled Go (`PicoClaw`) achieves lower $T_{\text{orch}}$ than Node.js V8 (`OpenClaw`) in W1, W2, W4, and W5 across all tested platforms. In compute-bound Vector RAG (W3), a ranking inversion occurs: scalar Go dot-product loops (`PicoClaw` Cold $T_{\text{orch}} = 36.83$ ms on macOS, $45.09$ ms on Linux, $49.68$ ms on Windows 11) are outperformed by vectorized SIMD/BLAS routines in `PythonNative` ($21.52$ ms on macOS, $35.20$ ms on Linux) and `Bun` JSC ($28.32$ ms on Linux, $39.99$ ms on Windows 11, and $18.09$ ms Warm Session 2 on macOS).
- **Tool-RAG Schema Pruning (Table 5 & Figure 5b; Option B Exploratory Qualification on x86_64):** $-87.1\%$ prompt token reduction (`7,091` to `917` tokens). Same-session controlled speedup on **macOS M4** (`tool_rag_mitigation_trials.jsonl`): **7.28x** vs. 54-Tool Full (**2.10x** vs. 15-Tool Minimal). Exploratory cross-session ratios on x86_64 referenced against each node's primary-campaign baseline (`raw_trials.jsonl` / `warm_cache_trials.jsonl`, non-causal): **5.16x** (Linux x86_64), **4.64x** (Windows 11 NVIDIA), and **9.96x** (Windows Intel iGPU) vs. 54-Tool Full (**1.79x**, **1.71x**, and **2.35x** vs. 15-Tool Minimal).
- **KV-Cache Thrashing $T_2/T_3$ (Table 4):** Measured eviction penalties (Minimal / Full): **6.85x / 19.46x** on macOS M4, **1.48x / 2.63x** on Linux x86_64, and **2.01x / 2.30x** on Windows 11 NVIDIA (not executed on Intel iGPU, scoped to W2/W5).
- **Absolute $T_{\text{orch}}$ Cache Invariance (Table 3):** Observed bound $|\Delta T_{\text{orch}}| < 2.0\text{ ms}$ (maximum observed delta **$1.95\text{ ms}$** for PicoClaw (Go) on Windows 11 NVIDIA).
- **Windows CPU Cycles (Table 1 & Figure 6c/d):** Windows 11 NVIDIA: **45.8M** cycles in PicoClaw vs. **528.1M** in OpenClaw Full (**11.54x**). Windows Intel iGPU: **87.8M** vs. **1446.1M** (**16.47x**).
- **Linux Thermal Throttling Stratification (M7 / E6):** Exported in `audit_export/linux_throttling_stratification.csv`. Stratifying Linux physical trials by hardware throttling events (`cpu_pkg_throttle_events`) demonstrates that thermal build-up and package frequency modulation physically underpin positive lag-1 autocorrelation ($r_1 > 0$), while absolute energy comparisons remain intra-node (RAPL+NVML vs. Apple SMC).
- **Primary Two-Sample Inference via Contiguous Block Permutation (M4 / Phase 3.5):** Two-sample rank tests in Table 2 adopt contiguous block permutation (`block_permutation_mwu`, $B=5000$) with adaptive block length $b \in \{3, 5, 8, 12\}$ as the primary inference method, treating analytical $r_1$-VIF variance inflation solely as sensitivity analysis (due to empirical AR(1) Type I error of ~8.2% to 12.7% under $n=30$).
- **Expanded TOST Block-Size Sensitivity & Proportional SESOI (M2 / M3 / Table 7):** Sensitivity evaluation across $b \in \{2, 3, 5, 8, 12, \text{adaptive}\}$ in `audit_export/tost_block_sensitivity.csv` demonstrates decision stability, with the 13 cells exhibiting $|r_1| \in [0.85, 0.91]$ maintaining invariant decisions across $b \in \{8, 12\}$. A parallel proportional SESOI analysis ($\Delta_{\text{prop}} = \max(2.0\text{ ms}, 0.10 \times |\text{median}(c_1)|)$) is reported alongside the fixed $\pm 5.0\text{ ms}$ bound.
- **Uniform W5 `python_native` Segregation Across All 4 Platforms (M1 / Phase 4.8):** Segregation was applied uniformly to all four platforms. Even on Linux where prompt tokens matched (`2,259/38`), Regime B presented a cold initialization anomaly ($T_{	ext{orch}} = 1,416.3	ext{ ms}$); uniform segregation prevents biased partial comparisons of a defective prototype arm.
- **Workload W5 — Token Audit, `python_native` Segregation (M1) & Schema/Judge Sub-Table (C5 / E3):** All 4 platforms are reported in Table 8 with full token/finish-reason audit in `audit_export/w5_token_and_schema_audit.csv`. Because `python_native` (LangChain Core) experienced schema-validation failure and truncated prompts (`1,287/26` tokens vs. `2,007--6,921/33--38` for comparable arms; TTFT `50.0 ms` vs. `4,939.5 ms` on macOS Regime A; `1,416.3 ms` Warm initialization anomaly on Linux), it is **excluded from Tables 2 and 7** and **segregated into Part B of Table 8** (`¶`). Per C5, the `Quality Score (1-5)` column was removed from comparative Table 8; prototype diagnostics from `W5_langchain_real_world/evaluator.py` (local `Meta-Llama-3.2-3B-Instruct Q4_K_M`, `temperature=0.0`, `max_tokens=150`, 5-point 3-issue rubric with keyword fallback, $N=30$ outputs/regime, subject to same-family bias per Zheng et al. 2023) are isolated in Table 8's separate **Schema & Prototype Judge Audit** sub-table (`1.0/5.0` `"Empty output"` on macOS from schema validation failure; `3.0/5.0` partial 1-issue match on Intel iGPU). **No comparative output-quality evaluation was conducted across runtimes.**

---

## 5. `N/A` SYMBOL TAXONOMY

No `N/A` cell was replaced by `0`. All symbols are defined consistently across Tables 1 and 8 and Figure 2(b):

| Symbol | Scope | Hardware / Methodological Rationale |
| :--- | :--- | :--- |
| `N/A*` | Windows (NVIDIA & Intel iGPU) — Hardware Instructions | Windows NT user-mode restricts hardware PMU retired instruction counters (`CR4.PCE`) without a privileged driver. Empirical Win32 CPU cycles are reported via `QueryProcessCycleTime` (11.54x NVIDIA; 16.47x Intel iGPU). |
| `N/A‡` | All Platforms — `neural_baseline` (RSS, Instr/Cycles) | Direct HTTP pass-through to `llama-server` without a client orchestrator process ($T_{\text{orch}} \equiv 0$). |
| `N/A§` | Tables 1, 8 & Figure 2(b) — Windows `python_native` (RSS & Cycles) | Windows `py.exe` launcher wrapper (PEP 397) exposes the ephemeral parent stub PID (~4.9 MB) rather than the child `python.exe` worker heap/cycles; stub metrics are excluded uniformly. |
| `N/A||` | macOS ARM64 — Bun JSC Engine | Secondary JS-engine ablation introduced after the Apple M4 primary Cold/Warm campaign froze; evaluated in Cold & Warm on x86_64 nodes, with supplementary macOS Warm Session 2 trials archived in `inter_session_trials.jsonl`. |
| `N/A**` | Windows Intel iGPU — Package Energy & EDP | Intel HD Graphics 4600 executes on shared DDR3 system memory (UMA) without discrete NVML sensors or ring-0 RAPL MSR access in unprivileged user-mode ($P_{\text{idle}} = 28.50\text{ W}$). |
| `¶` | Table 8 Part B — Segregated W5 `python_native` | Schema-validation failure / truncated prompt (`1,287/26` tokens vs. `2,007--6,921/33--38`; TTFT `50 ms` on macOS); excluded from Tables 2 and 7 per M1. |

---

## 6. BIBLIOGRAPHIC INVENTORY (`references.bib`)

All **28 primary bibliographic entries** in `references.bib` carry checked DOIs, ISBNs, or arXiv identifiers:
- **Corrected Entry:** `maricq2018taming` (author names checked against OSDI '18 proceedings: *Aleksander Maricq* and *Ryan Stutsman*).
- **Replaced Entry:** Prior `goldsman1997methods` entry carried an unrelated TOMACS DOI and was replaced by the Moving Block Bootstrap reference (`kuensch1989jackknife`, DOI: `10.1214/aos/1176347265`).
- **Rank-Test, Serial-Dependence & Offload References (C6 / Etapa 4):** `bayley1946effective` (DOI: `10.2307/2983560`), `zimmerman1993rank` (DOI: `10.1037/h0078850`), `yue2004mann` (DOI: `10.1023/B:WARM.0000043140.61082.60`), `fagerland2009wilcoxon` (DOI: `10.1002/sim.3561`), and `sheng2023flexgen` (ICML 2023 / PMLR 202, DOI: `10.48550/arXiv.2303.06865`).
- **Core Systems, Statistical & Evaluation References:** `kalibera2013rigorous`, `hoefler2015scientific`, `schuirmann1987comparison`, `lakens2017equivalence`, `mann1947test`, `kruskal1952use`, `holm1979simple`, `cliff1993dominance`, `vargha2000critique`, `weaver2013nondeterminism`, `kwon2023vllm`, `yao2023react`, `zheng2023judging`, `reddi2020mlperf`, `you2023zeus`, `barroso2007case`, `fahad2019comparative`, `williams2009roofline`, and `smith2016software`.
- **Technical Specifications Separated:** Vendor documentation and PEPs (Microsoft Learn `QueryProcessCycleTime` / Win32 PSAPI, Intel 64 and IA-32 SDM Vol. 3B Ch. 20, Python PEP 397) are referenced explicitly as technical documentation in table notes.

---

## 7. REGENERATED FIGURES (300 DPI, ENGLISH) AND SHA-256 DIGESTS

| File | Description | SHA-256 |
| :--- | :--- | :--- |
| `figures/fig1_architecture_topology.png` | Quad-platform hardware topology diagram (4 physical nodes, English labels, dynamic dataset count, wrapped sensor boundary notes). | `e05883699a68bd5d4a4bf3e656a3fa9f18aaef3e4ba792473c15da95f13084da` |
| `figures/fig2_exp1_cold_start_rss.png` | Panel (a) W1 cold latency with numerical labels and Intel iGPU/Bun scope note; Panel (b) W2 Peak RSS across 4 platforms with unified N/A§ (Win Stub) hatched block. | `90c0ca6275b5e9139398f53adb68130300580b16be6ce245187b8179fcb6e7e5` |
| `figures/fig3_exp2_latency_overhead.png` | Panel (a) W2 client T_orch across 4 platforms with numerical labels; Panel (b) W1--W4 Phi_orch with non-overlapping W3 Ranking Inversion callout. | `c7c27045097b1ac351bb10ec7e19501bf02ba152afdc7b7bc04ab16f8f2f0647` |
| `figures/fig4_exp3_energy_edp.png` | Panel (a) W2 net dynamic energy (J & Watts); Panel (b) W2 EDP with uncapped Y-axis (>=6,600 J·s) and numerical bar labels; clean top notice and English Intel iGPU N/A** note. | `5acbd2e2fd656aee1037c9da0412056fede9204668e6acea65fad0fe145578d8` |
| `figures/fig5_exp4_tools_and_bloat.png` | Panel (a) Linux W1--W4 context bloat latency with bar labels; Panel (b) Quad-platform Tool-RAG Cold speedups (7.28x macOS, 5.16x Linux, 4.64x Win NVIDIA, 9.96x Win Intel). | `95a3103a8515747d6c5b71803424d0a8a2b8af47944898ac9514f0079b1654e2` |
| `figures/fig6_pmc_hardware_counters.png` | 2x2 quad-platform microarchitectural figure: (a) macOS ARM64 instructions, (b) Linux x86_64 instructions, (c) Windows NVIDIA & Intel iGPU CPU cycles, (d) 4-platform relative bloat ratios. | `7c08c8baaf613a9311e08b270d5bfa4b3d26f5b6f65d1a34406ded59e050564e` |

---

## 8. METHODOLOGICAL LIMITATIONS, EXTERNAL VALIDITY & LICENSING

1. **Offload & Memory Topology Asymmetry (UMA vs. Hybrid PCIe vs. Shared DDR3):** Apple M4 executes full on-die GPU offload (`-ngl 99`, 120 GB/s). Dell G15 nodes (Linux and Windows 11) execute under hybrid offload (`-ngl 16`) bounded by 4 GB GDDR6 VRAM with continuous PCIe streaming (~5.2 GB/s). Intel HD Graphics 4600 executes over shared DDR3-1600 RAM. Absolute Regime B latency and package energy comparisons are restricted to within-node contrasts.
2. **Windows User-Mode Telemetry Boundaries:** Absence of ring-0 privileges blocks direct PMU `INST_RETIRED.ANY` (`CR4.PCE`) and Intel iGPU RAPL MSR access; empirical Win32 `QueryProcessCycleTime` cycles are reported without synthetic IPC extrapolation.
3. **Unequal Workload Scope on Windows Intel iGPU — W2, W5 & Tool-RAG Only (E8):** On shared DDR3-1600 memory, Regime A trial durations spanned **53.5 s/trial** (`picoclaw`/`openclaw_minimal` W2) to **226.7 s/trial** (54-tool `openclaw_full` W2), with comparable W5 arms at **50.1--56.9 s/trial**. Expanding to W1--W4 (including 10-turn W4 dialogues), KV-Thrashing, and MCP across two 30-rep sessions would require multi-day continuous execution and expose results to thermal/OS drift.
4. **Unequal Runtime Scope for Bun JSC — x86_64 Only in Consolidated Matrix (E8):** Bun (`bun_minimal`, JavaScriptCore) was added as a secondary JS-engine ablation after the Apple M4 primary Cold/Warm campaign froze; it is evaluated across Cold and Warm on all three x86_64 nodes (`N/A||` in macOS consolidated tables; supplementary macOS Warm Session 2 Bun trials are archived in `inter_session_trials.jsonl`).
5. **Segregation of W5 `python_native` (M1) & De-Scoped Prototype Judge (E3 / C5):** Schema-validation failure and truncated prompts (`1,287/26` tokens) make `python_native` W5 non-comparable (excluded from Tables 2 and 7; segregated in Part B of Table 8). Prototype judge outputs (`Llama-3.2-3B-Instruct`, $N=30$/regime, same-family bias risk) were moved out of comparative columns into Table 8's separate Schema & Prototype Judge Audit sub-table; no cross-runtime quality claims are made.
6. **Linux Mobile CPU Thermal/PL Throttling (M8):** Positive intra-trial deltas in `cpu_pkg_throttle_events` elevated lag-1 autocorrelation ($r_1$) on Linux x86_64 under `-ngl 16` offload, addressed via $n_{\text{eff}}$-adjusted Mann-Whitney $U$ variance (Table 2) and Moving Block Bootstrap ($b=3$, Table 7).
7. **External Validity Boundaries & Licensing (C9):** Measurements are scoped to a single 3B quantized model (`Meta-Llama-3.2-3B-Instruct Q4_K_M`, Meta Llama 3.2 Community License), a single inference server (`llama-server` / `llama.cpp`, MIT License), synthetic deterministic workloads (W1--W5), and heterogeneous platform sensors. All evaluated `PicoClaw` and `OpenClaw` workers are clean-room academic implementations isolated for systems benchmarking (code: MIT License; data: CC BY 4.0).

---

## 9. ARTIFACT INVENTORY SUMMARY

All derived artifacts — manuscript source (`paper/manuscript.tex`), `references.bib`, analysis scripts, Tables 1--8 (`.md`/`.tex`), Figures 1--6 (300 DPI), saved `pytest -q` transcript, 35-`.jsonl` access guide (`audit_export/REVIEW_PACKAGE_README.md`), lightweight text chunks (`audit_txt_chunks/`), `data/manifest_sha256.json`, and `audit_export_quad_platform.zip` — were regenerated directly from the raw datasets on disk.
