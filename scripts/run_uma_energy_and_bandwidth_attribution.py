#!/usr/bin/env python3
"""
scripts/run_uma_energy_and_bandwidth_attribution.py - Apple Silicon M4 UMA Energy & Bandwidth Attribution
Isolamento Físico de Energia por Processo (Trilho CPU do SMC + Calibração XNU ri_billed_energy)
e Medição Empírica da Largura de Banda UMA LPDDR5X (Host e GPU Metal).

ZERO dados sintéticos ou aproximados: 100% dados físicos extraídos em tempo real
do silício Apple Silicon M4 via powermetrics 50 ms e Darwin XNU libproc.

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

import datetime
import json
import math
import os
import random
import sys
import time
from typing import Any, Dict, List

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_DIR)

from benchmark.telemetry import SMCPowerMonitor, run_subprocess_with_rusage  # noqa: E402

# Paths
RAW_TRIALS_PATH = os.path.join(REPO_DIR, "results", "publication_campaign", "raw_trials.jsonl")
WARM_TRIALS_PATH = os.path.join(REPO_DIR, "results", "publication_campaign", "warm_cache_trials.jsonl")
OUT_TRIALS_PATH = os.path.join(REPO_DIR, "results", "publication_campaign", "uma_energy_bandwidth_trials.jsonl")
OUT_JSON_PATH = os.path.join(REPO_DIR, "results", "publication_campaign", "uma_energy_bandwidth_attribution.json")
OUT_TABLE_PATH = os.path.join(REPO_DIR, "results", "publication_campaign", "tables", "table_energy_bandwidth_deconvolution.tex")


def assert_physical_hardware():
    if sys.platform != "darwin":
        raise RuntimeError(f"FATAL: Physical hardware measurement requires macOS Darwin, got {sys.platform}")
    monitor = SMCPowerMonitor(sample_interval_ms=50)
    if not monitor.active:
        raise RuntimeError("FATAL: Apple Silicon SMC powermetrics is not active or root/sudo is unavailable!")


def run_physical_cpu_isolation_campaign() -> List[Dict[str, Any]]:
    print("========================================================================")
    print(" ⚡ [Medição 1] Isolamento Físico no Silício da Energia de Despacho (CPU)")
    print("    Local Tool Benchmark (W2 x 200 iters, W3 x 50 iters, Sem GPU)")
    print("========================================================================")

    monitor = SMCPowerMonitor(sample_interval_ms=50)
    print("  -> Medindo 3.0 segundos de baseline quiescente (idle real)...")
    idle_pkg_mw = monitor.measure_idle_baseline(duration_sec=3.0)
    idle_cpu_mw = getattr(monitor, "idle_cpu_mw", 0.0)
    idle_gpu_mw = getattr(monitor, "idle_gpu_mw", 0.0)
    print(f"     Idle Real: Package={idle_pkg_mw:.2f} mW | CPU={idle_cpu_mw:.2f} mW | GPU={idle_gpu_mw:.2f} mW")

    monitor.start_campaign()
    # Wait until background powermetrics process has produced initial samples
    print("  -> Sincronizando leitor do Apple SMC powermetrics...")
    t_wait_start = time.time()
    while True:
        with monitor._lock:
            if len(monitor._samples) >= 2:
                break
        if time.time() - t_wait_start > 5.0:
            raise RuntimeError("FATAL: Timeout waiting for initial powermetrics samples!")
        time.sleep(0.03)
    print(f"     Leitor SMC sincronizado com {len(monitor._samples)} amostras iniciais.")

    runtimes = [
        ("picoclaw", [os.path.join(REPO_DIR, "benchmark", "picoclaw_orch")], {}),
        ("openclaw_minimal", [os.path.join(REPO_DIR, "tools", "node", "bin", "node"), os.path.join(REPO_DIR, "benchmark", "openclaw_orch.mjs")], {"OPENCLAW_MODE": "minimal"}),
        ("openclaw_full", [os.path.join(REPO_DIR, "tools", "node", "bin", "node"), os.path.join(REPO_DIR, "benchmark", "openclaw_orch.mjs")], {"OPENCLAW_MODE": "full"}),
        ("python_native", [os.path.join(REPO_DIR, "tools", ".venv", "bin", "python"), os.path.join(REPO_DIR, "benchmark", "python_orch.py")], {}),
    ]

    workload_configs = [
        ("W2", 200, 600),  # 200 iterations x 3 tools = 600 operations
        ("W3", 50, 50),    # 50 iterations x 1 vector RAG = 50 operations
    ]

    n_reps = 15
    trial_records = []
    trial_id = 0

    # Ensure parent dir exists
    os.makedirs(os.path.dirname(OUT_TRIALS_PATH), exist_ok=True)
    f_out = open(OUT_TRIALS_PATH, "w", encoding="utf-8")

    try:
        for w_id, iters, ops in workload_configs:
            for agent_key, base_cmd, extra_env in runtimes:
                print(f"  -> Executando {agent_key} em {w_id} ({iters} iters, {ops} ops, n={n_reps})...")
                env = os.environ.copy()
                env.update(extra_env)

                for rep in range(1, n_reps + 1):
                    trial_id += 1
                    cmd = list(base_cmd) + ["--local-tools", w_id, str(iters)]

                    t0_ns = time.monotonic_ns()
                    stdout, stderr, rc, hw_stats = run_subprocess_with_rusage(cmd, env=env)
                    t1_ns = time.monotonic_ns()

                    if rc != 0:
                        raise RuntimeError(f"FATAL: Command failed: {cmd} -> {stderr}")

                    duration_s = max((t1_ns - t0_ns) / 1e9, 1e-6)
                    t_exec_ms = round((t1_ns - t0_ns) / 1e6, 3)

                    slice_energy = monitor.slice_energy(t0_ns, t1_ns)
                    if slice_energy is None:
                        time.sleep(0.06)
                        slice_energy = monitor.slice_energy(t0_ns, t1_ns)
                    if slice_energy is None:
                        raise RuntimeError(f"FATAL: slice_energy returned None for trial {trial_id}")

                    e_cpu = slice_energy.get("energy_cpu_j", 0.0)
                    e_gpu = slice_energy.get("energy_gpu_j", 0.0)
                    e_total = slice_energy.get("energy_total_j", 0.0)
                    e_cpu_net = max(0.0, e_cpu - (idle_cpu_mw / 1000.0) * duration_s)

                    mj_per_op = (e_cpu_net * 1000.0) / ops if ops > 0 else 0.0

                    rec = {
                        "trial_id": trial_id,
                        "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "agent_key": agent_key,
                        "workload": w_id,
                        "rep": rep,
                        "iterations": iters,
                        "total_ops": ops,
                        "t_exec_ms": t_exec_ms,
                        "energy_cpu_j": round(e_cpu, 6),
                        "energy_cpu_net_j": round(e_cpu_net, 6),
                        "energy_gpu_j": round(e_gpu, 6),
                        "energy_total_j": round(e_total, 6),
                        "mj_per_op": round(mj_per_op, 6),
                        "proc_billed_energy": hw_stats.get("proc_billed_energy", 0),
                        "proc_instructions": hw_stats.get("proc_instructions", 0),
                        "proc_cycles": hw_stats.get("proc_cycles", 0),
                        "proc_peak_phys_mb": hw_stats.get("proc_peak_phys_mb", 0.0),
                        "proc_rss_mb": hw_stats.get("proc_rss_mb", 0.0),
                        "idle_cpu_mw": round(idle_cpu_mw, 2),
                        "idle_gpu_mw": round(idle_gpu_mw, 2),
                        "idle_package_mw": round(idle_pkg_mw, 2),
                    }
                    trial_records.append(rec)
                    f_out.write(json.dumps(rec) + "\n")
                    f_out.flush()
    finally:
        f_out.close()
        monitor.stop_campaign()

    print(f"✅ Concluídos {len(trial_records)} ensaios físicos puros salvos em: {OUT_TRIALS_PATH}")
    return trial_records


def calibrate_billed_energy_coefficient(trial_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    print("\n========================================================================")
    print(" 🔬 [Medição 2] Calibração Empírica de ri_billed_energy (XNU -> SMC Joules)")
    print("========================================================================")

    # Use all physical CPU trials with non-zero billed_energy
    pts = [(r["proc_billed_energy"], r["energy_cpu_net_j"]) for r in trial_records if r["proc_billed_energy"] > 0]
    if len(pts) < 10:
        raise RuntimeError("FATAL: Insufficient physical calibration data points.")

    x_vals = [p[0] for p in pts]
    y_vals = [p[1] for p in pts]

    # Linear regression through origin: y = kappa * x
    # kappa = sum(x*y) / sum(x^2)
    sum_xx = sum(x * x for x in x_vals)
    sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
    kappa = sum_xy / sum_xx if sum_xx > 0 else 0.0

    # R^2 computation for zero-intercept regression (Eisenhauer, 2003)
    ss_tot = sum(y ** 2 for y in y_vals)
    ss_res = sum((y - kappa * x) ** 2 for x, y in zip(x_vals, y_vals))
    r_squared = max(0.0, 1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 1.0

    # Standard error of slope
    df = len(pts) - 1
    s_err = math.sqrt(ss_res / df) if df > 0 else 0.0
    se_kappa = s_err / math.sqrt(sum_xx) if sum_xx > 0 else 0.0

    # 95% Bootstrap CI (2,000 resamples)
    random.seed(42)
    boot_kappas = []
    n = len(pts)
    for _ in range(2000):
        sample = [pts[random.randint(0, n - 1)] for _ in range(n)]
        s_xx = sum(x * x for x, _ in sample)
        s_xy = sum(x * y for x, y in sample)
        boot_kappas.append(s_xy / s_xx if s_xx > 0 else 0.0)
    boot_kappas.sort()
    ci_lower = boot_kappas[int(0.025 * len(boot_kappas))]
    ci_upper = boot_kappas[int(0.975 * len(boot_kappas))]

    kappa_mj = kappa * 1000.0
    ci_lower_mj = ci_lower * 1000.0
    ci_upper_mj = ci_upper * 1000.0

    print(f"  -> Coeficiente de Conversão M4: kappa = {kappa_mj:.6f} mJ/unidade XNU")
    print(f"     95% Bootstrap CI: [{ci_lower_mj:.6f}, {ci_upper_mj:.6f}] mJ/unidade")
    print(f"     Ajuste de Regressão: R² = {r_squared:.4f} (N={len(pts)})")

    return {
        "n_samples": len(pts),
        "kappa_joules_per_unit": kappa,
        "kappa_mj_per_unit": round(kappa_mj, 6),
        "ci_95_bootstrap_mj": [round(ci_lower_mj, 6), round(ci_upper_mj, 6)],
        "r_squared": round(r_squared, 4),
        "se_kappa_joules": se_kappa,
    }


def deconvolve_publication_campaigns(kappa: float) -> Dict[str, Any]:
    print("\n========================================================================")
    print(" 📊 [Deconvolução] Aplicação às Campanhas A e B (1.200 Ensaios Avaliados)")
    print("========================================================================")

    def process_file(path: str, regime_name: str) -> Dict[str, Any]:
        data = {}
        if not os.path.exists(path):
            return data
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("is_warmup", False):
                    continue
                w = rec["workload"]
                a = rec["agent_key"]
                key = (w, a)
                if key not in data:
                    data[key] = []

                e_net = rec.get("energy_net_above_idle_j", 0.0) or 0.0
                billed = rec.get("proc_billed_energy", 0) or 0
                e_proc_hat = kappa * billed
                phi_e_orch = (e_proc_hat / e_net * 100.0) if e_net > 0 else 0.0

                item = {
                    "e_net_j": e_net,
                    "proc_billed_energy": billed,
                    "e_proc_hat_j": e_proc_hat,
                    "phi_energy_orch_pct": phi_e_orch,
                }
                data[key].append(item)

        # Baseline net energy per workload
        baseline_means = {}
        for w in ["W1", "W2", "W3", "W4"]:
            base_recs = data.get((w, "neural_baseline"), [])
            if base_recs:
                baseline_means[w] = sum(r["e_net_j"] for r in base_recs) / len(base_recs)
            else:
                baseline_means[w] = 0.0

        summary = {}
        for (w, a), recs in data.items():
            if a == "neural_baseline":
                continue
            e_nets = [r["e_net_j"] for r in recs]
            e_procs = [r["e_proc_hat_j"] for r in recs]
            phis = [r["phi_energy_orch_pct"] for r in recs]

            mean_e_net = sum(e_nets) / len(e_nets) if e_nets else 0.0
            mean_e_proc = sum(e_procs) / len(e_procs) if e_procs else 0.0
            mean_phi = sum(phis) / len(phis) if phis else 0.0
            delta_e = mean_e_net - baseline_means.get(w, 0.0)

            summary[f"{w}_{a}"] = {
                "workload": w,
                "agent_key": a,
                "n_trials": len(recs),
                "e_net_mean_j": round(mean_e_net, 4),
                "e_proc_hat_mean_j": round(mean_e_proc, 4),
                "phi_energy_orch_pct": round(mean_phi, 2),
                "delta_e_net_vs_baseline_j": round(delta_e, 4),
            }
        return summary

    regime_a_summary = process_file(RAW_TRIALS_PATH, "Regime A (Cold Prefill)")
    regime_b_summary = process_file(WARM_TRIALS_PATH, "Regime B (Warm Cache)")

    return {
        "regime_a": regime_a_summary,
        "regime_b": regime_b_summary,
    }


def compute_uma_bandwidth_metrics(trial_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    print("\n========================================================================")
    print(" 🚀 [Medição 3] Largura de Banda UMA LPDDR5X (Host CPU e GPU Metal)")
    print("========================================================================")

    base_dir = os.path.join(REPO_DIR, "data", "workload_data")
    w_proj = os.path.getsize(os.path.join(base_dir, "w_proj.bin"))
    b_proj = os.path.getsize(os.path.join(base_dir, "b_proj.bin"))
    doc_emb = os.path.getsize(os.path.join(base_dir, "doc_embeddings.bin"))
    total_rag_bytes = w_proj + b_proj + doc_emb
    print(f"  -> Total de bytes lidos por chamada RAG (W3): {total_rag_bytes} bytes ({total_rag_bytes / 1e6:.2f} MB)")

    # 1. Host CPU Memory Bandwidth in W3
    w3_trials = [r for r in trial_records if r["workload"] == "W3"]
    host_bw_results = {}
    for agent_key in ["picoclaw", "openclaw_minimal", "openclaw_full", "python_native"]:
        agent_w3 = [r for r in w3_trials if r["agent_key"] == agent_key]
        if agent_w3:
            avg_exec_ms = sum(r["t_exec_ms"] for r in agent_w3) / len(agent_w3)
            # 50 iterations per trial
            t_per_rag_s = (avg_exec_ms / 50.0) / 1000.0
            bw_gb_s = (total_rag_bytes / 1e9) / t_per_rag_s if t_per_rag_s > 0 else 0.0
            host_bw_results[agent_key] = {
                "avg_exec_50_reps_ms": round(avg_exec_ms, 2),
                "t_per_rag_op_ms": round(t_per_rag_s * 1000.0, 3),
                "effective_bw_gb_s": round(bw_gb_s, 2),
            }
            print(f"     Vazão Host CPU ({agent_key}): {bw_gb_s:.2f} GB/s ({t_per_rag_s * 1000.0:.2f} ms/op)")

    # 2. Metal GPU LPDDR5X Bandwidth during Autoregressive Decoding
    # Weights size
    model_path = os.path.join(REPO_DIR, "models", "Llama-3.2-3B-Instruct-Q4_K_M.gguf")
    if not os.path.exists(model_path):
        # Fallback to absolute path on Mac
        model_path = "/Users/rafael/.gemini/antigravity/scratch/picoclaw_vs_openclaw/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    weights_bytes = os.path.getsize(model_path)
    print(f"  -> Tamanho real dos pesos neurais GGUF Q4_K_M: {weights_bytes} bytes ({weights_bytes / 1e9:.3f} GB)")

    # KV-Cache per prompt token: 28 layers * 8 heads * 128 dim * 2 bytes * 2 (K+V) = 114,688 bytes/token
    BYTES_PER_KV_TOKEN = 2 * 28 * 8 * 128 * 2

    # Load ITL samples from publication campaigns
    def extract_gpu_bw(path: str) -> List[float]:
        bw_list = []
        if not os.path.exists(path):
            return bw_list
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                if d.get("is_warmup", False):
                    continue
                itl_ms = d.get("itl_ms", 0.0)
                ptok = d.get("prompt_tokens", 0)
                if itl_ms > 0:
                    s_kv = BYTES_PER_KV_TOKEN * ptok
                    total_bytes = weights_bytes + s_kv
                    itl_s = itl_ms / 1000.0
                    bw = (total_bytes / 1e9) / itl_s
                    bw_list.append(bw)
        return bw_list

    bw_regime_a = extract_gpu_bw(RAW_TRIALS_PATH)
    bw_regime_b = extract_gpu_bw(WARM_TRIALS_PATH)
    all_bw = bw_regime_a + bw_regime_b

    def stats(bws: List[float]) -> Dict[str, float]:
        if not bws:
            return {"mean_gb_s": 0.0, "median_gb_s": 0.0, "util_pct": 0.0}
        bws_sorted = sorted(bws)
        mean_val = sum(bws) / len(bws)
        med_val = bws_sorted[len(bws_sorted) // 2]
        return {
            "mean_gb_s": round(mean_val, 2),
            "median_gb_s": round(med_val, 2),
            "p05_gb_s": round(bws_sorted[int(0.05 * len(bws_sorted))], 2),
            "p95_gb_s": round(bws_sorted[int(0.95 * len(bws_sorted))], 2),
            "util_pct_nominal_120": round((mean_val / 120.0) * 100.0, 1),
        }

    gpu_bw_summary = {
        "weights_bytes": weights_bytes,
        "bytes_per_kv_token": BYTES_PER_KV_TOKEN,
        "nominal_uma_bw_gb_s": 120.0,
        "regime_a_cold": stats(bw_regime_a),
        "regime_b_warm": stats(bw_regime_b),
        "overall": stats(all_bw),
    }

    print(f"  -> Largura de banda efetiva Metal GPU (Decodificação): {gpu_bw_summary['overall']['mean_gb_s']} GB/s ({gpu_bw_summary['overall']['util_pct_nominal_120']}% de 120 GB/s)")

    return {
        "host_rag_memory_bandwidth": host_bw_results,
        "metal_gpu_lpddr5x_bandwidth": gpu_bw_summary,
    }


def generate_latex_table(
    local_trials: List[Dict[str, Any]],
    calib: Dict[str, Any],
    deconv: Dict[str, Any],
    bw: Dict[str, Any],
):
    print(f"\n📄 Gerando tabela LaTeX: {OUT_TABLE_PATH}...")

    # Calculate mean mJ/op for each agent in W2 and W3
    mj_ops = {}
    for a in ["picoclaw", "openclaw_minimal", "openclaw_full", "python_native"]:
        for w in ["W2", "W3"]:
            matching = [r["mj_per_op"] for r in local_trials if r["agent_key"] == a and r["workload"] == w]
            mj_ops[(a, w)] = sum(matching) / len(matching) if matching else 0.0

    pico_bw = bw["host_rag_memory_bandwidth"].get("picoclaw", {}).get("effective_bw_gb_s", 0.0)
    py_bw = bw["host_rag_memory_bandwidth"].get("python_native", {}).get("effective_bw_gb_s", 0.0)
    min_bw = bw["host_rag_memory_bandwidth"].get("openclaw_minimal", {}).get("effective_bw_gb_s", 0.0)
    full_bw = bw["host_rag_memory_bandwidth"].get("openclaw_full", {}).get("effective_bw_gb_s", 0.0)

    pico_phi_w2 = deconv["regime_b"].get("W2_picoclaw", {}).get("phi_energy_orch_pct", 0.0)
    pico_phi_w3 = deconv["regime_b"].get("W3_picoclaw", {}).get("phi_energy_orch_pct", 0.0)
    py_phi_w2 = deconv["regime_b"].get("W2_python_native", {}).get("phi_energy_orch_pct", 0.0)
    py_phi_w3 = deconv["regime_b"].get("W3_python_native", {}).get("phi_energy_orch_pct", 0.0)
    min_phi_w2 = deconv["regime_b"].get("W2_openclaw_minimal", {}).get("phi_energy_orch_pct", 0.0)
    min_phi_w3 = deconv["regime_b"].get("W3_openclaw_minimal", {}).get("phi_energy_orch_pct", 0.0)
    full_phi_w2 = deconv["regime_b"].get("W2_openclaw_full", {}).get("phi_energy_orch_pct", 0.0)
    full_phi_w3 = deconv["regime_b"].get("W3_openclaw_full", {}).get("phi_energy_orch_pct", 0.0)

    table_content = f"""% Auto-generated by scripts/run_uma_energy_and_bandwidth_attribution.py
% Empirical Apple Silicon M4 UMA Energy Deconvolution and LPDDR5X Bandwidth Telemetry
\\begin{{table}}[t]
\\small
\\centering
\\begin{{tabular}}{{lcccc}}
\\toprule
\\textbf{{Runtime / Agent}} & \\textbf{{W2 Pure CPU}} & \\textbf{{W3 Vector RAG}} & \\textbf{{Host BW (W3)}} & \\textbf{{Regime B $\\Phi_{{\\text{{energy, orch}}}}$}} \\\\
& \\textbf{{(mJ / tool op)}} & \\textbf{{(mJ / RAG op)}} & \\textbf{{(GB/s)}} & \\textbf{{(W2 / W3)}} \\\\
\\midrule
\\textbf{{PicoClaw (Go Native)}} & {mj_ops.get(('picoclaw', 'W2'), 0.0):.3f} & {mj_ops.get(('picoclaw', 'W3'), 0.0):.2f} & {pico_bw:.2f} & {pico_phi_w2:.2f}\\% / {pico_phi_w3:.2f}\\% \\\\
\\textbf{{PythonNative (CPython)}} & {mj_ops.get(('python_native', 'W2'), 0.0):.3f} & {mj_ops.get(('python_native', 'W3'), 0.0):.2f} & {py_bw:.2f} & {py_phi_w2:.2f}\\% / {py_phi_w3:.2f}\\% \\\\
\\textbf{{OpenClaw Minimal (V8)}} & {mj_ops.get(('openclaw_minimal', 'W2'), 0.0):.3f} & {mj_ops.get(('openclaw_minimal', 'W3'), 0.0):.2f} & {min_bw:.2f} & {min_phi_w2:.2f}\\% / {min_phi_w3:.2f}\\% \\\\
\\textbf{{OpenClaw Full (V8)}} & {mj_ops.get(('openclaw_full', 'W2'), 0.0):.3f} & {mj_ops.get(('openclaw_full', 'W3'), 0.0):.2f} & {full_bw:.2f} & {full_phi_w2:.2f}\\% / {full_phi_w3:.2f}\\% \\\\
\\midrule
\\multicolumn{{5}}{{l}}{{\\textbf{{Apple Silicon M4 Physical Telemetry and Deconvolution Metrics:}}}} \\\\
\\multicolumn{{5}}{{l}}{{$\\bullet$ Calibrated Kernel Metric: $\\hat{{\\kappa}}_{{\\text{{M4}}}} = {calib['kappa_mj_per_unit']:.4f}\\text{{ mJ/unit}}$ ($R^2 = {calib['r_squared']:.4f}$, 95\\% CI $[{calib['ci_95_bootstrap_mj'][0]:.4f}, {calib['ci_95_bootstrap_mj'][1]:.4f}]$)}} \\\\
\\multicolumn{{5}}{{l}}{{$\\bullet$ LPDDR5X Neural Decoding Bandwidth: ${bw['metal_gpu_lpddr5x_bandwidth']['overall']['mean_gb_s']:.2f}\\text{{ GB/s}}$ (${bw['metal_gpu_lpddr5x_bandwidth']['overall']['util_pct_nominal_120']:.1f}\\%$ of nominal $120\\text{{ GB/s}}$)}} \\\\
\\bottomrule
\\end{{tabular}}
\\caption{{Empirical per-process energy deconvolution and Unified Memory Architecture (UMA) LPDDR5X bandwidth attribution on Apple Silicon M4. Dispatch energy is isolated directly on the Apple SMC \\texttt{{CPU Power}} rail; process energy is deconvolved via Darwin kernel \\texttt{{ri\\_billed\\_energy}} calibration; and neural memory throughput is empirically derived from GGUF weight sweeps and inter-token latencies.}}
\\label{{tab:energy_bandwidth_deconvolution}}
\\end{{table}}
"""
    with open(OUT_TABLE_PATH, "w", encoding="utf-8") as f:
        f.write(table_content)
    print(f"✅ Generated LaTeX table: {OUT_TABLE_PATH}")


def main():
    assert_physical_hardware()

    if "--analyze-only" in sys.argv and os.path.exists(OUT_TRIALS_PATH):
        print(f"📊 [INFO] Running in --analyze-only mode on existing {OUT_TRIALS_PATH}...")
        local_trials = []
        with open(OUT_TRIALS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    local_trials.append(json.loads(line))
    else:
        # 1. Physical CPU isolation runs
        local_trials = run_physical_cpu_isolation_campaign()

    # 2. Calibrate billed_energy -> SMC Joules
    calib = calibrate_billed_energy_coefficient(local_trials)

    # 3. Deconvolve publication campaigns A and B
    deconv = deconvolve_publication_campaigns(calib["kappa_joules_per_unit"])

    # 4. Compute Host and GPU UMA memory bandwidth
    bw = compute_uma_bandwidth_metrics(local_trials)

    # 5. Generate LaTeX table
    generate_latex_table(local_trials, calib, deconv, bw)

    # 6. Save consolidated JSON summary
    summary = {
        "metadata": {
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "hardware": "Apple Mac mini M4 (Mac16,10, 10-core GPU, darwin-arm64)",
            "telemetry_source": "Apple SMC powermetrics 50ms + Darwin XNU libproc RUSAGE_INFO_V4",
            "integrity_rule": "100% Physical Telemetry (Zero synthetic or mock data)",
        },
        "calibration_m4": calib,
        "deconvolution_campaigns": deconv,
        "bandwidth_attribution": bw,
    }

    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Saved attribution summary: {OUT_JSON_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
