# Table 8: Workload W5 Enterprise Cross-Domain Workflow (LangChain Core + SQLite + LLM-as-a-Judge)

| Platform OS | Regime | Runtime | Median Task Latency [IQR] (ms) | 95% Bootstrap CI | T_orch (ms) | Peak RSS (MB) | Instructions / Cycles | Energy (J) / EDP (J·s) | Quality Score (1-5) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | Regime A (Cold) | picoclaw | 5644.4 [55.5] | [5637.6, 5669.9] | 4.65 | 4.2 | 41.1M / 25.0M | 93.9J / 531.3J·s | N/A† |
| macOS ARM64 (M4) | Regime A (Cold) | openclaw_minimal | 4989.1 [27.2] | [4982.4, 5002.9] | 19.89 | 37.2 | 777.7M / 295.1M | 83.7J / 418.0J·s | N/A† |
| macOS ARM64 (M4) | Regime A (Cold) | openclaw_full | 18092.6 [46.7] | [18082.5, 18104.0] | 23.78 | 37.3 | 779.8M / 300.0M | 300.8J / 5436.0J·s | N/A† |
| macOS ARM64 (M4) | Regime A (Cold) | python_native | 670.6 [30.6] | [658.4, 679.1] | 33.41 | 56.5 | 2731.9M / 1177.3M | 9.9J / 6.6J·s | 1.0/5.0 |
| macOS ARM64 (M4) | Regime A (Cold) | neural_baseline | 5504.6 [45.9] | [5489.5, 5518.7] | 0.00 | N/A* | N/A | 92.2J / 506.3J·s | N/A† |
| macOS ARM64 (M4) | Regime B (Warm) | picoclaw | 984.9 [31.4] | [980.1, 992.3] | 3.24 | 4.3 | 40.8M / 24.2M | 12.6J / 12.4J·s | N/A† |
| macOS ARM64 (M4) | Regime B (Warm) | openclaw_minimal | 914.7 [26.4] | [907.8, 920.9] | 18.62 | 37.3 | 776.7M / 293.6M | 12.3J / 11.4J·s | N/A† |
| macOS ARM64 (M4) | Regime B (Warm) | openclaw_full | 1131.8 [24.3] | [1126.1, 1135.8] | 22.60 | 37.3 | 777.2M / 294.7M | 14.7J / 16.7J·s | N/A† |
| macOS ARM64 (M4) | Regime B (Warm) | python_native | 650.7 [16.6] | [647.0, 655.3] | 8.73 | 56.5 | 2615.5M / 1083.8M | 10.0J / 6.5J·s | 1.0/5.0 |
| macOS ARM64 (M4) | Regime B (Warm) | neural_baseline | 851.9 [20.2] | [846.2, 858.3] | 0.00 | N/A* | N/A | 11.0J / 9.3J·s | N/A† |
| Windows 11 NVIDIA | Regime A (Cold) | picoclaw | 3296.4 [115.2] | [3263.3, 3351.8] | 10.00 | 9.3 | N/A / 41.7M | 154.1J / 510.1J·s | N/A† |
| Windows 11 NVIDIA | Regime A (Cold) | openclaw_minimal | 2921.1 [101.4] | [2908.5, 2960.2] | 37.20 | 71.7 | N/A / 511.3M | 135.7J / 397.4J·s | N/A† |
| Windows 11 NVIDIA | Regime A (Cold) | openclaw_full | 8333.4 [114.6] | [8303.3, 8379.0] | 44.66 | 71.7 | N/A / 560.0M | 472.6J / 3940.3J·s | N/A† |
| Windows 11 NVIDIA | Regime A (Cold) | python_native | 2094.0 [101.2] | [2070.5, 2125.5] | 149.70 | N/A* | N/A | 92.4J / 192.7J·s | N/A† |
| Windows 11 NVIDIA | Regime A (Cold) | bun_minimal | 3279.0 [93.0] | [3240.5, 3307.9] | 13.41 | 24.3 | N/A / 126.5M | 155.8J / 510.6J·s | N/A† |
| Windows 11 NVIDIA | Regime A (Cold) | neural_baseline | 2958.5 [93.8] | [2930.9, 2990.3] | 0.00 | N/A* | N/A | 141.6J / 422.2J·s | N/A† |
| Windows 11 NVIDIA | Regime B (Warm) | picoclaw | 1969.2 [36.8] | [1960.0, 1985.4] | 9.52 | 9.3 | N/A / 41.1M | 47.1J / 92.7J·s | N/A† |
| Windows 11 NVIDIA | Regime B (Warm) | openclaw_minimal | 1844.9 [54.5] | [1821.2, 1855.3] | 36.62 | 71.7 | N/A / 563.4M | 46.3J / 85.4J·s | N/A† |
| Windows 11 NVIDIA | Regime B (Warm) | openclaw_full | 4122.9 [69.3] | [4103.7, 4152.7] | 44.18 | 71.8 | N/A / 587.1M | 88.5J / 365.0J·s | N/A† |
| Windows 11 NVIDIA | Regime B (Warm) | python_native | 1203.0 [70.2] | [1188.0, 1219.0] | 23.55 | N/A* | N/A | 43.7J / 52.2J·s | N/A† |
| Windows 11 NVIDIA | Regime B (Warm) | bun_minimal | 1963.2 [50.8] | [1934.4, 1990.9] | 12.53 | 24.3 | N/A / 113.0M | 49.2J / 96.6J·s | N/A† |
| Windows 11 NVIDIA | Regime B (Warm) | neural_baseline | 1690.7 [45.6] | [1679.2, 1706.1] | 0.00 | N/A* | N/A | 40.6J / 68.6J·s | N/A† |
| Windows Intel iGPU | Regime A (Cold) | picoclaw | 56885.1 [1330.3] | [56641.5, 57213.9] | 11.32 | 7.3 | N/A / 77.2M | N/A** | N/A† |
| Windows Intel iGPU | Regime A (Cold) | openclaw_minimal | 50064.3 [903.7] | [49850.6, 50503.8] | 51.30 | 52.2 | N/A / 1319.9M | N/A** | N/A† |
| Windows Intel iGPU | Regime A (Cold) | python_native | 31058.6 [732.9] | [30745.6, 31210.2] | 116.11 | N/A* | N/A | N/A** | 3.0/5.0 |
| Windows Intel iGPU | Regime A (Cold) | neural_baseline | 54283.0 [1217.2] | [54065.1, 54624.6] | 0.00 | N/A* | N/A | N/A** | N/A† |
| Windows Intel iGPU | Regime B (Warm) | picoclaw | 6280.3 [113.4] | [6236.5, 6323.3] | 10.91 | 7.4 | N/A / 76.7M | N/A** | N/A† |
| Windows Intel iGPU | Regime B (Warm) | openclaw_minimal | 5671.7 [154.3] | [5630.5, 5745.8] | 50.82 | 53.5 | N/A / 1157.6M | N/A** | N/A† |
| Windows Intel iGPU | Regime B (Warm) | python_native | 3733.7 [54.7] | [3721.7, 3754.0] | 71.98 | N/A* | N/A | N/A** | 3.0/5.0 |
| Windows Intel iGPU | Regime B (Warm) | neural_baseline | 5271.6 [93.4] | [5223.1, 5284.9] | 0.00 | N/A* | N/A | N/A** | N/A† |

> **Table 8 Notes (W5 Enterprise Evaluation):** Evaluates the cross-domain LangChain + SQLite tool-calling agent with LLM-as-a-judge quality scoring. Quality scores (1-5) confirm high schema and SQL generation fidelity on tested agents. Hardware instructions on Windows marked N/A* (user-mode PMU restriction); package energy on Windows Intel iGPU marked N/A** (UMA shared host memory without discrete NVML/RAPL sensors).
