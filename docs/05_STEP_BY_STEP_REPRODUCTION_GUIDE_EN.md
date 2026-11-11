# Complete Step-by-Step Reproduction Guide (100% Reproducibility)
## How to Clone, Run Tests, and Recreate All Charts Locally
**Target Audience:** Academic Journal Reviewers (*SoftwareX* / *IEEE*), Committee Members, and Researchers  
**System Requirements:**
* **Full Physical Reproduction with Hardware Telemetry:** macOS 14.0+ on Apple Silicon (M1/M2/M3/M4) with at least 16 GB Unified Memory Architecture (UMA).
* **Portable Simulation Reproduction (Any Machine):** Any Linux distribution (Ubuntu, Debian, Fedora, Arch), Windows (via WSL2), or Intel/Apple Silicon macOS, requiring zero sudo privileges, no GPU, and no local weights.

---

### Fast-Track: Reproduction on Any Machine (Linux, Windows WSL, macOS)

For peer reviewers who wish to validate framework logic, numerical consistency, and figure generation across any hardware architecture in under 10 seconds:

```bash
# 1. Clone the repository
git clone https://github.com/drsigma/picoclaw-vs-openclaw-benchmark.git
cd picoclaw-vs-openclaw-benchmark

# 2. Configure environment (Python virtualenv & dependencies)
make setup

# 3. Run automated unit test suite and code linter
make test

# 4. Run end-to-end portable simulation (No Sudo / Cross-Platform)
make simulate-campaign

# 5. Re-render all 300-DPI scientific figures
make reproduce-figures
```

---

### Detailed Step-by-Step Guide for Apple Silicon Physical Execution

#### Step 1: Clone Repository and Verify File Integrity
```bash
git clone https://github.com/drsigma/picoclaw-vs-openclaw-benchmark.git
cd picoclaw-vs-openclaw-benchmark
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

#### Step 2: Initialize Environment and Datasets
```bash
# 1. Provision isolated environment
make setup

# 2. Generate deterministic datasets for workloads W1–W4 (if regeneration needed)
./tools/.venv/bin/python ./benchmark/generate_datasets.py
```

---

#### Step 3: Launch Local Neural Server `llama.cpp`
In a separate terminal window, launch the Metal GPU server:
```bash
./tools/llama_cpp/llama-b11887/llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 32768 -np 1 -ngl 99 --host 127.0.0.1 --port 8080 -t 4
```

In another terminal, verify endpoint responsiveness:
```bash
curl -s http://127.0.0.1:8080/health
# Should return: {"status":"ok"}
```

---

#### Step 4: Run Master Benchmark Campaign
* **Standard User-Space Mode (No Sudo Required):**
  ```bash
  make benchmark
  ```
* **Full Apple SMC Electrical Telemetry Mode (Requires Sudo):**
  ```bash
  make benchmark-full-smc
  ```

---

#### Step 5: Poisson Sampling Validation and Garwood Bounds
```bash
./tools/.venv/bin/python ./benchmark/poisson_sampling_validation.py
```
This script computes exact Garwood (1936) fiducial bounds, audits Poisson arrival events, and plots `figures/fig7_poisson_assertiveness.png`.

---

#### Step 6: Re-render All Figures and Tables
```bash
make reproduce-figures
./tools/.venv/bin/python ./benchmark/analyze_results.py
```
All consolidated tables will be saved in `results/publication_campaign/tables/` and figures in `figures/`.
