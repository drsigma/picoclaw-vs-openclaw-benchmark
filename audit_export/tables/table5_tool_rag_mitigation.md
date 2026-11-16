# Table 5: Tool-RAG Dynamic Schema Pruning & Prompt Bloat Mitigation (W2)

| Platform | Catalog Arm | Prompt Tokens | Median Task Latency (ms) [95% CI] | Speedup vs Baseline | Token Reduction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| macOS ARM64 (M4) | OpenClaw Full (54 tools baseline) | ~7,091 | 18335.53 [18328.75, 18349.69] | 1.00x (Baseline) | 0.0% |
| macOS ARM64 (M4) | OpenClaw Tool-RAG (15 retrieved tools) | ~2,177 | 1592.30 [724.93, 2459.96] | 11.52x | -69.3% |
| macOS ARM64 (M4) | PicoClaw Tool-RAG (15 retrieved tools) | ~2,177 | 1611.21 [707.49, 2524.11] | 11.38x | -69.3% |
| Linux x86_64 | OpenClaw Full (54 tools baseline) | ~7,091 | 7891.12 [7876.42, 7903.51] | 1.00x (Baseline) | 0.0% |
| Linux x86_64 | OpenClaw Tool-RAG (15 retrieved tools) | ~2,177 | 1308.45 [1042.76, 1567.90] | 6.03x | -69.3% |
| Linux x86_64 | PicoClaw Tool-RAG (15 retrieved tools) | ~2,177 | 1268.82 [1012.06, 1530.23] | 6.22x | -69.3% |
| Windows 11 x86_64 | OpenClaw Full (54 tools baseline) | ~7,091 | 7663.76 [7628.67, 7693.36] | 1.00x (Baseline) | 0.0% |
| Windows 11 x86_64 | OpenClaw Tool-RAG (15 retrieved tools) | ~2,177 | 1361.14 [1155.92, 1554.49] | 5.63x | -69.3% |
| Windows 11 x86_64 | PicoClaw Tool-RAG (15 retrieved tools) | ~2,177 | 1323.86 [1102.81, 1522.09] | 5.79x | -69.3% |
