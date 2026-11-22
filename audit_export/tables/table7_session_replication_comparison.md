# Table 7: Multi-Platform Dual-Session Empirical Contrast Replication & Block-Bootstrap TOST Equivalence Matrix

| Platform OS | Regime | Workload | Runtime Contrast (vs PicoClaw Go) | Session 1 Δ (ms) [IQR] | Session 2 Δ (ms) [IQR] | Diff $\Delta_2 - \Delta_1$ (ms) | 90% MBB CI ($b=3$) (ms) | $p_{\text{TOST}}$ ($\pm 5.0$ ms) | Equivalence Status (Lakens 2017) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | Regime B (Warm) | W1 | Node Minimal vs PicoClaw | 15.57 [0.75] | 15.37 [0.80] | -0.20 | [-0.38, +0.04] | < 0.0002 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W1 | PythonNative vs PicoClaw | 6.86 [0.54] | 6.74 [0.76] | -0.12 | [-0.23, +0.24] | < 0.0002 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W2 | Node Minimal vs PicoClaw | 14.80 [0.82] | 14.89 [0.70] | +0.09 | [-0.25, +0.36] | < 0.0002 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W2 | PythonNative vs PicoClaw | 6.42 [0.64] | 6.33 [0.76] | -0.09 | [-0.35, +0.19] | < 0.0002 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W3 | Node Minimal vs PicoClaw | 0.35 [2.50] | 0.78 [3.81] | +0.43 | [+0.04, +1.36] | < 0.0002 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W3 | PythonNative vs PicoClaw | -13.17 [2.89] | -12.92 [1.79] | +0.25 | [-0.55, +0.83] | < 0.0002 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W4 | Node Minimal vs PicoClaw | 15.00 [2.22] | 14.97 [3.70] | -0.03 | [-1.15, +1.04] | < 0.0002 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W4 | PythonNative vs PicoClaw | 3.98 [3.18] | 3.57 [3.87] | -0.41 | [-1.70, +0.77] | < 0.0002 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W5 | Node Minimal vs PicoClaw | 15.29 [0.68] | 15.10 [0.86] | -0.19 | [-0.49, +0.04] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W1 | Node Minimal vs PicoClaw | 23.92 [2.03] | 23.65 [1.91] | -0.27 | [-1.23, +0.63] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W1 | Node Full vs PicoClaw | 29.33 [2.46] | 28.34 [1.94] | -0.99 | [-1.59, -0.31] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W1 | PythonNative vs PicoClaw | 9.67 [4.32] | 10.84 [4.11] | +1.17 | [-0.40, +2.50] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W1 | Bun Minimal vs PicoClaw | 0.52 [1.74] | 0.56 [1.70] | +0.04 | [-0.69, +0.50] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W2 | Node Minimal vs PicoClaw | 24.44 [1.79] | 23.09 [2.55] | -1.35 | [-2.24, -0.32] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W2 | Node Full vs PicoClaw | 28.58 [2.04] | 27.79 [2.53] | -0.79 | [-1.70, -0.21] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W2 | PythonNative vs PicoClaw | 9.93 [3.13] | 8.88 [3.25] | -1.05 | [-2.25, +0.06] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W2 | Bun Minimal vs PicoClaw | -0.24 [2.68] | -0.82 [3.37] | -0.58 | [-1.69, +0.74] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W3 | Node Minimal vs PicoClaw | 12.50 [4.80] | 11.35 [4.29] | -1.15 | [-2.24, +1.72] | 0.0026 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W3 | Node Full vs PicoClaw | 17.01 [3.60] | 17.35 [4.21] | +0.34 | [-1.18, +1.77] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W3 | PythonNative vs PicoClaw | -10.42 [8.41] | -10.07 [6.28] | +0.35 | [-2.62, +3.43] | 0.0082 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W3 | Bun Minimal vs PicoClaw | -16.54 [5.76] | -15.78 [3.99] | +0.76 | [-0.73, +3.05] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W4 | Node Minimal vs PicoClaw | 22.40 [7.48] | 24.25 [8.74] | +1.86 | [-1.26, +5.99] | 0.1196 | Inconclusive |
| Linux x86_64 | Regime A (Cold) | W4 | Node Full vs PicoClaw | 76.39 [8.46] | 73.19 [8.52] | -3.20 | [-5.34, -0.43] | 0.0708 | Inconclusive |
| Linux x86_64 | Regime A (Cold) | W4 | PythonNative vs PicoClaw | 1.54 [6.58] | 3.77 [8.39] | +2.22 | [+0.85, +6.10] | 0.1572 | Inconclusive |
| Linux x86_64 | Regime A (Cold) | W4 | Bun Minimal vs PicoClaw | -16.11 [8.26] | -13.78 [6.54] | +2.33 | [-2.15, +5.67] | 0.0840 | Inconclusive |
| Linux x86_64 | Regime A (Cold) | W5 | Node Minimal vs PicoClaw | 23.81 [1.99] | 23.24 [1.26] | -0.57 | [-1.00, -0.02] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W5 | Node Full vs PicoClaw | 29.52 [1.53] | 28.93 [2.15] | -0.59 | [-1.17, +0.00] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W5 | Bun Minimal vs PicoClaw | 0.74 [1.14] | 0.71 [1.58] | -0.03 | [-0.29, +0.51] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W1 | Node Minimal vs PicoClaw | 22.83 [1.56] | 22.96 [1.66] | +0.13 | [-0.71, +0.97] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W1 | Node Full vs PicoClaw | 28.46 [1.81] | 28.61 [1.62] | +0.15 | [-0.64, +0.82] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W1 | PythonNative vs PicoClaw | 10.67 [4.25] | 10.46 [2.29] | -0.21 | [-1.93, +1.75] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W1 | Bun Minimal vs PicoClaw | -0.26 [1.48] | 0.51 [1.46] | +0.77 | [-0.12, +1.25] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W2 | Node Minimal vs PicoClaw | 22.88 [1.60] | 23.12 [1.80] | +0.24 | [-0.45, +0.72] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W2 | Node Full vs PicoClaw | 27.40 [1.29] | 27.97 [1.73] | +0.56 | [-0.14, +0.96] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W2 | PythonNative vs PicoClaw | 10.74 [3.01] | 11.45 [3.50] | +0.71 | [-0.92, +1.39] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W2 | Bun Minimal vs PicoClaw | -0.39 [1.44] | 0.11 [1.42] | +0.50 | [-0.45, +1.08] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W3 | Node Minimal vs PicoClaw | 11.01 [3.89] | 11.26 [4.31] | +0.25 | [-1.43, +2.44] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W3 | Node Full vs PicoClaw | 15.12 [3.45] | 16.96 [3.93] | +1.83 | [-0.44, +2.96] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W3 | PythonNative vs PicoClaw | -12.43 [4.19] | -12.57 [3.62] | -0.13 | [-1.17, +1.70] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W3 | Bun Minimal vs PicoClaw | -15.44 [5.18] | -16.33 [4.16] | -0.89 | [-2.75, +1.38] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W4 | Node Minimal vs PicoClaw | 22.57 [6.68] | 21.73 [9.81] | -0.83 | [-5.16, +2.67] | 0.0562 | Inconclusive |
| Linux x86_64 | Regime B (Warm) | W4 | Node Full vs PicoClaw | 72.90 [6.90] | 75.30 [7.37] | +2.40 | [-1.10, +5.05] | 0.0524 | Inconclusive |
| Linux x86_64 | Regime B (Warm) | W4 | PythonNative vs PicoClaw | 0.91 [7.39] | -2.52 [6.70] | -3.43 | [-7.66, -1.04] | 0.2578 | Inconclusive |
| Linux x86_64 | Regime B (Warm) | W4 | Bun Minimal vs PicoClaw | -16.65 [5.27] | -19.44 [4.37] | -2.79 | [-4.13, -0.34] | 0.0058 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W5 | Node Minimal vs PicoClaw | 23.10 [1.48] | 23.34 [1.91] | +0.23 | [-0.35, +0.72] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W5 | Node Full vs PicoClaw | 28.25 [1.73] | 28.54 [2.11] | +0.29 | [-0.10, +0.93] | < 0.0002 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W5 | Bun Minimal vs PicoClaw | 0.56 [0.96] | 0.68 [1.92] | +0.12 | [-0.44, +0.64] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W1 | Node Minimal vs PicoClaw | 27.90 [3.41] | 28.26 [5.00] | +0.35 | [-1.59, +1.67] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W1 | Node Full vs PicoClaw | 34.57 [3.30] | 34.28 [4.10] | -0.29 | [-1.76, +1.43] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W1 | PythonNative vs PicoClaw | 22.09 [18.42] | 14.38 [21.90] | -7.71 | [-13.67, +1.84] | 0.5606 | Inconclusive |
| Windows 11 NVIDIA | Regime A (Cold) | W1 | Bun Minimal vs PicoClaw | 4.05 [2.91] | 5.26 [4.82] | +1.22 | [-0.99, +2.26] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W2 | Node Minimal vs PicoClaw | 27.65 [5.05] | 29.56 [2.26] | +1.92 | [-0.14, +3.39] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W2 | Node Full vs PicoClaw | 35.30 [3.78] | 36.96 [1.85] | +1.66 | [+0.13, +2.43] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W2 | PythonNative vs PicoClaw | 13.86 [8.42] | 15.23 [17.64] | +1.37 | [-3.61, +8.20] | 0.1708 | Inconclusive |
| Windows 11 NVIDIA | Regime A (Cold) | W2 | Bun Minimal vs PicoClaw | 3.75 [4.58] | 5.47 [3.38] | +1.72 | [-0.56, +2.93] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W3 | Node Minimal vs PicoClaw | 25.09 [6.58] | 24.94 [5.63] | -0.15 | [-2.12, +2.04] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W3 | Node Full vs PicoClaw | 30.48 [5.28] | 32.02 [5.65] | +1.54 | [-0.38, +2.54] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W3 | PythonNative vs PicoClaw | 2.14 [12.30] | 5.59 [14.90] | +3.45 | [-1.62, +8.43] | 0.3574 | Inconclusive |
| Windows 11 NVIDIA | Regime A (Cold) | W3 | Bun Minimal vs PicoClaw | -11.27 [6.49] | -9.79 [4.20] | +1.48 | [-2.01, +2.61] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W4 | Node Minimal vs PicoClaw | 56.40 [9.98] | 56.15 [11.01] | -0.25 | [-4.87, +2.70] | 0.0464 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W4 | Node Full vs PicoClaw | 151.39 [11.40] | 153.95 [14.19] | +2.56 | [-2.61, +7.69] | 0.2348 | Inconclusive |
| Windows 11 NVIDIA | Regime A (Cold) | W4 | PythonNative vs PicoClaw | 135.11 [37.63] | 150.29 [38.30] | +15.17 | [-3.31, +34.39] | 0.7856 | Inconclusive |
| Windows 11 NVIDIA | Regime A (Cold) | W4 | Bun Minimal vs PicoClaw | -2.59 [8.85] | -1.86 [10.93] | +0.74 | [-4.07, +3.62] | 0.0270 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W5 | Node Minimal vs PicoClaw | 26.96 [2.72] | 26.76 [3.24] | -0.20 | [-1.93, +0.95] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W5 | Node Full vs PicoClaw | 34.46 [3.62] | 34.83 [3.90] | +0.37 | [-1.14, +1.42] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W5 | Bun Minimal vs PicoClaw | 3.54 [3.56] | 3.98 [2.97] | +0.44 | [-1.05, +1.70] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W1 | Node Minimal vs PicoClaw | 27.91 [1.35] | 27.67 [1.42] | -0.23 | [-0.82, +0.20] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W1 | Node Full vs PicoClaw | 35.48 [1.76] | 34.74 [1.83] | -0.74 | [-1.30, +0.06] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W1 | PythonNative vs PicoClaw | 17.23 [9.86] | 19.31 [10.23] | +2.08 | [-1.19, +5.72] | 0.0748 | Inconclusive |
| Windows 11 NVIDIA | Regime B (Warm) | W1 | Bun Minimal vs PicoClaw | 3.88 [2.33] | 3.57 [2.53] | -0.31 | [-1.19, +1.02] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W2 | Node Minimal vs PicoClaw | 29.94 [1.31] | 30.00 [1.61] | +0.06 | [-0.59, +0.41] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W2 | Node Full vs PicoClaw | 36.51 [2.34] | 36.53 [2.32] | +0.02 | [-1.27, +0.59] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W2 | PythonNative vs PicoClaw | 19.54 [13.05] | 18.41 [13.74] | -1.13 | [-6.52, +2.53] | 0.1116 | Inconclusive |
| Windows 11 NVIDIA | Regime B (Warm) | W2 | Bun Minimal vs PicoClaw | 4.84 [2.53] | 4.89 [1.89] | +0.04 | [-0.54, +0.46] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W3 | Node Minimal vs PicoClaw | 22.41 [4.22] | 23.46 [2.22] | +1.04 | [-0.45, +2.67] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W3 | Node Full vs PicoClaw | 30.85 [3.45] | 29.71 [4.03] | -1.14 | [-1.69, +0.14] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W3 | PythonNative vs PicoClaw | 0.60 [11.45] | 0.56 [10.73] | -0.03 | [-6.50, +6.28] | 0.1410 | Inconclusive |
| Windows 11 NVIDIA | Regime B (Warm) | W3 | Bun Minimal vs PicoClaw | -12.31 [2.83] | -11.50 [3.79] | +0.81 | [-0.78, +1.87] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W4 | Node Minimal vs PicoClaw | 51.15 [5.43] | 51.41 [5.90] | +0.26 | [-2.03, +1.90] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W4 | Node Full vs PicoClaw | 128.24 [3.04] | 134.18 [5.43] | +5.94 | [+4.02, +6.86] | 0.7958 | Inconclusive |
| Windows 11 NVIDIA | Regime B (Warm) | W4 | PythonNative vs PicoClaw | 136.76 [28.46] | 149.11 [35.79] | +12.35 | [-2.41, +24.41] | 0.8166 | Inconclusive |
| Windows 11 NVIDIA | Regime B (Warm) | W4 | Bun Minimal vs PicoClaw | -2.67 [5.83] | -3.18 [4.48] | -0.51 | [-2.95, +1.33] | 0.0012 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W5 | Node Minimal vs PicoClaw | 27.28 [2.08] | 27.40 [2.16] | +0.12 | [-0.91, +0.76] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W5 | Node Full vs PicoClaw | 34.56 [1.37] | 34.14 [1.76] | -0.41 | [-1.08, +0.02] | < 0.0002 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W5 | Bun Minimal vs PicoClaw | 3.14 [1.92] | 3.60 [2.30] | +0.45 | [-0.77, +1.23] | < 0.0002 | Equivalent |
| Windows Intel iGPU | Regime A (Cold) | W2 | Node Minimal vs PicoClaw | 43.12 [4.01] | 42.48 [6.08] | -0.64 | [-1.76, +1.66] | 0.0004 | Equivalent |
| Windows Intel iGPU | Regime A (Cold) | W2 | Node Full vs PicoClaw | 54.37 [3.28] | 54.94 [6.01] | +0.57 | [-1.82, +1.45] | < 0.0002 | Equivalent |
| Windows Intel iGPU | Regime A (Cold) | W2 | PythonNative vs PicoClaw | 30.78 [15.02] | 27.40 [14.89] | -3.38 | [-10.48, +4.24] | 0.3736 | Inconclusive |
| Windows Intel iGPU | Regime A (Cold) | W2 | Bun Minimal vs PicoClaw | 9.55 [2.40] | 9.72 [4.85] | +0.17 | [-0.94, +1.64] | 0.0036 | Equivalent |
| Windows Intel iGPU | Regime A (Cold) | W5 | Node Minimal vs PicoClaw | 39.77 [2.40] | 39.44 [2.79] | -0.32 | [-1.05, +0.59] | < 0.0002 | Equivalent |
| Windows Intel iGPU | Regime B (Warm) | W2 | Node Minimal vs PicoClaw | 42.60 [2.34] | 43.45 [2.80] | +0.85 | [-0.52, +1.34] | < 0.0002 | Equivalent |
| Windows Intel iGPU | Regime B (Warm) | W2 | Node Full vs PicoClaw | 54.74 [3.17] | 54.98 [2.40] | +0.24 | [-0.88, +1.57] | < 0.0002 | Equivalent |
| Windows Intel iGPU | Regime B (Warm) | W2 | PythonNative vs PicoClaw | 29.02 [8.26] | 32.56 [8.79] | +3.54 | [+0.98, +7.26] | 0.3020 | Inconclusive |
| Windows Intel iGPU | Regime B (Warm) | W2 | Bun Minimal vs PicoClaw | 8.99 [2.21] | 9.46 [1.35] | +0.47 | [-0.22, +1.01] | < 0.0002 | Equivalent |
| Windows Intel iGPU | Regime B (Warm) | W5 | Node Minimal vs PicoClaw | 39.77 [2.06] | 40.60 [2.04] | +0.83 | [-0.31, +1.58] | < 0.0002 | Equivalent |

> **Table 7 Notes (Fixed-SESOI Moving Block Bootstrap TOST; M1--M5):** Evaluates inter-session replication of $\Delta T_{\text{orch}} = T_{\text{orch}}(\text{Runtime}) - T_{\text{orch}}(\text{PicoClaw})$ across all 4 platforms and workloads W1--W5 using Moving Block Bootstrap (block size $b=3$, $B=5{,}000$ resamples; Künsch 1989) to preserve lag-1 serial dependence, tested against a **fixed, pre-specified data-independent SESOI of $\pm 5.0\text{ ms}$** ($<0.2\%$ of Regime A task duration). Exact order-statistic **90% MBB CIs** align mathematically with one-sided $\alpha = 0.05$ TOST under the standardized 3-state decision rule (Schuirmann 1987; Lakens 2017): `Equivalent` (90% CI entirely inside $[-5.0, +5.0]\text{ ms}$, $p_{\text{TOST}} < 0.05$), `Different` (90% CI wholly outside $[-5.0, +5.0]\text{ ms}$), or `Inconclusive` (90% CI straddles the SESOI boundary). Across **95 valid pairs** (**7 confounded W5 `python_native` pairs excluded per M1**): **76 (80.0%)** are `Equivalent`, **0 (0.0%)** are `Different`, and **19 (20.0%)** are `Inconclusive` (concentrated in 10-turn W4 multi-step loops and Windows `python_native` startup variance).
