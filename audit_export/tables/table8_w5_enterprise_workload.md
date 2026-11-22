# Table 8: Workload W5 Enterprise Cross-Domain Workflow (LangChain Core + SQLite + LLM-as-a-Judge)

### Part A: Comparable W5 Orchestrators & Direct Neural Baseline

| Platform OS | Regime | Runtime | Prompt / Comp. Tokens | Median Task Latency [IQR] (ms) | 95% Bootstrap CI | T_orch (ms) | Peak RSS (MB) | Instructions / Cycles | Energy (J) / EDP (J·s) | Quality Score (1-5) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | Regime A (Cold) | picoclaw | 2259 / 38 | 5644.4 [55.5] | [5637.6, 5669.9] | 4.65 | 4.2 | 41.1M / 25.0M | 93.9J / 531.3J·s | N/A† |
| macOS ARM64 (M4) | Regime A (Cold) | openclaw_minimal | 2007 / 35 | 4989.1 [27.2] | [4982.4, 5002.9] | 19.89 | 37.2 | 777.7M / 295.1M | 83.7J / 418.0J·s | N/A† |
| macOS ARM64 (M4) | Regime A (Cold) | openclaw_full | 6921 / 35 | 18092.6 [46.7] | [18082.5, 18104.0] | 23.78 | 37.3 | 779.8M / 300.0M | 300.8J / 5436.0J·s | N/A† |
| macOS ARM64 (M4) | Regime A (Cold) | neural_baseline | 2252 / 33 | 5504.6 [45.9] | [5489.5, 5518.7] | 0.00 | N/A‡ | N/A‡ | 92.2J / 506.3J·s | N/A† |
| macOS ARM64 (M4) | Regime B (Warm) | picoclaw | 2259 / 38 | 984.9 [31.4] | [980.1, 992.3] | 3.24 | 4.3 | 40.8M / 24.2M | 12.6J / 12.4J·s | N/A† |
| macOS ARM64 (M4) | Regime B (Warm) | openclaw_minimal | 2007 / 35 | 914.7 [26.4] | [907.8, 920.9] | 18.62 | 37.3 | 776.7M / 293.6M | 12.3J / 11.4J·s | N/A† |
| macOS ARM64 (M4) | Regime B (Warm) | openclaw_full | 6921 / 35 | 1131.8 [24.3] | [1126.1, 1135.8] | 22.60 | 37.3 | 777.2M / 294.7M | 14.7J / 16.7J·s | N/A† |
| macOS ARM64 (M4) | Regime B (Warm) | neural_baseline | 2252 / 33 | 851.9 [20.2] | [846.2, 858.3] | 0.00 | N/A‡ | N/A‡ | 11.0J / 9.3J·s | N/A† |
| Linux x86_64 | Regime A (Cold) | picoclaw | 2259 / 38 | 3100.7 [28.0] | [3084.6, 3119.2] | 4.34 | 8.8 | 11.0M / 18.7M | 245.6J / 762.3J·s | N/A† |
| Linux x86_64 | Regime A (Cold) | openclaw_minimal | 2007 / 35 | 2711.1 [28.4] | [2702.3, 2721.5] | 28.92 | 85.0 | 745.5M / 480.9M | 213.9J / 581.3J·s | N/A† |
| Linux x86_64 | Regime A (Cold) | openclaw_full | 6921 / 35 | 8258.5 [39.7] | [8142.4, 8294.0] | 34.07 | 85.6 | 802.1M / 523.8M | 594.4J / 4909.0J·s | N/A† |
| Linux x86_64 | Regime A (Cold) | bun_minimal | 2259 / 38 | 3092.7 [38.3] | [3078.3, 3104.8] | 4.95 | 23.0 | 51.2M / 64.7M | 246.2J / 761.6J·s | N/A† |
| Linux x86_64 | Regime A (Cold) | neural_baseline | 2252 / 33 | 2896.6 [33.1] | [2861.7, 2912.2] | 0.00 | N/A‡ | N/A‡ | 220.5J / 634.3J·s | N/A† |
| Linux x86_64 | Regime B (Warm) | picoclaw | 2259 / 38 | 1580.9 [32.6] | [1564.2, 1585.0] | 4.92 | 8.8 | 11.2M / 19.2M | 111.2J / 175.8J·s | N/A† |
| Linux x86_64 | Regime B (Warm) | openclaw_minimal | 2007 / 35 | 1419.6 [31.0] | [1408.4, 1425.6] | 27.78 | 85.1 | 744.6M / 502.8M | 100.8J / 143.5J·s | N/A† |
| Linux x86_64 | Regime B (Warm) | openclaw_full | 6921 / 35 | 3117.6 [29.7] | [3111.0, 3127.8] | 33.28 | 85.6 | 747.1M / 510.4M | 177.9J / 554.9J·s | N/A† |
| Linux x86_64 | Regime B (Warm) | bun_minimal | 2259 / 38 | 1571.4 [32.1] | [1565.2, 1576.7] | 5.39 | 22.8 | 48.1M / 59.4M | 109.1J / 171.0J·s | N/A† |
| Linux x86_64 | Regime B (Warm) | neural_baseline | 2252 / 33 | 1387.0 [23.9] | [1377.3, 1394.2] | 0.00 | N/A‡ | N/A‡ | 95.7J / 133.9J·s | N/A† |
| Windows 11 NVIDIA | Regime A (Cold) | picoclaw | 2254 / 37 | 3296.4 [115.2] | [3263.3, 3351.8] | 10.00 | 9.3 | N/A* / 41.7M | 154.1J / 510.1J·s | N/A† |
| Windows 11 NVIDIA | Regime A (Cold) | openclaw_minimal | 2007 / 35 | 2921.1 [101.4] | [2908.5, 2960.2] | 37.20 | 71.7 | N/A* / 511.3M | 135.7J / 397.4J·s | N/A† |
| Windows 11 NVIDIA | Regime A (Cold) | openclaw_full | 6921 / 35 | 8333.4 [114.6] | [8303.3, 8379.0] | 44.66 | 71.7 | N/A* / 560.0M | 472.6J / 3940.3J·s | N/A† |
| Windows 11 NVIDIA | Regime A (Cold) | bun_minimal | 2254 / 37 | 3279.0 [93.0] | [3240.5, 3307.9] | 13.41 | 24.3 | N/A* / 126.5M | 155.8J / 510.6J·s | N/A† |
| Windows 11 NVIDIA | Regime A (Cold) | neural_baseline | 2252 / 33 | 2958.5 [93.8] | [2930.9, 2990.3] | 0.00 | N/A‡ | N/A‡ | 141.6J / 422.2J·s | N/A† |
| Windows 11 NVIDIA | Regime B (Warm) | picoclaw | 2254 / 37 | 1969.2 [36.8] | [1960.0, 1985.4] | 9.52 | 9.3 | N/A* / 41.1M | 47.1J / 92.7J·s | N/A† |
| Windows 11 NVIDIA | Regime B (Warm) | openclaw_minimal | 2007 / 35 | 1844.9 [54.5] | [1821.2, 1855.3] | 36.62 | 71.7 | N/A* / 563.4M | 46.3J / 85.4J·s | N/A† |
| Windows 11 NVIDIA | Regime B (Warm) | openclaw_full | 6921 / 35 | 4122.9 [69.3] | [4103.7, 4152.7] | 44.18 | 71.8 | N/A* / 587.1M | 88.5J / 365.0J·s | N/A† |
| Windows 11 NVIDIA | Regime B (Warm) | bun_minimal | 2254 / 37 | 1963.2 [50.8] | [1934.4, 1990.9] | 12.53 | 24.3 | N/A* / 113.0M | 49.2J / 96.6J·s | N/A† |
| Windows 11 NVIDIA | Regime B (Warm) | neural_baseline | 2252 / 33 | 1690.7 [45.6] | [1679.2, 1706.1] | 0.00 | N/A‡ | N/A‡ | 40.6J / 68.6J·s | N/A† |
| Windows Intel iGPU | Regime A (Cold) | picoclaw | 2254 / 37 | 56885.1 [1330.3] | [56641.5, 57213.9] | 11.32 | 7.3 | N/A* / 77.2M | N/A** | N/A† |
| Windows Intel iGPU | Regime A (Cold) | openclaw_minimal | 2007 / 35 | 50064.3 [903.7] | [49850.6, 50503.8] | 51.30 | 52.2 | N/A* / 1319.9M | N/A** | N/A† |
| Windows Intel iGPU | Regime A (Cold) | neural_baseline | 2252 / 33 | 54283.0 [1217.2] | [54065.1, 54624.6] | 0.00 | N/A‡ | N/A‡ | N/A** | N/A† |
| Windows Intel iGPU | Regime B (Warm) | picoclaw | 2254 / 37 | 6280.3 [113.4] | [6236.5, 6323.3] | 10.91 | 7.4 | N/A* / 76.7M | N/A** | N/A† |
| Windows Intel iGPU | Regime B (Warm) | openclaw_minimal | 2007 / 35 | 5671.7 [154.3] | [5630.5, 5745.8] | 50.82 | 53.5 | N/A* / 1157.6M | N/A** | N/A† |
| Windows Intel iGPU | Regime B (Warm) | neural_baseline | 2252 / 33 | 5271.6 [93.4] | [5223.1, 5284.9] | 0.00 | N/A‡ | N/A‡ | N/A** | N/A† |

### Part B: Segregated / Non-Comparable Arm (`python_native` — Excluded from W5 Performance Contrasts: Schema-Failure / Confounded Prompt)¶

| Platform OS | Regime | Runtime (Segregated) | Prompt / Comp. Tokens | Median Task Latency [IQR] (ms) | 95% Bootstrap CI | T_orch (ms) | Peak RSS (MB) | Instructions / Cycles | Energy (J) / EDP (J·s) | Quality Score (1-5) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | Regime A (Cold) | `python_native`¶ [Excluded: Schema-Failure / Confounded] | 1287 / 26 | 670.6 [30.6] | [658.4, 679.1] | 33.41 | 56.5 | 2731.9M / 1177.3M | 9.9J / 6.6J·s | 1.0/5.0 |
| macOS ARM64 (M4) | Regime B (Warm) | `python_native`¶ [Excluded: Schema-Failure / Confounded] | 1287 / 26 | 650.7 [16.6] | [647.0, 655.3] | 8.73 | 56.5 | 2615.5M / 1083.8M | 10.0J / 6.5J·s | 1.0/5.0 |
| Linux x86_64 | Regime A (Cold) | `python_native`¶ [Excluded: Schema-Failure / Confounded] | 2259 / 38 | 3114.1 [30.1] | [3097.6, 3809.2] | 17.12 | 40.2 | 2674.4M / 4799.1M | 252.6J / 784.4J·s | N/A† |
| Linux x86_64 | Regime B (Warm) | `python_native`¶ [Excluded: Schema-Failure / Confounded] | 2259 / 38 | 2992.4 [56.8] | [2980.0, 3027.3] | 1416.32 | 87.4 | 4669.0M / 6471.4M | 196.5J / 588.2J·s | N/A† |
| Windows 11 NVIDIA | Regime A (Cold) | `python_native`¶ [Excluded: Schema-Failure / Confounded] | 1287 / 26 | 2094.0 [101.2] | [2070.5, 2125.5] | 149.70 | N/A§ | N/A* / N/A§ | 92.4J / 192.7J·s | N/A† |
| Windows 11 NVIDIA | Regime B (Warm) | `python_native`¶ [Excluded: Schema-Failure / Confounded] | 1287 / 26 | 1203.0 [70.2] | [1188.0, 1219.0] | 23.55 | N/A§ | N/A* / N/A§ | 43.7J / 52.2J·s | N/A† |
| Windows Intel iGPU | Regime A (Cold) | `python_native`¶ [Excluded: Schema-Failure / Confounded] | 1287 / 26 | 31058.6 [732.9] | [30745.6, 31210.2] | 116.11 | N/A§ | N/A* / N/A§ | N/A** | 3.0/5.0 |
| Windows Intel iGPU | Regime B (Warm) | `python_native`¶ [Excluded: Schema-Failure / Confounded] | 1287 / 26 | 3733.7 [54.7] | [3721.7, 3754.0] | 71.98 | N/A§ | N/A* / N/A§ | N/A** | 3.0/5.0 |

> **Table 8 Notes (M1 W5 Token Audit, `python_native` Segregation & Complete N/A Taxonomy):** Evaluates the cross-domain LangChain + SQLite tool-calling workflow across all 4 experimental platforms (complete token/finish-reason audit exported in `audit_export/w5_token_and_schema_audit.csv` and `audit_export/anomaly_and_cache_diagnostics.csv`).
> - `¶` (**Segregated / Non-Comparable Arm — M1**): `python_native` (LangChain Core) in W5 is explicitly segregated into Part B and **excluded from all W5 performance, energy, and TOST contrasts** (Tables 2 and 7). On macOS M4, Windows 11 NVIDIA, and Windows Intel iGPU, `python_native` executed a confounded/truncated prompt (`1,287` prompt / `26` completion tokens vs. `2,007–6,921` prompt / `33–38` completion tokens for comparable arms; TTFT `50.0 ms` vs. `4,939.5 ms` in Regime A on macOS; `finish_reason=stop` on Intel iGPU; `quality_score = 1.0/5.0` on macOS and `3.0/5.0` on Intel iGPU); on Linux x86_64 Regime B it exhibited a `1,416.3 ms` LangChain initialization anomaly. Any apparent latency or energy advantage of `python_native` in W5 is strictly an artifact of schema failure and prompt truncation, not runtime efficiency.
> - `N/A*` (**Windows Hardware Instructions**): Hardware PMU retired instruction counters are restricted in Windows unprivileged user-mode (`CR4.PCE`); CPU cycles are reported empirically via Win32 `QueryProcessCycleTime`.
> - `N/A†` (**Quality Score**): LLM-as-a-Judge semantic quality scoring was uninstrumented on non-LangChain client runs and on Linux/Windows NVIDIA W5 campaigns. Where instrumented on `python_native` LangChain Core, empirical medians were `1.0/5.0` on macOS M4 (strict schema validation mismatch) and `3.0/5.0` on Windows Intel iGPU (partial query completion).
> - `N/A‡` (**Direct Neural Baseline**): `neural_baseline` dispatches HTTP requests directly to `llama-server` without a client agent process ($T_{\text{orch}} \equiv 0$); client Peak RSS, instructions, and cycles do not exist.
> - `N/A§` (**Windows `py.exe` Launcher Stub**): On Windows, `python_native` launches via `py.exe` (PEP 397), whose parent wrapper PID (~4.9 MB) does not capture the child `python.exe` worker heap or CPU cycles; stub measurements are excluded.
> - `N/A**` (**Windows Intel iGPU Energy / EDP**): Intel HD Graphics 4600 operates on shared DDR3 system memory (UMA) without discrete NVML sensors or ring-0 RAPL MSR access in unprivileged user-mode.
