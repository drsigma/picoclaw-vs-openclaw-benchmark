# Windows Intel Graphics Dedicated Campaign Audit Report

- **Hardware:** `MSI Z97 XPOWER AC (MS-7914) | Intel(R) Core(TM) i7-4790K CPU @ 4.00GHz (4C/8T) | 15.88 GiB Shared RAM | Intel(R) HD Graphics 4600 (driver 20.19.15.4531, iGPU UMA, no dGPU)`
- **OS:** `Microsoft Windows 10 Pro 22H2 (Build 19045.6466, kernel 10.0.19041.6456, 64 bits)`
- **Execution Backend / Offload:** `llama.cpp_cpu_avx2_intel_igpu_host` (`-ngl 0`)
- **Zero-Mock & Zero-NVML Compliance:** Verified (`nvidia-smi` / NVML never invoked; unavailable user-mode counters explicitly recorded as `N/A`).

## Regime B (Warm KV-Cache) Summary

| Workload | Arm | n | $T_{\text{task}}$ Med (ms) | $T_{\text{orch}}$ Med (ms) | Peak Phys (MB) | Cache Hit % | W5 Score |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| W2 | `bun_minimal` | 30 | 5017.58 | 23.188 | 23.691 | 100.0% | N/A |
| W2 | `neural_baseline` | 30 | 4701.833 | 0.0 | 0.0 | 100.0% | N/A |
| W5 | `neural_baseline` | 30 | 5271.65 | 0.0 | 0.0 | 96.67% | N/A |
| W2 | `openclaw_full` | 30 | 11819.537 | 68.962 | 54.715 | 100.0% | N/A |
| W2 | `openclaw_minimal` | 30 | 4894.065 | 56.801 | 56.084 | 100.0% | N/A |
| W5 | `openclaw_minimal` | 30 | 5671.657 | 50.817 | 53.521 | 100.0% | N/A |
| W2 | `picoclaw` | 30 | 5036.507 | 14.085 | 8.279 | 100.0% | N/A |
| W5 | `picoclaw` | 30 | 6280.329 | 10.914 | 7.361 | 100.0% | N/A |
| W2 | `python_native` | 30 | 5039.0 | 43.752 | 34.988 | 100.0% | N/A |
| W5 | `python_native` | 30 | 3733.717 | 71.984 | 62.559 | 100.0% | 3.0 |

## Regime A (Cold Prefill) Summary

| Workload | Arm | n | $T_{\text{task}}$ Med (ms) | $T_{\text{orch}}$ Med (ms) | Peak Phys (MB) | Cache Hit % | W5 Score |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| W2 | `bun_minimal` | 30 | 53564.676 | 23.697 | 23.646 | 0.0% | N/A |
| W2 | `neural_baseline` | 30 | 51817.812 | 0.0 | 0.0 | 0.0% | N/A |
| W5 | `neural_baseline` | 30 | 54282.971 | 0.0 | 0.0 | 0.0% | N/A |
| W2 | `openclaw_full` | 30 | 226696.862 | 68.893 | 54.764 | 0.0% | N/A |
| W2 | `openclaw_minimal` | 30 | 53505.916 | 57.86 | 54.709 | 0.0% | N/A |
| W5 | `openclaw_minimal` | 30 | 50064.299 | 51.303 | 52.186 | 0.0% | N/A |
| W2 | `picoclaw` | 30 | 53505.8 | 14.03 | 8.191 | 0.0% | N/A |
| W5 | `picoclaw` | 30 | 56885.098 | 11.324 | 7.277 | 0.0% | N/A |
| W2 | `python_native` | 30 | 53578.0 | 45.635 | 34.875 | 0.0% | N/A |
| W5 | `python_native` | 30 | 31058.584 | 116.108 | 62.527 | 0.0% | 3.0 |
