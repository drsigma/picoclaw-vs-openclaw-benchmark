# Table 4: KV-Cache Thrashing & Attention Eviction (Regimes T1, T2, T3)

| Platform | Regime Mode | Description | OpenClaw Minimal (ms) [IQR] | OpenClaw Full (ms) [IQR] | Full-to-Minimal Catalog Ratio | Minimal Cache Penalty ($T_2/T_3$) | Full Cache Penalty ($T_2/T_3$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | T1 | Sequential Interleaved Tasks | 5267.6 [26.5] | 18406.4 [14.3] | 3.49x | --- | --- |
| macOS ARM64 (M4) | T2 | Uncontrolled Context Thrashing | 5399.2 [50.6] | 18425.6 [177.4] | 3.41x | 6.85x | 19.46x |
| macOS ARM64 (M4) | T3 | Block-Isolated Allocation | 788.2 [32.7] | 946.8 [24.4] | 1.20x | --- | --- |
| Linux x86_64 | T1 | Sequential Interleaved Tasks | 3113.4 [25.6] | 8167.0 [31.6] | 2.62x | --- | --- |
| Linux x86_64 | T2 | Uncontrolled Context Thrashing | 4128.8 [27.4] | 8172.6 [25.4] | 1.98x | 1.96x | 2.63x |
| Linux x86_64 | T3 | Block-Isolated Allocation | 2101.6 [22.7] | 3112.8 [29.5] | 1.48x | --- | --- |
| Windows 11 NVIDIA | T1 | Sequential Interleaved Tasks | 2849.6 [53.4] | 7605.2 [56.4] | 2.67x | --- | --- |
| Windows 11 NVIDIA | T2 | Uncontrolled Context Thrashing | 3108.3 [149.4] | 7743.7 [88.9] | 2.49x | 2.01x | 2.30x |
| Windows 11 NVIDIA | T3 | Block-Isolated Allocation | 1550.1 [48.9] | 3371.8 [89.8] | 2.18x | --- | --- |

> **Table 4 Notes:**
> - `Full-to-Minimal Catalog Ratio`: Latency ratio of 54-tool catalog to 15-tool minimal catalog under identical memory regime.
> - `Minimal Cache Penalty (T2/T3)`: Slowdown induced by uncontrolled context thrashing ($T_2$) relative to isolated slot retention ($T_3$) for minimal catalog.
> - `Full Cache Penalty (T2/T3)`: Slowdown induced by uncontrolled context thrashing ($T_2$) relative to isolated slot retention ($T_3$) for full catalog.
