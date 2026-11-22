# Table 6: Live MCP Transport IPC Ablation (In-Process vs Stdio vs Loopback HTTP)

| Platform | Transport Protocol | Median IPC Dispatch (ms) [IQR] | 95% Bootstrap CI | Overhead vs In-Process |
| :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | Native In-Process Dispatch | 1.384 [0.360] | [1.354, 1.442] | 1.00x |
| macOS ARM64 (M4) | Standard I/O JSON-RPC Pipes | 1.275 [0.799] | [1.238, 1.331] | 0.92x |
| macOS ARM64 (M4) | Loopback HTTP REST Sockets | 2.389 [0.614] | [2.342, 2.432] | 1.73x |
| Linux x86_64 | Native In-Process Dispatch | 1.071 [0.038] | [1.067, 1.079] | 1.00x |
| Linux x86_64 | Standard I/O JSON-RPC Pipes | 1.103 [0.320] | [1.097, 1.111] | 1.03x |
| Linux x86_64 | Loopback HTTP REST Sockets | 1.965 [0.095] | [1.944, 1.976] | 1.83x |
| Windows 11 NVIDIA | Native In-Process Dispatch | 1.883 [0.138] | [1.856, 1.911] | 1.00x |
| Windows 11 NVIDIA | Standard I/O JSON-RPC Pipes | 1.989 [0.208] | [1.953, 2.086] | 1.06x |
| Windows 11 NVIDIA | Loopback HTTP REST Sockets | 26.632 [23.945] | [23.374, 27.351] | 14.14x |

> **Table 6 Notes:** Evaluates live MCP tool transport mechanisms. Evaluated across the 3 primary physical testbed nodes (macOS M4, Linux x86_64, Windows 11 NVIDIA). Windows Intel iGPU was dedicated to W2 and W5 workloads.
