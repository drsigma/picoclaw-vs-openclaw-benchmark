# Table 7: Dual-Session Empirical Replication Comparison (W2 Tool Chain)

| Platform OS | Runtime Engine | Session 1 Median (ms) [IQR] | Session 2 Median (ms) [IQR] | Relative Delta (%) | Mann-Whitney $U$ | $p$-value | Cliff's $\delta$ | Replication Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Linux x86_64 | PicoClaw (Go) | 2725.00 [29.63] | 2769.46 [32.99] | +1.63% | 119.0 | 0.0000 | -0.736 | Replicated (|Δ| < 2.0%) |
| Linux x86_64 | OpenClaw Minimal | 2760.46 [31.18] | 2792.50 [37.85] | +1.16% | 167.0 | 0.0000 | -0.629 | Replicated (|Δ| < 2.0%) |
| Linux x86_64 | OpenClaw Full | 7891.12 [49.39] | 7865.18 [60.84] | -0.33% | 545.0 | 0.1624 | +0.211 | Replicated (|Δ| < 2.0%) |
| Linux x86_64 | PythonNative | 2747.65 [31.94] | 2782.59 [40.59] | +1.27% | 185.0 | 0.0001 | -0.589 | Replicated (|Δ| < 2.0%) |
| Linux x86_64 | Bun Minimal | 2773.73 [23.58] | 2779.57 [26.50] | +0.21% | 409.0 | 0.5493 | -0.091 | Replicated (|Δ| < 2.0%) |
| Windows 11 | PicoClaw (Go) | 2746.68 [81.32] | 2758.80 [91.63] | +0.44% | 355.0 | 0.1624 | -0.211 | Replicated (|Δ| < 2.0%) |
| Windows 11 | OpenClaw Minimal | 2767.66 [68.10] | 2795.99 [74.88] | +1.02% | 325.0 | 0.0657 | -0.278 | Replicated (|Δ| < 2.0%) |
| Windows 11 | OpenClaw Full | 7663.76 [94.25] | 7720.38 [89.74] | +0.74% | 254.0 | 0.0038 | -0.436 | Replicated (|Δ| < 2.0%) |
| Windows 11 | PythonNative | 2750.00 [78.75] | 2797.00 [63.00] | +1.71% | 342.0 | 0.1116 | -0.240 | Replicated (|Δ| < 2.0%) |
| Windows 11 | Bun Minimal | 2745.86 [94.21] | 2757.29 [62.92] | +0.42% | 410.0 | 0.5592 | -0.089 | Replicated (|Δ| < 2.0%) |

> **Table 7 Notes:** macOS ARM64 was executed as a single canonical physical campaign of $N=30$ independent physical trials per cell. Linux x86_64 and Windows 11 underwent complete from-scratch dual-session replications ($N=30$ per session, total $N=60$ per condition) demonstrating across-session divergence under 2.0% across all runtimes.
