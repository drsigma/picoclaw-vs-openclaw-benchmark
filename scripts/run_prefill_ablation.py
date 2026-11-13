#!/usr/bin/env python3
"""
scripts/run_prefill_ablation.py - Controlled Tool Catalog Schema Prefill & KV Cache Ablation
Ablação Controlada de Prefill de Esquemas de Ferramentas e Reuso de KV-Cache

Evaluates latency scaling of tool schema injection across 8 catalog sizes [0, 5, 10, 15, 25, 40, 54, 100]
and prompt cache configurations [cache_prompt=False, True] directly against llama.cpp Metal GPU server.
Fits Linear, Quadratic, and Power-Law (T = a * N^alpha) models on level medians with 95% bootstrap CIs.
Saves trials to results/publication_campaign/prefill_ablation.jsonl and outputs LaTeX table.

Author: Rafael Paniccia Cassetta (UFABC)
"""

import datetime
import json
import os
import sys
import time
import urllib.request

import numpy as np
from scipy.optimize import curve_fit

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_URL = os.environ.get("LLAMA_API_URL", "http://127.0.0.1:8080/v1/chat/completions")
HEALTH_URL = os.environ.get("LLAMA_HEALTH_URL", "http://127.0.0.1:8080/health")
OUTPUT_DIR = os.path.join(REPO_DIR, "results", "publication_campaign")
JSONL_OUT = os.path.join(OUTPUT_DIR, "prefill_ablation.jsonl")
TEX_OUT = os.path.join(OUTPUT_DIR, "tables", "table_prefill_ablation.tex")
FIT_OUT = os.path.join(OUTPUT_DIR, "prefill_regression_fit.json")


def check_server_health() -> bool:
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


def call_llama_streaming(messages: list[dict], tools: list[dict], cache_prompt: bool, max_tokens: int = 4) -> dict:
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

    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers={"Content-Type": "application/json"})

    t0 = time.perf_counter()
    first_token_time = None
    prompt_tokens = 0
    cached_tokens = 0
    uncached_prompt_tokens = 0
    completion_tokens = 0
    prompt_ms = 0.0
    predicted_ms = 0.0
    has_timings = False

    with urllib.request.urlopen(req, timeout=180) as resp:
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
                    uncached_prompt_tokens = int(timings.get("prompt_n", uncached_prompt_tokens))
                    cached_tokens = int(timings.get("cache_n", cached_tokens))
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

    if prompt_tokens == 0:
        prompt_tokens = cached_tokens + uncached_prompt_tokens

    if not has_timings:
        prompt_ms = ttft_ms
        predicted_ms = max(0.0, t_total_ms - ttft_ms)

    return {
        "ttft_ms": round(ttft_ms, 2),
        "prompt_ms": round(prompt_ms, 2),
        "predicted_ms": round(predicted_ms, 2),
        "t_total_ms": round(t_total_ms, 2),
        "prompt_tokens": prompt_tokens,
        "cached_tokens": cached_tokens,
        "uncached_prompt_tokens": uncached_prompt_tokens,
        "completion_tokens": completion_tokens,
        "http_status": 200,
    }


def power_law_func(x, a, alpha):
    return a * np.power(x, alpha)


def compute_aicc(n: int, k: int, rss: float) -> float:
    if rss <= 0 or n <= k + 1:
        return float("nan")
    aic = n * np.log(rss / n) + 2 * k
    aicc = aic + (2 * k * (k + 1)) / (n - k - 1)
    return float(aicc)


def compute_prefill_regression_fit(records: list[dict]) -> dict:
    # Filter non-warmup cold prefill trials
    cold_trials = [r for r in records if not r.get("is_warmup", False) and not r.get("cache_prompt", False)]
    if not cold_trials:
        cold_trials = [r for r in records if not r.get("cache_prompt", False)]

    # Group by tool_count to compute level medians
    tool_counts = sorted(list({r["tool_count"] for r in cold_trials}))
    medians_n = []
    medians_y = []
    level_data = {}

    for tc in tool_counts:
        subset = [r for r in cold_trials if r["tool_count"] == tc]
        n_p = float(np.median([r["prompt_tokens"] for r in subset]))
        p_ms = float(np.median([r["prompt_ms"] for r in subset]))
        medians_n.append(n_p)
        medians_y.append(p_ms)
        level_data[tc] = subset

    N = np.array(medians_n, dtype=float)
    y = np.array(medians_y, dtype=float)
    n_pts = len(N)
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))

    # 1. Linear Fit: y = beta_1 * N + beta_0 (k=2)
    lin_coeffs = np.polyfit(N, y, 1)
    beta_1 = float(lin_coeffs[0])
    beta_0 = float(lin_coeffs[1])
    y_pred_lin = beta_1 * N + beta_0
    ss_res_lin = float(np.sum((y - y_pred_lin) ** 2))
    r2_lin = 1.0 - (ss_res_lin / ss_tot) if ss_tot > 0 else 1.0
    aicc_lin = compute_aicc(n_pts, 2, ss_res_lin)

    # 2. Quadratic Fit: y = beta_2 * N^2 + beta_1 * N + beta_0 (k=3)
    quad_coeffs = np.polyfit(N, y, 2)
    beta_2_q = float(quad_coeffs[0])
    beta_1_q = float(quad_coeffs[1])
    beta_0_q = float(quad_coeffs[2])
    y_pred_quad = beta_2_q * (N ** 2) + beta_1_q * N + beta_0_q
    ss_res_quad = float(np.sum((y - y_pred_quad) ** 2))
    r2_quad = 1.0 - (ss_res_quad / ss_tot) if ss_tot > 0 else 1.0
    aicc_quad = compute_aicc(n_pts, 3, ss_res_quad)

    # 3. Power-Law Fit: y = a * N^alpha (k=2)
    try:
        popt_pow, _ = curve_fit(power_law_func, N, y, p0=[1.0, 1.2], maxfev=10000)
        a_pow = float(popt_pow[0])
        alpha_pow = float(popt_pow[1])
        y_pred_pow = power_law_func(N, a_pow, alpha_pow)
        ss_res_pow = float(np.sum((y - y_pred_pow) ** 2))
        r2_pow = 1.0 - (ss_res_pow / ss_tot) if ss_tot > 0 else 1.0
        aicc_pow = compute_aicc(n_pts, 2, ss_res_pow)
    except Exception as e:
        print(f"⚠️ Power-law fit warning: {e}")
        a_pow, alpha_pow, r2_pow, aicc_pow = float("nan"), float("nan"), float("nan"), float("nan")

    # Bootstrap 95% Confidence Intervals (2000 resamples)
    n_boot = 2000
    rng = np.random.default_rng(42)
    boot_lin_b1, boot_lin_b0 = [], []
    boot_quad_b2, boot_quad_b1, boot_quad_b0 = [], [], []
    boot_pow_a, boot_pow_alpha = [], []

    for _ in range(n_boot):
        resampled_n = []
        resampled_y = []
        for tc in tool_counts:
            trials = level_data[tc]
            sampled_idx = rng.integers(0, len(trials), size=len(trials))
            sampled_tokens = [trials[i]["prompt_tokens"] for i in sampled_idx]
            sampled_ms = [trials[i]["prompt_ms"] for i in sampled_idx]
            resampled_n.append(float(np.median(sampled_tokens)))
            resampled_y.append(float(np.median(sampled_ms)))

        b_N = np.array(resampled_n, dtype=float)
        b_y = np.array(resampled_y, dtype=float)

        # Linear
        try:
            lc = np.polyfit(b_N, b_y, 1)
            boot_lin_b1.append(float(lc[0]))
            boot_lin_b0.append(float(lc[1]))
        except Exception:
            pass

        # Quadratic
        try:
            qc = np.polyfit(b_N, b_y, 2)
            boot_quad_b2.append(float(qc[0]))
            boot_quad_b1.append(float(qc[1]))
            boot_quad_b0.append(float(qc[2]))
        except Exception:
            pass

        # Power law
        try:
            popt, _ = curve_fit(power_law_func, b_N, b_y, p0=[a_pow, alpha_pow], maxfev=5000)
            boot_pow_a.append(float(popt[0]))
            boot_pow_alpha.append(float(popt[1]))
        except Exception:
            pass

    def ci95(arr):
        if len(arr) == 0:
            return [float("nan"), float("nan")]
        return [round(float(np.percentile(arr, 2.5)), 6), round(float(np.percentile(arr, 97.5)), 6)]

    fit_results = {
        "dataset": "results/publication_campaign/prefill_ablation.jsonl",
        "n_levels": n_pts,
        "n_total_eval_samples": len(cold_trials),
        "target_variable": "prompt_ms (T_prefill in milliseconds)",
        "predictor_variable": "prompt_tokens (N)",
        "bootstrap_resamples": n_boot,
        "linear_fit": {
            "formula": "T_prefill = beta_1 * N + beta_0",
            "beta_1": round(beta_1, 6),
            "beta_0": round(beta_0, 4),
            "beta_1_ci95": ci95(boot_lin_b1),
            "beta_0_ci95": ci95(boot_lin_b0),
            "r_squared": round(r2_lin, 5),
            "aicc": round(aicc_lin, 2),
        },
        "quadratic_fit": {
            "formula": "T_prefill = beta_2 * N^2 + beta_1 * N + beta_0",
            "beta_2": round(beta_2_q, 8),
            "beta_1": round(beta_1_q, 6),
            "beta_0": round(beta_0_q, 4),
            "beta_2_ci95": ci95(boot_quad_b2),
            "beta_1_ci95": ci95(boot_quad_b1),
            "beta_0_ci95": ci95(boot_quad_b0),
            "r_squared": round(r2_quad, 5),
            "aicc": round(aicc_quad, 2),
        },
        "power_law_fit": {
            "formula": "T_prefill = a * N^alpha",
            "a": round(a_pow, 6),
            "alpha": round(alpha_pow, 4),
            "a_ci95": ci95(boot_pow_a),
            "alpha_ci95": ci95(boot_pow_alpha),
            "r_squared": round(r2_pow, 5),
            "aicc": round(aicc_pow, 2),
        },
    }

    with open(FIT_OUT, "w", encoding="utf-8") as f:
        json.dump(fit_results, f, indent=2)
    print(f"✅ Generated prefill regression fit: {FIT_OUT}")
    return fit_results


def generate_latex_table(records: list[dict]):
    latex = r"""\begin{table*}[t]
\centering
\caption{Controlled Tool Catalog Schema Prefill and KV-Cache Reuse Characterization on \texttt{llama.cpp} Metal GPU Server. Evaluates prompt token length ($N_{\text{prompt}}$), Time-to-First-Token (TTFT), and Prefill duration ($T_{\text{prefill}}$) across 8 catalog sizes ($T \in \{0, 5, 10, 15, 25, 40, 54, 100\}$) under Cold Prefill ($\texttt{cache\_prompt} = \text{false}$) versus Warm KV-Cache Reuse ($\texttt{cache\_prompt} = \text{true}$). Values denote empirical median ($n=30$ evaluations per condition following 3 priming warmups).}
\label{tab:prefill_ablation}
\small
\begin{tabular}{r r r r r r r r}
\hline
\textbf{Tools} & \textbf{Prompt Tokens} & \textbf{Cached Tokens (Warm)} & \textbf{Cold TTFT [ms]} & \textbf{Warm TTFT [ms]} & \textbf{Cold Prefill [ms]} & \textbf{Warm Prefill [ms]} & \textbf{Speedup} \\
\hline
"""

    eval_records = [r for r in records if not r.get("is_warmup", False)]
    tool_counts = sorted(list({r["tool_count"] for r in eval_records}))
    if not tool_counts:
        tool_counts = [0, 5, 10, 15, 25, 40, 54, 100]

    for tc in tool_counts:
        cold_recs = [r for r in eval_records if r["tool_count"] == tc and not r["cache_prompt"]]
        warm_recs = [r for r in eval_records if r["tool_count"] == tc and r["cache_prompt"]]

        n_p = int(round(np.median([r["prompt_tokens"] for r in cold_recs]))) if cold_recs else 0
        cached_warm = int(round(np.median([r.get("cached_tokens", 0) for r in warm_recs]))) if warm_recs else 0
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

    tool_counts = [0, 5, 10, 15, 25, 40, 54, 100]
    cache_modes = [False, True]
    warmup_reps = 3
    eval_reps = 30

    messages = [
        {"role": "system", "content": "You are a concise technical systems assistant."},
        {"role": "user", "content": "State the primary determinant of memory bus contention in multi-core SoCs in one sentence."}
    ]

    print(f"🚀 Running Controlled Prefill & KV-Cache Ablation Campaign ({len(tool_counts)} catalog levels x 2 cache modes x (3 warmups + 30 evals) = {len(tool_counts)*2*(warmup_reps+eval_reps)} requests)...")

    # Wipe or initialize output JSONL for fresh, clean physical run
    all_records = []
    with open(JSONL_OUT, "w", encoding="utf-8") as f:
        pass

    for tc in tool_counts:
        tools = build_tool_catalog(tc)
        print(f"\n📦 Catalog Level: {tc} tools")

        for cache_prompt in cache_modes:
            mode_label = "Warm (KV Cache Reuse)" if cache_prompt else "Cold (Prompt Prefill)"
            print(f"  ⚡ Cache Mode: {mode_label}")

            # 1. Warmups (isolated priming block)
            for w in range(1, warmup_reps + 1):
                metrics = call_llama_streaming(messages, tools, cache_prompt=cache_prompt, max_tokens=4)
                rec = {
                    "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "tool_count": tc,
                    "cache_prompt": cache_prompt,
                    "rep": w,
                    "is_warmup": True,
                    **metrics,
                }
                all_records.append(rec)
                with open(JSONL_OUT, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec) + "\n")

            # 2. Evaluations (consecutive block)
            for rep in range(1, eval_reps + 1):
                metrics = call_llama_streaming(messages, tools, cache_prompt=cache_prompt, max_tokens=4)
                rec = {
                    "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "tool_count": tc,
                    "cache_prompt": cache_prompt,
                    "rep": rep,
                    "is_warmup": False,
                    **metrics,
                }
                all_records.append(rec)
                with open(JSONL_OUT, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec) + "\n")

            # Summary for this condition block
            eval_subset = [r for r in all_records if r["tool_count"] == tc and r["cache_prompt"] == cache_prompt and not r["is_warmup"]]
            ttft_med = np.median([r["ttft_ms"] for r in eval_subset])
            prefill_med = np.median([r["prompt_ms"] for r in eval_subset])
            tok_med = int(np.median([r["prompt_tokens"] for r in eval_subset]))
            cached_med = int(np.median([r["cached_tokens"] for r in eval_subset]))
            print(f"    -> Median Tokens: {tok_med} (Cached: {cached_med}) | TTFT: {ttft_med:.1f} ms | Prefill: {prefill_med:.1f} ms")

    print(f"\n✅ Prefill ablation completed successfully! Saved {len(all_records)} trials to {JSONL_OUT}")

    # Generate outputs
    generate_latex_table(all_records)
    compute_prefill_regression_fit(all_records)


if __name__ == "__main__":
    run_prefill_ablation()
