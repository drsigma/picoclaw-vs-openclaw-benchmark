# Table 7: Multi-Platform Dual-Session Empirical Contrast Replication & Block-Bootstrap TOST Equivalence Matrix

| Platform OS | Regime | Workload | Runtime Contrast (vs PicoClaw Go) | Session 1 Δ (ms) [IQR] | Session 2 Δ (ms) [IQR] | Diff $\Delta_2 - \Delta_1$ (ms) | 90% MBB CI ($b=3$) (ms) | $p_{\text{TOST}}$ | $p_{\text{TOST, adj}}$ (Holm) | Equivalence Status (Lakens 2017) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | Regime B (Warm) | W1 | Node Minimal vs PicoClaw | 15.57 [0.75] | 15.37 [0.80] | -0.20 | [-0.42, +0.03] | < 0.0001 | < 0.0001 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W1 | PythonNative vs PicoClaw | 6.86 [0.54] | 6.74 [0.76] | -0.12 | [-0.23, +0.24] | < 0.0001 | < 0.0001 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W2 | Node Minimal vs PicoClaw | 14.80 [0.82] | 14.89 [0.70] | +0.09 | [-0.25, +0.37] | < 0.0001 | < 0.0001 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W2 | PythonNative vs PicoClaw | 6.42 [0.64] | 6.33 [0.76] | -0.09 | [-0.35, +0.19] | < 0.0001 | < 0.0001 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W3 | Node Minimal vs PicoClaw | 0.35 [2.50] | 0.78 [3.81] | +0.43 | [+0.06, +1.34] | < 0.0001 | < 0.0001 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W3 | PythonNative vs PicoClaw | -13.17 [2.89] | -12.92 [1.79] | +0.25 | [-0.54, +0.83] | < 0.0001 | < 0.0001 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W4 | Node Minimal vs PicoClaw | 15.00 [2.22] | 14.97 [3.70] | -0.03 | [-1.13, +1.04] | < 0.0001 | < 0.0001 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W4 | PythonNative vs PicoClaw | 3.98 [3.18] | 3.57 [3.87] | -0.41 | [-1.72, +0.77] | < 0.0001 | < 0.0001 | Equivalent |
| macOS ARM64 (M4) | Regime B (Warm) | W5 | Node Minimal vs PicoClaw | 15.29 [0.68] | 15.10 [0.86] | -0.19 | [-0.49, +0.04] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W1 | Node Minimal vs PicoClaw | 23.92 [2.03] | 23.65 [1.91] | -0.27 | [-1.24, +0.62] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W1 | Node Full vs PicoClaw | 29.33 [2.46] | 28.34 [1.94] | -0.99 | [-1.62, -0.31] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W1 | PythonNative vs PicoClaw | 9.67 [4.32] | 10.84 [4.11] | +1.17 | [-0.41, +2.45] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W1 | Bun Minimal vs PicoClaw | 0.52 [1.74] | 0.56 [1.70] | +0.04 | [-0.71, +0.49] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W2 | Node Minimal vs PicoClaw | 24.44 [1.79] | 23.09 [2.55] | -1.35 | [-2.23, -0.31] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W2 | Node Full vs PicoClaw | 28.58 [2.04] | 27.79 [2.53] | -0.79 | [-1.70, -0.21] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W2 | PythonNative vs PicoClaw | 9.93 [3.13] | 8.88 [3.25] | -1.05 | [-2.22, +0.06] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W2 | Bun Minimal vs PicoClaw | -0.24 [2.68] | -0.82 [3.37] | -0.58 | [-1.65, +0.75] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W3 | Node Minimal vs PicoClaw | 12.50 [4.80] | 11.35 [4.29] | -1.15 | [-2.32, +1.73] | 0.0019 | 0.0475 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W3 | Node Full vs PicoClaw | 17.01 [3.60] | 17.35 [4.21] | +0.34 | [-1.14, +1.78] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W3 | PythonNative vs PicoClaw | -10.42 [8.41] | -10.07 [6.28] | +0.35 | [-2.70, +3.34] | 0.0088 | 0.1936 | Inconclusive |
| Linux x86_64 | Regime A (Cold) | W3 | Bun Minimal vs PicoClaw | -16.54 [5.76] | -15.78 [3.99] | +0.76 | [-0.69, +3.00] | 0.0001 | 0.0031 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W4 | Node Minimal vs PicoClaw | 22.40 [7.48] | 24.25 [8.74] | +1.86 | [-1.34, +6.09] | 0.1244 | 1.0000 | Inconclusive |
| Linux x86_64 | Regime A (Cold) | W4 | Node Full vs PicoClaw | 76.39 [8.46] | 73.19 [8.52] | -3.20 | [-5.29, -0.43] | 0.0654 | 1.0000 | Inconclusive |
| Linux x86_64 | Regime A (Cold) | W4 | PythonNative vs PicoClaw | 1.54 [6.58] | 3.77 [8.39] | +2.22 | [+0.81, +6.04] | 0.1568 | 1.0000 | Inconclusive |
| Linux x86_64 | Regime A (Cold) | W4 | Bun Minimal vs PicoClaw | -16.11 [8.26] | -13.78 [6.54] | +2.33 | [-2.23, +5.76] | 0.0900 | 1.0000 | Inconclusive |
| Linux x86_64 | Regime A (Cold) | W5 | Node Minimal vs PicoClaw | 23.81 [1.99] | 23.24 [1.26] | -0.57 | [-1.01, -0.02] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W5 | Node Full vs PicoClaw | 29.52 [1.53] | 28.93 [2.15] | -0.59 | [-1.16, +0.02] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime A (Cold) | W5 | Bun Minimal vs PicoClaw | 0.74 [1.14] | 0.71 [1.58] | -0.03 | [-0.29, +0.49] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W1 | Node Minimal vs PicoClaw | 22.83 [1.56] | 22.96 [1.66] | +0.13 | [-0.74, +0.96] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W1 | Node Full vs PicoClaw | 28.46 [1.81] | 28.61 [1.62] | +0.15 | [-0.64, +0.82] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W1 | PythonNative vs PicoClaw | 10.67 [4.25] | 10.46 [2.29] | -0.21 | [-1.97, +1.75] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W1 | Bun Minimal vs PicoClaw | -0.26 [1.48] | 0.51 [1.46] | +0.77 | [-0.14, +1.25] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W2 | Node Minimal vs PicoClaw | 22.88 [1.60] | 23.12 [1.80] | +0.24 | [-0.45, +0.73] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W2 | Node Full vs PicoClaw | 27.40 [1.29] | 27.97 [1.73] | +0.56 | [-0.11, +0.96] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W2 | PythonNative vs PicoClaw | 10.74 [3.01] | 11.45 [3.50] | +0.71 | [-0.92, +1.40] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W2 | Bun Minimal vs PicoClaw | -0.39 [1.44] | 0.11 [1.42] | +0.50 | [-0.48, +1.08] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W3 | Node Minimal vs PicoClaw | 11.01 [3.89] | 11.26 [4.31] | +0.25 | [-1.41, +2.44] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W3 | Node Full vs PicoClaw | 15.12 [3.45] | 16.96 [3.93] | +1.83 | [-0.43, +2.89] | 0.0001 | 0.0031 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W3 | PythonNative vs PicoClaw | -12.43 [4.19] | -12.57 [3.62] | -0.13 | [-1.17, +1.71] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W3 | Bun Minimal vs PicoClaw | -15.44 [5.18] | -16.33 [4.16] | -0.89 | [-2.77, +1.36] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W4 | Node Minimal vs PicoClaw | 22.57 [6.68] | 21.73 [9.81] | -0.83 | [-5.17, +2.58] | 0.0569 | 1.0000 | Inconclusive |
| Linux x86_64 | Regime B (Warm) | W4 | Node Full vs PicoClaw | 72.90 [6.90] | 75.30 [7.37] | +2.40 | [-1.18, +5.11] | 0.0577 | 1.0000 | Inconclusive |
| Linux x86_64 | Regime B (Warm) | W4 | PythonNative vs PicoClaw | 0.91 [7.39] | -2.52 [6.70] | -3.43 | [-7.61, -1.05] | 0.2694 | 1.0000 | Inconclusive |
| Linux x86_64 | Regime B (Warm) | W4 | Bun Minimal vs PicoClaw | -16.65 [5.27] | -19.44 [4.37] | -2.79 | [-4.13, -0.37] | 0.0046 | 0.1058 | Inconclusive |
| Linux x86_64 | Regime B (Warm) | W5 | Node Minimal vs PicoClaw | 23.10 [1.48] | 23.34 [1.91] | +0.23 | [-0.35, +0.73] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W5 | Node Full vs PicoClaw | 28.25 [1.73] | 28.54 [2.11] | +0.29 | [-0.07, +0.94] | < 0.0001 | < 0.0001 | Equivalent |
| Linux x86_64 | Regime B (Warm) | W5 | Bun Minimal vs PicoClaw | 0.56 [0.96] | 0.68 [1.92] | +0.12 | [-0.44, +0.64] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W1 | Node Minimal vs PicoClaw | 27.90 [3.41] | 28.26 [5.00] | +0.35 | [-1.62, +1.68] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W1 | Node Full vs PicoClaw | 34.57 [3.30] | 34.28 [4.10] | -0.29 | [-1.76, +1.43] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W1 | PythonNative vs PicoClaw | 22.09 [18.42] | 14.38 [21.90] | -7.71 | [-13.67, +2.05] | 0.5539 | 1.0000 | Inconclusive |
| Windows 11 NVIDIA | Regime A (Cold) | W1 | Bun Minimal vs PicoClaw | 4.05 [2.91] | 5.26 [4.82] | +1.22 | [-0.97, +2.28] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W2 | Node Minimal vs PicoClaw | 27.65 [5.05] | 29.56 [2.26] | +1.92 | [-0.14, +3.39] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W2 | Node Full vs PicoClaw | 35.30 [3.78] | 36.96 [1.85] | +1.66 | [+0.13, +2.43] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W2 | PythonNative vs PicoClaw | 13.86 [8.42] | 15.23 [17.64] | +1.37 | [-3.63, +8.09] | 0.1661 | 1.0000 | Inconclusive |
| Windows 11 NVIDIA | Regime A (Cold) | W2 | Bun Minimal vs PicoClaw | 3.75 [4.58] | 5.47 [3.38] | +1.72 | [-0.57, +2.94] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W3 | Node Minimal vs PicoClaw | 25.09 [6.58] | 24.94 [5.63] | -0.15 | [-2.08, +2.07] | 0.0001 | 0.0031 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W3 | Node Full vs PicoClaw | 30.48 [5.28] | 32.02 [5.65] | +1.54 | [-0.38, +2.56] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W3 | PythonNative vs PicoClaw | 2.14 [12.30] | 5.59 [14.90] | +3.45 | [-1.45, +8.46] | 0.3577 | 1.0000 | Inconclusive |
| Windows 11 NVIDIA | Regime A (Cold) | W3 | Bun Minimal vs PicoClaw | -11.27 [6.49] | -9.79 [4.20] | +1.48 | [-2.02, +2.58] | 0.0007 | 0.0189 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W4 | Node Minimal vs PicoClaw | 56.40 [9.98] | 56.15 [11.01] | -0.25 | [-4.76, +2.70] | 0.0419 | 0.8380 | Inconclusive |
| Windows 11 NVIDIA | Regime A (Cold) | W4 | Node Full vs PicoClaw | 151.39 [11.40] | 153.95 [14.19] | +2.56 | [-2.38, +7.66] | 0.2308 | 1.0000 | Inconclusive |
| Windows 11 NVIDIA | Regime A (Cold) | W4 | PythonNative vs PicoClaw | 135.11 [37.63] | 150.29 [38.30] | +15.17 | [-3.85, +34.26] | 0.7806 | 1.0000 | Inconclusive |
| Windows 11 NVIDIA | Regime A (Cold) | W4 | Bun Minimal vs PicoClaw | -2.59 [8.85] | -1.86 [10.93] | +0.74 | [-3.99, +3.64] | 0.0266 | 0.5586 | Inconclusive |
| Windows 11 NVIDIA | Regime A (Cold) | W5 | Node Minimal vs PicoClaw | 26.96 [2.72] | 26.76 [3.24] | -0.20 | [-1.95, +0.95] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W5 | Node Full vs PicoClaw | 34.46 [3.62] | 34.83 [3.90] | +0.37 | [-1.17, +1.44] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime A (Cold) | W5 | Bun Minimal vs PicoClaw | 3.54 [3.56] | 3.98 [2.97] | +0.44 | [-1.05, +1.65] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W1 | Node Minimal vs PicoClaw | 27.91 [1.35] | 27.67 [1.42] | -0.23 | [-0.82, +0.20] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W1 | Node Full vs PicoClaw | 35.48 [1.76] | 34.74 [1.83] | -0.74 | [-1.31, +0.06] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W1 | PythonNative vs PicoClaw | 17.23 [9.86] | 19.31 [10.23] | +2.08 | [-1.18, +5.72] | 0.0769 | 1.0000 | Inconclusive |
| Windows 11 NVIDIA | Regime B (Warm) | W1 | Bun Minimal vs PicoClaw | 3.88 [2.33] | 3.57 [2.53] | -0.31 | [-1.21, +1.04] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W2 | Node Minimal vs PicoClaw | 29.94 [1.31] | 30.00 [1.61] | +0.06 | [-0.59, +0.39] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W2 | Node Full vs PicoClaw | 36.51 [2.34] | 36.53 [2.32] | +0.02 | [-1.30, +0.60] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W2 | PythonNative vs PicoClaw | 19.54 [13.05] | 18.41 [13.74] | -1.13 | [-6.62, +2.87] | 0.1117 | 1.0000 | Inconclusive |
| Windows 11 NVIDIA | Regime B (Warm) | W2 | Bun Minimal vs PicoClaw | 4.84 [2.53] | 4.89 [1.89] | +0.04 | [-0.58, +0.46] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W3 | Node Minimal vs PicoClaw | 22.41 [4.22] | 23.46 [2.22] | +1.04 | [-0.45, +2.62] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W3 | Node Full vs PicoClaw | 30.85 [3.45] | 29.71 [4.03] | -1.14 | [-1.68, +0.17] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W3 | PythonNative vs PicoClaw | 0.60 [11.45] | 0.56 [10.73] | -0.03 | [-6.27, +6.05] | 0.1425 | 1.0000 | Inconclusive |
| Windows 11 NVIDIA | Regime B (Warm) | W3 | Bun Minimal vs PicoClaw | -12.31 [2.83] | -11.50 [3.79] | +0.81 | [-0.78, +1.84] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W4 | Node Minimal vs PicoClaw | 51.15 [5.43] | 51.41 [5.90] | +0.26 | [-1.95, +1.92] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W4 | Node Full vs PicoClaw | 128.24 [3.04] | 134.18 [5.43] | +5.94 | [+4.04, +6.86] | 0.7929 | 1.0000 | Inconclusive |
| Windows 11 NVIDIA | Regime B (Warm) | W4 | PythonNative vs PicoClaw | 136.76 [28.46] | 149.11 [35.79] | +12.35 | [-2.41, +24.69] | 0.8185 | 1.0000 | Inconclusive |
| Windows 11 NVIDIA | Regime B (Warm) | W4 | Bun Minimal vs PicoClaw | -2.67 [5.83] | -3.18 [4.48] | -0.51 | [-2.95, +1.33] | 0.0010 | 0.0260 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W5 | Node Minimal vs PicoClaw | 27.28 [2.08] | 27.40 [2.16] | +0.12 | [-0.91, +0.77] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W5 | Node Full vs PicoClaw | 34.56 [1.37] | 34.14 [1.76] | -0.41 | [-1.08, +0.04] | < 0.0001 | < 0.0001 | Equivalent |
| Windows 11 NVIDIA | Regime B (Warm) | W5 | Bun Minimal vs PicoClaw | 3.14 [1.92] | 3.60 [2.30] | +0.45 | [-0.77, +1.22] | < 0.0001 | < 0.0001 | Equivalent |
| Windows Intel iGPU | Regime A (Cold) | W2 | Node Minimal vs PicoClaw | 43.12 [4.01] | 42.48 [6.08] | -0.64 | [-1.73, +1.66] | 0.0003 | 0.0084 | Equivalent |
| Windows Intel iGPU | Regime A (Cold) | W2 | Node Full vs PicoClaw | 54.37 [3.28] | 54.94 [6.01] | +0.57 | [-1.82, +1.45] | < 0.0001 | < 0.0001 | Equivalent |
| Windows Intel iGPU | Regime A (Cold) | W2 | PythonNative vs PicoClaw | 30.78 [15.02] | 27.40 [14.89] | -3.38 | [-10.53, +4.48] | 0.3750 | 1.0000 | Inconclusive |
| Windows Intel iGPU | Regime A (Cold) | W2 | Bun Minimal vs PicoClaw | 9.55 [2.40] | 9.72 [4.85] | +0.17 | [-0.89, +1.65] | 0.0032 | 0.0768 | Inconclusive |
| Windows Intel iGPU | Regime A (Cold) | W5 | Node Minimal vs PicoClaw | 39.77 [2.40] | 39.44 [2.79] | -0.32 | [-1.09, +0.57] | < 0.0001 | < 0.0001 | Equivalent |
| Windows Intel iGPU | Regime B (Warm) | W2 | Node Minimal vs PicoClaw | 42.60 [2.34] | 43.45 [2.80] | +0.85 | [-0.52, +1.32] | < 0.0001 | < 0.0001 | Equivalent |
| Windows Intel iGPU | Regime B (Warm) | W2 | Node Full vs PicoClaw | 54.74 [3.17] | 54.98 [2.40] | +0.24 | [-0.85, +1.57] | < 0.0001 | < 0.0001 | Equivalent |
| Windows Intel iGPU | Regime B (Warm) | W2 | PythonNative vs PicoClaw | 29.02 [8.26] | 32.56 [8.79] | +3.54 | [+0.90, +7.30] | 0.2985 | 1.0000 | Inconclusive |
| Windows Intel iGPU | Regime B (Warm) | W2 | Bun Minimal vs PicoClaw | 8.99 [2.21] | 9.46 [1.35] | +0.47 | [-0.22, +1.02] | < 0.0001 | < 0.0001 | Equivalent |
| Windows Intel iGPU | Regime B (Warm) | W5 | Node Minimal vs PicoClaw | 39.77 [2.06] | 40.60 [2.04] | +0.83 | [-0.33, +1.59] | < 0.0001 | < 0.0001 | Equivalent |

> **Table 7 Methodological Specification (Fixed-SESOI Moving Block Bootstrap TOST + Holm-Bonferroni; Etapa 2):**
> - **(a) Estimator:** Difference of session medians $\hat{\theta} = \text{median}(c_2) - \text{median}(c_1)$ evaluated against a fixed, pre-specified data-independent SESOI of $\Delta_{\text{SESOI}} = \pm 5.0\text{ ms}$ (practical orchestration jitter bound, $<0.2\%$ of Regime A task duration).
> - **(b) Deviation Unit:** Per-trial paired orchestrator contrasts $c_i = T_{\text{orch}, i}(\text{Runtime}) - T_{\text{orch}, i}(\text{PicoClaw})$ ($n=30$ per session) resampled in contiguous overlapping blocks via Moving Block Bootstrap ($B=10{,}000$ resamples; Künsch 1989) to preserve serial dependence without distorting per-trial median dispersion.
> - **(c) Block-Size Rule:** Primary block size $b = \text{round}(n^{1/3}) = 3$ for $n=30$ trials per session.
> - **(d) Block-Size Sensitivity ($b \in \{2, 3, 5\}$, exported in `audit_export/tost_block_sensitivity.csv`):** Under Holm-Bonferroni FWER control ($p_{\text{TOST, adj}} < 0.05$), all three block lengths yield identical decisions across the 95 valid pairs: $b=2$: **71 `Equivalent` / 24 `Inconclusive` / 0 `Different`** (unadjusted: 76/19/0); $b=3$: **71 / 24 / 0** (unadjusted: 76/19/0); $b=5$: **71 / 24 / 0** (unadjusted: 78/17/0).
> - **Three-State Decision Rule (Schuirmann 1987; Lakens 2017) + Multiple-Comparison Control:** Order-statistic **90% MBB CIs** align with one-sided $\alpha = 0.05$ TOST, combined with Holm-Bonferroni FWER adjustment across all 95 valid pairs (7 confounded W5 `python_native` pairs excluded per M1): `Equivalent` (90% CI entirely inside $[-5.0, +5.0]\text{ ms}$ and $p_{\text{TOST, adj}} < 0.05$: **71 [74.7%]**), `Different` (90% CI wholly outside $[-5.0, +5.0]\text{ ms}$: **0 [0.0%]**), or `Inconclusive` (**24 [25.3%]**, comprising 19 pairs whose 90% CI crosses $\pm 5.0\text{ ms}$ plus 5 pairs failing the Holm-Bonferroni adjusted threshold).
