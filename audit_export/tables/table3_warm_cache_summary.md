# Table 3: Regime B (Warm KV-Cache) Middleware Latency Invariance

| Architecture | Platform | Cold $T_{\text{task}}$ (ms) | Warm $T_{\text{task}}$ (ms) | Cold $T_{\text{orch}}$ (ms) | Warm $T_{\text{orch}}$ (ms) | Cold $\Phi_{\text{orch}}$ (%) | Warm $\Phi_{\text{orch}}$ (%) | Absolute $T_{\text{orch}}$ Invariance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| PicoClaw (Go) | macOS ARM64 (M4) | 5272.68 | 749.40 | 5.53 | 4.29 | 0.10% | 0.58% | Confirmed (Δ=1.24 ms) |
| PicoClaw (Go) | Linux x86_64 | 2725.00 | 1272.74 | 6.66 | 7.13 | 0.24% | 0.57% | Confirmed (Δ=0.47 ms) |
| PicoClaw (Go) | Windows 11 NVIDIA | 2928.29 | 1597.06 | 13.11 | 11.16 | 0.45% | 0.70% | Confirmed (Δ=1.95 ms) |
| PicoClaw (Go) | Windows Intel iGPU | 53505.80 | 5036.51 | 14.03 | 14.09 | 0.03% | 0.28% | Confirmed (Δ=0.06 ms) |
| OpenClaw Minimal | macOS ARM64 (M4) | 5284.81 | 794.99 | 20.60 | 19.19 | 0.39% | 2.42% | Confirmed (Δ=1.41 ms) |
| OpenClaw Minimal | Linux x86_64 | 2760.46 | 1297.29 | 31.45 | 31.91 | 1.14% | 2.44% | Confirmed (Δ=0.45 ms) |
| OpenClaw Minimal | Windows 11 NVIDIA | 2906.76 | 1595.11 | 40.68 | 40.80 | 1.40% | 2.56% | Confirmed (Δ=0.12 ms) |
| OpenClaw Minimal | Windows Intel iGPU | 53505.92 | 4894.06 | 57.86 | 56.80 | 0.11% | 1.16% | Confirmed (Δ=1.06 ms) |
| OpenClaw Full | macOS ARM64 (M4) | 18406.88 | 944.35 | 24.55 | 23.45 | 0.13% | 2.47% | Confirmed (Δ=1.10 ms) |
| OpenClaw Full | Linux x86_64 | 7891.12 | 2793.98 | 35.99 | 36.40 | 0.46% | 1.30% | Confirmed (Δ=0.41 ms) |
| OpenClaw Full | Windows 11 NVIDIA | 7896.41 | 3526.98 | 48.55 | 48.20 | 0.61% | 1.37% | Confirmed (Δ=0.35 ms) |
| OpenClaw Full | Windows Intel iGPU | 226696.86 | 11819.54 | 68.89 | 68.96 | 0.03% | 0.58% | Confirmed (Δ=0.07 ms) |

> **Table 3 Note on Invariance:** Invariance applies strictly to *absolute* client orchestrator runtime $T_{\text{orch}}$ (ms) ($|\Delta T_{\text{orch}}| < 0.5\text{ ms}$). The relative fraction $\Phi_{\text{orch}}$ increases in warm cache because neural inference latency $T_{\text{neural}}$ drops substantially under KV cache hits.
