# Table 2: Non-Parametric Hypothesis Testing & Effect Sizes (Mann-Whitney U, r1-Adjusted Variance, Cliff's Delta, Holm-Bonferroni)

| Platform | Regime | Workload | Comparison | $n_{\text{eff}}$ ($r_1>0$) | $U$ Statistic | $p$-value (adj, std) | $p$-value (adj, $r_1$-corrected) | Cliff's $\delta$ | Vargha-Delaney $A_{12}$ | Effect Magnitude |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| macOS (M4) | Regime A (Cold Prefill) | W1 | PicoClaw vs OpenClaw Full | 30.0/26.2 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime A (Cold Prefill) | W1 | PicoClaw vs OpenClaw Minimal | 30.0/30.0 | 299.0 | 0.8866 | 1.0000 | -0.336 | 0.332 | Medium |
| macOS (M4) | Regime A (Cold Prefill) | W1 | OpenClaw Minimal vs OpenClaw Full | 30.0/26.2 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime A (Cold Prefill) | W1 | PicoClaw vs PythonNative | 30.0/30.0 | 388.0 | 1.0000 | 1.0000 | -0.138 | 0.431 | Negligible |
| macOS (M4) | Regime A (Cold Prefill) | W2 | PicoClaw vs OpenClaw Full | 28.8/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime A (Cold Prefill) | W2 | PicoClaw vs OpenClaw Minimal | 28.8/21.7 | 316.0 | 1.0000 | 1.0000 | -0.298 | 0.351 | Small |
| macOS (M4) | Regime A (Cold Prefill) | W2 | OpenClaw Minimal vs OpenClaw Full | 21.7/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime A (Cold Prefill) | W2 | PicoClaw vs PythonNative | 28.8/30.0 | 352.0 | 1.0000 | 1.0000 | -0.218 | 0.391 | Small |
| macOS (M4) | Regime A (Cold Prefill) | W3 | PicoClaw vs OpenClaw Full | 30.0/13.8 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime A (Cold Prefill) | W3 | PicoClaw vs OpenClaw Minimal | 30.0/30.0 | 509.0 | 1.0000 | 1.0000 | +0.131 | 0.566 | Negligible |
| macOS (M4) | Regime A (Cold Prefill) | W3 | OpenClaw Minimal vs OpenClaw Full | 30.0/13.8 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime A (Cold Prefill) | W3 | PicoClaw vs PythonNative | 30.0/23.8 | 592.0 | 1.0000 | 1.0000 | +0.316 | 0.658 | Small |
| macOS (M4) | Regime A (Cold Prefill) | W4 | PicoClaw vs OpenClaw Full | 26.1/11.9 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime A (Cold Prefill) | W4 | PicoClaw vs OpenClaw Minimal | 26.1/28.1 | 253.0 | 0.1542 | 0.2734 | -0.438 | 0.281 | Medium |
| macOS (M4) | Regime A (Cold Prefill) | W4 | OpenClaw Minimal vs OpenClaw Full | 28.1/11.9 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime A (Cold Prefill) | W4 | PicoClaw vs PythonNative | 26.1/30.0 | 294.0 | 0.7527 | 1.0000 | -0.347 | 0.327 | Medium |
| macOS (M4) | Regime A (Cold Prefill) | W5 | PicoClaw vs OpenClaw Full | 29.0/23.3 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime A (Cold Prefill) | W5 | PicoClaw vs OpenClaw Minimal | 29.0/30.0 | 900.0 | < 0.0001 | < 0.0001 | +1.000 | 1.000 | Large |
| macOS (M4) | Regime A (Cold Prefill) | W5 | OpenClaw Minimal vs OpenClaw Full | 30.0/23.3 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime B (Warm Cache) | W1 | PicoClaw vs OpenClaw Full | 30.0/23.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime B (Warm Cache) | W1 | PicoClaw vs OpenClaw Minimal | 30.0/30.0 | 195.0 | 0.0086 | 0.0108 | -0.567 | 0.217 | Large |
| macOS (M4) | Regime B (Warm Cache) | W1 | OpenClaw Minimal vs OpenClaw Full | 30.0/23.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime B (Warm Cache) | W1 | PicoClaw vs PythonNative | 30.0/30.0 | 388.0 | 1.0000 | 1.0000 | -0.138 | 0.431 | Negligible |
| macOS (M4) | Regime B (Warm Cache) | W2 | PicoClaw vs OpenClaw Full | 30.0/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime B (Warm Cache) | W2 | PicoClaw vs OpenClaw Minimal | 30.0/30.0 | 2.0 | < 0.0001 | < 0.0001 | -0.996 | 0.002 | Large |
| macOS (M4) | Regime B (Warm Cache) | W2 | OpenClaw Minimal vs OpenClaw Full | 30.0/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime B (Warm Cache) | W2 | PicoClaw vs PythonNative | 30.0/30.0 | 198.0 | 0.0100 | 0.0124 | -0.560 | 0.220 | Large |
| macOS (M4) | Regime B (Warm Cache) | W3 | PicoClaw vs OpenClaw Full | 30.0/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime B (Warm Cache) | W3 | PicoClaw vs OpenClaw Minimal | 30.0/30.0 | 390.0 | 1.0000 | 1.0000 | -0.133 | 0.433 | Negligible |
| macOS (M4) | Regime B (Warm Cache) | W3 | OpenClaw Minimal vs OpenClaw Full | 30.0/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime B (Warm Cache) | W3 | PicoClaw vs PythonNative | 30.0/30.0 | 671.0 | 0.0524 | 0.0613 | +0.491 | 0.746 | Large |
| macOS (M4) | Regime B (Warm Cache) | W4 | PicoClaw vs OpenClaw Full | 18.4/21.2 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime B (Warm Cache) | W4 | PicoClaw vs OpenClaw Minimal | 18.4/30.0 | 30.0 | < 0.0001 | < 0.0001 | -0.933 | 0.033 | Large |
| macOS (M4) | Regime B (Warm Cache) | W4 | OpenClaw Minimal vs OpenClaw Full | 30.0/21.2 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime B (Warm Cache) | W4 | PicoClaw vs PythonNative | 18.4/28.2 | 31.0 | < 0.0001 | < 0.0001 | -0.931 | 0.034 | Large |
| macOS (M4) | Regime B (Warm Cache) | W5 | PicoClaw vs OpenClaw Full | 30.0/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| macOS (M4) | Regime B (Warm Cache) | W5 | PicoClaw vs OpenClaw Minimal | 30.0/30.0 | 900.0 | < 0.0001 | < 0.0001 | +1.000 | 1.000 | Large |
| macOS (M4) | Regime B (Warm Cache) | W5 | OpenClaw Minimal vs OpenClaw Full | 30.0/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W1 | PicoClaw vs OpenClaw Full | 30.0/11.8 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W1 | PicoClaw vs OpenClaw Minimal | 30.0/30.0 | 259.0 | 0.1942 | 0.2331 | -0.424 | 0.288 | Medium |
| Linux x86_64 | Regime A (Cold Prefill) | W1 | OpenClaw Minimal vs OpenClaw Full | 30.0/11.8 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W1 | PicoClaw vs PythonNative | 30.0/26.6 | 315.0 | 1.0000 | 1.0000 | -0.300 | 0.350 | Small |
| Linux x86_64 | Regime A (Cold Prefill) | W1 | PicoClaw vs Bun Minimal | 30.0/12.3 | 435.0 | 1.0000 | 1.0000 | -0.033 | 0.483 | Negligible |
| Linux x86_64 | Regime A (Cold Prefill) | W2 | PicoClaw vs OpenClaw Full | 18.7/6.7 | 0.0 | < 0.0001 | 0.0108 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W2 | PicoClaw vs OpenClaw Minimal | 18.7/30.0 | 216.0 | 0.0267 | 0.1292 (NS*) | -0.520 | 0.240 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W2 | OpenClaw Minimal vs OpenClaw Full | 30.0/6.7 | 0.0 | < 0.0001 | 0.0045 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W2 | PicoClaw vs PythonNative | 18.7/19.1 | 256.0 | 0.1733 | 0.9982 | -0.431 | 0.284 | Medium |
| Linux x86_64 | Regime A (Cold Prefill) | W2 | PicoClaw vs Bun Minimal | 18.7/30.0 | 440.0 | 1.0000 | 1.0000 | -0.022 | 0.489 | Negligible |
| Linux x86_64 | Regime A (Cold Prefill) | W3 | PicoClaw vs OpenClaw Full | 13.3/3.7 | 0.0 | < 0.0001 | 0.2026 (NS*) | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W3 | PicoClaw vs OpenClaw Minimal | 13.3/22.4 | 231.0 | 0.0569 | 0.7091 | -0.487 | 0.257 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W3 | OpenClaw Minimal vs OpenClaw Full | 22.4/3.7 | 0.0 | < 0.0001 | 0.1251 (NS*) | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W3 | PicoClaw vs PythonNative | 13.3/22.0 | 292.0 | 0.7158 | 1.0000 | -0.351 | 0.324 | Medium |
| Linux x86_64 | Regime A (Cold Prefill) | W3 | PicoClaw vs Bun Minimal | 13.3/13.1 | 502.0 | 1.0000 | 1.0000 | +0.116 | 0.558 | Negligible |
| Linux x86_64 | Regime A (Cold Prefill) | W4 | PicoClaw vs OpenClaw Full | 10.7/8.3 | 0.0 | < 0.0001 | 0.0162 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W4 | PicoClaw vs OpenClaw Minimal | 10.7/4.5 | 199.0 | 0.0104 | 1.0000 (NS*) | -0.558 | 0.221 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W4 | OpenClaw Minimal vs OpenClaw Full | 4.5/8.3 | 0.0 | < 0.0001 | 0.2251 (NS*) | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W4 | PicoClaw vs PythonNative | 10.7/4.9 | 171.0 | 0.0021 | 1.0000 (NS*) | -0.620 | 0.190 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W4 | PicoClaw vs Bun Minimal | 10.7/5.8 | 247.0 | 0.1212 | 1.0000 | -0.451 | 0.274 | Medium |
| Linux x86_64 | Regime A (Cold Prefill) | W5 | PicoClaw vs OpenClaw Full | 10.0/5.5 | 0.0 | < 0.0001 | 0.0839 (NS*) | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W5 | PicoClaw vs OpenClaw Minimal | 10.0/23.2 | 900.0 | < 0.0001 | 0.0004 | +1.000 | 1.000 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W5 | OpenClaw Minimal vs OpenClaw Full | 23.2/5.5 | 0.0 | < 0.0001 | 0.0192 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime A (Cold Prefill) | W5 | PicoClaw vs Bun Minimal | 10.0/15.8 | 513.0 | 1.0000 | 1.0000 | +0.140 | 0.570 | Negligible |
| Linux x86_64 | Regime B (Warm Cache) | W1 | PicoClaw vs OpenClaw Full | 14.0/27.8 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W1 | PicoClaw vs OpenClaw Minimal | 14.0/30.0 | 191.0 | 0.0069 | 0.1251 (NS*) | -0.576 | 0.212 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W1 | OpenClaw Minimal vs OpenClaw Full | 30.0/27.8 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W1 | PicoClaw vs PythonNative | 14.0/30.0 | 124.0 | < 0.0001 | 0.0085 | -0.724 | 0.138 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W1 | PicoClaw vs Bun Minimal | 14.0/16.5 | 500.0 | 1.0000 | 1.0000 | +0.111 | 0.556 | Negligible |
| Linux x86_64 | Regime B (Warm Cache) | W2 | PicoClaw vs OpenClaw Full | 10.0/30.0 | 0.0 | < 0.0001 | 0.0002 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W2 | PicoClaw vs OpenClaw Minimal | 10.0/17.6 | 96.0 | < 0.0001 | 0.0418 | -0.787 | 0.107 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W2 | OpenClaw Minimal vs OpenClaw Full | 17.6/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W2 | PicoClaw vs PythonNative | 10.0/29.2 | 67.0 | < 0.0001 | 0.0050 | -0.851 | 0.074 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W2 | PicoClaw vs Bun Minimal | 10.0/18.8 | 417.0 | 1.0000 | 1.0000 | -0.073 | 0.463 | Negligible |
| Linux x86_64 | Regime B (Warm Cache) | W3 | PicoClaw vs OpenClaw Full | 27.0/24.3 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W3 | PicoClaw vs OpenClaw Minimal | 27.0/28.6 | 260.0 | 0.1983 | 0.3267 | -0.422 | 0.289 | Medium |
| Linux x86_64 | Regime B (Warm Cache) | W3 | OpenClaw Minimal vs OpenClaw Full | 28.6/24.3 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W3 | PicoClaw vs PythonNative | 27.0/30.0 | 35.0 | < 0.0001 | < 0.0001 | -0.922 | 0.039 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W3 | PicoClaw vs Bun Minimal | 27.0/20.7 | 623.0 | 0.3982 | 0.9982 | +0.384 | 0.692 | Medium |
| Linux x86_64 | Regime B (Warm Cache) | W4 | PicoClaw vs OpenClaw Full | 30.0/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W4 | PicoClaw vs OpenClaw Minimal | 30.0/5.6 | 32.0 | < 0.0001 | 0.0326 | -0.929 | 0.036 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W4 | OpenClaw Minimal vs OpenClaw Full | 5.6/30.0 | 0.0 | < 0.0001 | 0.0127 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W4 | PicoClaw vs PythonNative | 30.0/30.0 | 33.0 | < 0.0001 | < 0.0001 | -0.927 | 0.037 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W4 | PicoClaw vs Bun Minimal | 30.0/23.5 | 50.0 | < 0.0001 | < 0.0001 | -0.889 | 0.056 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W5 | PicoClaw vs OpenClaw Full | 21.2/19.5 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W5 | PicoClaw vs OpenClaw Minimal | 21.2/19.5 | 900.0 | < 0.0001 | < 0.0001 | +1.000 | 1.000 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W5 | OpenClaw Minimal vs OpenClaw Full | 19.5/19.5 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Linux x86_64 | Regime B (Warm Cache) | W5 | PicoClaw vs Bun Minimal | 21.2/30.0 | 490.0 | 1.0000 | 1.0000 | +0.089 | 0.544 | Negligible |
| Windows 11 | Regime A (Cold Prefill) | W1 | PicoClaw vs OpenClaw Full | 30.0/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime A (Cold Prefill) | W1 | PicoClaw vs OpenClaw Minimal | 30.0/27.5 | 306.0 | 1.0000 | 1.0000 | -0.320 | 0.340 | Small |
| Windows 11 | Regime A (Cold Prefill) | W1 | OpenClaw Minimal vs OpenClaw Full | 27.5/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime A (Cold Prefill) | W1 | PicoClaw vs PythonNative | 30.0/30.0 | 348.0 | 1.0000 | 1.0000 | -0.227 | 0.387 | Small |
| Windows 11 | Regime A (Cold Prefill) | W1 | PicoClaw vs Bun Minimal | 30.0/30.0 | 458.0 | 1.0000 | 1.0000 | +0.018 | 0.509 | Negligible |
| Windows 11 | Regime A (Cold Prefill) | W2 | PicoClaw vs OpenClaw Full | 19.2/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime A (Cold Prefill) | W2 | PicoClaw vs OpenClaw Minimal | 19.2/30.0 | 598.0 | 0.9638 | 1.0000 | +0.329 | 0.664 | Small |
| Windows 11 | Regime A (Cold Prefill) | W2 | OpenClaw Minimal vs OpenClaw Full | 30.0/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime A (Cold Prefill) | W2 | PicoClaw vs PythonNative | 19.2/30.0 | 648.0 | 0.1505 | 0.4387 | +0.440 | 0.720 | Medium |
| Windows 11 | Regime A (Cold Prefill) | W2 | PicoClaw vs Bun Minimal | 19.2/22.8 | 667.0 | 0.0617 | 0.3503 | +0.482 | 0.741 | Large |
| Windows 11 | Regime A (Cold Prefill) | W3 | PicoClaw vs OpenClaw Full | 27.5/25.2 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime A (Cold Prefill) | W3 | PicoClaw vs OpenClaw Minimal | 27.5/20.7 | 399.0 | 1.0000 | 1.0000 | -0.113 | 0.443 | Negligible |
| Windows 11 | Regime A (Cold Prefill) | W3 | OpenClaw Minimal vs OpenClaw Full | 20.7/25.2 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime A (Cold Prefill) | W3 | PicoClaw vs PythonNative | 27.5/30.0 | 515.0 | 1.0000 | 1.0000 | +0.144 | 0.572 | Negligible |
| Windows 11 | Regime A (Cold Prefill) | W3 | PicoClaw vs Bun Minimal | 27.5/30.0 | 447.0 | 1.0000 | 1.0000 | -0.007 | 0.497 | Negligible |
| Windows 11 | Regime A (Cold Prefill) | W4 | PicoClaw vs OpenClaw Full | 30.0/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime A (Cold Prefill) | W4 | PicoClaw vs OpenClaw Minimal | 30.0/30.0 | 28.0 | < 0.0001 | < 0.0001 | -0.938 | 0.031 | Large |
| Windows 11 | Regime A (Cold Prefill) | W4 | OpenClaw Minimal vs OpenClaw Full | 30.0/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime A (Cold Prefill) | W4 | PicoClaw vs PythonNative | 30.0/30.0 | 26.0 | < 0.0001 | < 0.0001 | -0.942 | 0.029 | Large |
| Windows 11 | Regime A (Cold Prefill) | W4 | PicoClaw vs Bun Minimal | 30.0/30.0 | 55.0 | < 0.0001 | < 0.0001 | -0.878 | 0.061 | Large |
| Windows 11 | Regime A (Cold Prefill) | W5 | PicoClaw vs OpenClaw Full | 28.6/22.8 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime A (Cold Prefill) | W5 | PicoClaw vs OpenClaw Minimal | 28.6/24.7 | 900.0 | < 0.0001 | < 0.0001 | +1.000 | 1.000 | Large |
| Windows 11 | Regime A (Cold Prefill) | W5 | OpenClaw Minimal vs OpenClaw Full | 24.7/22.8 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime A (Cold Prefill) | W5 | PicoClaw vs Bun Minimal | 28.6/30.0 | 536.0 | 1.0000 | 1.0000 | +0.191 | 0.596 | Small |
| Windows 11 | Regime B (Warm Cache) | W1 | PicoClaw vs OpenClaw Full | 22.5/11.4 | 0.0 | < 0.0001 | 0.0002 | -1.000 | 0.000 | Large |
| Windows 11 | Regime B (Warm Cache) | W1 | PicoClaw vs OpenClaw Minimal | 22.5/30.0 | 164.0 | 0.0013 | 0.0063 | -0.636 | 0.182 | Large |
| Windows 11 | Regime B (Warm Cache) | W1 | OpenClaw Minimal vs OpenClaw Full | 30.0/11.4 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime B (Warm Cache) | W1 | PicoClaw vs PythonNative | 22.5/30.0 | 185.0 | 0.0048 | 0.0175 | -0.589 | 0.206 | Large |
| Windows 11 | Regime B (Warm Cache) | W1 | PicoClaw vs Bun Minimal | 22.5/24.2 | 348.0 | 1.0000 | 1.0000 | -0.227 | 0.387 | Small |
| Windows 11 | Regime B (Warm Cache) | W2 | PicoClaw vs OpenClaw Full | 28.2/21.9 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime B (Warm Cache) | W2 | PicoClaw vs OpenClaw Minimal | 28.2/30.0 | 482.0 | 1.0000 | 1.0000 | +0.071 | 0.536 | Negligible |
| Windows 11 | Regime B (Warm Cache) | W2 | OpenClaw Minimal vs OpenClaw Full | 30.0/21.9 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime B (Warm Cache) | W2 | PicoClaw vs PythonNative | 28.2/30.0 | 570.0 | 1.0000 | 1.0000 | +0.267 | 0.633 | Small |
| Windows 11 | Regime B (Warm Cache) | W2 | PicoClaw vs Bun Minimal | 28.2/30.0 | 775.0 | < 0.0001 | 0.0002 | +0.722 | 0.861 | Large |
| Windows 11 | Regime B (Warm Cache) | W3 | PicoClaw vs OpenClaw Full | 16.3/19.3 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime B (Warm Cache) | W3 | PicoClaw vs OpenClaw Minimal | 16.3/30.0 | 114.0 | < 0.0001 | 0.0022 | -0.747 | 0.127 | Large |
| Windows 11 | Regime B (Warm Cache) | W3 | OpenClaw Minimal vs OpenClaw Full | 30.0/19.3 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime B (Warm Cache) | W3 | PicoClaw vs PythonNative | 16.3/30.0 | 267.0 | 0.2642 | 0.9982 | -0.407 | 0.297 | Medium |
| Windows 11 | Regime B (Warm Cache) | W3 | PicoClaw vs Bun Minimal | 16.3/30.0 | 485.0 | 1.0000 | 1.0000 | +0.078 | 0.539 | Negligible |
| Windows 11 | Regime B (Warm Cache) | W4 | PicoClaw vs OpenClaw Full | 20.5/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime B (Warm Cache) | W4 | PicoClaw vs OpenClaw Minimal | 20.5/14.0 | 8.0 | < 0.0001 | 0.0001 | -0.982 | 0.009 | Large |
| Windows 11 | Regime B (Warm Cache) | W4 | OpenClaw Minimal vs OpenClaw Full | 14.0/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime B (Warm Cache) | W4 | PicoClaw vs PythonNative | 20.5/23.6 | 4.0 | < 0.0001 | < 0.0001 | -0.991 | 0.004 | Large |
| Windows 11 | Regime B (Warm Cache) | W4 | PicoClaw vs Bun Minimal | 20.5/18.6 | 7.0 | < 0.0001 | < 0.0001 | -0.984 | 0.008 | Large |
| Windows 11 | Regime B (Warm Cache) | W5 | PicoClaw vs OpenClaw Full | 30.0/15.1 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime B (Warm Cache) | W5 | PicoClaw vs OpenClaw Minimal | 30.0/30.0 | 900.0 | < 0.0001 | < 0.0001 | +1.000 | 1.000 | Large |
| Windows 11 | Regime B (Warm Cache) | W5 | OpenClaw Minimal vs OpenClaw Full | 30.0/15.1 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows 11 | Regime B (Warm Cache) | W5 | PicoClaw vs Bun Minimal | 30.0/12.8 | 519.0 | 1.0000 | 1.0000 | +0.153 | 0.577 | Small |
| Windows Intel iGPU | Regime A (Cold Prefill) | W2 | PicoClaw vs OpenClaw Full | 24.8/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows Intel iGPU | Regime A (Cold Prefill) | W2 | PicoClaw vs OpenClaw Minimal | 24.8/22.2 | 441.0 | 1.0000 | 1.0000 | -0.020 | 0.490 | Negligible |
| Windows Intel iGPU | Regime A (Cold Prefill) | W2 | OpenClaw Minimal vs OpenClaw Full | 22.2/30.0 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows Intel iGPU | Regime A (Cold Prefill) | W2 | PicoClaw vs PythonNative | 24.8/20.3 | 456.0 | 1.0000 | 1.0000 | +0.013 | 0.507 | Negligible |
| Windows Intel iGPU | Regime A (Cold Prefill) | W2 | PicoClaw vs Bun Minimal | 24.8/24.9 | 406.0 | 1.0000 | 1.0000 | -0.098 | 0.451 | Negligible |
| Windows Intel iGPU | Regime A (Cold Prefill) | W5 | PicoClaw vs OpenClaw Minimal | 30.0/30.0 | 871.0 | < 0.0001 | < 0.0001 | +0.936 | 0.968 | Large |
| Windows Intel iGPU | Regime B (Warm Cache) | W2 | PicoClaw vs OpenClaw Full | 30.0/24.3 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows Intel iGPU | Regime B (Warm Cache) | W2 | PicoClaw vs OpenClaw Minimal | 30.0/30.0 | 826.0 | < 0.0001 | < 0.0001 | +0.836 | 0.918 | Large |
| Windows Intel iGPU | Regime B (Warm Cache) | W2 | OpenClaw Minimal vs OpenClaw Full | 30.0/24.3 | 0.0 | < 0.0001 | < 0.0001 | -1.000 | 0.000 | Large |
| Windows Intel iGPU | Regime B (Warm Cache) | W2 | PicoClaw vs PythonNative | 30.0/30.0 | 405.0 | 1.0000 | 1.0000 | -0.100 | 0.450 | Negligible |
| Windows Intel iGPU | Regime B (Warm Cache) | W2 | PicoClaw vs Bun Minimal | 30.0/25.6 | 422.0 | 1.0000 | 1.0000 | -0.062 | 0.469 | Negligible |
| Windows Intel iGPU | Regime B (Warm Cache) | W5 | PicoClaw vs OpenClaw Minimal | 20.7/30.0 | 872.0 | < 0.0001 | < 0.0001 | +0.938 | 0.969 | Large |

> **Table 2 Methodological Notes on Statistical Inference, $r_1$ Variance Adjustment, and W5 Exclusion:**
> - **Positive-Autocorrelation Variance Adjustment (M4):** Standard Mann-Whitney $U$ assumes i.i.d. observations ($n=30$). For cells exhibiting positive lag-1 autocorrelation ($r_1 > 0$), effective sample size $n_{\text{eff}} = n(1-r_1)/(1+r_1)$ is used to inflate the asymptotic variance of $U$ by $\text{VIF} = [(n_{\text{eff},1}+n_{\text{eff},2}+1)/(n_{\text{eff},1} n_{\text{eff},2})] / [(n_1+n_2+1)/(n_1 n_2)]$ (for $r_1 \le 0$, $n_{\text{eff}} = n$ is retained conservatively). Across 146 contrasts, **99** are significant under standard Holm-Bonferroni and **91** remain significant under $r_1$-corrected Holm-Bonferroni; **8** contrast(s) marked `(NS*)` lose significance after accounting for positive autocorrelation.
> - **Workload W5 Segregation (M1):** `python_native` (LangChain Core) in W5 is excluded from all pairwise latency/performance contrasts in Table 2 due to schema validation failure and confounded prompt truncation (see Table 8 and `w5_token_and_schema_audit.csv`).
> - **Multiple Testing Correction:** Family-wise error rate across all pairwise hypothesis tests is controlled via the Holm-Bonferroni step-down procedure (Holm 1979) applied separately to standard and $r_1$-adjusted $p$-values.
