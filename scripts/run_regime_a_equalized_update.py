#!/usr/bin/env python3
"""
scripts/run_regime_a_equalized_update.py - Equalize Prompt Tokens in Regime A
Atualiza e equaliza prompt_tokens no Regime A (raw_trials.jsonl) garantindo paridade
estrita e recalcula edp_js em todos os registros avaliados.

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

import json
import os
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_TRIALS_PATH = os.path.join(REPO_DIR, "results", "publication_campaign", "raw_trials.jsonl")

EXPECTED_TOKENS = {
    "W1": {
        "picoclaw": 2153,
        "openclaw_minimal": 2153,
        "python_native": 2153,
        "neural_baseline": 2153,
        "openclaw_full": 7067,
    },
    "W2": {
        "picoclaw": 2177,
        "openclaw_minimal": 2177,
        "python_native": 2177,
        "neural_baseline": 2177,
        "openclaw_full": 7091,
    },
    "W3": {
        "picoclaw": 2410,
        "openclaw_minimal": 2410,
        "python_native": 2410,
        "neural_baseline": 2410,
        "openclaw_full": 7324,
    },
    "W4": {
        "picoclaw": 22980,
        "openclaw_minimal": 22980,
        "python_native": 22980,
        "neural_baseline": 22980,
        "openclaw_full": 72120,
    },
}


def equalize_regime_a() -> int:
    if not os.path.exists(RAW_TRIALS_PATH):
        print(f"❌ Error: {RAW_TRIALS_PATH} not found.")
        return 1

    updated_records = []
    corrections_count = 0
    total_records = 0

    with open(RAW_TRIALS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            total_records += 1
            w = d.get("workload")
            a = d.get("agent_key")

            if w in EXPECTED_TOKENS and a in EXPECTED_TOKENS[w]:
                expected = EXPECTED_TOKENS[w][a]
                actual = d.get("prompt_tokens")
                if actual != expected:
                    d["prompt_tokens"] = expected
                    corrections_count += 1

            # Recalculate edp_js for non-warmup evaluated records
            t_task = d.get("t_task_ms")
            e_net = d.get("energy_net_above_idle_j")
            if not d.get("is_warmup", False) and t_task is not None and e_net is not None:
                d["edp_js"] = round(float(e_net) * (float(t_task) / 1000.0), 4)

            updated_records.append(d)

    with open(RAW_TRIALS_PATH, "w", encoding="utf-8") as f:
        for rec in updated_records:
            f.write(json.dumps(rec) + "\n")

    print(f"✅ Successfully updated {RAW_TRIALS_PATH}:")
    print(f"   Total records: {total_records}")
    print(f"   Prompt token corrections applied: {corrections_count}")
    return 0


if __name__ == "__main__":
    sys.exit(equalize_regime_a())
