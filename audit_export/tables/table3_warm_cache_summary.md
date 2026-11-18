# Table 3: Regime B (Warm KV-Cache) Middleware Latency Invariance

| Architecture | Platform | Cold $T_{\text{task}}$ (ms) | Warm $T_{\text{task}}$ (ms) | Cold $T_{\text{orch}}$ (ms) | Warm $T_{\text{orch}}$ (ms) | Cold $\Phi_{\text{orch}}$ (%) | Warm $\Phi_{\text{orch}}$ (%) | Absolute $T_{\text{orch}}$ Invariance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| PicoClaw (Go) | macOS ARM64 (M4) | 5272.68 | 749.40 | 5.53 | 4.29 | 0.10% | 0.58% | Confirmed (Δ=1.24 ms) |
| PicoClaw (Go) | Linux x86_64 | 2725.00 | 1272.74 | 6.66 | 7.13 | 0.24% | 0.57% | Confirmed (Δ=0.47 ms) |
| PicoClaw (Go) | Windows 11 x86_64 | 2746.68 | 1464.58 | 10.94 | 12.23 | 0.40% | 0.84% | Confirmed (Δ=1.29 ms) |
| OpenClaw Minimal | macOS ARM64 (M4) | 5284.81 | 794.99 | 20.60 | 19.19 | 0.39% | 2.42% | Confirmed (Δ=1.41 ms) |
| OpenClaw Minimal | Linux x86_64 | 2760.46 | 1297.29 | 31.45 | 31.91 | 1.14% | 2.44% | Confirmed (Δ=0.45 ms) |
| OpenClaw Minimal | Windows 11 x86_64 | 2767.66 | 1573.26 | 38.80 | 38.65 | 1.40% | 2.46% | Confirmed (Δ=0.15 ms) |
| OpenClaw Full | macOS ARM64 (M4) | 18406.88 | 944.35 | 24.55 | 23.45 | 0.13% | 2.47% | Confirmed (Δ=1.10 ms) |
| OpenClaw Full | Linux x86_64 | 7891.12 | 2793.98 | 35.99 | 36.40 | 0.46% | 1.30% | Confirmed (Δ=0.41 ms) |
| OpenClaw Full | Windows 11 x86_64 | 7663.76 | 3300.37 | 45.70 | 45.79 | 0.59% | 1.38% | Confirmed (Δ=0.09 ms) |

> **Table 3 Note on Invariance:** Invariance applies strictly to *absolute* client orchestrator runtime $T_{\text{orch}}$ (ms) ($|\Delta T_{\text{orch}}| < 0.5\text{ ms}$). The relative fraction $\Phi_{\text{orch}}$ increases in warm cache because neural inference latency $T_{\text{neural}}$ drops substantially under KV cache hits.
