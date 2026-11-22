# Table 5: Tool-RAG Dynamic Schema Pruning & Prompt Bloat Mitigation (W2)

| Platform | Regime | Catalog Condition | Prompt Tokens | Median Latency (ms) [95% CI] | Speedup vs 54-Tool Full | Token Reduction |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | Regime A (Cold Prefill) | OpenClaw Full (54 tools static) | 7091 | 18468.46 [18464.22, 18476.83] | 1.00x | 0.0% (Baseline) |
| macOS ARM64 (M4) | Regime A (Cold Prefill) | OpenClaw Minimal (15 tools static) | 2177 | 5324.84 [5317.16, 5348.39] | 3.47x | -69.3% |
| macOS ARM64 (M4) | Regime A (Cold Prefill) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 2537.07 [2522.85, 2540.24] | 7.28x | -87.1% |
| macOS ARM64 (M4) | Regime A (Cold Prefill) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 2568.31 [2561.18, 2578.78] | 7.19x | -87.1% |
| macOS ARM64 (M4) | Regime B (Warm Cache) | OpenClaw Full (54 tools static) | 7091 | 971.45 [959.08, 982.65] | 1.00x | 0.0% (Baseline) |
| macOS ARM64 (M4) | Regime B (Warm Cache) | OpenClaw Minimal (15 tools static) | 2177 | 819.37 [813.60, 831.71] | 1.19x | -69.3% |
| macOS ARM64 (M4) | Regime B (Warm Cache) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 767.86 [756.62, 772.89] | 1.27x | -87.1% |
| macOS ARM64 (M4) | Regime B (Warm Cache) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 751.05 [743.25, 759.51] | 1.29x | -87.1% |
| Linux x86_64 | Regime A (Cold Prefill) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 1516.48 [1505.32, 1535.32] | 5.16x | -87.1% |
| Linux x86_64 | Regime A (Cold Prefill) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 1483.55 [1468.16, 1496.08] | 5.28x | -87.1% |
| Linux x86_64 | Regime B (Warm Cache) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 972.08 [954.00, 982.73] | 2.71x | -87.1% |
| Linux x86_64 | Regime B (Warm Cache) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 911.69 [907.03, 930.19] | 2.89x | -87.1% |
| Windows 11 NVIDIA | Regime A (Cold Prefill) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 1700.12 [1683.97, 1728.18] | 4.64x | -87.1% |
| Windows 11 NVIDIA | Regime A (Cold Prefill) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 1656.47 [1631.61, 1680.57] | 4.77x | -87.1% |
| Windows 11 NVIDIA | Regime B (Warm Cache) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 1263.13 [1242.51, 1274.96] | 2.79x | -87.1% |
| Windows 11 NVIDIA | Regime B (Warm Cache) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 1217.15 [1208.85, 1224.19] | 2.90x | -87.1% |
| Windows Intel iGPU | Regime A (Cold Prefill) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 22754.52 [22614.32, 22978.52] | 9.96x | -87.1% |
| Windows Intel iGPU | Regime A (Cold Prefill) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 22850.07 [22624.09, 23045.96] | 9.92x | -87.1% |
| Windows Intel iGPU | Regime B (Warm Cache) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 4006.80 [3998.94, 4037.60] | 2.95x | -87.1% |
| Windows Intel iGPU | Regime B (Warm Cache) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 3966.00 [3946.33, 3982.04] | 2.98x | -87.1% |

> **Table 5 Methodological Notes:**
> - **Baseline Normalization Methodology:** On macOS ARM64, speedup factors are computed strictly against the internal unmitigated 54-tool baseline measured within the identical unified session (`tool_rag_mitigation_trials.jsonl`). On Linux x86_64, Windows 11 NVIDIA, and Windows Intel Graphics, the pruned arms are referenced against the primary unmitigated prefill baseline of OpenClaw Full from the main campaign (`raw_trials.jsonl` for Regime A, `warm_cache_trials.jsonl` for Regime B), ensuring consistent within-node physical references without cross-session synthesis.
> - **Dynamic Schema Pruning:** Dynamic schema pruning reduces prompt tokens from the unmitigated schema down to the retrieved schema.
> - **Regime Contrast:** In Regime A (Cold Prefill), dynamic schema pruning eliminates quadratic prompt attention. In Regime B (Warm KV Cache), prefix KV reuse amortizes tool schema attention, confirming that Tool-RAG primary utility lies in cold prefill mitigation.
