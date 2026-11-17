# Table 5: Tool-RAG Dynamic Schema Pruning & Prompt Bloat Mitigation (W2)

| Platform | Regime | Catalog Condition | Prompt Tokens | Median Latency (ms) [95% CI] | Speedup vs 54-Tool Full | Token Reduction |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | Regime A (Cold Prefill) | OpenClaw Full (54 tools static) | 7091 | 18335.53 [18328.75, 18349.69] | 1.00x | 0.0% (Baseline) |
| macOS ARM64 (M4) | Regime A (Cold Prefill) | OpenClaw Minimal (15 tools static) | 2177 | 5269.28 [5261.62, 5277.70] | 3.48x | -69.3% |
| macOS ARM64 (M4) | Regime A (Cold Prefill) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 2467.33 [2463.82, 2470.64] | 7.43x | -87.1% |
| macOS ARM64 (M4) | Regime A (Cold Prefill) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 2531.35 [2527.06, 2542.49] | 7.24x | -87.1% |
| macOS ARM64 (M4) | Regime B (Warm Cache) | OpenClaw Full (54 tools static) | 7091 | 914.49 [910.84, 919.15] | 1.00x | 0.0% (Baseline) |
| macOS ARM64 (M4) | Regime B (Warm Cache) | OpenClaw Minimal (15 tools static) | 2177 | 768.61 [764.01, 771.38] | 1.19x | -69.3% |
| macOS ARM64 (M4) | Regime B (Warm Cache) | OpenClaw Tool-RAG (Top-5 dynamic) | 917 | 722.01 [716.50, 723.62] | 1.27x | -87.1% |
| macOS ARM64 (M4) | Regime B (Warm Cache) | PicoClaw Tool-RAG (Top-5 dynamic) | 917 | 703.83 [698.28, 706.90] | 1.30x | -87.1% |
| Linux x86_64 | Regime A (Cold Prefill) | OpenClaw Tool-RAG (Top-5 dynamic)* | 917 | 1589.16 [1574.89, 1596.55] | 4.97x | -87.1% |
| Linux x86_64 | Regime A (Cold Prefill) | PicoClaw Tool-RAG (Top-5 dynamic)* | 917 | 1550.23 [1537.74, 1557.13] | 5.09x | -87.1% |
| Linux x86_64 | Regime B (Warm Cache) | OpenClaw Tool-RAG (Top-5 dynamic)* | 917 | 1020.78 [1014.40, 1035.71] | 2.74x | -87.1% |
| Linux x86_64 | Regime B (Warm Cache) | PicoClaw Tool-RAG (Top-5 dynamic)* | 917 | 991.58 [982.62, 1008.38] | 2.82x | -87.1% |
| Windows 11 | Regime A (Cold Prefill) | OpenClaw Tool-RAG (Top-5 dynamic)* | 917 | 1570.06 [1558.12, 1579.07] | 4.88x | -87.1% |
| Windows 11 | Regime A (Cold Prefill) | PicoClaw Tool-RAG (Top-5 dynamic)* | 917 | 1535.42 [1528.50, 1541.06] | 4.99x | -87.1% |
| Windows 11 | Regime B (Warm Cache) | OpenClaw Tool-RAG (Top-5 dynamic)* | 917 | 1143.19 [1126.96, 1153.95] | 2.89x | -87.1% |
| Windows 11 | Regime B (Warm Cache) | PicoClaw Tool-RAG (Top-5 dynamic)* | 917 | 1089.98 [1080.90, 1100.58] | 3.03x | -87.1% |

> **Table 5 Methodological Notes:**
> - **Baseline Normalization Methodology:** On macOS ARM64, speedup factors are computed strictly against the internal unmitigated 54-tool baseline measured within the identical unified session (`tool_rag_mitigation_trials.jsonl`). On Linux x86_64 and Windows 11, the dedicated tool-RAG experiment evaluated the pruned arms (917 tokens); their speedup factors are computed relative to the consolidated primary prefill baseline of OpenClaw Full from the main campaign (`raw_trials.jsonl` for Regime A, `warm_cache_trials.jsonl` for Regime B), ensuring consistent within-node physical references without cross-session synthesis.
> - **Prompt Token Reduction:** Dynamic schema pruning achieves $-87.1\%$ prompt token reduction (917 tokens vs 7,091 tokens unmitigated).
> - **Regime Contrast:** In Regime A (Cold Prefill), dynamic schema pruning eliminates quadratic prompt attention, yielding a **7.43x speedup on macOS** (and ~6.04x across the full W1-W4 suite). In Regime B (Warm KV Cache), prefix KV reuse amortizes tool schema attention, resulting in modest Tool-RAG speedups (1.27x vs 54-tool catalog), demonstrating that Tool-RAG's primary utility lies in cold prefill mitigation.
> - `*` On Linux x86_64 and Windows 11, pruned arms reflect empirical evaluations from `tool_rag_mitigation_trials.jsonl` referenced against the primary unmitigated prefill baseline.
