# Table 3: Regime B (Warm KV-Cache) Orchestration Bottleneck Persistence

| Architecture | Platform | Cold $T_{\text{task}}$ (ms) | Warm $T_{\text{task}}$ (ms) | Cold $\Phi_{\text{orch}}$ (%) | Warm $\Phi_{\text{orch}}$ (%) | Warm $T_{\text{orch}}$ (ms) | Cache Invariance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| PicoClaw (Go) | macOS ARM64 (M4) | 5265.14 | 744.87 | 0.14% | 0.80% | 5.98 | Confirmed |
| PicoClaw (Go) | Linux x86_64 | 2725.00 | 1272.74 | 0.24% | 0.57% | 7.13 | Confirmed |
| PicoClaw (Go) | Windows 11 x86_64 | 2746.68 | 1464.58 | 0.40% | 0.84% | 12.23 | Confirmed |
| OpenClaw Minimal | macOS ARM64 (M4) | 5269.28 | 768.61 | 0.41% | 2.71% | 20.83 | Confirmed |
| OpenClaw Minimal | Linux x86_64 | 2760.46 | 1297.29 | 1.14% | 2.44% | 31.91 | Confirmed |
| OpenClaw Minimal | Windows 11 x86_64 | 2767.66 | 1573.26 | 1.40% | 2.46% | 38.65 | Confirmed |
| OpenClaw Full | macOS ARM64 (M4) | 18335.53 | 914.49 | 0.14% | 2.74% | 25.06 | Confirmed |
| OpenClaw Full | Linux x86_64 | 7891.12 | 2793.98 | 0.46% | 1.30% | 36.40 | Confirmed |
| OpenClaw Full | Windows 11 x86_64 | 7663.76 | 3300.37 | 0.59% | 1.38% | 45.79 | Confirmed |
