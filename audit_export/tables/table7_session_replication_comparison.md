# Table 7: Multi-Platform Dual-Session Empirical Contrast Replication & TOST Equivalence Matrix

| Platform OS | Regime | Workload | Runtime Contrast (vs PicoClaw Go) | Session 1 Δ (ms) [IQR] | Session 2 Δ (ms) [IQR] | Relative Divergence (%) | 95% Bootstrap CI of Diff | TOST Equivalence $p$-value | Replication Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | Regime B (Warm) | W1 | Node Minimal vs PicoClaw | 15.57 [0.75] | 15.37 [0.80] | -1.26% | [-0.31, +2.25] | 8.012e-08 | Equivalence Proven ($p < 0.05$) |
| macOS ARM64 (M4) | Regime B (Warm) | W1 | PythonNative vs PicoClaw | 6.86 [0.54] | 6.74 [0.76] | -1.76% | [-0.23, +0.28] | 3.123e-42 | Equivalence Proven ($p < 0.05$) |
| macOS ARM64 (M4) | Regime B (Warm) | W2 | Node Minimal vs PicoClaw | 14.80 [0.82] | 14.89 [0.70] | +0.63% | [-0.09, +0.48] | 3.397e-38 | Equivalence Proven ($p < 0.05$) |
| macOS ARM64 (M4) | Regime B (Warm) | W2 | PythonNative vs PicoClaw | 6.42 [0.64] | 6.33 [0.76] | -1.48% | [-0.34, +0.25] | 9.114e-39 | Equivalence Proven ($p < 0.05$) |
| macOS ARM64 (M4) | Regime B (Warm) | W3 | Node Minimal vs PicoClaw | 0.35 [2.50] | 0.78 [3.81] | +124.64% | [-0.65, +2.70] | 2.123e-05 | Equivalence Proven ($p < 0.05$) |
| macOS ARM64 (M4) | Regime B (Warm) | W3 | PythonNative vs PicoClaw | -13.17 [2.89] | -12.92 [1.79] | -1.93% | [-1.08, +0.93] | 1.643e-13 | Equivalence Proven ($p < 0.05$) |
| macOS ARM64 (M4) | Regime B (Warm) | W4 | Node Minimal vs PicoClaw | 15.00 [2.22] | 14.97 [3.70] | -0.18% | [-0.52, +2.58] | 4.703e-06 | Equivalence Proven ($p < 0.05$) |
| macOS ARM64 (M4) | Regime B (Warm) | W4 | PythonNative vs PicoClaw | 3.98 [3.18] | 3.57 [3.87] | -10.29% | [-2.92, +0.40] | 2.921e-05 | Equivalence Proven ($p < 0.05$) |
| macOS ARM64 (M4) | Regime B (Warm) | W5 | Node Minimal vs PicoClaw | 15.29 [0.68] | 15.10 [0.86] | -1.24% | [-0.53, -0.03] | 5.887e-41 | Equivalence Proven ($p < 0.05$) |
| macOS ARM64 (M4) | Regime B (Warm) | W5 | PythonNative vs PicoClaw | 5.55 [0.28] | 857.44 [29.67] | +15360.46% | [+845.09, +856.79] | 1.000e+00 | Divergence Detected |
| Linux x86_64 | Regime A (Cold) | W1 | Node Minimal vs PicoClaw | 23.92 [2.03] | 23.65 [1.91] | -1.13% | [-44.71, +62.15] | 5.437e-01 | Replicated ($|\Delta| < 10\%$) |
| Linux x86_64 | Regime A (Cold) | W1 | Node Full vs PicoClaw | 29.33 [2.46] | 28.34 [1.94] | -3.38% | [-42.64, +39.14] | 4.616e-01 | Replicated ($|\Delta| < 10\%$) |
| Linux x86_64 | Regime A (Cold) | W1 | PythonNative vs PicoClaw | 9.67 [4.32] | 10.84 [4.11] | +12.14% | [-51.64, +55.66] | 4.691e-01 | Divergence Detected |
| Linux x86_64 | Regime A (Cold) | W1 | Bun Minimal vs PicoClaw | 0.52 [1.74] | 0.56 [1.70] | +7.09% | [-38.06, +42.55] | 4.186e-01 | Replicated ($|\Delta| < 10\%$) |
| Linux x86_64 | Regime A (Cold) | W2 | Node Minimal vs PicoClaw | 24.44 [1.79] | 23.09 [2.55] | -5.52% | [-66.99, +63.94] | 4.695e-01 | Replicated ($|\Delta| < 10\%$) |
| Linux x86_64 | Regime A (Cold) | W2 | Node Full vs PicoClaw | 28.58 [2.04] | 27.79 [2.53] | -2.77% | [-55.65, +53.02] | 4.583e-01 | Replicated ($|\Delta| < 10\%$) |
| Linux x86_64 | Regime A (Cold) | W2 | PythonNative vs PicoClaw | 9.93 [3.13] | 8.88 [3.25] | -10.57% | [-56.19, +54.22] | 4.655e-01 | Divergence Detected |
| Linux x86_64 | Regime A (Cold) | W2 | Bun Minimal vs PicoClaw | -0.24 [2.68] | -0.82 [3.37] | +244.90% | [-45.52, +87.66] | 6.682e-01 | Divergence Detected |
| Linux x86_64 | Regime A (Cold) | W3 | Node Minimal vs PicoClaw | 12.50 [4.80] | 11.35 [4.29] | -9.19% | [-0.96, +54.51] | 8.718e-01 | Replicated ($|\Delta| < 10\%$) |
| Linux x86_64 | Regime A (Cold) | W3 | Node Full vs PicoClaw | 17.01 [3.60] | 17.35 [4.21] | +2.01% | [-4.02, +30.74] | 6.435e-01 | Replicated ($|\Delta| < 10\%$) |
| Linux x86_64 | Regime A (Cold) | W3 | PythonNative vs PicoClaw | -10.42 [8.41] | -10.07 [6.28] | -3.32% | [-15.34, +82.51] | 8.584e-01 | Replicated ($|\Delta| < 10\%$) |
| Linux x86_64 | Regime A (Cold) | W3 | Bun Minimal vs PicoClaw | -16.54 [5.76] | -15.78 [3.99] | -4.57% | [-2.15, +32.96] | 7.123e-01 | Replicated ($|\Delta| < 10\%$) |
| Linux x86_64 | Regime A (Cold) | W4 | Node Minimal vs PicoClaw | 22.40 [7.48] | 24.25 [8.74] | +8.29% | [-28.47, +34.61] | 4.564e-01 | Replicated ($|\Delta| < 10\%$) |
| Linux x86_64 | Regime A (Cold) | W4 | Node Full vs PicoClaw | 76.39 [8.46] | 73.19 [8.52] | -4.18% | [-67.88, +18.88] | 7.077e-01 | Replicated ($|\Delta| < 10\%$) |
| Linux x86_64 | Regime A (Cold) | W4 | PythonNative vs PicoClaw | 1.54 [6.58] | 3.77 [8.39] | +143.97% | [-31.75, +47.52] | 4.663e-01 | Divergence Detected |
| Linux x86_64 | Regime A (Cold) | W4 | Bun Minimal vs PicoClaw | -16.11 [8.26] | -13.78 [6.54] | -14.47% | [-64.92, +47.48] | 5.417e-01 | Divergence Detected |
| Linux x86_64 | Regime A (Cold) | W5 | Node Minimal vs PicoClaw | 23.81 [1.99] | 23.24 [1.26] | -2.38% | [-1.37, +31.41] | 6.703e-01 | Replicated ($|\Delta| < 10\%$) |
| Linux x86_64 | Regime A (Cold) | W5 | Node Full vs PicoClaw | 29.52 [1.53] | 28.93 [2.15] | -2.00% | [-1.12, +0.58] | 4.045e-15 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime A (Cold) | W5 | PythonNative vs PicoClaw | 12.28 [5.50] | 1477.88 [49.56] | +11936.37% | [+955.34, +1405.75] | 1.000e+00 | Divergence Detected |
| Linux x86_64 | Regime A (Cold) | W5 | Bun Minimal vs PicoClaw | 0.74 [1.14] | 0.71 [1.58] | -3.51% | [-0.60, +0.51] | 1.583e-24 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W1 | Node Minimal vs PicoClaw | 22.83 [1.56] | 22.96 [1.66] | +0.59% | [-1.07, +1.02] | 3.887e-14 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W1 | Node Full vs PicoClaw | 28.46 [1.81] | 28.61 [1.62] | +0.54% | [-0.80, +0.97] | 3.978e-15 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W1 | PythonNative vs PicoClaw | 10.67 [4.25] | 10.46 [2.29] | -1.94% | [-1.39, +0.92] | 4.793e-11 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W1 | Bun Minimal vs PicoClaw | -0.26 [1.48] | 0.51 [1.46] | -298.59% | [-0.35, +0.64] | 5.621e-26 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W2 | Node Minimal vs PicoClaw | 22.88 [1.60] | 23.12 [1.80] | +1.06% | [-0.60, +0.69] | 5.387e-21 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W2 | Node Full vs PicoClaw | 27.40 [1.29] | 27.97 [1.73] | +2.06% | [-0.36, +0.93] | 2.461e-20 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W2 | PythonNative vs PicoClaw | 10.74 [3.01] | 11.45 [3.50] | +6.66% | [-1.41, +0.90] | 1.238e-10 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W2 | Bun Minimal vs PicoClaw | -0.39 [1.44] | 0.11 [1.42] | -127.86% | [-0.37, +0.77] | 1.080e-23 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W3 | Node Minimal vs PicoClaw | 11.01 [3.89] | 11.26 [4.31] | +2.24% | [-1.36, +1.43] | 2.071e-09 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W3 | Node Full vs PicoClaw | 15.12 [3.45] | 16.96 [3.93] | +12.11% | [-0.24, +2.41] | 2.163e-07 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W3 | PythonNative vs PicoClaw | -12.43 [4.19] | -12.57 [3.62] | +1.06% | [-1.53, +2.47] | 1.335e-05 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W3 | Bun Minimal vs PicoClaw | -15.44 [5.18] | -16.33 [4.16] | +5.74% | [-1.49, +1.94] | 6.291e-07 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W4 | Node Minimal vs PicoClaw | 22.57 [6.68] | 21.73 [9.81] | -3.70% | [-4.02, +2.40] | 1.132e-02 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W4 | Node Full vs PicoClaw | 72.90 [6.90] | 75.30 [7.37] | +3.30% | [-0.29, +5.50] | 6.056e-07 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W4 | PythonNative vs PicoClaw | 0.91 [7.39] | -2.52 [6.70] | -376.26% | [-5.85, +0.52] | 8.442e-02 | Divergence Detected |
| Linux x86_64 | Regime B (Warm) | W4 | Bun Minimal vs PicoClaw | -16.65 [5.27] | -19.44 [4.37] | +16.75% | [-3.70, +0.51] | 7.905e-04 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W5 | Node Minimal vs PicoClaw | 23.10 [1.48] | 23.34 [1.91] | +1.00% | [-0.90, +0.56] | 6.217e-19 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W5 | Node Full vs PicoClaw | 28.25 [1.73] | 28.54 [2.11] | +1.01% | [-0.72, +1.35] | 3.703e-13 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W5 | PythonNative vs PicoClaw | 1411.46 [35.55] | 1422.09 [18.48] | +0.75% | [+0.17, +24.09] | 1.369e-38 | Equivalence Proven ($p < 0.05$) |
| Linux x86_64 | Regime B (Warm) | W5 | Bun Minimal vs PicoClaw | 0.56 [0.96] | 0.68 [1.92] | +21.85% | [-0.64, +0.43] | 4.308e-25 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime A (Cold) | W1 | Node Minimal vs PicoClaw | 27.90 [3.41] | 28.26 [5.00] | +1.26% | [-65.86, +33.20] | 6.164e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows 11 NVIDIA | Regime A (Cold) | W1 | Node Full vs PicoClaw | 34.57 [3.30] | 34.28 [4.10] | -0.85% | [-29.56, +19.15] | 4.708e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows 11 NVIDIA | Regime A (Cold) | W1 | PythonNative vs PicoClaw | 22.09 [18.42] | 14.38 [21.90] | -34.89% | [-85.67, +55.17] | 5.369e-01 | Divergence Detected |
| Windows 11 NVIDIA | Regime A (Cold) | W1 | Bun Minimal vs PicoClaw | 4.05 [2.91] | 5.26 [4.82] | +30.05% | [-50.00, +60.20] | 4.366e-01 | Divergence Detected |
| Windows 11 NVIDIA | Regime A (Cold) | W2 | Node Minimal vs PicoClaw | 27.65 [5.05] | 29.56 [2.26] | +6.93% | [-44.47, +43.72] | 4.154e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows 11 NVIDIA | Regime A (Cold) | W2 | Node Full vs PicoClaw | 35.30 [3.78] | 36.96 [1.85] | +4.71% | [-51.78, +36.54] | 4.952e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows 11 NVIDIA | Regime A (Cold) | W2 | PythonNative vs PicoClaw | 13.86 [8.42] | 15.23 [17.64] | +9.91% | [-39.62, +50.85] | 5.019e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows 11 NVIDIA | Regime A (Cold) | W2 | Bun Minimal vs PicoClaw | 3.75 [4.58] | 5.47 [3.38] | +45.73% | [-59.17, +64.94] | 4.531e-01 | Divergence Detected |
| Windows 11 NVIDIA | Regime A (Cold) | W3 | Node Minimal vs PicoClaw | 25.09 [6.58] | 24.94 [5.63] | -0.58% | [-51.44, +50.71] | 4.355e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows 11 NVIDIA | Regime A (Cold) | W3 | Node Full vs PicoClaw | 30.48 [5.28] | 32.02 [5.65] | +5.04% | [-55.72, +47.45] | 4.596e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows 11 NVIDIA | Regime A (Cold) | W3 | PythonNative vs PicoClaw | 2.14 [12.30] | 5.59 [14.90] | +160.86% | [-37.17, +51.17] | 4.526e-01 | Divergence Detected |
| Windows 11 NVIDIA | Regime A (Cold) | W3 | Bun Minimal vs PicoClaw | -11.27 [6.49] | -9.79 [4.20] | -13.16% | [-71.25, +58.57] | 4.861e-01 | Divergence Detected |
| Windows 11 NVIDIA | Regime A (Cold) | W4 | Node Minimal vs PicoClaw | 56.40 [9.98] | 56.15 [11.01] | -0.44% | [-43.51, +32.51] | 3.676e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows 11 NVIDIA | Regime A (Cold) | W4 | Node Full vs PicoClaw | 151.39 [11.40] | 153.95 [14.19] | +1.69% | [-9.80, +13.96] | 1.499e-03 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime A (Cold) | W4 | PythonNative vs PicoClaw | 135.11 [37.63] | 150.29 [38.30] | +11.23% | [-42.60, +60.10] | 2.934e-01 | Divergence Detected |
| Windows 11 NVIDIA | Regime A (Cold) | W4 | Bun Minimal vs PicoClaw | -2.59 [8.85] | -1.86 [10.93] | -28.48% | [-28.61, +52.85] | 6.002e-01 | Divergence Detected |
| Windows 11 NVIDIA | Regime A (Cold) | W5 | Node Minimal vs PicoClaw | 26.96 [2.72] | 26.76 [3.24] | -0.74% | [-31.17, +37.02] | 4.327e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows 11 NVIDIA | Regime A (Cold) | W5 | Node Full vs PicoClaw | 34.46 [3.62] | 34.83 [3.90] | +1.08% | [-21.79, +40.38] | 5.354e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows 11 NVIDIA | Regime A (Cold) | W5 | PythonNative vs PicoClaw | 133.79 [76.12] | 130.15 [87.25] | -2.72% | [-240.05, +249.60] | 4.118e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows 11 NVIDIA | Regime A (Cold) | W5 | Bun Minimal vs PicoClaw | 3.54 [3.56] | 3.98 [2.97] | +12.35% | [-33.46, +32.97] | 4.224e-01 | Divergence Detected |
| Windows 11 NVIDIA | Regime B (Warm) | W1 | Node Minimal vs PicoClaw | 27.91 [1.35] | 27.67 [1.42] | -0.84% | [-1.33, -0.18] | 2.333e-20 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W1 | Node Full vs PicoClaw | 35.48 [1.76] | 34.74 [1.83] | -2.08% | [-1.43, -0.35] | 7.424e-22 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W1 | PythonNative vs PicoClaw | 17.23 [9.86] | 19.31 [10.23] | +12.09% | [-3.36, +5.85] | 7.300e-02 | Divergence Detected |
| Windows 11 NVIDIA | Regime B (Warm) | W1 | Bun Minimal vs PicoClaw | 3.88 [2.33] | 3.57 [2.53] | -8.09% | [-0.82, +0.61] | 1.130e-18 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W2 | Node Minimal vs PicoClaw | 29.94 [1.31] | 30.00 [1.61] | +0.19% | [-0.28, +1.00] | 7.822e-20 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W2 | Node Full vs PicoClaw | 36.51 [2.34] | 36.53 [2.32] | +0.05% | [-1.46, +0.14] | 3.434e-17 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W2 | PythonNative vs PicoClaw | 19.54 [13.05] | 18.41 [13.74] | -5.77% | [-7.47, +1.35] | 1.805e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows 11 NVIDIA | Regime B (Warm) | W2 | Bun Minimal vs PicoClaw | 4.84 [2.53] | 4.89 [1.89] | +0.90% | [-0.95, +0.80] | 1.909e-16 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W3 | Node Minimal vs PicoClaw | 22.41 [4.22] | 23.46 [2.22] | +4.65% | [+0.25, +3.01] | 3.587e-06 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W3 | Node Full vs PicoClaw | 30.85 [3.45] | 29.71 [4.03] | -3.69% | [-1.79, +0.91] | 3.026e-08 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W3 | PythonNative vs PicoClaw | 0.60 [11.45] | 0.56 [10.73] | -5.27% | [-3.82, +5.42] | 4.666e-02 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W3 | Bun Minimal vs PicoClaw | -12.31 [2.83] | -11.50 [3.79] | -6.61% | [-1.16, +1.46] | 1.293e-09 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W4 | Node Minimal vs PicoClaw | 51.15 [5.43] | 51.41 [5.90] | +0.50% | [-0.90, +4.14] | 1.630e-05 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W4 | Node Full vs PicoClaw | 128.24 [3.04] | 134.18 [5.43] | +4.63% | [+3.87, +8.51] | 9.927e-16 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W4 | PythonNative vs PicoClaw | 136.76 [28.46] | 149.11 [35.79] | +9.03% | [-6.31, +18.54] | 1.765e-02 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W4 | Bun Minimal vs PicoClaw | -2.67 [5.83] | -3.18 [4.48] | +18.95% | [-2.34, +1.89] | 4.806e-05 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W5 | Node Minimal vs PicoClaw | 27.28 [2.08] | 27.40 [2.16] | +0.44% | [-0.89, +0.61] | 2.102e-18 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W5 | Node Full vs PicoClaw | 34.56 [1.37] | 34.14 [1.76] | -1.19% | [-0.87, +0.59] | 2.737e-20 | Equivalence Proven ($p < 0.05$) |
| Windows 11 NVIDIA | Regime B (Warm) | W5 | PythonNative vs PicoClaw | 13.94 [15.04] | 20.91 [14.28] | +50.00% | [-230.72, +239.57] | 4.486e-01 | Divergence Detected |
| Windows 11 NVIDIA | Regime B (Warm) | W5 | Bun Minimal vs PicoClaw | 3.14 [1.92] | 3.60 [2.30] | +14.46% | [-0.94, +0.97] | 6.443e-16 | Equivalence Proven ($p < 0.05$) |
| Windows Intel iGPU | Regime A (Cold) | W2 | Node Minimal vs PicoClaw | 43.12 [4.01] | 42.48 [6.08] | -1.49% | [-32.85, +40.64] | 4.055e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows Intel iGPU | Regime A (Cold) | W2 | Node Full vs PicoClaw | 54.37 [3.28] | 54.94 [6.01] | +1.06% | [-33.36, +34.72] | 3.031e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows Intel iGPU | Regime A (Cold) | W2 | PythonNative vs PicoClaw | 30.78 [15.02] | 27.40 [14.89] | -10.97% | [-34.61, +23.61] | 4.950e-01 | Divergence Detected |
| Windows Intel iGPU | Regime A (Cold) | W2 | Bun Minimal vs PicoClaw | 9.55 [2.40] | 9.72 [4.85] | +1.79% | [-36.01, +31.34] | 4.048e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows Intel iGPU | Regime A (Cold) | W5 | Node Minimal vs PicoClaw | 39.77 [2.40] | 39.44 [2.79] | -0.81% | [-35.18, +35.78] | 4.363e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows Intel iGPU | Regime A (Cold) | W5 | PythonNative vs PicoClaw | 102.63 [25.18] | 101.71 [10.38] | -0.89% | [-30.81, +26.59] | 2.292e-01 | Replicated ($|\Delta| < 10\%$) |
| Windows Intel iGPU | Regime B (Warm) | W2 | Node Minimal vs PicoClaw | 42.60 [2.34] | 43.45 [2.80] | +2.00% | [-0.61, +1.39] | 9.367e-17 | Equivalence Proven ($p < 0.05$) |
| Windows Intel iGPU | Regime B (Warm) | W2 | Node Full vs PicoClaw | 54.74 [3.17] | 54.98 [2.40] | +0.44% | [-1.98, +1.24] | 3.603e-13 | Equivalence Proven ($p < 0.05$) |
| Windows Intel iGPU | Regime B (Warm) | W2 | PythonNative vs PicoClaw | 29.02 [8.26] | 32.56 [8.79] | +12.20% | [-1.19, +5.95] | 1.029e-01 | Divergence Detected |
| Windows Intel iGPU | Regime B (Warm) | W2 | Bun Minimal vs PicoClaw | 8.99 [2.21] | 9.46 [1.35] | +5.22% | [-0.16, +1.24] | 2.538e-18 | Equivalence Proven ($p < 0.05$) |
| Windows Intel iGPU | Regime B (Warm) | W5 | Node Minimal vs PicoClaw | 39.77 [2.06] | 40.60 [2.04] | +2.08% | [-0.71, +1.53] | 3.508e-14 | Equivalence Proven ($p < 0.05$) |
| Windows Intel iGPU | Regime B (Warm) | W5 | PythonNative vs PicoClaw | 61.50 [4.82] | 59.97 [2.55] | -2.49% | [-3.51, +1.68] | 2.428e-08 | Equivalence Proven ($p < 0.05$) |

> **Table 7 Notes (Dual-Session Replication & TOST Summary):** Evaluates empirical contrasts $\Delta T_{\text{orch}} = T_{\text{orch}}(\text{Runtime}) - T_{\text{orch}}(\text{PicoClaw})$ across independent experimental sessions across all 4 platforms and workloads W1--W5 using Two One-Sided Tests (`ttost_ind`, equivalence margin $\max(5.0\text{ ms}, 15\%\cdot|\bar{\Delta}_1|)$). Across 102 evaluated pairs: **53 (52.0%)** achieved `Equivalence Proven` ($p < 0.05$), **29 (28.4%)** met `Replicated` ($|\Delta| < 10\%$), and **20 (19.6%)** showed `Divergence Detected` (principally `PythonNative` in W5 due to cross-session dynamic LangChain import/startup variability).
