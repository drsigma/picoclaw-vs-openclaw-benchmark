# Table 5: Tool-RAG Dynamic Schema Pruning & Prompt Bloat Mitigation (W2)

| Platform | Regime | Catalog Condition | Prompt Tokens | Median Latency (ms) [95% CI] | Speedup vs 54-Tool Full | Speedup vs 15-Tool Minimal | Token Reduction |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | Regime A (Cold Prefill) | OpenClaw Full (54 tools static) | 7091 | 18468.46 [18464.22, 18476.83] | 1.00x | 0.29x | 0.0% (Baseline) |
| macOS ARM64 (M4) | Regime A (Cold Prefill) | OpenClaw Minimal (15 tools static) | 2177 | 5324.84 [5317.16, 5348.39] | 3.47x | 1.00x | -69.3% |
| macOS ARM64 (M4) | Regime A (Cold Prefill) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 2537.07 [2522.85, 2540.24] | 7.28x | 2.10x | -87.1% |
| macOS ARM64 (M4) | Regime A (Cold Prefill) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 2568.31 [2561.18, 2578.78] | 7.19x | 2.07x | -87.1% |
| macOS ARM64 (M4) | Regime B (Warm Cache) | OpenClaw Full (54 tools static) | 7091 | 971.45 [959.08, 982.65] | 1.00x | 0.84x | 0.0% (Baseline) |
| macOS ARM64 (M4) | Regime B (Warm Cache) | OpenClaw Minimal (15 tools static) | 2177 | 819.37 [813.60, 831.71] | 1.19x | 1.00x | -69.3% |
| macOS ARM64 (M4) | Regime B (Warm Cache) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 767.86 [756.62, 772.89] | 1.27x | 1.07x | -87.1% |
| macOS ARM64 (M4) | Regime B (Warm Cache) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 751.05 [743.25, 759.51] | 1.29x | 1.09x | -87.1% |
| Linux x86_64 | Regime A (Cold Prefill) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 1516.48 [1505.32, 1535.32] | 5.16x | 1.79x | -87.1% |
| Linux x86_64 | Regime A (Cold Prefill) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 1483.55 [1468.16, 1496.08] | 5.28x | 1.83x | -87.1% |
| Linux x86_64 | Regime B (Warm Cache) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 972.08 [954.00, 982.73] | 2.71x | 1.31x | -87.1% |
| Linux x86_64 | Regime B (Warm Cache) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 911.69 [907.03, 930.19] | 2.89x | 1.40x | -87.1% |
| Windows 11 NVIDIA | Regime A (Cold Prefill) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 1700.12 [1683.97, 1728.18] | 4.64x | 1.71x | -87.1% |
| Windows 11 NVIDIA | Regime A (Cold Prefill) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 1656.47 [1631.61, 1680.57] | 4.77x | 1.75x | -87.1% |
| Windows 11 NVIDIA | Regime B (Warm Cache) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 1263.13 [1242.51, 1274.96] | 2.79x | 1.26x | -87.1% |
| Windows 11 NVIDIA | Regime B (Warm Cache) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 1217.15 [1208.85, 1224.19] | 2.90x | 1.31x | -87.1% |
| Windows Intel iGPU | Regime A (Cold Prefill) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 22754.52 [22614.32, 22978.52] | 9.96x | 2.35x | -87.1% |
| Windows Intel iGPU | Regime A (Cold Prefill) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 22850.07 [22624.09, 23045.96] | 9.92x | 2.34x | -87.1% |
| Windows Intel iGPU | Regime B (Warm Cache) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 4006.80 [3998.94, 4037.60] | 2.95x | 1.22x | -87.1% |
| Windows Intel iGPU | Regime B (Warm Cache) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 3966.00 [3946.33, 3982.04] | 2.98x | 1.23x | -87.1% |

> **Table 5 Methodological Notes (Option B Exploratory x86_64 Qualification & Minimal-Catalog Contrast):**
> - **Baseline Normalization & Non-Causal Qualification on x86_64:** On **macOS ARM64**, both `Speedup vs 54-Tool Full` and `Speedup vs 15-Tool Minimal` reference controlled same-session unmitigated baselines measured inside the unified session (`tool_rag_mitigation_trials.jsonl`). On **Linux x86_64, Windows 11 NVIDIA, and Windows Intel Graphics**, the pruned Tool-RAG arms are referenced against each node's **primary-campaign baseline** (`raw_trials.jsonl` for Regime A; `warm_cache_trials.jsonl` for Regime B) rather than a same-session baseline. Accordingly, all x86_64 Tool-RAG speedup ratios are reported as **exploratory cross-session reference ratios** (never described as internal baselines) and **support no causal claims** regarding Tool-RAG speedup on x86_64.
> - **Contrast vs. 15-Tool Minimal:** Reporting `Speedup vs 15-Tool Minimal` quantifies the incremental latency reduction of Top-5 dynamic retrieval relative to the 15-tool catalog (macOS same-session `OpenClaw Tool-RAG`: Cold 2.10x, Warm 1.07x; x86_64 exploratory cross-session: Cold 1.71x--2.35x, Warm 1.22x--1.40x).
> - **Regime Contrast:** In Regime A (Cold Prefill), dynamic schema pruning reduces prompt attention prefill tokens by $-87.1\%$ (`7,091` to `917`). In Regime B (Warm KV Cache), prefix KV reuse amortizes tool schema attention, confirming that Tool-RAG's primary utility lies in cold prefill mitigation.
