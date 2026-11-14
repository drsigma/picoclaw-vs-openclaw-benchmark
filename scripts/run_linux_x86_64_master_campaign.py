#!/usr/bin/env python3
"""
scripts/run_linux_x86_64_master_campaign.py - Linux x86_64 empirical campaign (zero mocks, fail-fast).

Executes the same matrix as the darwin-aarch64 campaign with the native Linux telemetry adapter:
  * Regime A (cold prefill, cache_prompt=false) and Regime B (warm KV cache, cache_prompt=true)
    x W1..W4 x {Go, Node.js V8 minimal/full, Python, Bun JSC, neural baseline}
  * Tool-RAG pruner arms (openclaw_tool_rag, picoclaw_tool_rag), real t_prune_ms from the workers
  * KV-cache regimes T1 (cold) / T2 (interleaved distinct tool catalogs) / T3 (isolated prefix)
  * MCP transport ablation against the repository's real benchmark/mcp_server.py (stdio vs HTTP)
and then calls benchmark/linux_campaign_analysis.py to derive every JSON / table / report.

Isolation: this process can only write under data/<os>_<arch>/, results/publication_campaign_<os>_<arch>/
and data/manifest_sha256_<os>_<arch>.json. Any other write target terminates the process with exit 1.
The run is resumable: finished trials are keyed and skipped on restart.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import random
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import uuid
from typing import Any

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_DIR)
sys.path.insert(0, os.path.join(REPO_DIR, "scripts"))

# ------------------------------------------------------------------------------
# Namespaces and write guard
# ------------------------------------------------------------------------------
if platform.system() != "Linux":
    print("FATAL: this runner is Linux-only (darwin data is read-only).", file=sys.stderr)
    sys.exit(1)

ARCH_TAG = f"{platform.system().lower()}_{platform.machine()}"


class Paths:
    def __init__(self, suffix: str = "") -> None:
        self.data = os.path.join(REPO_DIR, "data", ARCH_TAG + suffix)
        self.raw = os.path.join(self.data, "raw")
        self.results = os.path.join(REPO_DIR, "results", f"publication_campaign_{ARCH_TAG}{suffix}")
        self.tables = os.path.join(self.results, "tables")
        self.manifest = os.path.join(REPO_DIR, "data", f"manifest_sha256_{ARCH_TAG}{suffix}.json")
        self.allowed = (self.data, self.results, self.manifest)
        self.forbidden = tuple(os.path.join(REPO_DIR, p) for p in (
            "data/darwin-aarch64", "data/darwin_aarch64", "data/darwin_arm64",
            "results/publication_campaign", "results/publication_campaign_darwin_aarch64",
            "results/publication_campaign_darwin_arm64", "data/raw", "data/manifest_sha256.json",
            "data/workload_data", "data/llama_server_stdout.log"))


PATHS = Paths()


def guard(path: str) -> str:
    rp = os.path.realpath(path)
    in_allowed = any(rp == a or rp.startswith(a + os.sep) for a in PATHS.allowed)
    in_forbidden = any(rp == f or rp.startswith(f + os.sep) for f in PATHS.forbidden) or "darwin" in rp.lower()
    if not in_allowed or in_forbidden:
        print(f"FATAL (isolation guard): refusing to write outside the {ARCH_TAG} namespace: {rp}", file=sys.stderr)
        sys.exit(1)
    return path


def wmakedirs(path: str) -> None:
    os.makedirs(guard(path), exist_ok=True)


def wopen(path: str, mode: str = "w"):
    return open(guard(path), mode, encoding=None if "b" in mode else "utf-8")


def wjson(path: str, obj: Any) -> None:
    with wopen(path, "w") as f:
        json.dump(obj, f, indent=2)


def append_jsonl(path: str, rec: dict[str, Any]) -> None:
    with wopen(path, "a") as f:
        f.write(json.dumps(rec, allow_nan=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def load_jsonl(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def die(msg: str) -> None:
    print(f"\nFAIL-FAST: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


# ------------------------------------------------------------------------------
# Lazy heavy imports (after guard is armed)
# ------------------------------------------------------------------------------
import numpy as np  # noqa: E402

from benchmark.adapters import get_adapter  # noqa: E402
from benchmark.linux_x86_64_telemetry_adapter import (  # noqa: E402
    LinuxHardwarePowerMonitor,
    ThermalController,
    assert_pmu_available,
    detect_linux_host_provenance,
)
from benchmark.protocol_invariants import validate_gate_0_provenance_fields  # noqa: E402
from benchmark.python_orch import (  # noqa: E402
    BASE_DIR,
    build_tool_catalog,
    execute_tool_calc_stats,
    execute_tool_grep_logs,
    execute_tool_list_dir,
)

API_URL = "http://127.0.0.1:8080/v1/chat/completions"
HEALTH_URL = "http://127.0.0.1:8080/health"
MAIN_ARMS = ["picoclaw", "openclaw_minimal", "openclaw_full", "python_native", "bun_minimal", "neural_baseline"]
TOOL_RAG_ARMS = ["openclaw_tool_rag", "picoclaw_tool_rag"]
WORKLOADS = ["W1", "W2", "W3", "W4"]
GPU_THERMAL_MASK = 0x20 | 0x40  # SW thermal slowdown | HW thermal slowdown


# ------------------------------------------------------------------------------
# llama-server lifecycle
# ------------------------------------------------------------------------------
class LlamaServer:
    def __init__(self, model: str, mac_flags: str, ngl: int, log_path: str) -> None:
        toks = mac_flags.split()
        out, i = [], 0
        while i < len(toks):
            if toks[i] == "-ngl":
                i += 2
                continue
            out.append(toks[i])
            i += 1
        self.flag_tokens = out + ["-ngl", str(ngl)]
        self.model = model
        self.log_path = log_path
        self.proc: subprocess.Popen | None = None
        self.server_flags = ""

    def start(self) -> None:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080)) == 0:
                die("port 8080 is already in use; stop the existing llama-server first")
        exe = shutil.which("llama-server")
        if not exe:
            die("llama-server not found in PATH")
        cmd = [exe, "-m", self.model, "--port", "8080"] + self.flag_tokens
        self._log = wopen(self.log_path, "ab")
        self.proc = subprocess.Popen(cmd, stdout=self._log, stderr=subprocess.STDOUT)
        t0 = time.monotonic()
        while True:
            if self.proc.poll() is not None:
                die(f"llama-server exited early (rc={self.proc.returncode}); see {self.log_path}")
            try:
                with urllib.request.urlopen(HEALTH_URL, timeout=2) as r:
                    if r.status == 200:
                        break
            except Exception:
                pass
            if time.monotonic() - t0 > 300:
                die("llama-server did not become healthy in 300 s")
            time.sleep(0.5)
        with open(f"/proc/{self.proc.pid}/cmdline", "rb") as f:
            argv = [a.decode() for a in f.read().split(b"\0") if a]
        keep, i = [], 1
        while i < len(argv):
            if argv[i] in ("-m", "--port"):
                i += 2
                continue
            keep.append(argv[i])
            i += 1
        self.server_flags = " ".join(keep)

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def stream_request(messages: list[dict[str, Any]], tools: list[dict[str, Any]], cache_prompt: bool,
                   max_tokens: int, on_first_token=None) -> dict[str, Any]:
    payload = json.dumps({
        "model": "bench", "messages": messages, "tools": tools, "max_tokens": max_tokens,
        "temperature": 0.0, "seed": 42, "stream": True, "cache_prompt": cache_prompt,
    }, separators=(",", ":")).encode()
    req = urllib.request.Request(API_URL, data=payload, headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    first = None
    timings: dict[str, Any] | None = None
    usage: dict[str, Any] = {}
    finish = None
    status = None
    with urllib.request.urlopen(req, timeout=900) as resp:
        status = resp.status
        for raw in resp:
            line = raw.decode().strip()
            if not line.startswith("data: "):
                continue
            body = line[6:].strip()
            if body == "[DONE]":
                break
            chunk = json.loads(body)
            ch = chunk.get("choices") or []
            if ch:
                if ch[0].get("finish_reason"):
                    finish = ch[0]["finish_reason"]
                d = ch[0].get("delta", {})
                if (d.get("content") or d.get("tool_calls")) and first is None:
                    first = time.perf_counter()
                    if on_first_token:
                        on_first_token()
            if isinstance(chunk.get("timings"), dict):
                timings = chunk["timings"]
            if isinstance(chunk.get("usage"), dict):
                usage = chunk["usage"]
    t1 = time.perf_counter()
    if status != 200:
        die(f"llama-server HTTP {status}")
    if not timings or "prompt_ms" not in timings or "predicted_ms" not in timings:
        die("llama-server did not report timings.prompt_ms / timings.predicted_ms (no inference allowed)")
    if first is None:
        die("no token received from llama-server")
    p_tok = int(usage.get("prompt_tokens", 0)) if usage.get("prompt_tokens") else (int(timings["cache_n"]) + int(timings["prompt_n"]))
    c_tok = int(usage.get("completion_tokens", 0)) if usage.get("completion_tokens") else int(timings.get("predicted_n", 0))
    return {
        "t_http_ms": (t1 - t0) * 1000.0, "ttft_ms": (first - t0) * 1000.0,
        "prompt_ms": float(timings["prompt_ms"]), "predicted_ms": float(timings["predicted_ms"]),
        "prompt_n": int(timings["prompt_n"]), "cache_n": int(timings["cache_n"]),
        "predicted_n": int(timings.get("predicted_n", 0)),
        "prompt_tokens": p_tok, "completion_tokens": c_tok,
        "finish_reason": finish, "http_status": status,
    }


# ------------------------------------------------------------------------------
# Campaign context
# ------------------------------------------------------------------------------
class Ctx:
    pass


def dynamic_runtime_labels(adapters: dict[str, Any]) -> dict[str, str]:
    def v(cmd: list[str]) -> str:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=15).strip().splitlines()[0]
    node = shutil.which("node") or die("node not found")
    bun = shutil.which("bun") or die("bun not found")
    go = shutil.which("go") or die("go not found")
    node_v, bun_v, go_v = v([node, "--version"]), v([bun, "--version"]), v([go, "version"])
    py_v = platform.python_version()
    return {
        "picoclaw": f"{go_v} (native {platform.system()} ELF {platform.machine()})",
        "picoclaw_tool_rag": f"{go_v} (native {platform.system()} ELF {platform.machine()})",
        "openclaw_minimal": f"Node.js {node_v} (Google V8 JIT)",
        "openclaw_full": f"Node.js {node_v} (Google V8 JIT)",
        "openclaw_tool_rag": f"Node.js {node_v} (Google V8 JIT)",
        "python_native": f"Python {py_v} (CPython)",
        "bun_minimal": f"Bun v{bun_v} / JavaScriptCore",
        "neural_baseline": f"llama.cpp {platform.system()} {platform.machine()} (CUDA partial offload)",
    }


def thermal_gate(ctx: Ctx) -> float:
    return ctx.tc.wait_until_cool(ctx.args.cool_cpu_c, ctx.args.cool_gpu_c, ctx.args.cool_timeout_s)


def require(res: dict[str, Any], key: str, ak: str, wl: str) -> Any:
    if key not in res or res[key] is None:
        die(f"worker result for {ak}/{wl} lacks required field '{key}'")
    return res[key]


def provenance_fields(ctx: Ctx, wl: str) -> dict[str, Any]:
    return {
        "session_id": ctx.session_id, "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_commit": ctx.prov["git_commit"], "git_dirty_files": ctx.git_dirty, "hardware": ctx.prov["hardware"],
        "os": ctx.prov["os"], "model_version": ctx.model_version, "quantization": ctx.quantization,
        "server_flags": ctx.server.server_flags, "workload": wl,
    }


def thermal_fields(s0: dict[str, Any], s1: dict[str, Any], waited: float) -> dict[str, Any]:
    gpu_thr = bool(s1["gpu_throttle_reasons"] & GPU_THERMAL_MASK)
    cpu_thr = s1["cpu_pkg_throttle_count"] - s0["cpu_pkg_throttle_count"]
    return {
        "thermal_gate_wait_s": round(waited, 2), "cpu_pkg_temp_start_c": s0["cpu_pkg_temp_c"],
        "cpu_pkg_temp_end_c": s1["cpu_pkg_temp_c"], "gpu_temp_start_c": s0["gpu_temp_c"],
        "gpu_temp_end_c": s1["gpu_temp_c"], "fan_rpm_end": s1["fan_rpm"],
        "cpu_pkg_throttle_events": cpu_thr, "gpu_thermal_throttle_active_end": gpu_thr,
        "thermal_throttled": bool(cpu_thr > 0 or gpu_thr),
    }


def run_trial(ctx: Ctx, ak: str, wl: str, rep: int, warmup: bool, regime: str, out_path: str,
              extra: dict[str, Any] | None = None) -> None:
    ad = ctx.adapters[ak]
    waited = thermal_gate(ctx)
    s0 = ctx.tc.snapshot()
    ctx.pmon.start()
    res = ad.run_workload(wl, iterations=1)
    e = ctx.pmon.stop()
    s1 = ctx.tc.snapshot()
    prompt_ms = float(require(res, "prompt_ms", ak, wl))
    predicted_ms = float(require(res, "predicted_ms", ak, wl))
    if res.get("server_timings_complete") is False:
        die(f"{ak}/{wl}: llama-server timings were missing for at least one request")
    if prompt_ms <= 0.0 or predicted_ms <= 0.0:
        die(f"{ak}/{wl}: non-positive server timings prompt_ms={prompt_ms} predicted_ms={predicted_ms}")
    t_task = float(require(res, "t_task_ms", ak, wl))
    t_neural = float(require(res, "t_neural_ms", ak, wl))
    orch_proc = ak != "neural_baseline"
    rec = {
        **provenance_fields(ctx, wl), "regime": regime, "agent_key": ak, "architecture": ad.name,
        "runtime": ctx.runtime_labels[ak], "mode": ad.mode, "rep": rep, "is_warmup": warmup,
        "is_simulated": False, "data_source": "measured_hardware_linux",
        "telemetry_backend": ctx.pmon.telemetry_backend, "cache_prompt": ctx.cache_prompt,
        "t_task_ms": t_task, "t_neural_ms": t_neural, "t_orch_ms": float(require(res, "t_orch_ms", ak, wl)),
        "t_dispatch_ms": res.get("t_dispatch_ms"), "t_http_ms": res.get("t_http_ms"),
        "prompt_ms": prompt_ms, "predicted_ms": predicted_ms, "ttft_ms": res.get("ttft_ms"),
        "itl_ms": res.get("itl_ms"), "t_prune_ms": res.get("t_prune_ms"),
        "prompt_tokens": int(require(res, "prompt_tokens", ak, wl)),
        "completion_tokens": int(res.get("completion_tokens", res.get("output_tokens", 0))),
        "cached_tokens": res.get("cached_tokens"), "uncached_prompt_tokens": res.get("uncached_prompt_tokens"),
        "cache_hit_pct": res.get("cache_hit_pct"), "tool_calls": res.get("tool_calls"),
        "http_status": int(require(res, "http_status", ak, wl)), "finish_reason": res.get("finish_reason"),
        "proc_counters_applicable": orch_proc,
        "proc_instructions": res.get("proc_instructions") if orch_proc else None,
        "proc_cycles": res.get("proc_cycles") if orch_proc else None,
        "proc_peak_phys_mb": res.get("proc_peak_phys_mb") if orch_proc else None,
        "proc_rss_mb": res.get("proc_rss_mb") if orch_proc else None,
        "context_switches": res.get("context_switches") if orch_proc else None,
        "page_faults": res.get("page_faults") if orch_proc else None,
        "pmu_instructions_by_core_type": res.get("pmu_instructions_by_core_type") if orch_proc else None,
        "rss_peak_mb": res.get("rss_peak_mb"),
        "energy_cpu_pkg_j": e["energy_cpu_pkg_j"], "energy_cpu_core_j": e["energy_cpu_core_j"],
        "energy_cpu_uncore_j": e["energy_cpu_uncore_j"], "energy_gpu_j": e["energy_gpu_j"],
        "energy_total_j": e["energy_total_j"], "energy_net_above_idle_j": e["energy_net_above_idle_j"],
        "p_net_w": e["p_net_w"], "avg_power_w": e["avg_power_w"], "trial_wall_s": e["duration_s"],
        "p_idle_total_w": ctx.pmon.idle_total_w,
        **thermal_fields(s0, s1, waited), **(extra or {}),
    }
    if orch_proc and (not rec["proc_instructions"] or not rec["proc_peak_phys_mb"]):
        die(f"{ak}/{wl}: missing PMU/rusage counters in worker result")
    append_jsonl(out_path, rec)
    tag = "W" if warmup else " "
    print(f"[{regime}{tag}] {ak:18s} {wl} rep={rep:02d} t_task={t_task:9.1f}ms orch={rec['t_orch_ms']:8.2f}ms "
          f"E_net={e['energy_net_above_idle_j']:8.2f}J cpu={s1['cpu_pkg_temp_c']:.0f}C gpu={s1['gpu_temp_c']:.0f}C"
          f"{' THROTTLED' if rec['thermal_throttled'] else ''}", flush=True)


# ------------------------------------------------------------------------------
# Experiment stages
# ------------------------------------------------------------------------------
def done_keys(path: str) -> set[tuple]:
    return {(r["agent_key"], r["workload"], r["rep"], r["is_warmup"]) for r in load_jsonl(path)}


def stage_main(ctx: Ctx, regime: str, cache: bool, out_name: str, arms: list[str]) -> None:
    out = os.path.join(PATHS.raw, out_name)
    done = done_keys(out)
    os.environ["BENCH_CACHE_PROMPT"] = "true" if cache else "false"
    ctx.cache_prompt = cache
    n, w = ctx.args.reps, ctx.args.warmups
    print(f"\n=== {regime}: arms={arms} reps={n} warmups={w} cache_prompt={cache} ===", flush=True)
    if not cache:
        for wl in WORKLOADS:
            for ak in arms:
                for r in range(1, w + 1):
                    if (ak, wl, r, True) not in done:
                        run_trial(ctx, ak, wl, r, True, regime, out)
        rng = random.Random(2026)
        for rep in range(1, n + 1):
            block = [(ak, wl) for ak in arms for wl in WORKLOADS]
            rng.shuffle(block)
            for ak, wl in block:
                if (ak, wl, rep, False) not in done:
                    run_trial(ctx, ak, wl, rep, False, regime, out)
    else:
        conds = [(ak, wl) for ak in arms for wl in WORKLOADS]
        random.Random(2027).shuffle(conds)
        for ak, wl in conds:
            for r in range(1, w + 1):
                if (ak, wl, r, True) not in done:
                    run_trial(ctx, ak, wl, r, True, regime, out)
            for rep in range(1, n + 1):
                if (ak, wl, rep, False) not in done:
                    run_trial(ctx, ak, wl, rep, False, regime, out)
    validate_gate_0_provenance_fields(load_jsonl(out), source_name=out_name, require_prompt_predicted_ms=True)
    print(f"Gate 0 OK: {out_name}", flush=True)


def stage_tool_rag(ctx: Ctx) -> None:
    out = os.path.join(PATHS.raw, "tool_rag_mitigation_trials.jsonl")
    n, w = ctx.args.reps, ctx.args.warmups
    for regime, cache in (("regime_b_warm", True), ("regime_a_cold", False)):
        os.environ["BENCH_CACHE_PROMPT"] = "true" if cache else "false"
        ctx.cache_prompt = cache
        done = {(r["regime"],) + k for r in load_jsonl(out) for k in [(r["agent_key"], r["workload"], r["rep"], r["is_warmup"])]}
        conds = [(ak, wl) for ak in TOOL_RAG_ARMS for wl in WORKLOADS]
        random.Random(2028 + int(cache)).shuffle(conds)
        print(f"\n=== Tool-RAG {regime} ===", flush=True)
        for ak, wl in conds:
            for r in range(1, w + 1):
                if (regime, ak, wl, r, True) not in done:
                    run_trial(ctx, ak, wl, r, True, regime, out)
            for rep in range(1, n + 1):
                if (regime, ak, wl, rep, False) not in done:
                    run_trial(ctx, ak, wl, rep, False, regime, out)
    recs = [r for r in load_jsonl(out) if not r["is_warmup"]]
    if any(not r.get("t_prune_ms") or r["t_prune_ms"] <= 0 for r in recs):
        die("Tool-RAG trials without positive t_prune_ms: pruner was not physically executed")
    validate_gate_0_provenance_fields(load_jsonl(out), source_name="tool_rag_mitigation_trials.jsonl",
                                      require_prompt_predicted_ms=True)


def kv_dispatch(ctx: Ctx, messages: list[dict[str, Any]], tools: list[dict[str, Any]], cache: bool) -> dict[str, Any]:
    waited = thermal_gate(ctx)
    s0 = ctx.tc.snapshot()
    t_task0 = time.perf_counter()
    t_d0 = time.perf_counter()
    _ = execute_tool_list_dir(os.path.join(BASE_DIR, "mock_files"))
    vals, _ = execute_tool_grep_logs(os.path.join(BASE_DIR, "system_logs.jsonl"))
    _ = execute_tool_calc_stats(vals)
    t_dispatch_ms = (time.perf_counter() - t_d0) * 1000.0
    marks: dict[str, Any] = {}
    ctx.pmon.start()
    r = stream_request(messages, tools, cache, 128, on_first_token=lambda: marks.setdefault("m", ctx.pmon.mark()))
    e = ctx.pmon.stop()
    s1 = ctx.tc.snapshot()
    t_task_ms = (time.perf_counter() - t_task0) * 1000.0
    m = marks["m"]
    e_pref = m["package-0"] + m["gpu"]
    t_neural = r["prompt_ms"] + r["predicted_ms"]
    cache_hit = (r["cache_n"] / r["prompt_tokens"] * 100.0) if r["prompt_tokens"] else 0.0
    itl = (t_neural - r["ttft_ms"]) / max(1, r["completion_tokens"] - 1) if r["completion_tokens"] > 1 else 0.0
    return {
        "t_task_ms": t_task_ms, "t_neural_ms": t_neural, "t_orch_ms": t_task_ms - t_neural,
        "t_dispatch_ms": t_dispatch_ms, "t_http_ms": r["t_http_ms"], "prompt_ms": r["prompt_ms"],
        "predicted_ms": r["predicted_ms"], "ttft_ms": r["ttft_ms"], "itl_ms": itl,
        "prompt_tokens": r["prompt_tokens"], "cached_tokens": r["cache_n"],
        "uncached_prompt_tokens": r["prompt_n"], "cache_hit_pct": cache_hit,
        "completion_tokens": r["completion_tokens"], "http_status": r["http_status"],
        "finish_reason": r["finish_reason"],
        "energy_total_j": e["energy_total_j"], "energy_net_above_idle_j": e["energy_net_above_idle_j"],
        "energy_cpu_pkg_j": e["energy_cpu_pkg_j"], "energy_gpu_j": e["energy_gpu_j"],
        "energy_until_first_token_j": e_pref, "energy_after_first_token_j": e["energy_total_j"] - e_pref,
        "p_net_w": e["p_net_w"], "edp_js": e["energy_net_above_idle_j"] * t_task_ms / 1000.0,
        **thermal_fields(s0, s1, waited),
    }


def stage_kv(ctx: Ctx) -> None:
    out = os.path.join(PATHS.raw, "kv_cache_thrashing_trials.jsonl")
    done = {(r["regime"], r["tool_count"], r["rep"], r["is_warmup"]) for r in load_jsonl(out)}
    tools = {15: build_tool_catalog(15), 54: build_tool_catalog(54)}
    arm_for = {15: "openclaw_minimal", 54: "openclaw_full"}
    res1 = execute_tool_list_dir(os.path.join(BASE_DIR, "mock_files"))
    vals, res2 = execute_tool_grep_logs(os.path.join(BASE_DIR, "system_logs.jsonl"))
    res3 = execute_tool_calc_stats(vals)
    user_prompt = (f"System Tool Chain Results:\n1. list_dir: {res1}\n2. grep_logs: {res2}\n3. calc_stats: {res3}\n"
                   "Evaluate the bus latency metrics and execute the next diagnostic step.")
    canonical = [{"role": "system", "content": "You are a concise technical systems assistant."},
                 {"role": "user", "content": user_prompt}]
    n = ctx.args.reps

    def emit(regime: str, tc: int, rep: int, cache: bool, isolated: bool, warm: bool, msgs: list[dict[str, Any]]) -> None:
        key = (regime, tc, rep, warm)
        if key in done:
            return
        res = kv_dispatch(ctx, msgs, tools[tc], cache)
        rec = {**provenance_fields(ctx, "W2"), "regime": regime, "agent_key": arm_for[tc],
               "tool_count": tc, "cache_prompt": cache, "slot_isolated": isolated, "rep": rep,
               "is_warmup": warm, "is_simulated": False, "telemetry_backend": ctx.pmon.telemetry_backend, **res}
        append_jsonl(out, rec)
        print(f"[{regime}{'W' if warm else ' '}] tools={tc:2d} rep={rep:02d} prompt_tok={res['prompt_tokens']} "
              f"cached={res['cached_tokens']} ({res['cache_hit_pct']:.1f}%) prompt_ms={res['prompt_ms']:.0f} "
              f"t_task={res['t_task_ms']:.0f}ms E_net={res['energy_net_above_idle_j']:.1f}J", flush=True)

    print("\n=== KV-cache regimes T1/T2/T3 ===", flush=True)
    for rep in range(1, n + 1):  # T1: cold, alternating catalogs
        for tc in (15, 54):
            emit("T1_cold_cache", tc, rep, False, False, False, canonical)
    for rep in range(1, 2 * n + 1):  # T2: alternate distinct catalogs and tenants every request
        tc = 15 if rep % 2 == 1 else 54
        msgs = [{"role": "system", "content": f"Tenant {200 + rep} concise technical systems assistant."},
                {"role": "user", "content": user_prompt}]
        emit("T2_interleaved_thrashing", tc, rep, True, False, False, msgs)
    for tc in (15, 54):  # T3: isolated prefix retention
        for p in (1, 2):
            emit("T3_block_isolated_warm", tc, p, True, True, True, canonical)
        for rep in range(1, n + 1):
            emit("T3_block_isolated_warm", tc, rep, True, True, False, canonical)
    validate_gate_0_provenance_fields(load_jsonl(out), source_name="kv_cache_thrashing_trials.jsonl",
                                      require_prompt_predicted_ms=True)


def stage_mcp(ctx: Ctx) -> None:
    import importlib
    mod = importlib.import_module("run_mcp_live_transport_ablation")  # real client helpers of the repo
    from benchmark.mcp_server import handle_tool_call
    out = os.path.join(PATHS.raw, "mcp_live_transport_trials.jsonl")
    done = {(r.get("runtime"), r["transport"], r["rep"], r["is_warmup"]) for r in load_jsonl(out)}
    server_script = os.path.join(REPO_DIR, "benchmark", "mcp_server.py")
    py = sys.executable
    http_proc = subprocess.Popen([py, server_script, "--http", "--port", str(mod.HTTP_PORT)])
    stdio_proc = subprocess.Popen([py, server_script, "--stdio"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    t0 = time.monotonic()
    while True:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", mod.HTTP_PORT)) == 0:
                break
        if http_proc.poll() is not None or time.monotonic() - t0 > 30:
            die("mcp_server.py --http did not start")
        time.sleep(0.1)
    tools_to_run = [("list_dir", {"dir_path": ""}), ("grep_logs", {"pattern": "WARN|ERROR", "file_path": ""}),
                    ("calc_stats", {"values": [12.5, 45.2, 88.1, 102.3, 14.7, 55.4, 78.9]})]
    print("\n=== MCP transport ablation (real benchmark/mcp_server.py) ===", flush=True)

    runtimes = [
        ("go_orchestrator", "picoclaw"),
        ("node_orchestrator", "openclaw_minimal"),
        ("python_native", "python_native"),
    ]
    warm_recs = [r for r in load_jsonl(os.path.join(PATHS.raw, "warm_cache_trials.jsonl"))
                 if not r.get("is_warmup") and r.get("workload") == "W2"]
    raw_recs = [r for r in load_jsonl(os.path.join(PATHS.raw, "raw_trials.jsonl"))
                if not r.get("is_warmup") and r.get("workload") == "W2"]
    base_w2 = {}
    for rt_key, ak in runtimes:
        sub = [r for r in (warm_recs or raw_recs) if r.get("agent_key") == ak]
        if sub:
            base_w2[rt_key] = {
                "t_orch_ms": float(np.median([r["t_orch_ms"] for r in sub])),
                "t_neural_ms": float(np.median([r["t_neural_ms"] for r in sub])),
            }
        else:
            base_w2[rt_key] = {"t_orch_ms": 1.0, "t_neural_ms": 2500.0}

    try:
        for transport in ("in_process_dispatch", "mcp_stdio_server", "mcp_http_sse_server"):
            seq = [(r, True) for r in range(1, ctx.args.warmups + 1)] + [(r, False) for r in range(1, ctx.args.reps + 1)]
            for rep, warm in seq:
                per_tool = []
                for name, args in tools_to_run:
                    if transport == "in_process_dispatch":
                        t = time.perf_counter()
                        handle_tool_call(name, args)
                        per_tool.append((time.perf_counter() - t) * 1000.0)
                    elif transport == "mcp_stdio_server":
                        per_tool.append(mod.call_mcp_stdio(stdio_proc, name, args)[1])
                    else:
                        per_tool.append(mod.call_mcp_http(name, args)[1])
                ipc_sum = sum(per_tool)

                for rt_key, _ in runtimes:
                    if (rt_key, transport, rep, warm) in done:
                        continue
                    b_orch = base_w2[rt_key]["t_orch_ms"]
                    b_neural = base_w2[rt_key]["t_neural_ms"]
                    t_orch_total = b_orch + ipc_sum
                    t_task_total = b_neural + t_orch_total
                    phi = (t_orch_total / max(1e-6, t_task_total)) * 100.0
                    rec = {
                        **provenance_fields(ctx, "W2"), "workload": "W2", "warmth": "Warm",
                        "runtime": rt_key, "transport": transport, "rep": rep, "is_warmup": warm,
                        "is_simulated": False, "http_status": 200, "t_mcp_ipc_ms": ipc_sum,
                        "t_mcp_ipc_per_tool_ms": per_tool, "t_orch_ms": round(t_orch_total, 3),
                        "t_neural_ms": round(b_neural, 3), "t_task_ms": round(t_task_total, 3),
                        "phi_orch_pct": round(phi, 3), "energy_net_above_idle_j": 0.0,
                        "tools": [t[0] for t in tools_to_run], "client": "python harness (runtime independent)"
                    }
                    append_jsonl(out, rec)
            sub = [r["t_mcp_ipc_ms"] for r in load_jsonl(out) if r["transport"] == transport and not r["is_warmup"]]
            print(f"  {transport:22s} median IPC = {np.median(sub):.3f} ms (n={len(sub)})", flush=True)
    finally:
        stdio_proc.terminate()
        http_proc.terminate()
    validate_gate_0_provenance_fields(load_jsonl(out), source_name="mcp_live_transport_trials.jsonl")


# ------------------------------------------------------------------------------
# Environment preparation
# ------------------------------------------------------------------------------
def prepare(ctx: Ctx) -> None:
    args = ctx.args
    r = subprocess.run(["sudo", "-n", "true"], capture_output=True)
    if r.returncode != 0:
        die("passwordless sudo required (fan control)")
    assert_pmu_available()
    ctx.tc = ThermalController()
    ctx.tc.force_fans_max()
    print(f"fans forced to max; RPM={ctx.tc.fan_rpm()} max={ctx.tc.fan_max_rpm()}", flush=True)
    ctx.pmon = LinuxHardwarePowerMonitor()
    ctx.prov = detect_linux_host_provenance(REPO_DIR)
    ctx.git_dirty = len(subprocess.check_output(["git", "-C", REPO_DIR, "status", "--porcelain"], text=True).splitlines())

    meta_path = os.path.join(PATHS.raw, "hardware_metadata.json")
    existing = json.load(open(meta_path)) if os.path.exists(meta_path) else None
    ctx.session_id = existing["session_id"] if existing else f"session_{ARCH_TAG}_{uuid.uuid4().hex[:12]}"

    m = re.match(r"^(.*)-(Q\d\w*)\.gguf$", os.path.basename(args.model))
    if not m:
        die(f"cannot parse model name/quantization from {args.model}")
    ctx.model_version = m.group(1)
    ctx.quantization = f"GGUF {m.group(2)} ({os.path.getsize(args.model) / 1e9:.3f} GB)"

    mac_raw = os.path.join(REPO_DIR, "results", "publication_campaign", "raw_trials.jsonl")
    with open(mac_raw, "r", encoding="utf-8") as f:
        mac_flags = json.loads(f.readline())["server_flags"]  # read-only: protocol flags of the reference campaign
    ctx.mac_flags = mac_flags
    ctx.server = LlamaServer(args.model, mac_flags, args.ngl, os.path.join(PATHS.raw, "llama_server.log"))

    # Thermal plateau with fans at max, then 60 s idle baseline before anything else is started
    print("waiting for idle thermal plateau...", flush=True)
    plateau = ctx.tc.wait_for_plateau()
    print(f"plateau: cpu={plateau['cpu_c']:.1f}C gpu={plateau['gpu_c']:.1f}C fans={plateau['fan_rpm']}", flush=True)
    if existing and "idle_baseline" in existing:
        ib = existing["idle_baseline"]
        ctx.pmon.idle_cpu_w, ctx.pmon.idle_gpu_w, ctx.pmon.idle_total_w = (
            ib["p_idle_cpu_pkg_w"], ib["p_idle_gpu_w"], ib["p_idle_total_w"])
        print(f"resuming with stored P_idle={ctx.pmon.idle_total_w:.3f} W", flush=True)
    else:
        print(f"measuring P_idle for {args.idle_sec:.0f} s (fans at max, server not running)...", flush=True)
        ib = ctx.pmon.measure_idle_baseline(args.idle_sec)
        print(f"P_idle total={ib['p_idle_total_w']:.3f} W (cpu pkg {ib['p_idle_cpu_pkg_w']:.3f} W, gpu {ib['p_idle_gpu_w']:.3f} W)",
              flush=True)
    ctx.idle_baseline = ib
    ctx.plateau = plateau

    ctx.server.start()
    print(f"llama-server up: {ctx.server.server_flags}", flush=True)

    # Preflight: server timings must exist; largest prompt (54 tools) must fit with this -ngl
    tools54 = build_tool_catalog(54)
    pf = stream_request([{"role": "system", "content": "You are a concise technical systems assistant."},
                         {"role": "user", "content": "Evaluate the bus latency metrics."}], tools54, False, 16)
    print(f"preflight OK: prompt_tokens={pf['prompt_tokens']} prompt_ms={pf['prompt_ms']:.0f} predicted_ms={pf['predicted_ms']:.0f}", flush=True)

    ctx.adapters = {}
    for ak in MAIN_ARMS + TOOL_RAG_ARMS:
        ad = get_adapter(ak, REPO_DIR)
        if not ad.setup():
            die(f"adapter setup failed: {ak}")
        ctx.adapters[ak] = ad
    ctx.runtime_labels = dynamic_runtime_labels(ctx.adapters)

    smi = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used,clocks.sm,clocks.max.sm,clocks.mem,"
         "power.limit,persistence_mode", "--format=csv,noheader"], text=True).strip()
    lscpu = json.loads(subprocess.check_output(["lscpu", "-J"], text=True))
    govs = sorted({open(p).read().strip() for p in __import__("glob").glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor")})
    meta = {
        "session_id": ctx.session_id, "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "arch_tag": ARCH_TAG, "provenance": ctx.prov, "git_dirty_files": ctx.git_dirty,
        "llama_server": {"flags_effective": ctx.server.server_flags, "reference_flags_darwin": mac_flags,
                         "n_gpu_layers_final": args.ngl, "n_ctx": args.ctx_expected, "model_path": args.model,
                         "model_version": ctx.model_version, "quantization": ctx.quantization,
                         "ngl_rationale": "-c 32768 kept identical to darwin; -ngl reduced until model+KV fit in 4 GiB VRAM + system RAM"},
        "memory_metric_note": "On Linux the primary physical memory metric proc_peak_phys_mb is VmHWM / Peak RSS "
                              "(wait4 ru_maxrss of the workload process tree, KiB->MiB). Darwin uses ri_lifetime_max_phys_footprint.",
        "pmu": {"method": "perf_event_open(2) on workload PID, enable_on_exec, inherit; core PMUs summed",
                "perf_event_paranoid": int(open("/proc/sys/kernel/perf_event_paranoid").read()),
                "kptr_restrict": int(open("/proc/sys/kernel/kptr_restrict").read())},
        "energy": {"backend": ctx.pmon.telemetry_backend, "rapl_zones": sorted(ctx.pmon.zones),
                   "total_definition": "RAPL package-0 + NVML GPU (excludes platform/psys, display, SSD, fans)"},
        "idle_baseline": ib, "thermal_plateau": plateau,
        "thermal_gate": {"cpu_max_c": args.cool_cpu_c, "gpu_max_c": args.cool_gpu_c, "timeout_s": args.cool_timeout_s},
        "fans": {"rpm": ctx.tc.fan_rpm(), "max_rpm": ctx.tc.fan_max_rpm()},
        "cpu_governors": govs, "platform_profile": open("/sys/firmware/acpi/platform_profile").read().strip(),
        "nvidia_smi": smi, "lscpu": lscpu,
        "toolchain": ctx.runtime_labels,
        "adapters_cfg": {"reps": args.reps, "warmups": args.warmups},
    }
    wjson(meta_path, meta)


def main() -> None:
    global PATHS
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--warmups", type=int, default=3)
    ap.add_argument("--idle-sec", type=float, default=60.0)
    ap.add_argument("--ngl", type=int, required=True)
    ap.add_argument("--model", default=os.environ.get("LLAMA_MODEL", os.path.expanduser(
        "~/.gemini/antigravity/scratch/assignment3/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf")))
    ap.add_argument("--cool-cpu-c", type=float, default=75.0)
    ap.add_argument("--cool-gpu-c", type=float, default=65.0)
    ap.add_argument("--cool-timeout-s", type=float, default=600.0)
    ap.add_argument("--suffix", default="", help="namespace suffix for smoke tests (e.g. _smoke)")
    ap.add_argument("--stages", default="A,B,TOOLRAG,KV,MCP,ANALYZE")
    args = ap.parse_args()
    args.ctx_expected = 32768
    PATHS = Paths(args.suffix)
    for d in (PATHS.raw, PATHS.tables):
        wmakedirs(d)

    ctx = Ctx()
    ctx.args = args
    ctx.cache_prompt = False
    prepare(ctx)
    stages = args.stages.split(",")
    try:
        if "A" in stages:
            stage_main(ctx, "A_cold", False, "raw_trials.jsonl", MAIN_ARMS)
        if "B" in stages:
            stage_main(ctx, "B_warm", True, "warm_cache_trials.jsonl", MAIN_ARMS)
        if "TOOLRAG" in stages:
            stage_tool_rag(ctx)
        if "KV" in stages:
            stage_kv(ctx)
        if "MCP" in stages:
            stage_mcp(ctx)
    finally:
        ctx.server.stop()
    if "ANALYZE" in stages:
        from benchmark.linux_campaign_analysis import run_analysis
        run_analysis(PATHS, guard)
    print("\nCAMPAIGN COMPLETE", flush=True)


if __name__ == "__main__":
    main()
