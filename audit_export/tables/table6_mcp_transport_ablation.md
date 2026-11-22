# Table 6: Live MCP Transport IPC Ablation (In-Process vs Stdio vs Loopback HTTP)

| Platform | Transport Protocol | Median IPC Dispatch (ms) [IQR] | 95% Bootstrap CI | Overhead vs In-Process |
| :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | Native In-Process Dispatch | 1.384 [0.360] | [1.353, 1.460] | 1.00x |
| macOS ARM64 (M4) | Standard I/O JSON-RPC Pipes | 1.275 [0.799] | [1.237, 1.350] | 0.92x |
| macOS ARM64 (M4) | Loopback HTTP REST Sockets | 2.389 [0.614] | [2.342, 2.432] | 1.73x |
| Linux x86_64 | Native In-Process Dispatch | 1.109 [0.061] | [1.098, 1.119] | 1.00x |
| Linux x86_64 | Standard I/O JSON-RPC Pipes | 1.406 [0.415] | [1.190, 1.495] | 1.27x |
| Linux x86_64 | Loopback HTTP REST Sockets | 1.707 [0.218] | [1.689, 1.765] | 1.54x |
| Windows 11 NVIDIA | Native In-Process Dispatch | 1.883 [0.138] | [1.860, 1.918] | 1.00x |
| Windows 11 NVIDIA | Standard I/O JSON-RPC Pipes | 1.989 [0.208] | [1.953, 2.085] | 1.06x |
| Windows 11 NVIDIA | Loopback HTTP REST Sockets | 26.632 [23.945] | [23.307, 27.351] | 14.14x |
