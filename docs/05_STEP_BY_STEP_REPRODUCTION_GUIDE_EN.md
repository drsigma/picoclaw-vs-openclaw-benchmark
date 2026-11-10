# Complete Step-by-Step Reproduction Guide (100% Reproducibility)
## How to Clone, Run Tests, and Recreate All Charts Locally
**Target Audience:** Academic Journal Reviewers, Defense Committee Members, and Researchers  
**Minimum Requirements:** macOS 14.0+ on Apple Silicon (M1/M2/M3/M4) with at least 16 GB Unified Memory Architecture (UMA).

---

### Step 1: Navigate to Repository and Verify File Integrity

Navigate to the repository root:
```bash
cd /Users/rafael/.gemini/antigravity/scratch/picoclaw-vs-openclaw-benchmark
```

Verify cryptographic integrity of all binaries, datasets, and reports against the SHA-256 manifest:
```bash
python3 -c '
import json, hashlib, os
manifest = json.load(open("data/manifest_sha256.json"))
ok, fail = 0, 0
for rel_path, meta in manifest.items():
    if os.path.exists(rel_path):
        h = hashlib.sha256(open(rel_path, "rb").read()).hexdigest()
        if h == meta["sha256"]:
            ok += 1
        else:
            print(f"[FAIL] {rel_path}: mismatch!")
            fail += 1
print(f"Verification finished: {ok} files intact, {fail} failures.")
'
```

---

### Step 2: Initialize the Python Environment and Compile Orchestrators

The project is completely self-contained and does not require system-wide Xcode tools:

```bash
# 1. Activate isolated CPython 3.12.3 interpreter
VENV_PYTHON="../picoclaw_vs_openclaw/.venv/bin/python"

# 2. Compile static Go ARM64 orchestrator (if recompiling from source)
CGO_ENABLED=0 ../picoclaw_vs_openclaw/tools/go/bin/go build \
    -o ./benchmark/picoclaw_orch \
    ./benchmark/picoclaw_orch.go

# 3. Generate deterministic datasets for workloads W1–W4 (50 configs, JSONL logs, and 100k RAG projection)
$VENV_PYTHON ./benchmark/generate_datasets.py
```

---

### Step 3: Launch Local Neural Server `llama.cpp`

Open a terminal window and launch the Metal GPU server:
```bash
../picoclaw_vs_openclaw/tools/llama_cpp/llama-b11887/llama-server \
  -m ../picoclaw_vs_openclaw/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```

In a second window, test health check endpoint:
```bash
curl -s http://127.0.0.1:8080/health
# Expected output: {"status":"ok"}
```

---

### Step 4: Run Poisson Statistical Validation ($\ge 90\%$ Assertiveness)

Execute the Poisson analytical engine:
```bash
$VENV_PYTHON ./benchmark/poisson_sampling_validation.py
```

This script automatically executes:
1. Calculates theoretical sample bounds ($K \ge 271$ events for $90\%$ assertiveness; $K \ge 1,537$ for $95\%$).
2. Evaluates physical empirical samples with $n = 100$ repetitions ($K = 300$ tool calls on W2 and $K = 1,000$ tool calls on W4).
3. Computes exact Garwood (1936) Chi-Square Confidence Intervals.
4. Generates consolidated dataset in `data/poisson_results.json`.
5. Plots high-resolution scientific chart in `figures/fig7_poisson_assertiveness.png`.

---

### Step 5: Execute Independent Physical Campaigns (Empirical Reproducibility)

To run a complete live physical campaign executing live queries against the Metal GPU and collecting hardware metrics:
```bash
$VENV_PYTHON ./benchmark/run_live_campaign.py campaign_run_6 ./campaign_run_6
```

To compare all physical campaigns (`campaign_run_1` through `campaign_run_5`) with ANOVA and CV%:
```bash
$VENV_PYTHON ./benchmark/compare_campaigns.py
```
This generates the cross-campaign reproducibility chart `figures/fig8_three_campaigns_reproducibility.png` and documentation in `campaign_comparison/CAMPAIGN_COMPARISON.md` and `CAMPAIGN_COMPARISON_EN.md`.

---

### Step 6: Regenerate All Figures and Reports in Word and PDF

To recreate all scientific figures (Figures 1 to 8) and compile `.docx` and `.pdf` reports:
```bash
# 1. Regenerate original charts at 300 DPI
$VENV_PYTHON ./benchmark/generate_charts.py

# 2. Compile formal course reports (System Testing Report and Revised Work Plan)
$VENV_PYTHON ./benchmark/build_reports.py

# 3. Compile Layperson Defense Guide
$VENV_PYTHON ./benchmark/build_layperson_guide.py
```

All compiled reports will be ready in the `reports/` directory.
