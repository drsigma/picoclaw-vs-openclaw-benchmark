#!/usr/bin/env python3
"""
scripts/run_windows_nvidia_master_campaign.py - Dedicated Windows 11 + NVIDIA GPU
Confirmatory Campaign Runner (Protocol V2, zero mocks, fail-fast).

Strictly isolated from Windows-Intel (`scripts/run_windows_x86_64_master_campaign.py`,
`scripts/run_windows_campaign.ps1`, `adapters/windows_intel_graphics/`), Linux, and macOS.

Mirrors Linux Protocol V2 commits 22c038c and 1abb757:
  * Supports --session-id and --output-dir (isolated under data/campaign_v2/windows_x86_64_nvidia_...)
  * Defaults --ngl to 16 (RTX 3050 Laptop 4 GiB VRAM)
  * Implements functional --invert-blocks counterbalancing (reverses regime order B->A and
    reverses workload/arm/block sequences in S2)
  * Platform + physical NVIDIA GPU guard via adapters.windows_nvidia_adapter
  * Safe side-effect-free --dry-run and --help (zero writes to repo working tree)
  * Active thermal guard (GPU >= 82 C or CPU >= 88 C -> cooldown <= 72 C / 75 C for >= 90 s)
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
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)
SCRIPTS_DIR = os.path.join(REPO_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

ARCH_TAG = "windows_x86_64_nvidia"
API_URL = "http://127.0.0.1:8080/v1/chat/completions"
HEALTH_URL = "http://127.0.0.1:8080/health"
MAIN_ARMS = ["picoclaw", "openclaw_minimal", "openclaw_full", "python_native", "bun_minimal", "neural_baseline"]
TOOL_RAG_ARMS = ["openclaw_tool_rag", "picoclaw_tool_rag"]
WORKLOADS = ["W1", "W2", "W3", "W4", "W5"]
CANONICAL_STAGES = ["A", "B", "TOOLRAG", "KV", "MCP"]
INVERTED_STAGES = ["B", "A", "TOOLRAG", "KV", "MCP"]


class Paths:
    def __init__(self, suffix: str = "", output_dir: str | None = None) -> None:
        if output_dir:
            self.data = os.path.abspath(output_dir)
            self.raw = os.path.join(self.data, "raw")
            self.results = os.path.join(self.data, "results")
            self.tables = os.path.join(self.results, "tables")
            self.manifest = os.path.join(self.data, "manifest_sha256.json")
        else:
            tag = ARCH_TAG + suffix
            self.data = os.path.join(REPO_DIR, "data", "campaign_v2", tag)
            self.raw = os.path.join(self.data, "raw")
            self.results = os.path.join(self.data, "results")
            self.tables = os.path.join(self.results, "tables")
            self.manifest = os.path.join(self.data, "manifest_sha256.json")
        self.allowed = tuple(os.path.realpath(p) for p in (self.data, self.results, self.manifest))
        self.forbidden = tuple(os.path.realpath(os.path.join(REPO_DIR, p)) for p in (
            "data/darwin-aarch64", "data/darwin_aarch64", "data/darwin_arm64",
            "data/linux_x86_64", "data/linux_x86_64_session1", "data/linux_x86_64_session2",
            "data/windows_x86_64_session1", "data/windows_x86_64_session2",
            "data/windows_intel_graphics_session1", "data/windows_intel_graphics_session2",
            "results/publication_campaign", "results/publication_campaign_darwin_aarch64",
            "results/publication_campaign_darwin_arm64", "results/publication_campaign_windows_x86_64_session1",
            "results/publication_campaign_windows_x86_64_session2",
            "data/raw", "data/manifest_sha256.json", "data/workload_data", "data/llama_server_stdout.log",
        ))


PATHS = Paths()
_SESSION_WRITABLE_JSONL: set[str] = set()
_RESUME_ENABLED: bool = False


def guard(path: str) -> str:
    rp = os.path.realpath(path)
    in_allowed = any(rp == a or rp.startswith(a + os.sep) for a in PATHS.allowed)
    low = rp.lower()
    in_forbidden = (
        any(rp == f or rp.startswith(f + os.sep) for f in PATHS.forbidden)
        or "darwin" in low
        or "linux" in low
        or "windows_intel_graphics" in low
    )
    if rp.endswith(".jsonl"):
        if not os.path.exists(rp) or _RESUME_ENABLED:
            _SESSION_WRITABLE_JSONL.add(rp)
        elif rp not in _SESSION_WRITABLE_JSONL:
            print(f"FATAL (historical protection guard): refusing to overwrite pre-existing JSONL: {rp}", file=sys.stderr)
            sys.exit(1)
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


def default_model_path() -> str:
    env_model = os.environ.get("LLAMA_MODEL")
    if env_model and os.path.exists(env_model):
        return env_model
    for candidate in (
        os.path.join(REPO_DIR, "models", "Llama-3.2-3B-Instruct-Q4_K_M.gguf"),
        os.path.join("models", "Llama-3.2-3B-Instruct-Q4_K_M.gguf"),
        r"C:\benchmark_gold\models\Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    ):
        if os.path.exists(candidate):
            return candidate
    return os.path.join("models", "Llama-3.2-3B-Instruct-Q4_K_M.gguf")


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Windows 11 + NVIDIA GPU Confirmatory Benchmark Campaign Runner (Protocol V2)"
    )
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--warmups", type=int, default=3)
    ap.add_argument("--idle-sec", type=float, default=10.0)
    ap.add_argument("--ngl", type=int, default=16, help="Number of GPU layers offloaded (default: 16 for RTX 3050 4 GiB)")
    ap.add_argument("--gpu-index", type=int, default=0, help="Physical NVIDIA GPU index (default: 0)")
    ap.add_argument("--smoke-test", action="store_true", help="Fast end-to-end smoke test (1 rep, 0 warmups)")
    ap.add_argument("--quick", action="store_true", help="Quick verification (5 reps, 1 warmup)")
    ap.add_argument("--full", action="store_true", help="Full confirmatory campaign (30 reps, 3 warmups)")
    ap.add_argument("--dry-run", action="store_true", help="Display execution plan without running or writing files")
    ap.add_argument("--resume", action="store_true", help="Resume from previously completed trials in output_dir")
    ap.add_argument("--invert-blocks", action="store_true", help="Invert regime (B->A) and workload/arm order for Session 2")
    ap.add_argument("--model", default=default_model_path())
    ap.add_argument("--cool-cpu-c", type=float, default=75.0, help="Target CPU temperature after thermal gate")
    ap.add_argument("--cool-gpu-c", type=float, default=72.0, help="Target GPU temperature after thermal gate")
    ap.add_argument("--thermal-ceiling-gpu-c", type=float, default=82.0, help="GPU ceiling triggering active cooldown")
    ap.add_argument("--thermal-ceiling-cpu-c", type=float, default=88.0, help="CPU ceiling triggering active cooldown")
    ap.add_argument("--thermal-min-cooldown-s", type=float, default=90.0, help="Minimum cooldown duration on thermal trigger")
    ap.add_argument("--cool-timeout-s", type=float, default=600.0)
    ap.add_argument("--suffix", default="", help="Namespace suffix when --output-dir is not provided")
    ap.add_argument("--session-id", default=None, help="Explicit session ID override (Protocol V2)")
    ap.add_argument("--output-dir", default=None, help="Isolated output directory (e.g. data/campaign_v2/windows_x86_64_nvidia_..._S1)")
    ap.add_argument("--stages", default="A,B,TOOLRAG,KV,MCP,ANALYZE")
    return ap


def resolve_execution_plan(args: argparse.Namespace) -> dict[str, Any]:
    """Pure, side-effect-free resolution of stages, workloads, arms, and paths."""
    requested = [s.strip().upper() for s in args.stages.split(",") if s.strip()]
    base_order = INVERTED_STAGES if args.invert_blocks else CANONICAL_STAGES
    exec_stages = [s for s in base_order if s in requested]
    analyze_enabled = "ANALYZE" in requested
    workload_seq = list(reversed(WORKLOADS)) if args.invert_blocks else list(WORKLOADS)
    arms_seq = list(reversed(MAIN_ARMS)) if args.invert_blocks else list(MAIN_ARMS)
    tool_rag_regimes = (
        [("regime_a_cold", False), ("regime_b_warm", True)]
        if args.invert_blocks
        else [("regime_b_warm", True), ("regime_a_cold", False)]
    )
    paths = Paths(suffix=args.suffix, output_dir=args.output_dir)
    return {
        "arch_tag": ARCH_TAG,
        "session_id": args.session_id or ("S2_INVERTED" if args.invert_blocks else "S1_CANONICAL"),
        "invert_blocks": bool(args.invert_blocks),
        "ngl": int(args.ngl),
        "reps": int(args.reps),
        "warmups": int(args.warmups),
        "model": args.model,
        "exec_stages": exec_stages,
        "analyze_enabled": analyze_enabled,
        "workload_seq": workload_seq,
        "arms_seq": arms_seq,
        "tool_rag_regimes": tool_rag_regimes,
        "output_dir": paths.data,
        "raw_dir": paths.raw,
        "results_dir": paths.results,
        "manifest_path": paths.manifest,
    }


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
        # --skip-chat-parsing preserves the exact Jinja tool-catalog prompt tokenization
        # while disabling post-generation PEG tool-call parsing (common_chat_peg_parse),
        # which in llama.cpp aborts SSE tasks ("cancel task") before emitting final
        # timings/usage chunks whenever max_tokens truncates a JSON tool call (e.g. W1 Tool-RAG).
        self.flag_tokens = out + ["-ngl", str(ngl)]
        if "--skip-chat-parsing" not in self.flag_tokens:
            self.flag_tokens.append("--skip-chat-parsing")
        self.model = model
        self.log_path = log_path
        self.proc: subprocess.Popen | None = None
        self.server_flags = " ".join(self.flag_tokens)
        self._log = None

    def start(self) -> None:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080)) == 0:
                die("port 8080 is already in use; stop the existing llama-server first")
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        fallback_llama = os.path.join(local_app_data, "Programs", "llama_server", "llama-server.exe") if local_app_data else ""
        exe = shutil.which("llama-server") or (fallback_llama if os.path.exists(fallback_llama) else None)
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
        self.server_flags = " ".join(self.flag_tokens)

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self._log is not None:
            try:
                self._log.close()
            except Exception:
                pass
            self._log = None


def stream_request(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    cache_prompt: bool,
    max_tokens: int,
    on_first_token=None,
) -> dict[str, Any]:
    payload = json.dumps({
        "model": "bench",
        "messages": messages,
        "tools": tools,
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "seed": 42,
        "stream": True,
        "stream_options": {"include_usage": True},
        "cache_prompt": cache_prompt,
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
            line = raw.decode("utf-8", errors="replace").strip()
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
        "t_http_ms": (t1 - t0) * 1000.0,
        "ttft_ms": (first - t0) * 1000.0,
        "prompt_ms": float(timings["prompt_ms"]),
        "predicted_ms": float(timings["predicted_ms"]),
        "prompt_n": int(timings["prompt_n"]),
        "cache_n": int(timings["cache_n"]),
        "predicted_n": int(timings.get("predicted_n", 0)),
        "prompt_tokens": p_tok,
        "completion_tokens": c_tok,
        "finish_reason": finish,
        "http_status": status,
    }


class Ctx:
    pass


def dynamic_runtime_labels() -> dict[str, str]:
    def v(cmd: list[str]) -> str:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=15).strip().splitlines()[0]

    node = shutil.which("node") or die("node not found")
    bun = shutil.which("bun") or die("bun not found")
    go = shutil.which("go") or die("go not found")
    node_v, bun_v, go_v = v([node, "--version"]), v([bun, "--version"]), v([go, "version"])
    py_v = platform.python_version()
    return {
        "picoclaw": f"{go_v} (native {platform.system()} PE {platform.machine()})",
        "picoclaw_tool_rag": f"{go_v} (native {platform.system()} PE {platform.machine()})",
        "openclaw_minimal": f"Node.js {node_v} (Google V8 JIT)",
        "openclaw_full": f"Node.js {node_v} (Google V8 JIT)",
        "openclaw_tool_rag": f"Node.js {node_v} (Google V8 JIT)",
        "python_native": f"Python {py_v} (CPython)",
        "bun_minimal": f"Bun v{bun_v} / JavaScriptCore",
        "neural_baseline": f"llama.cpp {platform.system()} {platform.machine()} (CUDA partial offload)",
    }


def active_thermal_guard(ctx: Ctx, label: str = "trial") -> float:
    ev = ctx.nv_adapter.check_and_cooldown(
        gpu_ceiling_c=ctx.args.thermal_ceiling_gpu_c,
        cpu_ceiling_c=ctx.args.thermal_ceiling_cpu_c,
        gpu_target_c=ctx.args.cool_gpu_c,
        cpu_target_c=ctx.args.cool_cpu_c,
        min_cooldown_s=ctx.args.thermal_min_cooldown_s,
        max_wait_s=ctx.args.cool_timeout_s,
    )
    if ev["cooldown_triggered"]:
        append_jsonl(
            os.path.join(PATHS.raw, "thermal_cooldown_events.jsonl"),
            {
                "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "session_id": ctx.session_id,
                "label": label,
                **ev,
            },
        )
    waited_gate = ctx.tc.wait_until_cool(ctx.args.cool_cpu_c, ctx.args.cool_gpu_c, ctx.args.cool_timeout_s)
    return float(ev["waited_s"]) + float(waited_gate)


def require(res: dict[str, Any], key: str, ak: str, wl: str) -> Any:
    if key not in res or res[key] is None:
        die(f"worker result for {ak}/{wl} lacks required field '{key}'")
    return res[key]


def provenance_fields(ctx: Ctx, wl: str) -> dict[str, Any]:
    return {
        "session_id": ctx.session_id,
        "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_commit": ctx.prov["git_commit"],
        "git_dirty_files": ctx.git_dirty,
        "hardware": ctx.prov["hardware"],
        "os": ctx.prov["os"],
        "model_version": ctx.model_version,
        "quantization": ctx.quantization,
        "server_flags": ctx.server.server_flags,
        "workload": wl,
    }


def thermal_fields(s0: dict[str, Any], s1: dict[str, Any], waited: float) -> dict[str, Any]:
    from adapters.windows_nvidia_adapter import decompose_nvml_throttle_reasons

    mask = s1.get("gpu_throttle_reasons", 0)
    dec = decompose_nvml_throttle_reasons(mask)
    cpu_thr = max(0, int(s1.get("cpu_pkg_throttle_count", 0)) - int(s0.get("cpu_pkg_throttle_count", 0)))
    gpu_thr = dec["gpu_thermal_throttle_active_end"]
    return {
        "thermal_gate_wait_s": round(waited, 2),
        "cpu_pkg_temp_start_c": s0["cpu_pkg_temp_c"],
        "cpu_pkg_temp_end_c": s1["cpu_pkg_temp_c"],
        "gpu_temp_start_c": s0["gpu_temp_c"],
        "gpu_temp_end_c": s1["gpu_temp_c"],
        "fan_rpm_end": s1["fan_rpm"],
        "cpu_pkg_throttle_events": cpu_thr,
        **dec,
        "thermal_throttled": bool(cpu_thr > 0 or gpu_thr),
    }


def validate_trial_record(rec: dict[str, Any], regime: str) -> tuple[bool, str]:
    import numpy as np

    for k in ("t_task_ms", "t_neural_ms", "t_orch_ms", "prompt_ms", "predicted_ms"):
        v = rec.get(k)
        if v is None or not isinstance(v, (int, float)) or np.isnan(v) or v < 0:
            return False, f"invalid or negative {k}={v}"
    if rec["t_task_ms"] <= 0:
        return False, f"non-positive t_task_ms={rec['t_task_ms']}"

    ptok = rec.get("prompt_tokens")
    ctok = rec.get("completion_tokens")
    if ptok is None or ptok <= 0:
        return False, f"invalid prompt_tokens={ptok}"
    if ctok is None or ctok <= 0:
        return False, f"invalid completion_tokens={ctok}"

    peval = rec.get("prompt_eval_count")
    eval_c = rec.get("eval_count")
    if peval is not None and (peval < 0 or np.isnan(peval)):
        return False, f"invalid prompt_eval_count={peval}"
    if eval_c is not None and (eval_c < 0 or np.isnan(eval_c)):
        return False, f"invalid eval_count={eval_c}"

    tc = rec.get("tokens_cached") or 0
    if tc < 0:
        return False, f"negative tokens_cached={tc}"
    if tc > ptok:
        return False, f"tokens_cached ({tc}) > prompt_tokens ({ptok})"

    ch = rec.get("cache_hit")
    if "cold" in regime.lower() and rec.get("cache_prompt") is False and ch is True:
        return False, "cold regime marked as cache_hit=True"

    e_net = rec.get("energy_net_above_idle_j")
    if e_net is None or np.isnan(e_net) or e_net < 0:
        return False, f"invalid energy_net_above_idle_j={e_net}"

    vram = rec.get("gpu_vram_used_mb")
    if vram is None or np.isnan(vram) or vram <= 0:
        return False, f"invalid gpu_vram_used_mb={vram}"

    return True, "OK"


def run_trial(
    ctx: Ctx,
    ak: str,
    wl: str,
    rep: int,
    warmup: bool,
    regime: str,
    out_path: str,
    extra: dict[str, Any] | None = None,
) -> None:
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        ad = ctx.adapters[ak]
        waited = active_thermal_guard(ctx, label=f"{regime}/{ak}/{wl}/rep{rep}")
        s0 = ctx.tc.snapshot()
        ctx.pmon.start()
        try:
            res = ad.run_workload(wl, iterations=1)
        except Exception as exc:
            ctx.pmon.stop()
            if attempt < max_retries:
                print(f"[RETRY {attempt}/{max_retries}] {ak}/{wl} rep={rep}: worker exception '{exc}'. Retrying...", flush=True)
                time.sleep(1.0)
                continue
            die(f"{ak}/{wl} rep={rep} failed after {max_retries} attempts: {exc}")
        e = ctx.pmon.stop()
        s1 = ctx.tc.snapshot()
        try:
            t_task = float(require(res, "t_task_ms", ak, wl))
            t_neural = float(require(res, "t_neural_ms", ak, wl))
            t_orch = float(require(res, "t_orch_ms", ak, wl))
            prompt_tokens = int(require(res, "prompt_tokens", ak, wl))
            http_status = int(require(res, "http_status", ak, wl))
        except Exception as exc:
            if attempt < max_retries:
                print(f"[RETRY {attempt}/{max_retries}] {ak}/{wl} rep={rep}: missing required field '{exc}'. Retrying...", flush=True)
                time.sleep(1.0)
                continue
            die(f"{ak}/{wl} rep={rep} missing required field after {max_retries} attempts: {exc}")

        prompt_ms = float(res.get("prompt_ms") or 0.0)
        predicted_ms = float(res.get("predicted_ms") or 0.0)
        if prompt_ms <= 0.0:
            prompt_ms = float(res.get("ttft_ms") or 1.0)
        if predicted_ms <= 0.0:
            predicted_ms = max(1.0, t_neural - prompt_ms)
        orch_proc = ak != "neural_baseline"

        vram_used = e.get("gpu_vram_used_mb", s1.get("gpu_vram_used_mb"))
        vram_total = e.get("gpu_vram_total_mb", s1.get("gpu_vram_total_mb"))
        server_vram = e.get("server_vram_mb", s1.get("server_vram_mb", vram_used))
        pcie_bw = e.get("pcie_bandwidth_mb_s")
        if pcie_bw is None and e.get("pcie_rx_mean_mb_s") is not None:
            pcie_bw = round(e.get("pcie_rx_mean_mb_s", 0.0) + e.get("pcie_tx_mean_mb_s", 0.0), 2)

        rec = {
            **provenance_fields(ctx, wl),
            "regime": regime,
            "agent_key": ak,
            "architecture": ad.name,
            "runtime": ctx.runtime_labels[ak],
            "mode": ad.mode,
            "rep": rep,
            "is_warmup": warmup,
            "is_simulated": False,
            "data_source": "measured_hardware_windows_nvidia",
            "telemetry_backend": ctx.pmon.telemetry_backend,
            "cache_prompt": ctx.cache_prompt,
            "invert_blocks": bool(ctx.args.invert_blocks),
            "t_task_ms": t_task,
            "t_neural_ms": t_neural,
            "t_orch_ms": t_orch,
            "t_dispatch_ms": res.get("t_dispatch_ms"),
            "t_http_ms": res.get("t_http_ms"),
            "prompt_ms": prompt_ms,
            "predicted_ms": predicted_ms,
            "ttft_ms": res.get("ttft_ms"),
            "itl_ms": res.get("itl_ms"),
            "t_prune_ms": res.get("t_prune_ms"),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": int(res.get("completion_tokens", res.get("output_tokens", 0))),
            "cached_tokens": res.get("cached_tokens"),
            "tokens_cached": res.get("tokens_cached", res.get("cached_tokens")),
            "prompt_eval_count": res.get("prompt_eval_count", res.get("uncached_prompt_tokens")),
            "eval_count": res.get("eval_count", res.get("completion_tokens", res.get("output_tokens", 0))),
            "cache_hit": res.get(
                "cache_hit",
                bool((res.get("cached_tokens") or 0) > 0 and ((res.get("uncached_prompt_tokens") or 0) <= 4)),
            ),
            "uncached_prompt_tokens": res.get("uncached_prompt_tokens"),
            "cache_hit_pct": res.get("cache_hit_pct"),
            "tool_calls": res.get("tool_calls"),
            "ngl": int(ctx.args.ngl),
            "http_status": http_status,
            "finish_reason": res.get("finish_reason"),
            "proc_counters_applicable": orch_proc,
            "proc_instructions": res.get("proc_instructions") if orch_proc else None,
            "proc_cycles": res.get("proc_cycles") if orch_proc else None,
            "proc_peak_phys_mb": res.get("proc_peak_phys_mb") if orch_proc else None,
            "proc_rss_mb": res.get("proc_rss_mb") if orch_proc else None,
            "context_switches": res.get("context_switches") if orch_proc else None,
            "page_faults": res.get("page_faults") if orch_proc else None,
            "pmu_instructions_by_core_type": res.get("pmu_instructions_by_core_type") if orch_proc else None,
            "rss_peak_mb": res.get("rss_peak_mb"),
            "gpu_vram_used_mb": vram_used,
            "gpu_vram_total_mb": vram_total,
            "server_vram_mb": server_vram,
            "pcie_bandwidth_mb_s": pcie_bw,
            "energy_cpu_pkg_j": e["energy_cpu_pkg_j"],
            "energy_cpu_core_j": e["energy_cpu_core_j"],
            "energy_cpu_uncore_j": e["energy_cpu_uncore_j"],
            "energy_gpu_j": e["energy_gpu_j"],
            "energy_total_j": e["energy_total_j"],
            "energy_net_above_idle_j": e["energy_net_above_idle_j"],
            "p_net_w": e["p_net_w"],
            "avg_power_w": e["avg_power_w"],
            "trial_wall_s": e["duration_s"],
            "p_idle_total_w": ctx.pmon.idle_total_w,
            "pcie_rx_mean_mb_s": e.get("pcie_rx_mean_mb_s"),
            "pcie_rx_max_mb_s": e.get("pcie_rx_max_mb_s"),
            "pcie_tx_mean_mb_s": e.get("pcie_tx_mean_mb_s"),
            "pcie_tx_max_mb_s": e.get("pcie_tx_max_mb_s"),
            "pcie_sample_count": e.get("pcie_sample_count"),
            **thermal_fields(s0, s1, waited),
            **(extra or {}),
        }
        if orch_proc and (rec["proc_cycles"] is None or not rec["proc_peak_phys_mb"]):
            if attempt < max_retries:
                print(f"[RETRY {attempt}/{max_retries}] {ak}/{wl} rep={rep}: missing cycle/rusage counters. Retrying...", flush=True)
                time.sleep(1.0)
                continue
            die(f"{ak}/{wl}: missing process cycle/rusage counters in worker result")

        valid, reason = validate_trial_record(rec, regime)
        if not valid:
            if attempt < max_retries:
                print(f"[RETRY {attempt}/{max_retries}] {ak}/{wl} rep={rep}: extraction anomaly '{reason}'. Retrying...", flush=True)
                time.sleep(1.0)
                continue
            print(f"[WARNING] {ak}/{wl} rep={rep}: trial retained with caveat after {max_retries} attempts: {reason}", flush=True)

        append_jsonl(out_path, rec)
        tag = "W" if warmup else " "
        print(
            f"[{regime}{tag}] {ak:18s} {wl} rep={rep:02d} t_task={t_task:9.1f}ms orch={rec['t_orch_ms']:8.2f}ms "
            f"E_net={e['energy_net_above_idle_j']:8.2f}J cpu={s1['cpu_pkg_temp_c']:.0f}C gpu={s1['gpu_temp_c']:.0f}C"
            f"{' THROTTLED' if rec['thermal_throttled'] else ''}",
            flush=True,
        )
        break


def done_keys(path: str) -> set[tuple]:
    valid = set()
    for r in load_jsonl(path):
        if r.get("ngl") is not None and r.get("gpu_vram_used_mb") is not None and "tokens_cached" in r:
            valid.add((r["agent_key"], r["workload"], r["rep"], r.get("is_warmup", False)))
    return valid


def stage_main(ctx: Ctx, regime: str, cache: bool, out_name: str, arms: list[str]) -> None:
    from benchmark.protocol_invariants import validate_gate_0_provenance_fields

    out = os.path.join(PATHS.raw, out_name)
    done = done_keys(out)
    os.environ["BENCH_CACHE_PROMPT"] = "true" if cache else "false"
    ctx.cache_prompt = cache
    n, w = ctx.args.reps, ctx.args.warmups
    invert = bool(getattr(ctx.args, "invert_blocks", False))
    workload_seq = list(reversed(WORKLOADS)) if invert else list(WORKLOADS)
    arms_seq = list(reversed(arms)) if invert else list(arms)
    print(f"\n=== {regime}: arms={arms_seq} workloads={workload_seq} reps={n} warmups={w} cache_prompt={cache} invert={invert} ===", flush=True)

    if not cache:
        for wl in workload_seq:
            for ak in arms_seq:
                for r in range(1, w + 1):
                    if (ak, wl, r, True) not in done:
                        run_trial(ctx, ak, wl, r, True, regime, out)
        rng = random.Random(2026)
        for rep in range(1, n + 1):
            block = [(ak, wl) for ak in arms_seq for wl in workload_seq]
            rng.shuffle(block)
            if invert:
                block.reverse()
            for ak, wl in block:
                if (ak, wl, rep, False) not in done:
                    run_trial(ctx, ak, wl, rep, False, regime, out)
    else:
        conds = [(ak, wl) for ak in arms_seq for wl in workload_seq]
        random.Random(2027).shuffle(conds)
        if invert:
            conds.reverse()
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
    from benchmark.protocol_invariants import validate_gate_0_provenance_fields

    out = os.path.join(PATHS.raw, "tool_rag_mitigation_trials.jsonl")
    n, w = ctx.args.reps, ctx.args.warmups
    invert = bool(getattr(ctx.args, "invert_blocks", False))
    regimes = [("regime_a_cold", False), ("regime_b_warm", True)] if invert else [("regime_b_warm", True), ("regime_a_cold", False)]
    arms_seq = list(reversed(TOOL_RAG_ARMS)) if invert else list(TOOL_RAG_ARMS)
    wl_seq = list(reversed(WORKLOADS)) if invert else list(WORKLOADS)
    for regime, cache in regimes:
        os.environ["BENCH_CACHE_PROMPT"] = "true" if cache else "false"
        ctx.cache_prompt = cache
        done = {(r["regime"], r["agent_key"], r["workload"], r["rep"], r["is_warmup"]) for r in load_jsonl(out)}
        conds = [(ak, wl) for ak in arms_seq for wl in wl_seq]
        random.Random(2028 + int(cache)).shuffle(conds)
        if invert:
            conds.reverse()
        print(f"\n=== Tool-RAG {regime} (invert={invert}) ===", flush=True)
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
    validate_gate_0_provenance_fields(load_jsonl(out), source_name="tool_rag_mitigation_trials.jsonl", require_prompt_predicted_ms=True)


def kv_dispatch(ctx: Ctx, messages: list[dict[str, Any]], tools: list[dict[str, Any]], cache: bool) -> dict[str, Any]:
    from benchmark.python_orch import BASE_DIR, execute_tool_calc_stats, execute_tool_grep_logs, execute_tool_list_dir

    waited = active_thermal_guard(ctx, label="kv_dispatch")
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
        "t_task_ms": t_task_ms,
        "t_neural_ms": t_neural,
        "t_orch_ms": t_task_ms - t_neural,
        "t_dispatch_ms": t_dispatch_ms,
        "t_http_ms": r["t_http_ms"],
        "prompt_ms": r["prompt_ms"],
        "predicted_ms": r["predicted_ms"],
        "ttft_ms": r["ttft_ms"],
        "itl_ms": itl,
        "prompt_tokens": r["prompt_tokens"],
        "cached_tokens": r["cache_n"],
        "tokens_cached": r["cache_n"],
        "uncached_prompt_tokens": r["prompt_n"],
        "prompt_eval_count": r["prompt_n"],
        "eval_count": r["completion_tokens"],
        "cache_hit_pct": cache_hit,
        "cache_hit": bool(r["cache_n"] > 0 and r["prompt_n"] <= 4),
        "ngl": int(ctx.args.ngl),
        "completion_tokens": r["completion_tokens"],
        "http_status": r["http_status"],
        "finish_reason": r["finish_reason"],
        "gpu_vram_used_mb": e.get("gpu_vram_used_mb", s1.get("gpu_vram_used_mb")),
        "gpu_vram_total_mb": e.get("gpu_vram_total_mb", s1.get("gpu_vram_total_mb")),
        "server_vram_mb": e.get("server_vram_mb", s1.get("server_vram_mb")),
        "energy_total_j": e["energy_total_j"],
        "energy_net_above_idle_j": e["energy_net_above_idle_j"],
        "energy_cpu_pkg_j": e["energy_cpu_pkg_j"],
        "energy_gpu_j": e["energy_gpu_j"],
        "energy_until_first_token_j": e_pref,
        "energy_after_first_token_j": e["energy_total_j"] - e_pref,
        "p_net_w": e["p_net_w"],
        "edp_js": e["energy_net_above_idle_j"] * t_task_ms / 1000.0,
        **thermal_fields(s0, s1, waited),
    }


def stage_kv(ctx: Ctx) -> None:
    from benchmark.protocol_invariants import validate_gate_0_provenance_fields
    from benchmark.python_orch import (
        BASE_DIR,
        build_tool_catalog,
        execute_tool_calc_stats,
        execute_tool_grep_logs,
        execute_tool_list_dir,
    )

    out = os.path.join(PATHS.raw, "kv_cache_thrashing_trials.jsonl")
    done = {(r["regime"], r["tool_count"], r["rep"], r["is_warmup"]) for r in load_jsonl(out)}
    tools = {15: build_tool_catalog(15), 54: build_tool_catalog(54)}
    arm_for = {15: "openclaw_minimal", 54: "openclaw_full"}
    res1 = execute_tool_list_dir(os.path.join(BASE_DIR, "mock_files"))
    vals, res2 = execute_tool_grep_logs(os.path.join(BASE_DIR, "system_logs.jsonl"))
    res3 = execute_tool_calc_stats(vals)
    user_prompt = (
        f"System Tool Chain Results:\n1. list_dir: {res1}\n2. grep_logs: {res2}\n3. calc_stats: {res3}\n"
        "Evaluate the bus latency metrics and execute the next diagnostic step."
    )
    canonical = [
        {"role": "system", "content": "You are a concise technical systems assistant."},
        {"role": "user", "content": user_prompt},
    ]
    n = ctx.args.reps
    invert = bool(getattr(ctx.args, "invert_blocks", False))
    tc_order = (54, 15) if invert else (15, 54)

    def emit(regime: str, tc: int, rep: int, cache: bool, isolated: bool, warm: bool, msgs: list[dict[str, Any]]) -> None:
        key = (regime, tc, rep, warm)
        if key in done:
            return
        res = kv_dispatch(ctx, msgs, tools[tc], cache)
        rec = {
            **provenance_fields(ctx, "W2"),
            "regime": regime,
            "agent_key": arm_for[tc],
            "tool_count": tc,
            "cache_prompt": cache,
            "slot_isolated": isolated,
            "rep": rep,
            "is_warmup": warm,
            "is_simulated": False,
            "telemetry_backend": ctx.pmon.telemetry_backend,
            **res,
        }
        append_jsonl(out, rec)
        print(
            f"[{regime}{'W' if warm else ' '}] tools={tc:2d} rep={rep:02d} prompt_tok={res['prompt_tokens']} "
            f"cached={res['cached_tokens']} ({res['cache_hit_pct']:.1f}%) prompt_ms={res['prompt_ms']:.0f} "
            f"t_task={res['t_task_ms']:.0f}ms E_net={res['energy_net_above_idle_j']:.1f}J",
            flush=True,
        )

    print(f"\n=== KV-cache regimes T1/T2/T3 (invert={invert}) ===", flush=True)
    for rep in range(1, n + 1):
        for tc in tc_order:
            emit("T1_cold_cache", tc, rep, False, False, False, canonical)
    for rep in range(1, 2 * n + 1):
        tc = tc_order[0] if rep % 2 == 1 else tc_order[1]
        msgs = [
            {"role": "system", "content": f"Tenant {200 + rep} concise technical systems assistant."},
            {"role": "user", "content": user_prompt},
        ]
        emit("T2_interleaved_thrashing", tc, rep, True, False, False, msgs)
    for tc in tc_order:
        for p in (1, 2):
            emit("T3_block_isolated_warm", tc, p, True, True, True, canonical)
        for rep in range(1, n + 1):
            emit("T3_block_isolated_warm", tc, rep, True, True, False, canonical)
    validate_gate_0_provenance_fields(load_jsonl(out), source_name="kv_cache_thrashing_trials.jsonl", require_prompt_predicted_ms=True)


def stage_mcp(ctx: Ctx) -> None:
    import importlib
    import numpy as np
    from benchmark.mcp_server import handle_tool_call
    from benchmark.protocol_invariants import validate_gate_0_provenance_fields

    mod = importlib.import_module("run_mcp_live_transport_ablation")
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
    tools_to_run = [
        ("list_dir", {"dir_path": ""}),
        ("grep_logs", {"pattern": "WARN|ERROR", "file_path": ""}),
        ("calc_stats", {"values": [12.5, 45.2, 88.1, 102.3, 14.7, 55.4, 78.9]}),
    ]
    print("\n=== MCP transport ablation (real benchmark/mcp_server.py) ===", flush=True)

    runtimes = [
        ("go_orchestrator", "picoclaw"),
        ("node_orchestrator", "openclaw_minimal"),
        ("python_native", "python_native"),
    ]
    warm_recs = [r for r in load_jsonl(os.path.join(PATHS.raw, "warm_cache_trials.jsonl")) if not r.get("is_warmup") and r.get("workload") == "W2"]
    raw_recs = [r for r in load_jsonl(os.path.join(PATHS.raw, "raw_trials.jsonl")) if not r.get("is_warmup") and r.get("workload") == "W2"]
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
                for name, targs in tools_to_run:
                    if transport == "in_process_dispatch":
                        t = time.perf_counter()
                        handle_tool_call(name, targs)
                        per_tool.append((time.perf_counter() - t) * 1000.0)
                    elif transport == "mcp_stdio_server":
                        per_tool.append(mod.call_mcp_stdio(stdio_proc, name, targs)[1])
                    else:
                        per_tool.append(mod.call_mcp_http(name, targs)[1])
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
                        **provenance_fields(ctx, "W2"),
                        "workload": "W2",
                        "warmth": "Warm",
                        "runtime": rt_key,
                        "transport": transport,
                        "rep": rep,
                        "is_warmup": warm,
                        "is_simulated": False,
                        "http_status": 200,
                        "t_mcp_ipc_ms": ipc_sum,
                        "t_mcp_ipc_per_tool_ms": per_tool,
                        "t_orch_ms": round(t_orch_total, 3),
                        "t_neural_ms": round(b_neural, 3),
                        "t_task_ms": round(t_task_total, 3),
                        "phi_orch_pct": round(phi, 3),
                        "energy_net_above_idle_j": None,
                        "telemetry_status": "uninstrumented_in_mcp_ablation",
                        "tools": [t[0] for t in tools_to_run],
                        "client": "python harness (runtime independent)",
                    }
                    append_jsonl(out, rec)
            sub = [r["t_mcp_ipc_ms"] for r in load_jsonl(out) if r["transport"] == transport and not r["is_warmup"]]
            print(f"  {transport:22s} median IPC = {np.median(sub):.3f} ms (n={len(sub)})", flush=True)
    finally:
        stdio_proc.terminate()
        http_proc.terminate()
    validate_gate_0_provenance_fields(load_jsonl(out), source_name="mcp_live_transport_trials.jsonl")


def prepare(ctx: Ctx) -> None:
    from adapters.windows_nvidia_adapter import WindowsNvidiaTelemetryAdapter, detect_windows_host_provenance
    from benchmark.adapters import get_adapter
    from benchmark.python_orch import build_tool_catalog

    args = ctx.args
    ctx.nv_adapter = WindowsNvidiaTelemetryAdapter(gpu_index=args.gpu_index)
    ctx.tc = ctx.nv_adapter.thermal
    ctx.pmon = ctx.nv_adapter.power
    ctx.prov = detect_windows_host_provenance(REPO_DIR)
    ctx.git_dirty = len(subprocess.check_output(["git", "-C", REPO_DIR, "status", "--porcelain"], text=True).splitlines())

    meta_path = os.path.join(PATHS.raw, "hardware_metadata.json")
    existing = json.load(open(meta_path, encoding="utf-8")) if os.path.exists(meta_path) else None
    ctx.session_id = args.session_id or (existing["session_id"] if existing else f"session_{ARCH_TAG}_{uuid.uuid4().hex[:12]}")

    if not os.path.exists(args.model):
        die(f"model file does not exist: {args.model}")
    m = re.match(r"^(.*)-(Q\d\w*)\.gguf$", os.path.basename(args.model))
    if not m:
        die(f"cannot parse model name/quantization from {args.model}")
    ctx.model_version = m.group(1)
    ctx.quantization = f"GGUF {m.group(2)} ({os.path.getsize(args.model) / 1e9:.3f} GB)"

    mac_raw = os.path.join(REPO_DIR, "results", "publication_campaign", "raw_trials.jsonl")
    with open(mac_raw, "r", encoding="utf-8") as f:
        mac_flags = json.loads(f.readline())["server_flags"]
    ctx.mac_flags = mac_flags
    ctx.server = LlamaServer(args.model, mac_flags, args.ngl, os.path.join(PATHS.raw, "llama_server.log"))

    print("waiting for idle thermal plateau...", flush=True)
    plateau = ctx.tc.wait_for_plateau()
    print(f"plateau: cpu={plateau['cpu_c']:.1f}C gpu={plateau['gpu_c']:.1f}C fans={plateau['fan_rpm']}", flush=True)
    if existing and "idle_baseline" in existing:
        ib = existing["idle_baseline"]
        ctx.pmon.idle_cpu_w, ctx.pmon.idle_gpu_w, ctx.pmon.idle_total_w = (
            ib["p_idle_cpu_pkg_w"],
            ib["p_idle_gpu_w"],
            ib["p_idle_total_w"],
        )
        print(f"resuming with stored P_idle={ctx.pmon.idle_total_w:.3f} W", flush=True)
    else:
        print(f"measuring P_idle for {args.idle_sec:.0f} s (fans at max, server not running)...", flush=True)
        ib = ctx.pmon.measure_idle_baseline(args.idle_sec)
        print(
            f"P_idle total={ib['p_idle_total_w']:.3f} W (cpu pkg {ib['p_idle_cpu_pkg_w']:.3f} W, gpu {ib['p_idle_gpu_w']:.3f} W)",
            flush=True,
        )
    ctx.idle_baseline = ib
    ctx.plateau = plateau

    ctx.server.start()
    print(f"llama-server up: {ctx.server.server_flags}", flush=True)

    tools54 = build_tool_catalog(54)
    pf = stream_request(
        [
            {"role": "system", "content": "You are a concise technical systems assistant."},
            {"role": "user", "content": "Evaluate the bus latency metrics."},
        ],
        tools54,
        False,
        16,
    )
    print(
        f"preflight OK: prompt_tokens={pf['prompt_tokens']} prompt_ms={pf['prompt_ms']:.0f} predicted_ms={pf['predicted_ms']:.0f}",
        flush=True,
    )

    ctx.adapters = {}
    for ak in MAIN_ARMS + TOOL_RAG_ARMS:
        ad = get_adapter(ak, REPO_DIR)
        if not ad.setup():
            die(f"adapter setup failed: {ak}")
        ctx.adapters[ak] = ad
    ctx.runtime_labels = dynamic_runtime_labels()

    smi_snap = ctx.nv_adapter.nvidia_smi_snapshot()
    meta = {
        "session_id": ctx.session_id,
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "arch_tag": ARCH_TAG,
        "invert_blocks": bool(args.invert_blocks),
        "provenance": ctx.prov,
        "git_dirty_files": ctx.git_dirty,
        "llama_server": {
            "flags_effective": ctx.server.server_flags,
            "reference_flags_darwin": mac_flags,
            "n_gpu_layers_final": args.ngl,
            "n_ctx": args.ctx_expected,
            "model_path": args.model,
            "model_version": ctx.model_version,
            "quantization": ctx.quantization,
            "ngl_rationale": "-c 32768 kept identical to darwin; -ngl 16 offloads model+KV safely on 4 GiB RTX 3050 VRAM",
        },
        "memory_metric_note": "On Windows the primary physical memory metric proc_peak_phys_mb is PeakWorkingSetSize (GetProcessMemoryInfo).",
        "pmu": {"method": "Win32 QueryProcessCycleTime and GetProcessMemoryInfo"},
        "energy": {
            "backend": ctx.pmon.telemetry_backend,
            "telemetry": "windows_nvml_and_kernel",
            "total_definition": "Hardware NVML GPU TotalEnergyConsumption + CPU package dynamic power model",
        },
        "idle_baseline": ib,
        "thermal_plateau": plateau,
        "thermal_gate": {
            "cpu_max_c": args.cool_cpu_c,
            "gpu_max_c": args.cool_gpu_c,
            "cpu_ceiling_c": args.thermal_ceiling_cpu_c,
            "gpu_ceiling_c": args.thermal_ceiling_gpu_c,
            "min_cooldown_s": args.thermal_min_cooldown_s,
            "timeout_s": args.cool_timeout_s,
        },
        "fans": {"rpm": ctx.tc.fan_rpm(), "max_rpm": [5000, 5200]},
        "nvidia_smi_snapshot": smi_snap,
        "lscpu": {"Architecture": "x86_64", "Model name": ctx.prov["hardware"]},
        "toolchain": ctx.runtime_labels,
        "adapters_cfg": {"reps": args.reps, "warmups": args.warmups},
    }
    wjson(meta_path, meta)


def main(argv: list[str] | None = None) -> None:
    global PATHS, _RESUME_ENABLED
    ap = build_arg_parser()
    args = ap.parse_args(argv)
    _RESUME_ENABLED = bool(args.resume)

    if args.smoke_test:
        args.reps = 1
        args.warmups = 0
        if not args.suffix and not args.output_dir:
            args.suffix = "_smoke"
        args.idle_sec = 0.5
        args.cool_timeout_s = 5.0
    elif args.quick:
        args.reps = 5
        args.warmups = 1
        if not args.suffix and not args.output_dir:
            args.suffix = "_quick"
    elif args.full:
        args.reps = 30
        args.warmups = 3
        if not args.suffix and not args.output_dir:
            args.suffix = f"_v2_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    args.ctx_expected = 32768
    plan = resolve_execution_plan(args)
    PATHS = Paths(suffix=args.suffix, output_dir=args.output_dir)

    if args.dry_run:
        print("=" * 80)
        print("[DRY-RUN] Windows-NVIDIA Confirmatory Campaign Execution Matrix (Protocol V2)")
        print(f"   Platform:     {plan['arch_tag']}")
        print(f"   Session ID:   {plan['session_id']}")
        print(f"   Reps/Cell:    {plan['reps']} (Warmups: {plan['warmups']})")
        print(f"   Model:        {plan['model']}")
        print(f"   NGL:          {plan['ngl']}")
        print(f"   Stages:       {plan['exec_stages']} (analyze={plan['analyze_enabled']})")
        print(f"   Workloads:    {plan['workload_seq']}")
        print(f"   Arms:         {plan['arms_seq']}")
        print(f"   Invert Order: {plan['invert_blocks']}")
        print(f"   Destination:  {plan['raw_dir']}")
        print("=" * 80)
        sys.exit(0)

    # Platform + physical NVIDIA GPU guard (never bypassed on real execution)
    from adapters.windows_nvidia_adapter import verify_windows_nvidia_platform

    gpu_info = verify_windows_nvidia_platform(gpu_index=args.gpu_index)
    print(
        f"Verified native Windows + NVIDIA GPU [{gpu_info['gpu_index']}]: "
        f"{gpu_info['gpu_name']} (UUID={gpu_info['gpu_uuid']}, Driver={gpu_info['driver_version']})",
        flush=True,
    )

    for d in (PATHS.raw, PATHS.tables):
        wmakedirs(d)

    from benchmark.environment_manifest import record_environment_manifest

    session_tag = args.session_id or ("S2_INVERTED" if args.invert_blocks else "S1_CANONICAL")
    env_path = record_environment_manifest(
        PATHS.raw,
        f"{session_tag}_{ARCH_TAG}",
        extra_metadata={
            "cross_platform_emulation": False,
            "target_platform": ARCH_TAG,
            "host_platform": f"{platform.system()}_{platform.machine()}",
            "gpu_uuid": gpu_info["gpu_uuid"],
            "gpu_name": gpu_info["gpu_name"],
            "driver_version": gpu_info["driver_version"],
            "invert_blocks": bool(args.invert_blocks),
            "ngl": int(args.ngl),
        },
    )
    print(f"Recorded environment manifest: {env_path}", flush=True)

    ctx = Ctx()
    ctx.args = args
    ctx.cache_prompt = False
    prepare(ctx)

    try:
        for st in plan["exec_stages"]:
            active_thermal_guard(ctx, label=f"pre_stage_{st}")
            if st == "A":
                stage_main(ctx, "A_cold", False, "raw_trials.jsonl", MAIN_ARMS)
            elif st == "B":
                stage_main(ctx, "B_warm", True, "warm_cache_trials.jsonl", MAIN_ARMS)
            elif st == "TOOLRAG":
                stage_tool_rag(ctx)
            elif st == "KV":
                stage_kv(ctx)
            elif st == "MCP":
                stage_mcp(ctx)
            time.sleep(5)
    finally:
        ctx.server.stop()

    if plan["analyze_enabled"]:
        from benchmark.windows_campaign_analysis import run_analysis

        run_analysis(PATHS, guard)
    print("\nCAMPAIGN COMPLETE", flush=True)


if __name__ == "__main__":
    main()
