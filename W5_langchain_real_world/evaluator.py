#!/usr/bin/env python3
"""
W5_langchain_real_world/evaluator.py
Offline / Local LLM-as-a-Judge for evaluating cross-domain synthesis quality (Score: 1-5).
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any, Dict

API_URL = os.environ.get("LLAMA_API_URL", "http://127.0.0.1:8080/v1/chat/completions")

RUBRIC = """You are an expert systems auditor and AI benchmark evaluator.
Evaluate the following Cross-Domain Infrastructure and Compliance Audit Summary produced by an autonomous agent.

The evaluation must adhere to this 5-point rubric:
- 5 (Exceptional): Correctly identifies financial budget overruns (e.g., Alpha-Neural-Gateway > 5% variance), SLA latency breaches (e.g., Beta-Vector-Search > 120ms), and compliance quarantine violations (Gamma-Tool-Router). Exact cross-referencing between policy document and database records. Actionable and concise.
- 4 (Good): Identifies at least 2 of the 3 major issues with correct factual data from the database. Minor formatting or minor detail omitted.
- 3 (Adequate): Identifies 1-2 issues but with imprecise values or lacks cross-referencing between the policy document and database.
- 2 (Poor): Significant factual errors, hallucinations, or failure to synthesize across both database and document domains.
- 1 (Unacceptable): Irrelevant, empty, or completely wrong output.

Agent Output to Evaluate:
\"\"\"{output}\"\"\"

Respond STRICTLY in JSON format with two keys:
{{"quality_score": <integer from 1 to 5>, "reasoning": "<concise explanation>"}}
"""

def heuristic_evaluate(output: str) -> Dict[str, Any]:
    """Deterministic fallback evaluation when local LLM server is not reachable."""
    score = 1
    reasons = []
    lower = output.lower()
    
    # Check key domain detections:
    # 1. Budget overrun (Alpha-Neural-Gateway or 162000 or >5%)
    has_budget = "alpha" in lower or "162000" in lower or "budget" in lower or "overrun" in lower
    # 2. SLA breach (Beta-Vector-Search or 135 or latency)
    has_sla = "beta" in lower or "135" in lower or "latency" in lower or "sla" in lower
    # 3. Compliance issue (Gamma-Tool-Router or non_compliant or violation)
    has_compliance = "gamma" in lower or "quarantine" in lower or "violation" in lower or "non_compliant" in lower

    matches = sum([has_budget, has_sla, has_compliance])
    if matches == 3:
        score = 5
        reasons.append("Correctly identified budget overrun, SLA breach, and compliance violation.")
    elif matches == 2:
        score = 4
        reasons.append("Identified two key cross-domain issues.")
    elif matches == 1:
        score = 3
        reasons.append("Identified one issue with partial cross-domain context.")
    elif len(output.strip()) > 50:
        score = 2
        reasons.append("Produced detailed response but failed cross-domain ground-truth checks.")
    else:
        score = 1
        reasons.append("Output is too brief or invalid.")

    return {
        "quality_score": score,
        "reasoning": "Heuristic evaluation: " + " ".join(reasons)
    }

def evaluate_quality(agent_output: str, timeout_s: float = 10.0) -> Dict[str, Any]:
    """
    Evaluates agent output using the local LLM-as-a-judge if online,
    or falls back to deterministic heuristic evaluation.
    """
    if not agent_output or not agent_output.strip():
        return {"quality_score": 1, "reasoning": "Empty output"}

    prompt = RUBRIC.format(output=agent_output.strip())
    payload = {
        "model": "local-llm",
        "messages": [
            {"role": "system", "content": "You are a strict, objective AI evaluation judge. Always output valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 150,
        "cache_prompt": False
    }

    try:
        req = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            # Extract JSON block
            match = re.search(r"\{.*?\}", content, re.DOTALL)
            if match:
                res = json.loads(match.group(0))
                score = int(res.get("quality_score", 3))
                score = max(1, min(5, score))
                return {"quality_score": score, "reasoning": str(res.get("reasoning", ""))}
    except Exception:
        pass

    return heuristic_evaluate(agent_output)

if __name__ == "__main__":
    sample_output = (
        "Executive Audit Summary:\n"
        "1. Budget Overrun: Alpha-Neural-Gateway spent $162,000 against $150,000 budget (+8.0%), exceeding the 5% threshold.\n"
        "2. SLA Violation: Beta-Vector-Search exhibited P99 latency of 135.8ms, violating the Tier-2 limit of 120ms.\n"
        "3. Compliance Action: Gamma-Tool-Router has 1 active violation and is marked NON_COMPLIANT; quarantine required."
    )
    result = evaluate_quality(sample_output)
    print("Evaluation result:", json.dumps(result, indent=2))
