# Table 4: KV-Cache Thrashing & Attention Eviction (Regimes T1, T2, T3)

| Platform | Regime Mode | Description | OpenClaw Minimal Median (ms) [IQR] | OpenClaw Full Median (ms) [IQR] | Thrashing Overhead |
| :--- | :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | T1 | Sequential Interleaved Tasks | 5269.8 [17.6] | 18333.2 [24.1] | 3.48x |
| macOS ARM64 (M4) | T2 | Uncontrolled Context Thrashing | 5323.0 [198.4] | 18141.0 [402.9] | 3.41x |
| macOS ARM64 (M4) | T3 | Block-Isolated Allocation | 744.3 [9.3] | 896.4 [3.9] | 1.20x |
| Linux x86_64 | T1 | Sequential Interleaved Tasks | 3113.4 [25.6] | 8167.0 [31.6] | 2.62x |
| Linux x86_64 | T2 | Uncontrolled Context Thrashing | 4128.8 [27.4] | 8172.6 [25.4] | 1.98x |
| Linux x86_64 | T3 | Block-Isolated Allocation | 2101.6 [22.7] | 3112.8 [29.5] | 1.48x |
| Windows 11 x86_64 | T1 | Sequential Interleaved Tasks | 2802.5 [52.7] | 7646.1 [85.9] | 2.73x |
| Windows 11 x86_64 | T2 | Uncontrolled Context Thrashing | 3086.6 [92.3] | 7790.6 [55.7] | 2.52x |
| Windows 11 x86_64 | T3 | Block-Isolated Allocation | 1549.3 [6.0] | 3318.1 [71.1] | 2.14x |
