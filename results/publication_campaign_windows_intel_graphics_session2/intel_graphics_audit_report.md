# Windows Intel Graphics Dedicated Campaign Audit Report

- **Hardware:** `MSI Z97 XPOWER AC (MS-7914) | Intel(R) Core(TM) i7-4790K CPU @ 4.00GHz (4C/8T) | 15.88 GiB Shared RAM | Intel(R) HD Graphics 4600 (driver 20.19.15.4531, iGPU UMA, no dGPU)`
- **OS:** `Microsoft Windows 10 Pro 22H2 (Build 19045.6466, kernel 10.0.19041.6456, 64 bits)`
- **Execution Backend / Offload:** `llama.cpp_cpu_avx2_intel_igpu_host` (`-ngl 0`)
- **Zero-Mock & Zero-NVML Compliance:** Verified (`nvidia-smi` / NVML never invoked; unavailable user-mode counters explicitly recorded as `N/A`).

## Regime B (Warm KV-Cache) Summary

| Workload | Arm | n | $T_{\text{task}}$ Med (ms) | $T_{\text{orch}}$ Med (ms) | Peak Phys (MB) | Cache Hit % | W5 Score |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| W2 | `bun_minimal` | 30 | 4882.081 | 23.608 | 23.678 | 100.0% | N/A |
| W2 | `neural_baseline` | 30 | 4548.935 | 0.0 | 0.0 | 100.0% | N/A |
| W5 | `neural_baseline` | 30 | 5302.842 | 0.0 | 0.0 | 100.0% | N/A |
| W2 | `openclaw_full` | 30 | 11670.772 | 68.8 | 54.656 | 100.0% | N/A |
| W2 | `openclaw_minimal` | 30 | 4946.722 | 56.802 | 56.045 | 100.0% | N/A |
| W5 | `openclaw_minimal` | 30 | 5684.131 | 51.297 | 53.52 | 100.0% | N/A |
| W2 | `picoclaw` | 30 | 4833.18 | 13.784 | 8.227 | 100.0% | N/A |
| W5 | `picoclaw` | 30 | 6415.238 | 10.73 | 7.324 | 100.0% | N/A |
| W2 | `python_native` | 30 | 4890.5 | 46.23 | 34.953 | 100.0% | N/A |
| W5 | `python_native` | 30 | 3745.749 | 70.995 | 62.588 | 100.0% | 3.0 |

## Regime A (Cold Prefill) Summary

| Workload | Arm | n | $T_{\text{task}}$ Med (ms) | $T_{\text{orch}}$ Med (ms) | Peak Phys (MB) | Cache Hit % | W5 Score |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| W2 | `bun_minimal` | 30 | 53454.838 | 23.937 | 23.66 | 0.0% | N/A |
| W2 | `neural_baseline` | 30 | 51509.895 | 0.0 | 0.0 | 0.0% | N/A |
| W5 | `neural_baseline` | 30 | 54271.7 | 0.0 | 0.0 | 0.0% | N/A |
| W2 | `openclaw_full` | 30 | 226002.083 | 69.823 | 54.838 | 0.0% | N/A |
| W2 | `openclaw_minimal` | 30 | 53205.93 | 57.733 | 54.734 | 0.0% | N/A |
| W5 | `openclaw_minimal` | 30 | 49560.758 | 51.289 | 52.152 | 0.0% | N/A |
| W2 | `picoclaw` | 30 | 53338.497 | 14.3 | 8.246 | 0.0% | N/A |
| W5 | `picoclaw` | 30 | 56557.787 | 11.256 | 7.316 | 0.0% | N/A |
| W2 | `python_native` | 30 | 53429.5 | 44.231 | 34.924 | 0.0% | N/A |
| W5 | `python_native` | 30 | 30761.266 | 114.38 | 62.613 | 0.0% | 3.0 |
