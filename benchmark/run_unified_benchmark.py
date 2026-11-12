#!/usr/bin/env python3
"""
benchmark/run_unified_benchmark.py - Master Empirical Campaign Runner
Executes randomized, block-interleaved benchmark trials across all agent orchestrator
configurations with real hardware power telemetry (Apple SMC / Linux RAPL) and libproc attribution.
Fails fast with RuntimeError if neural endpoint is offline in real benchmark mode.
"""
from __future__ import annotations

import argparse
import http.server
import json
import os
import platform
import random
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from typing import Any

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_DIR)

from benchmark.adapters import get_adapter  # noqa: E402
from benchmark.analyze_results import analyze_publication_campaign  # noqa: E402
from benchmark.generate_charts import generate_all_charts  # noqa: E402
from benchmark.telemetry import (  # noqa: E402
    LinuxRAPLMonitor,
    SMCPowerMonitor,
)


class MockLlamaServerHandler(http.server.BaseHTTPRequestHandler):
    """
    Lightweight local mock loopback server for CI and dry-run validation.
    Handles /v1/chat/completions (streaming and non-streaming) and /health.
    """

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/health":
            body = b'{"status":"ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length).decode("utf-8", errors="ignore") if length > 0 else ""
        dynamic_tokens = max(1, len(raw_body.encode("utf-8")))

        is_streaming = '"stream":true' in raw_body.replace(" ", "")

        if is_streaming:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()

            # SSE chunk 1: role
            c1 = b'data: {"choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant"}}]}\n\n'
            self.wfile.write(c1)

            # SSE chunk 2: content
            c2 = b'data: {"choices":[{"finish_reason":null,"index":0,"delta":{"content":"Analysis complete."}}]}\n\n'
            self.wfile.write(c2)

            # SSE chunk 3: final timing with dynamic tokens
            c3 = f'data: {{"choices":[{{"finish_reason":"stop","index":0,"delta":{{}}}}],"timings":{{"prompt_ms":12.5,"predicted_ms":18.2,"prompt_n":{dynamic_tokens},"predicted_n":16}},"usage":{{"prompt_tokens":{dynamic_tokens},"completion_tokens":16}}}}\n\n'.encode("utf-8")
            self.wfile.write(c3)

            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
            self.close_connection = True
        else:
            resp_payload = {
                "id": "chatcmpl-mock-eval",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "Llama-3.2-3B-Instruct",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Analysis complete."},
                        "finish_reason": "stop",
                    }
                ],
                "timings": {"prompt_ms": 12.5, "predicted_ms": 18.2, "prompt_n": dynamic_tokens},
                "usage": {"prompt_tokens": dynamic_tokens, "completion_tokens": 16, "total_tokens": dynamic_tokens + 16},
            }
            body = json.dumps(resp_payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


def is_port_in_use(port: int = 8080) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def check_server_health(url: str = "http://127.0.0.1:8080/health", timeout: float = 2.0) -> bool:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def start_mock_server_if_needed(port: int = 8080) -> http.server.HTTPServer | None:
    if is_port_in_use(port):
        return None
    server = http.server.HTTPServer(("127.0.0.1", port), MockLlamaServerHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    return server


def collect_host_metadata() -> dict[str, Any]:
    meta = {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
    }
    if sys.platform == "darwin":
        try:
            res = subprocess.run(["sw_vers"], capture_output=True, text=True, timeout=2.0)
            meta["macos_version"] = res.stdout.strip().replace("\n", " | ")
        except Exception:
            pass
        try:
            res = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, timeout=2.0)
            meta["cpu_brand"] = res.stdout.strip()
        except Exception:
            pass
    try:
        node_bin = shutil.which("node") or os.path.join(REPO_DIR, "tools", "node", "bin", "node")
        if os.path.exists(node_bin):
            res = subprocess.run([node_bin, "--version"], capture_output=True, text=True, timeout=2.0)
            meta["node_version"] = res.stdout.strip()
    except Exception:
        pass
    try:
        go_bin = shutil.which("go") or os.path.join(REPO_DIR, "tools", "go", "bin", "go")
        if os.path.exists(go_bin):
            res = subprocess.run([go_bin, "version"], capture_output=True, text=True, timeout=2.0)
            meta["go_version"] = res.stdout.strip()
    except Exception:
        pass
    return meta


def run_campaign(
    reps_per_condition: int = 30,
    dry_run: bool = False,
    output_dir: str | None = None,
    cooldown_sec: float = 1.0,
):
    print("========================================================================")
    if dry_run:
        print(" 🧪 [PT-BR] Modo Dry-Run / Mock Rápido (Verificação Portátil de Pipeline)")
        print("    [EN-US] Dry-Run / Fast Mock Mode (Portable Pipeline Verification)")
    else:
        print(" 🚀 [PT-BR] Iniciando Campanha Experimental de Publicação (Medições Reais)")
        print("    [EN-US] Launching Publication Experimental Campaign (Hardware Measurements)")
    print("========================================================================")

    # Fail-Fast check when in real benchmark mode
    if not dry_run:
        health_url = os.environ.get("LLAMA_HEALTH_URL", "http://127.0.0.1:8080/health")
        if not check_server_health(health_url):
            raise RuntimeError(
                f"llama-server not reachable on {health_url}. "
                "Real benchmark mode requires llama-server listening on port 8080. "
                "Start llama-server or run with --dry-run for mock simulation."
            )

    if output_dir is None:
        output_dir = os.path.join(REPO_DIR, "results", "simulated_check" if dry_run else "publication_campaign")

    os.makedirs(output_dir, exist_ok=True)
    raw_trials_path = os.path.join(output_dir, "raw_trials.jsonl")

    # Start mock server if needed for dry-run
    if dry_run:
        port = 8088
        _mock_srv = start_mock_server_if_needed(port)
        _ = _mock_srv
        os.environ["LLAMA_API_URL"] = f"http://127.0.0.1:{port}/v1/chat/completions"
        print(f"🌐 [INFO] Local loopback mock server listening on 127.0.0.1:{port}.")
    else:
        os.environ["LLAMA_API_URL"] = "http://127.0.0.1:8080/v1/chat/completions"

    # Hardware Power Monitors
    smc_monitor = SMCPowerMonitor(sample_interval_ms=50)
    rapl_monitor = LinuxRAPLMonitor()

    if hasattr(os, "geteuid") and os.geteuid() == 0:
        print("ℹ️  [NOTICE] Running as root. Standard user execution with 'sudo -n' is supported.")

    telemetry_backend = "unprivileged_no_smc"
    if not dry_run:
        if smc_monitor.active:
            print("⚡ [INFO] Apple SMC hardware telemetry active (root powermetrics shunts).")
            print("         Measuring 5-second quiescent idle baseline...")
            idle_mw = smc_monitor.measure_idle_baseline(5.0)
            print(f"         Quiescent idle baseline package power: {idle_mw:.2f} mW.")
            telemetry_backend = smc_monitor.telemetry_backend
            print("         Starting continuous Apple SMC powermetrics sampler daemon...")
            smc_monitor.start_campaign()
        elif rapl_monitor.active:
            print("⚡ [INFO] Linux RAPL hardware energy counters active (/sys/class/powercap).")
            telemetry_backend = rapl_monitor.telemetry_backend
        else:
            print("⚠️  [NOTICE] Running unprivileged without root SMC shunts or RAPL.")
            print("            Latency, RSS, and process counters will be recorded.")
            print("            Joules energy fields will be recorded as null (N/A).\n")
            telemetry_backend = "unprivileged_no_smc" if sys.platform == "darwin" else "linux_psutil_unprivileged"

    host_meta = collect_host_metadata()
    agents = ["picoclaw", "openclaw_minimal", "openclaw_full", "python_native", "neural_baseline"]
    workloads = ["W1", "W2", "W3", "W4"]

    total_eval_trials = len(agents) * len(workloads) * reps_per_condition
    print(f"📊 Matrix: {len(agents)} agents x {len(workloads)} workloads x {reps_per_condition} reps = {total_eval_trials} evaluation trials.")

    # Instantiate and setup adapters
    adapter_instances = {}
    for ak in agents:
        ad = get_adapter(ak, REPO_DIR)
        if not ad.setup():
            raise RuntimeError(f"Failed to setup adapter '{ak}'. Check compiler and runtime paths.")
        adapter_instances[ak] = ad

    trials_written = 0
    rng = random.Random(42)

    try:
        with open(raw_trials_path, "w", encoding="utf-8") as out_f:
            # Phase A: Warmup rounds (3 per condition, discarded from statistics)
            if not dry_run:
                print("\n🔥 Executing warmup rounds (3 per condition, marked with is_warmup=True)...")
                for w in workloads:
                    for ak in agents:
                        for w_rep in range(3):
                            ad = adapter_instances[ak]
                            res = ad.run_workload(w, iterations=1)
                            record = {
                                "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                "agent_key": ak,
                                "architecture": ad.name,
                                "runtime": ad.runtime,
                                "workload": w,
                                "rep": w_rep + 1,
                                "is_warmup": True,
                                "is_simulated": False,
                                "data_source": "measured_hardware_warmup",
                                "t_task_ms": res.get("t_task_ms", 0.0),
                                "t_neural_ms": res.get("t_neural_ms", 0.0),
                                "t_orch_ms": res.get("t_orch_ms", 0.0),
                                "t_dispatch_ms": res.get("t_dispatch_ms", 0.0),
                                "t_http_ms": res.get("t_http_ms", 0.0),
                                "rss_peak_mb": res.get("rss_peak_mb", 0.0),
                                "proc_rss_mb": res.get("proc_rss_mb", res.get("rss_peak_mb", 0.0)),
                                "proc_instructions": res.get("proc_instructions", 0),
                                "proc_cycles": res.get("proc_cycles", 0),
                                "proc_billed_energy": res.get("proc_billed_energy", 0),
                                "proc_peak_phys_mb": round(res.get("proc_peak_phys_mb", 0.0), 2),
                                "prompt_tokens": res.get("prompt_tokens", 0),
                                "completion_tokens": res.get("completion_tokens", res.get("output_tokens", 0)),
                                "output_tokens": res.get("output_tokens", 0),
                                "tool_calls": res.get("tool_calls", 0),
                                "http_status": res.get("http_status", 200),
                                "finish_reason": res.get("finish_reason", "stop"),
                                "energy_total_j": None,
                                "energy_net_above_idle_j": None,
                                "edp_js": None,
                            }
                            out_f.write(json.dumps(record) + "\n")
                            out_f.flush()

            # Phase B: Main Evaluation Trials (Block-Interleaved Randomization)
            print("\n▶️  Dispatching randomized evaluation blocks...")
            for rep in range(1, reps_per_condition + 1):
                # Create block of all (agent, workload) conditions and shuffle
                block = [(ak, w) for ak in agents for w in workloads]
                rng.shuffle(block)

                for ak, w in block:
                    trials_written += 1
                    ad = adapter_instances[ak]

                    # Telemetry capture
                    t_start_ns = time.monotonic_ns()
                    if rapl_monitor.active:
                        rapl_monitor.start()

                    t0_trial = time.monotonic()
                    res = ad.run_workload(w, iterations=1)
                    t_elapsed_s = time.monotonic() - t0_trial
                    t_end_ns = time.monotonic_ns()

                    energy_dict = None
                    if smc_monitor.active:
                        energy_dict = smc_monitor.slice_energy(t_start_ns, t_end_ns)
                    elif rapl_monitor.active:
                        energy_dict = rapl_monitor.stop()

                    t_task_ms = res.get("t_task_ms", t_elapsed_s * 1000.0)
                    t_neural_ms = res.get("t_neural_ms", 0.0)
                    t_orch_ms = max(0.0, res.get("t_orch_ms", t_task_ms - t_neural_ms))
                    t_dispatch_ms = res.get("t_dispatch_ms", 0.0)
                    t_http_ms = res.get("t_http_ms", max(0.0, t_task_ms - t_neural_ms - t_dispatch_ms))
                    rss_peak = res.get("rss_peak_mb", 0.0)
                    tokens = res.get("output_tokens", 0)
                    prompt_tokens = res.get("prompt_tokens", 0)
                    completion_tokens = res.get("completion_tokens", tokens)

                    energy_total_j = None
                    energy_net_j = None
                    edp_js = None
                    j_per_token = None

                    if energy_dict is not None and energy_dict.get("energy_total_j") is not None:
                        energy_total_j = energy_dict["energy_total_j"]
                        energy_net_j = energy_dict["energy_net_above_idle_j"]
                        edp_js = round(energy_total_j * (t_task_ms / 1000.0), 4)
                        if tokens > 0:
                            j_per_token = round(energy_total_j / tokens, 4)
                        ds = "measured_hardware"
                    else:
                        ds = "dry_run_mock" if dry_run else "unprivileged_user_space"

                    trial_record = {
                        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "agent_key": ak,
                        "architecture": ad.name,
                        "runtime": ad.runtime,
                        "mode": ad.mode,
                        "workload": w,
                        "rep": rep,
                        "is_warmup": False,
                        "is_simulated": dry_run,
                        "data_source": ds,
                        "telemetry_backend": telemetry_backend,
                        "t_task_ms": round(t_task_ms, 2),
                        "t_neural_ms": round(t_neural_ms, 2),
                        "t_orch_ms": round(t_orch_ms, 3),
                        "phi_orch_pct": round((t_orch_ms / t_task_ms * 100.0) if t_task_ms > 0 else 0.0, 3),
                        "ttft_ms": round(res.get("ttft_ms", 0.0), 2),
                        "itl_ms": round(res.get("itl_ms", 0.0), 2),
                        "t_dispatch_ms": round(t_dispatch_ms, 3),
                        "t_http_ms": round(t_http_ms, 3),
                        "r_tool_ops_sec": round(res.get("r_tool_ops_sec", 0.0), 2),
                        "rss_idle_mb": round(res.get("rss_idle_mb", 0.0), 2),
                        "rss_peak_mb": round(rss_peak, 2),
                        "proc_rss_mb": round(res.get("proc_rss_mb", rss_peak), 2),
                        "proc_instructions": res.get("proc_instructions", 0),
                        "proc_cycles": res.get("proc_cycles", 0),
                        "proc_billed_energy": res.get("proc_billed_energy", 0),
                        "proc_peak_phys_mb": round(res.get("proc_peak_phys_mb", 0.0), 2),
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "output_tokens": tokens,
                        "tool_calls": res.get("tool_calls", 0),
                        "http_status": res.get("http_status", 200),
                        "finish_reason": res.get("finish_reason", "stop"),
                        "energy_total_j": energy_total_j,
                        "energy_net_above_idle_j": energy_net_j,
                        "edp_js": edp_js,
                        "joules_per_token": j_per_token,
                        "host_metadata": host_meta,
                    }

                    out_f.write(json.dumps(trial_record) + "\n")
                    out_f.flush()

                    edp_disp = f"{edp_js:.3f}J·s" if edp_js is not None else "N/A"
                    print(
                        f"   [{trials_written:03d}/{total_eval_trials:03d}] {ak:16s} {w} Rep {rep}: "
                        f"Task={t_task_ms:.1f}ms, Orch={t_orch_ms:.3f}ms, RAM={rss_peak:.1f}MB, EDP={edp_disp}"
                    )

                    if cooldown_sec > 0:
                        time.sleep(cooldown_sec)
    finally:
        if smc_monitor.active:
            smc_monitor.stop_campaign()

    # Generate analytical tables and statistical tests
    print("\n📈 Executing non-parametric statistical analysis...")
    analyze_publication_campaign(raw_trials_path, output_dir)

    # Generate publication charts
    print("\n🎨 Generating publication charts...")
    generate_all_charts(output_dir)


def main():
    parser = argparse.ArgumentParser(description="Unified Agent Benchmark Campaign Runner")
    parser.add_argument("--dry-run", action="store_true", help="Fast mock validation mode for CI and portable testing")
    parser.add_argument("--reps", type=int, default=None, help="Repetitions per condition (defaults: 2 for dry-run, 30 for publication)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for trials and tables")
    parser.add_argument("--cooldown", type=float, default=None, help="Cooldown sleep in seconds between trials")
    args = parser.parse_args()

    reps = args.reps if args.reps is not None else (2 if args.dry_run else 30)
    cooldown = args.cooldown if args.cooldown is not None else (0.05 if args.dry_run else 0.5)

    run_campaign(
        reps_per_condition=reps,
        dry_run=args.dry_run,
        output_dir=args.output_dir,
        cooldown_sec=cooldown,
    )


if __name__ == "__main__":
    main()
