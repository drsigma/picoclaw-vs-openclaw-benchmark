# Review & Reproduction Package Guide (`audit_export_quad_platform.zip`)

This archive consolidates the analytical artifacts, statistical summaries, publication figures, Markdown/LaTeX tables, primary bibliography, reproduction scripts, and saved test output for the **Quad-Platform PicoClaw vs. OpenClaw Benchmark**.

## 1. Contents Included Directly in This Archive

- **Reports:**
  - `audit_export/AUDIT_REPORT_FINAL.md` — Final reproducibility audit report (Portuguese/bilingual technical notes)
  - `audit_export/Systems_Replication_Report.md` — Quad-platform systems replication report (English)
- **Bibliography & Reproduction Scripts:**
  - `references.bib` — 21 primary bibliographic entries with DOIs/ISBNs/arXiv identifiers
  - `scripts/reproduce_quad_platform_analysis.py` — Master analysis, statistical test, table, and figure generator
  - `scripts/verify_manifest.py` — Cryptographic SHA-256 verification script
  - `data/manifest_sha256.json` — SHA-256 cryptographic manifest for all tracked repository artifacts
- **Saved Automated Test Transcript:**
  - `audit_export/pytest_output.txt` — Saved output from `pytest -q`
- **High-Resolution Figures (300 DPI):**
  - `audit_export/figures/fig1_architecture_topology.png` through `fig6_pmc_hardware_counters.png`
- **Consolidated Tables (Tables 1--8, Markdown & LaTeX):**
  - `audit_export/tables/table1_master_summary.{md,tex}`
  - `audit_export/tables/table2_statistical_tests.md`
  - `audit_export/tables/table3_warm_cache_summary.md`
  - `audit_export/tables/table4_kv_thrashing.md`
  - `audit_export/tables/table5_tool_rag_mitigation.md`
  - `audit_export/tables/table6_mcp_transport_ablation.{md,tex}`
  - `audit_export/tables/table7_session_replication_comparison.{md,tex}`
  - `audit_export/tables/table8_w5_enterprise_workload.{md,tex}`
- **Structured Tabular & Diagnostic Exports:**
  - `audit_export/quad_platform_consolidated_summary.csv`
  - `audit_export/anomaly_and_cache_diagnostics.csv`
  - `audit_export/w5_token_and_schema_audit.csv`
  - `audit_export/audit_summary_metrics.json`

## 2. Accessing All 35 Raw `.jsonl` Datasets (18,616 lines / 16,995 measured trials)

All raw empirical trial logs are version-controlled directly in the public Git repository (branch `main`) without external paywalls or binary blobs:

- **Repository URL:** `https://github.com/drsigma/picoclaw-vs-openclaw-benchmark` (branch `main`)
- **Clone Command:**
  ```bash
  git clone https://github.com/drsigma/picoclaw-vs-openclaw-benchmark.git
  cd picoclaw-vs-openclaw-benchmark
  git checkout main
  ```
- **Directory Layout of the 35 Raw `.jsonl` Files:**
  - `results/publication_campaign/*.jsonl` — macOS ARM64 (Apple Silicon M4) primary campaigns & ablations (7 files)
  - `data/*.jsonl` — macOS ARM64 supplementary MCP transport & LangChain external trials (2 files)
  - `data/linux_x86_64_session{1,2}/raw/*.jsonl` — Linux x86_64 (Dell G15 RTX 3050) Session 1 & Session 2 (10 files)
  - `data/windows_x86_64_session{1,2}/raw/*.jsonl` — Windows 11 NVIDIA (Dell G15 RTX 3050) Session 1 & Session 2 (10 files)
  - `data/windows_intel_graphics_session{1,2}/raw/*.jsonl` — Windows Intel HD 4600 iGPU Session 1 & Session 2 (6 files)

### Complete Path & SHA-256 Index of All 35 Raw `.jsonl` Datasets

| Relative Path | Platform | Session Identifier | Role | Workloads | Total Lines | Measured Trials | Warmup Trials | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | :--- |
| `results/publication_campaign/raw_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `raw` | W1, W2, W3, W4, W5 | 825 | 750 | 75 | `9f624bd429c810fbbaa2c952b18ea718b17d42b7b8667d6419c561ec7f60ed01` |
| `results/publication_campaign/warm_cache_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `warm` | W1, W2, W3, W4, W5 | 825 | 750 | 75 | `bd2854fd866a1d1b963ef7cfe8e659e6c68b59794c1cf6c3ac4f38952f79dea6` |
| `results/publication_campaign/kv_cache_thrashing_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `kv` | W2 | 90 | 90 | 0 | `48532324bcb7ad5c0d072c80571480e308dfdf48029312cded4677f47bbd3081` |
| `data/mcp_live_transport_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `mcp` | W2 | 135 | 135 | 0 | `03e8d3bd247e29c498e87a727daaa41d47e4d3b6005713d25a0a33301d3232c4` |
| `results/publication_campaign/tool_rag_mitigation_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `rag` | W1, W2, W3, W4 | 1056 | 960 | 96 | `3631f7843cef17e9a6c53fd2fc0970164c10ec090433d1f034e4d3238e35dc22` |
| `results/publication_campaign/prefill_ablation.jsonl` | macOS (M4) | `darwin_m4_session1` | `prefill` | 8 conditions | 528 | 480 | 48 | `ce1a12908ef22c0c40b1ff42c3a17a0914779234d9e81e003c7cf2d1b2ee9f5f` |
| `results/publication_campaign/uma_energy_bandwidth_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `uma` | W2, W3 | 120 | 120 | 0 | `960dbbe9c568134175a5c049a3e5f936bcebeb69c93777c4dc7037c6a58a31e3` |
| `data/external_framework_langchain_trials.jsonl` | macOS (M4) | `darwin_m4_session1` | `langchain` | W1, W2, W3, W4 | 144 | 120 | 24 | `2fe416fbf8b74ca4dcd18bfb7bb58f69044fa31b8c5fb60a9f3f3658ea458365` |
| `results/publication_campaign/inter_session_trials.jsonl` | macOS (M4) | `darwin_m4_session2` | `warm` | W1, W2, W3, W4, W5 | 825 | 750 | 75 | `ca99fe1748f8e4c171f4a180e258c183797aae3291f7e0d3e44433c77e106ba0` |
| `data/linux_x86_64_session1/raw/raw_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `65f27603213370acfc317357c2c8a01f2abb664858c443b1ae27941d9d9d54a5` |
| `data/linux_x86_64_session1/raw/warm_cache_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `c7388d9d64c9b765ff29e4c91d7e5406b02764cc7cac48d6c7a06d0fd0962d67` |
| `data/linux_x86_64_session1/raw/kv_cache_thrashing_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `kv` | W2 | 184 | 180 | 4 | `b5217cdfae6f7ef23ee994b2555e5050150da3ba6303fa250550d1534b6ec559` |
| `data/linux_x86_64_session1/raw/mcp_live_transport_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `mcp` | W2 | 297 | 270 | 27 | `e8ba4fcbc7403346fb946e524571fe6bf69722eee7d58a560eaceccd1dd7c5f8` |
| `data/linux_x86_64_session1/raw/tool_rag_mitigation_trials.jsonl` | Linux x86_64 | `linux_x86_64_session1` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `ac3c0f22fba876213b9ebe3f6e49edaa5e0c71446827ad6a9139bddf14650b32` |
| `data/linux_x86_64_session2/raw/raw_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `43df3c3249528937871d9728bb4437107696117be1ec3af8f171f457a810957b` |
| `data/linux_x86_64_session2/raw/warm_cache_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `3767a65018317e9e3e93efb0b595e6bc64150b2a454cce7d7baba473f9d379da` |
| `data/linux_x86_64_session2/raw/kv_cache_thrashing_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `kv` | W2 | 184 | 180 | 4 | `c67bfcd561c8ef224a44221a37494c4886d3598eaff1a18f4788977fcf20a328` |
| `data/linux_x86_64_session2/raw/mcp_live_transport_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `mcp` | W2 | 297 | 270 | 27 | `907a8e21bc41eedc92f3fec78b2e9dc46fd2fd31e80a9e6073426570b5c655e9` |
| `data/linux_x86_64_session2/raw/tool_rag_mitigation_trials.jsonl` | Linux x86_64 | `linux_x86_64_session2` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `65434ed3546fbb07f6fcabadeafe64762f4a774c7faab56ee7c3c552dd2d4598` |
| `data/windows_x86_64_session1/raw/raw_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `264db96648f43c8301a936cd9e8a26895a8c79d284b5a78dd62021a1b4006cf9` |
| `data/windows_x86_64_session1/raw/warm_cache_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `3091e23b550627a6b34b692f50566cf99f12ab3ac3fda820dbd2e66a953de019` |
| `data/windows_x86_64_session1/raw/kv_cache_thrashing_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `kv` | W2 | 184 | 180 | 4 | `5ab229460ef19505cd721cf795d7569337212a81fdd3652aa3275a4fb0f8de79` |
| `data/windows_x86_64_session1/raw/mcp_live_transport_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `mcp` | W2 | 297 | 270 | 27 | `9888d6edfabe937e2b0e85845314479b361013ba0fed24220ce58bf206abffab` |
| `data/windows_x86_64_session1/raw/tool_rag_mitigation_trials.jsonl` | Windows 11 | `windows_x86_64_session1` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `449bc5204c6f1cd222002eeebd95a3ebbdc45915002a188eb4fa4a7a3b1848f9` |
| `data/windows_x86_64_session2/raw/raw_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `raw` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `f42f751681083f82787947c10244fecdd24c21ba6e123abd3752870d30568297` |
| `data/windows_x86_64_session2/raw/warm_cache_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `warm` | W1, W2, W3, W4, W5 | 990 | 900 | 90 | `d2df5802ed7c48e3064da8d5eabd27e9f494756bffdb4ad1429560c5286eb891` |
| `data/windows_x86_64_session2/raw/kv_cache_thrashing_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `kv` | W2 | 184 | 180 | 4 | `f4ac5017ceae16ff4c28b936b988d5f76f96f225e81de1d627970ccb5ce28786` |
| `data/windows_x86_64_session2/raw/mcp_live_transport_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `mcp` | W2 | 297 | 270 | 27 | `d9b1e3500af1b210405a7c87de1c6d442ccba36a41e355a99bba68ab16d12e36` |
| `data/windows_x86_64_session2/raw/tool_rag_mitigation_trials.jsonl` | Windows 11 | `windows_x86_64_session2` | `rag` | W1, W2, W3, W4, W5 | 660 | 600 | 60 | `ad45f15cb9bea1c483692b6e4dcf39062c709b4f2f2fad1267316692ac616e62` |
| `data/windows_intel_graphics_session1/raw/raw_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session1` | `raw` | W2, W5 | 330 | 300 | 30 | `e6993e9edeb9964f2109972da4444e6bca4d9952260961eebf1a3286d2a71d80` |
| `data/windows_intel_graphics_session1/raw/warm_cache_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session1` | `warm` | W2, W5 | 330 | 300 | 30 | `081809a8c7b44808fb0cfe41d4bdf7a08d77e68f8e16dfcf1f678ecfe5b4f7ab` |
| `data/windows_intel_graphics_session1/raw/tool_rag_mitigation_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session1` | `rag` | W2 | 132 | 120 | 12 | `b4501867f7a7642c18f31130f0f35e926e9aeb3e19d8a028ce32acf28afff669` |
| `data/windows_intel_graphics_session2/raw/raw_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session2` | `raw` | W2, W5 | 330 | 300 | 30 | `920d68b0197e3039021a1ca327b41807c2cd7b60ed1b606371f6d30e65854a33` |
| `data/windows_intel_graphics_session2/raw/warm_cache_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session2` | `warm` | W2, W5 | 330 | 300 | 30 | `d922a01b5dd42bd5ce8b4b9248bf6a4cb636a45384c025d9bffcb010f021e22c` |
| `data/windows_intel_graphics_session2/raw/tool_rag_mitigation_trials.jsonl` | Windows Intel iGPU | `windows_intel_graphics_session2` | `rag` | W2 | 132 | 120 | 12 | `34736fbad16b3fb5d499c14805a4e4700d21337ed7a57090bad8b98811a04157` |
| **TOTAL (35 files)** | **4 Platforms** | **All Sessions** | **All** | **W1--W5 + Ablations** | **18,616** | **16,995** | **1,621** | **SHA-256 Computed** |

## 3. Step-by-Step Independent Reproduction Commands

From the root of the cloned repository (no GPU or local LLM weights required to reproduce all statistical analyses, tables, and figures from the 35 `.jsonl` datasets):

```bash
python3 -m venv .venv_repro
source .venv_repro/bin/activate
pip install -r requirements.txt

# 1. Verify SHA-256 digests of all tracked raw JSONL files and artifacts
python3 scripts/verify_manifest.py

# 2. Recompute all statistics, hypothesis tests, tables (1-8), figures (1-6), and reports
python3 scripts/reproduce_quad_platform_analysis.py

# 3. Execute automated verification suite
pytest -q
```
