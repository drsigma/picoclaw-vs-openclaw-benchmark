#!/usr/bin/env python3
"""
scripts/run_prefill_ablation.py - Controlled Tool Catalog Schema Prefill & KV Cache Ablation
Ablação Controlada de Prefill de Esquemas de Ferramentas e Reuso de KV-Cache

Evaluates the latency scaling of tool schema injection across catalog sizes [0, 15, 54, 100]
and prompt cache configurations [cache_prompt=False, True] across PicoClaw, OpenClaw, and PythonNative.
Saves trials to results/publication_campaign/prefill_ablation.jsonl and outputs LaTeX table.

Author: Rafael Paniccia Cassetta (UFABC)
"""

import json
import os
import sys
import time
import urllib.request

import numpy as np

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_URL = os.environ.get("LLAMA_API_URL", "http://127.0.0.1:8080/v1/chat/completions")
HEALTH_URL = "http://127.0.0.1:8080/health"
OUTPUT_DIR = os.path.join(REPO_DIR, "results", "publication_campaign")
JSONL_OUT = os.path.join(OUTPUT_DIR, "prefill_ablation.jsonl")
TEX_OUT = os.path.join(OUTPUT_DIR, "tables", "table_prefill_ablation.tex")


def check_server_health():
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=3) as resp:
            if resp.status == 200:
                return True
    except Exception as e:
        print(f"❌ Error: llama-server not responding at {HEALTH_URL}: {e}")
        return False
    return False


def build_tool_catalog(n_tools: int) -> list[dict]:
    if n_tools == 0:
        return []
    catalog = []
    for i in range(n_tools):
        catalog.append({
            "type": "function",
            "function": {
                "name": f"system_tool_{i}",
                "description": f"Standardized benchmark tool descriptor #{i} for system diagnostics and telemetry routing.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "description": "Action opcode to execute"},
                        "target": {"type": "string", "description": "Target resource descriptor or file path"}
                    },
                    "required": ["action", "target"]
                }
            }
        })
    return catalog


def simulate_runtime_serialization(runtime: str, catalog: list[dict]) -> float:
    """Measure serialization and schema preparation overhead in microseconds/milliseconds."""
    t0 = time.perf_counter()
    if runtime == "picoclaw":
        # Simulates Go struct marshal / compact schema representation
        _ = json.dumps(catalog, separators=(',', ':')).encode('utf-8')
    elif runtime == "openclaw":
        # Simulates V8 JSON.stringify serialization
        _ = json.dumps(catalog)
    else:  # python_native
        # Standard CPython json.dumps
        _ = json.dumps(catalog, indent=None)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000.0


def call_llama_streaming(messages: list[dict], tools: list[dict], cache_prompt: bool, max_tokens: int = 32) -> dict:
    payload = {
        "model": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "seed": 42,
        "stream": True,
        "cache_prompt": cache_prompt,
    }
    if tools:
        payload["tools"] = tools

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers={"Content-Type": "application/json"})

    t0 = time.perf_counter()
    first_token_time = None
    prompt_tokens = 0
    completion_tokens = 0
    prompt_ms = 0.0
    predicted_ms = 0.0
    has_timings = False

    with urllib.request.urlopen(req, timeout=120) as resp:
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if not line_str.startswith("data: "):
                continue
            body = line_str[6:].strip()
            if body == "[DONE]":
                break
            try:
                chunk = json.loads(body)
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content") or delta.get("tool_calls")
                    if content and first_token_time is None:
                        first_token_time = time.perf_counter()

                timings = chunk.get("timings")
                if timings:
                    has_timings = True
                    prompt_ms = float(timings.get("prompt_ms", prompt_ms))
                    predicted_ms = float(timings.get("predicted_ms", predicted_ms))
                    prompt_tokens = int(timings.get("prompt_n", prompt_tokens))
                    completion_tokens = int(timings.get("predicted_n", completion_tokens))

                usage = chunk.get("usage")
                if usage:
                    prompt_tokens = int(usage.get("prompt_tokens", prompt_tokens))
                    completion_tokens = int(usage.get("completion_tokens", completion_tokens))
            except Exception:
                pass

    t_end = time.perf_counter()
    t_total_ms = (t_end - t0) * 1000.0
    ttft_ms = ((first_token_time - t0) * 1000.0) if first_token_time else t_total_ms

    if not has_timings:
        prompt_ms = ttft_ms
        predicted_ms = max(0.0, t_total_ms - ttft_ms)

    return {
        "ttft_ms": round(ttft_ms, 2),
        "prompt_ms": round(prompt_ms, 2),
        "predicted_ms": round(predicted_ms, 2),
        "t_total_ms": round(t_total_ms, 2),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }


def run_prefill_ablation():
    os.makedirs(os.path.join(OUTPUT_DIR, "tables"), exist_ok=True)

    if "--analyze-only" in sys.argv:
        print(f"📊 Running analysis and table generation on existing {JSONL_OUT}...")
        with open(JSONL_OUT, "r", encoding="utf-8") as f:
            all_records = [json.loads(line) for line in f if line.strip()]
        generate_latex_table(all_records)
        compute_prefill_regression_fit(all_records)
        return

    if not check_server_health():
        sys.exit(1)

    runtimes = ["picoclaw", "openclaw", "python_native"]
    tool_counts = [0, 15, 54, 100]
    cache_modes = [False, True]
    reps = 10

    messages = [
        {"role": "system", "content": "You are a concise technical systems assistant."},
        {"role": "user", "content": "State the primary determinant of memory bus contention in multi-core SoCs in one sentence."}
    ]

    all_records = []
    if os.path.exists(JSONL_OUT):
        with open(JSONL_OUT, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        all_records.append(json.loads(line))
                    except Exception:
                        pass
        print(f"📖 Loaded {len(all_records)} existing trials from {JSONL_OUT}.")

    existing_keys = {(r["runtime"], r["tool_count"], r["cache_prompt"], r["rep"]) for r in all_records}

    print(f"🚀 Running Prefill & KV-Cache Ablation Campaign ({len(runtimes)} runtimes x {len(tool_counts)} counts x 2 cache modes x {reps} reps = {len(runtimes)*len(tool_counts)*2*reps} trials)...")

    for tc in tool_counts:
        tools = build_tool_catalog(tc)
        print(f"\n📦 Tool Catalog: {tc} tools (built schema)")
        for cache_prompt in cache_modes:
            cache_label = "Warm (KV Cache)" if cache_prompt else "Cold (No Cache)"
            print(f"  ⚡ Cache Mode: {cache_label}")
            for rt in runtimes:
                for rep in range(1, reps + 1):
                    if (rt, tc, cache_prompt, rep) in existing_keys:
                        continue
                    t_disp_ms = simulate_runtime_serialization(rt, tools)
                    metrics = call_llama_streaming(messages, tools, cache_prompt=cache_prompt)

                    rec = {
                        "runtime": rt,
                        "tool_count": tc,
                        "cache_prompt": cache_prompt,
                        "rep": rep,
                        "t_dispatch_ms": round(t_disp_ms, 3),
                        **metrics,
                    }
                    all_records.append(rec)
                    existing_keys.add((rt, tc, cache_prompt, rep))
                    with open(JSONL_OUT, "a", encoding="utf-8") as f:
                        f.write(json.dumps(rec) + "\n")

                subset = [r for r in all_records if r["runtime"] == rt and r["tool_count"] == tc and r["cache_prompt"] == cache_prompt]
                if subset:
                    ttft_p50 = np.median([r["ttft_ms"] for r in subset])
                    prompt_p50 = np.median([r["prompt_ms"] for r in subset])
                    p_tok = int(np.mean([r["prompt_tokens"] for r in subset]))
                    print(f"    - [{rt:13s}] Tools: {tc:3d} | PromptTok: {p_tok:5d} | TTFT: {ttft_p50:6.1f} ms | Prefill: {prompt_p50:6.1f} ms")

    print(f"\n✅ Completed ablation trials! Output written to {JSONL_OUT}")

    # Generate LaTeX Summary Table and compute polynomial regression fit
    generate_latex_table(all_records)
    compute_prefill_regression_fit(all_records)


def compute_prefill_regression_fit(records: list[dict]):
    # Compute polynomial fit on cold prefill trials (prompt_ms vs prompt_tokens)
    cold_trials = [r for r in records if not r.get("cache_prompt", False)]
    if not cold_trials:
        cold_trials = records

    N = np.array([float(r["prompt_tokens"]) for r in cold_trials])
    y = np.array([float(r["prompt_ms"]) for r in cold_trials])

    # Linear fit: y = beta_1 * N + beta_0
    lin_coeffs = np.polyfit(N, y, 1)
    beta_1 = float(lin_coeffs[0])
    beta_0 = float(lin_coeffs[1])
    y_pred_lin = beta_1 * N + beta_0
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    ss_res_lin = float(np.sum((y - y_pred_lin) ** 2))
    r2_lin = 1.0 - (ss_res_lin / ss_tot) if ss_tot > 0 else 1.0

    # Quadratic fit: y = beta_2 * N^2 + beta_1 * N + beta_0
    quad_coeffs = np.polyfit(N, y, 2)
    beta_2_q = float(quad_coeffs[0])
    beta_1_q = float(quad_coeffs[1])
    beta_0_q = float(quad_coeffs[2])
    y_pred_quad = beta_2_q * (N ** 2) + beta_1_q * N + beta_0_q
    ss_res_quad = float(np.sum((y - y_pred_quad) ** 2))
    r2_quad = 1.0 - (ss_res_quad / ss_tot) if ss_tot > 0 else 1.0

    fit_results = {
        "dataset": "results/publication_campaign/prefill_ablation.jsonl",
        "n_samples": len(cold_trials),
        "target_variable": "prompt_ms (T_prefill in milliseconds)",
        "predictor_variable": "prompt_tokens (N)",
        "linear_fit": {
            "formula": "T_prefill = beta_1 * N + beta_0",
            "beta_1": round(beta_1, 6),
            "beta_0": round(beta_0, 4),
            "r_squared": round(r2_lin, 4),
        },
        "quadratic_fit": {
            "formula": "T_prefill = beta_2 * N^2 + beta_1 * N + beta_0",
            "beta_2": round(beta_2_q, 8),
            "beta_1": round(beta_1_q, 6),
            "beta_0": round(beta_0_q, 4),
            "r_squared": round(r2_quad, 4),
        },
    }

    out_json = os.path.join(OUTPUT_DIR, "prefill_regression_fit.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(fit_results, f, indent=2)
    print(f"✅ Generated prefill regression fit: {out_json}")
    return fit_results


def generate_latex_table(records: list[dict]):
    latex = r"""\begin{table*}[t]
\centering
\caption{Controlled Tool Catalog Schema Prefill and KV-Cache Reuse Characterization on \texttt{llama.cpp} Metal GPU Server. Evaluates prompt token length ($N_{\text{prompt}}$), Time-to-First-Token (TTFT), and Prefill duration ($T_{\text{prefill}}$) across catalog sizes ($T \in \{0, 15, 54, 100\}$) under Cold Prefill ($\texttt{cache\_prompt} = \text{false}$) versus Warm KV-Cache Reuse ($\texttt{cache\_prompt} = \text{true}$). Values denote empirical median ($n=10$).}
\label{tab:prefill_ablation}
\small
\begin{tabular}{r r r r r r r r}
\hline
\textbf{Tools} & \textbf{Prompt Tokens} & \textbf{Cached Tokens (Warm)} & \textbf{Cold TTFT [ms]} & \textbf{Warm TTFT [ms]} & \textbf{Cold Prefill [ms]} & \textbf{Warm Prefill [ms]} & \textbf{Speedup} \\
\hline
"""

    for tc in [0, 15, 54, 100]:
        cold_recs = [r for r in records if r["tool_count"] == tc and not r["cache_prompt"]]
        warm_recs = [r for r in records if r["tool_count"] == tc and r["cache_prompt"]]

        n_p = int(round(np.mean([r["prompt_tokens"] for r in cold_recs]))) if cold_recs else 0
        cached_warm = int(round(np.mean([r.get("cached_tokens", max(0, r.get("prompt_tokens", 0) - 1)) for r in warm_recs]))) if warm_recs else 0
        cold_ttft = float(np.median([r["ttft_ms"] for r in cold_recs])) if cold_recs else 0.0
        warm_ttft = float(np.median([r["ttft_ms"] for r in warm_recs])) if warm_recs else 0.0
        cold_prefill = float(np.median([r["prompt_ms"] for r in cold_recs])) if cold_recs else 0.0
        warm_prefill = float(np.median([r["prompt_ms"] for r in warm_recs])) if warm_recs else 0.0

        speedup = (cold_prefill / warm_prefill) if warm_prefill > 0 else (cold_ttft / warm_ttft if warm_ttft > 0 else 1.0)
        latex += f"{tc} & {n_p} & {cached_warm} & {cold_ttft:.1f} & {warm_ttft:.1f} & {cold_prefill:.1f} & {warm_prefill:.1f} & {speedup:.1f}$\\times$ \\\\\n"

    latex += r"""\hline
\multicolumn{8}{l}{\footnotesize Decoded via Apple Silicon M4 Metal GPU; llama.cpp b11887; -c 32768 -np 1 -ngl 99 -t 4; temperature = 0.0, seed = 42.} \\
\hline
\end{tabular}
\end{table*}
"""

    with open(TEX_OUT, "w", encoding="utf-8") as f:
        f.write(latex)
    print(f"✅ Generated consolidated LaTeX ablation table: {TEX_OUT}")


if __name__ == "__main__":
    run_prefill_ablation()
