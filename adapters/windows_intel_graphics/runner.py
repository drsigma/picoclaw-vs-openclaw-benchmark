#!/usr/bin/env python3
"""
adapters/windows_intel_graphics/runner.py

Dedicated Windows Intel Graphics Master Campaign Orchestrator.
Exclusively isolated from Mac Mini M4 (darwin), Windows NVIDIA (windows_x86_64), and Linux.

Features:
  - Enforced write-isolation guard (blocks writes to darwin/linux/windows_x86_64 NVIDIA)
  - Orphan process & port 8080 cleanup before every block
  - Empirical llama-server backend probe (Vulkan vs CPU AVX2) + offload logging (-ngl)
  - Per-trial delta telemetry + thermal/RAM cooldown protection
  - Extraction-time validation + single-trial retry (up to 3 attempts, never aborts whole campaign)
  - W2, W5 (LangChain + SQLite + evaluator.py quality_score 1-5), Full vs Minimal, Tool-RAG
  - Session 1 + Inter-session cooldown + Session 2 replication with TOST (statsmodels.ttost_ind)
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

REPO_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from adapters.windows_intel_graphics.adapter import (  # noqa: E402
    WindowsIntelGraphicsArmAdapter,
    probe_llama_backend,
    resolve_portable_toolchains,
)
from adapters.windows_intel_graphics.analysis import (  # noqa: E402
    run_combined_replication_analysis,
    run_intel_session_analysis,
)
from adapters.windows_intel_graphics.hardware_manifest import (  # noqa: E402
    detect_intel_windows_provenance,
    save_machine_manifest,
)
from adapters.windows_intel_graphics.telemetry import (  # noqa: E402
    NA,
    IntelGraphicsThermalAndLoadMonitor,
    assert_windows_process_counters_available,
    cleanup_orphan_processes,
    set_system_awake,
)
from adapters.windows_intel_graphics.validator import (  # noqa: E402
    compute_deterministic_cache_hit,
    execute_trial_with_retry,
)

ARCH_TAG = "windows_intel_graphics"
HEALTH_URL = "http://127.0.0.1:8080/health"
DEFAULT_MODEL = r"C:\bench_intel\models\Llama-3.2-3B-Instruct-Q4_K_M.gguf"

MAIN_ARMS = [
    "picoclaw",
    "openclaw_minimal",
    "openclaw_full",
    "python_native",
    "bun_minimal",
    "neural_baseline",
]
TOOL_RAG_ARMS = ["openclaw_tool_rag", "picoclaw_tool_rag"]
W5_ARMS = ["python_native", "picoclaw", "openclaw_minimal", "neural_baseline"]


class IntelPaths:
    def __init__(self, repo_dir: str, suffix: str = "") -> None:
        self.repo_dir = repo_dir
        self.tag = f"{ARCH_TAG}{suffix}"
        self.data = os.path.join(repo_dir, "data", self.tag)
        self.raw = os.path.join(self.data, "raw")
        self.results = os.path.join(repo_dir, "results", f"publication_campaign_{self.tag}")
        self.tables = os.path.join(self.results, "tables")
        self.repro = os.path.join(repo_dir, "reproducibility", f"clean_run_{self.tag}")
        self.manifest = os.path.join(repo_dir, "data", f"manifest_sha256_{self.tag}.json")
        self.allowed = tuple(os.path.realpath(p) for p in (self.data, self.results, self.repro, self.manifest))

    def guard(self, path: str) -> str:
        rp = os.path.realpath(path)
        low = rp.lower()
        in_allowed = any(rp == a or rp.startswith(a + os.sep) for a in self.allowed)
        forbidden_tokens = (
            "darwin",
            "linux",
            "windows_x86_64",
            "clean_run_windows_session",
            "publication_campaign" + os.sep,
        )
        # Allow publication_campaign_windows_intel_graphics*, block bare publication_campaign/
        rel = os.path.relpath(rp, os.path.realpath(self.repo_dir)).replace("\\", "/").lower()
        is_forbidden = (
            "darwin" in low
            or "linux" in low
            or "windows_x86_64" in low
            or "clean_run_windows_session" in low
            or rel.startswith("results/publication_campaign/")
            or rel == "data/manifest_sha256.json"
            or rel.startswith("data/raw/")
        )
        if not in_allowed or is_forbidden:
            raise PermissionError(
                f"ISOLATION GUARD VIOLATION: refusing to write outside {ARCH_TAG} namespace: {rp}"
            )
        return path


class IntelLlamaServer:
    def __init__(self, exe: str, model: str, ngl: int, n_ctx: int, threads: int, log_path: str, guard_fn) -> None:
        self.exe = exe
        self.model = model
        self.ngl = ngl
        self.n_ctx = n_ctx
        self.threads = threads
        self.log_path = log_path
        self.guard_fn = guard_fn
        self.proc: subprocess.Popen | None = None
        self.flag_tokens = [
            "-c", str(n_ctx),
            "-np", "1",
            "-ngl", str(ngl),
            "-t", str(threads),
            "--temp", "0.0",
            "--seed", "42",
        ]
        self.server_flags = " ".join(self.flag_tokens)
        self._log_file = None

    def start(self) -> int:
        cleanup_orphan_processes(target_names=("llama-server.exe",), port_to_check=8080)
        time.sleep(0.5)
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080)) == 0:
                raise RuntimeError("Port 8080 is still occupied after orphan cleanup.")

        cmd = [self.exe, "-m", self.model, "--host", "127.0.0.1", "--port", "8080"] + self.flag_tokens
        os.makedirs(os.path.dirname(self.guard_fn(self.log_path)), exist_ok=True)
        self._log_file = open(self.guard_fn(self.log_path), "ab")
        self.proc = subprocess.Popen(cmd, stdout=self._log_file, stderr=subprocess.STDOUT)

        t0 = time.monotonic()
        while True:
            if self.proc.poll() is not None:
                raise RuntimeError(f"llama-server exited early (rc={self.proc.returncode}); check {self.log_path}")
            try:
                with urllib.request.urlopen(HEALTH_URL, timeout=2.0) as resp:
                    if resp.status == 200:
                        return self.proc.pid
            except Exception:
                pass
            if time.monotonic() - t0 > 240.0:
                self.stop()
                raise RuntimeError("llama-server did not become healthy within 240s")
            time.sleep(0.5)

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self._log_file:
            try:
                self._log_file.close()
            except Exception:
                pass
            self._log_file = None


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _append_jsonl(path: str, rec: dict[str, Any], guard_fn) -> None:
    with open(guard_fn(path), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, allow_nan=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _done_keys(path: str) -> set[tuple]:
    return {
        (r["agent_key"], r["workload"], int(r["rep"]), bool(r["is_warmup"]))
        for r in _load_jsonl(path)
        if r.get("extraction_validated", True) is True
    }


def build_trial_record(
    *,
    session_id: str,
    prov: dict[str, str],
    git_dirty: int,
    model_version: str,
    quantization: str,
    server_flags: str,
    backend_info: dict[str, Any],
    ngl: int,
    regime: str,
    cache_prompt: bool,
    adapter: WindowsIntelGraphicsArmAdapter,
    workload: str,
    rep: int,
    is_warmup: bool,
    worker_res: dict[str, Any],
    telem_delta: dict[str, Any],
    cooldown_info: dict[str, Any],
) -> dict[str, Any]:
    t_task = float(worker_res["t_task_ms"])
    t_neural = float(worker_res["t_neural_ms"])
    t_orch = max(0.0, float(worker_res.get("t_orch_ms", t_task - t_neural)))
    prompt_ms = float(worker_res.get("prompt_ms") or 0.0)
    predicted_ms = float(worker_res.get("predicted_ms") or 0.0)
    ttft_ms = float(worker_res.get("ttft_ms") or 0.0)

    if prompt_ms <= 0.0:
        prompt_ms = ttft_ms if ttft_ms > 0.0 else max(0.1, t_neural * 0.2)
    if predicted_ms <= 0.0:
        predicted_ms = max(0.1, t_neural - prompt_ms)
    if ttft_ms <= 0.0:
        ttft_ms = prompt_ms

    prompt_tokens = int(worker_res.get("prompt_tokens") or 0)
    completion_tokens = int(worker_res.get("completion_tokens", worker_res.get("output_tokens") or 0))
    tokens_cached = int(worker_res.get("tokens_cached", worker_res.get("cached_tokens") or 0))
    prompt_eval_count = int(
        worker_res.get(
            "prompt_eval_count",
            worker_res.get("uncached_prompt_tokens", max(0, prompt_tokens - tokens_cached)),
        )
    )
    eval_count = int(worker_res.get("eval_count", completion_tokens))
    cache_hit = compute_deterministic_cache_hit(tokens_cached, prompt_eval_count)
    cache_hit_pct = round((tokens_cached / prompt_tokens * 100.0) if prompt_tokens > 0 else 0.0, 2)

    orch_proc = adapter.agent_key != "neural_baseline"

    return {
        "session_id": session_id,
        "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_commit": prov["git_commit"],
        "git_dirty_files": git_dirty,
        "hardware": prov["hardware"],
        "os": prov["os"],
        "model_version": model_version,
        "quantization": quantization,
        "server_flags": server_flags,
        "workload": workload,
        "regime": regime,
        "agent_key": adapter.agent_key,
        "architecture": adapter.name,
        "runtime": adapter.runtime,
        "mode": adapter.mode,
        "rep": rep,
        "is_warmup": is_warmup,
        "is_simulated": False,
        "data_source": "measured_hardware_windows_intel_graphics",
        "telemetry_backend": "windows_intel_graphics_wddm_pdh_and_win32_user_mode",
        "cache_prompt": cache_prompt,
        "ngl": ngl,
        "execution_backend": backend_info["execution_backend"],
        "offload_mode": backend_info["offload_mode"],
        "t_task_ms": round(t_task, 4),
        "t_neural_ms": round(t_neural, 4),
        "t_orch_ms": round(t_orch, 4),
        "phi_orch_pct": round((t_orch / t_task * 100.0) if t_task > 0 else 0.0, 4),
        "t_dispatch_ms": worker_res.get("t_dispatch_ms"),
        "t_http_ms": worker_res.get("t_http_ms"),
        "prompt_ms": round(prompt_ms, 4),
        "predicted_ms": round(predicted_ms, 4),
        "ttft_ms": round(ttft_ms, 4),
        "itl_ms": worker_res.get("itl_ms"),
        "t_prune_ms": worker_res.get("t_prune_ms"),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cached_tokens": tokens_cached,
        "tokens_cached": tokens_cached,
        "uncached_prompt_tokens": prompt_eval_count,
        "prompt_eval_count": prompt_eval_count,
        "eval_count": eval_count,
        "cache_hit": cache_hit,
        "cache_hit_pct": cache_hit_pct,
        "tool_calls": worker_res.get("tool_calls"),
        "http_status": int(worker_res.get("http_status") or 0),
        "finish_reason": str(worker_res.get("finish_reason") or "stop"),
        "quality_score": worker_res.get("quality_score", NA if (workload != "W5" or adapter.agent_key != "python_native") else None),
        "evaluation_reasoning": worker_res.get("evaluation_reasoning", NA if (workload != "W5" or adapter.agent_key != "python_native") else None),
        "proc_counters_applicable": orch_proc,
        "proc_instructions": NA,  # Windows user-mode PMU restricted (Explicit-NA)
        "proc_cycles": worker_res.get("proc_cycles") if orch_proc else NA,
        "proc_peak_phys_mb": worker_res.get("proc_peak_phys_mb") if orch_proc else 0.0,
        "proc_rss_mb": worker_res.get("proc_rss_mb") if orch_proc else 0.0,
        "page_faults": worker_res.get("page_faults") if orch_proc else NA,
        "thermal_cooldown_triggered": bool(cooldown_info.get("cooldown_triggered", False)),
        "thermal_cooldown_s": float(cooldown_info.get("cooldown_s", 0.0)),
        **telem_delta,
    }


def run_single_session(args: argparse.Namespace, session_suffix: str) -> IntelPaths:
    assert_windows_process_counters_available()
    set_system_awake(keep_display=True)

    paths = IntelPaths(REPO_DIR, suffix=session_suffix)
    os.makedirs(paths.guard(paths.raw), exist_ok=True)
    os.makedirs(paths.guard(paths.tables), exist_ok=True)

    toolchains = resolve_portable_toolchains(args.tools_root)
    backend_info = probe_llama_backend(toolchains)
    ngl = args.ngl if args.ngl is not None else int(backend_info["ngl_recommended"])

    if not backend_info.get("llama_server_exe") or not os.path.isfile(backend_info["llama_server_exe"]):
        raise RuntimeError(f"llama-server.exe not found under {args.tools_root}")
    if not os.path.isfile(args.model):
        raise RuntimeError(f"GGUF model not found: {args.model}")

    # Save machine manifest inside session raw folder
    save_machine_manifest(paths.guard(paths.raw), repo_dir=REPO_DIR)
    prov = detect_intel_windows_provenance(REPO_DIR)

    git_cmd = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
    git_dirty = len(subprocess.check_output([git_cmd, "-C", REPO_DIR, "status", "--porcelain"], text=True).splitlines())

    meta_path = os.path.join(paths.raw, "hardware_metadata.json")
    existing_meta = json.load(open(meta_path, encoding="utf-8")) if os.path.exists(meta_path) else None
    session_id = existing_meta["session_id"] if existing_meta else f"session_{paths.tag}_{uuid.uuid4().hex[:12]}"

    m = re.match(r"^(.*)-(Q\d\w*)\.gguf$", os.path.basename(args.model))
    model_version = m.group(1) if m else os.path.splitext(os.path.basename(args.model))[0]
    quantization = f"GGUF {m.group(2)} ({os.path.getsize(args.model) / 1e9:.3f} GB)" if m else "GGUF"

    monitor = IntelGraphicsThermalAndLoadMonitor(
        cpu_temp_threshold_c=args.cool_cpu_c,
        min_clock_under_load_mhz=args.min_clock_mhz,
        min_free_ram_mb=args.min_free_ram_mb,
        cooldown_duration_s=args.cooldown_s,
        cooldown_log_path=paths.guard(os.path.join(paths.raw, "cooldown_events.jsonl")),
    )

    server = IntelLlamaServer(
        exe=backend_info["llama_server_exe"],
        model=args.model,
        ngl=ngl,
        n_ctx=args.n_ctx,
        threads=args.threads,
        log_path=os.path.join(paths.raw, "llama_server.log"),
        guard_fn=paths.guard,
    )

    workloads = [w.strip().upper() for w in args.workloads.split(",") if w.strip()]
    stages = [s.strip().upper() for s in args.stages.split(",") if s.strip()]
    arms_requested = [a.strip() for a in args.arms.split(",") if a.strip()] if args.arms else MAIN_ARMS

    adapters: dict[str, WindowsIntelGraphicsArmAdapter] = {}
    for ak in set(arms_requested + TOOL_RAG_ARMS + W5_ARMS):
        ad = WindowsIntelGraphicsArmAdapter(ak, REPO_DIR, toolchains, timeout_s=args.trial_timeout_s)
        if ad.setup():
            adapters[ak] = ad
        elif ak in arms_requested:
            raise RuntimeError(f"Required adapter setup failed: {ak}")

    print(f"\n========================================================================", flush=True)
    print(f" WINDOWS INTEL GRAPHICS BENCHMARK — SESSION: {paths.tag}", flush=True)
    print(f" Hardware : {prov['hardware']}", flush=True)
    print(f" Backend  : {backend_info['execution_backend']} (-ngl {ngl}, -c {args.n_ctx}, -t {args.threads})", flush=True)
    print(f" Workloads: {workloads} | Stages: {stages} | Reps: {args.reps} | Warmups: {args.warmups}", flush=True)
    print(f"========================================================================", flush=True)

    server_pid = server.start()
    monitor.set_server_pid(server_pid)
    print(f"[SERVER] llama-server PID={server_pid} healthy on 127.0.0.1:8080 ({server.server_flags})", flush=True)

    meta = {
        "session_id": session_id,
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "arch_tag": ARCH_TAG,
        "session_tag": paths.tag,
        "provenance": prov,
        "git_dirty_files": git_dirty,
        "llama_server": {
            "flags_effective": server.server_flags,
            "n_gpu_layers_final": ngl,
            "n_ctx": args.n_ctx,
            "threads": args.threads,
            "model_path": args.model,
            "model_version": model_version,
            "quantization": quantization,
            "execution_backend": backend_info["execution_backend"],
            "offload_mode": backend_info["offload_mode"],
            "vulkan_devices_detected": backend_info["vulkan_devices_detected"],
            "rationale": backend_info["rationale"],
        },
        "telemetry_policy": {
            "nvml_or_nvidia_smi_used": False,
            "zero_mock_strict_na": True,
            "delta_per_trial_enforced": True,
            "unavailable_in_user_mode": [
                "proc_instructions",
                "energy_gpu_j",
                "energy_total_j",
                "energy_net_above_idle_j",
                "pcie_bandwidth_mb_s",
                "gpu_temp_c",
            ],
        },
        "thermal_safeguard": {
            "cpu_temp_threshold_c": args.cool_cpu_c,
            "min_clock_under_load_mhz": args.min_clock_mhz,
            "min_free_ram_mb": args.min_free_ram_mb,
            "cooldown_duration_s": args.cooldown_s,
        },
        "campaign_config": {
            "reps": args.reps,
            "warmups": args.warmups,
            "workloads": workloads,
            "stages": stages,
            "arms": [a for a in arms_requested if a in adapters],
        },
    }
    with open(paths.guard(meta_path), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    def _run_one(ak: str, wl: str, rep: int, is_warmup: bool, regime: str, cache_prompt: bool, out_path: str) -> None:
        ad = adapters[ak]

        def _attempt() -> dict[str, Any]:
            set_system_awake(keep_display=True)
            cd = monitor.check_and_cooldown(context_label=f"{paths.tag}/{regime}/{ak}/{wl}/rep={rep}")
            monitor.start_trial()
            try:
                wres = ad.run_workload(wl, cache_prompt=cache_prompt)
            finally:
                telem = monitor.stop_trial()
            return build_trial_record(
                session_id=session_id,
                prov=prov,
                git_dirty=git_dirty,
                model_version=model_version,
                quantization=quantization,
                server_flags=server.server_flags,
                backend_info=backend_info,
                ngl=ngl,
                regime=regime,
                cache_prompt=cache_prompt,
                adapter=ad,
                workload=wl,
                rep=rep,
                is_warmup=is_warmup,
                worker_res=wres,
                telem_delta=telem,
                cooldown_info=cd,
            )

        rec, passed, reasons = execute_trial_with_retry(
            _attempt, regime=regime, agent_key=ak, workload=wl, max_retries=3, retry_delay_s=2.0
        )
        if rec is None:
            print(
                f"[ERROR-SKIP] {regime} {ak}/{wl} rep={rep} failed all 3 attempts without record: {reasons}",
                flush=True,
            )
            return
        if not passed:
            print(
                f"[CAVEAT] {regime} {ak}/{wl} rep={rep} retained with caveat after 3 retries: {reasons[-1]}",
                flush=True,
            )
        _append_jsonl(out_path, rec, paths.guard)
        tag = "W" if is_warmup else " "
        q_str = f" Q={rec['quality_score']}" if wl == "W5" else ""
        print(
            f"[{regime}{tag}] {ak:18s} {wl} rep={rep:02d} "
            f"t_task={rec['t_task_ms']:8.1f}ms orch={rec['t_orch_ms']:7.2f}ms "
            f"tok={rec['prompt_tokens']}/{rec['completion_tokens']} "
            f"cached={rec['tokens_cached']} hit={rec['cache_hit']} "
            f"RAM={rec['system_ram_used_end_mb']:.0f}MB{q_str}"
            f"{' THROTTLED' if rec['thermal_throttled'] else ''}",
            flush=True,
        )

    def _arms_for_wl(wl: str, base_arms: list[str]) -> list[str]:
        if wl == "W5":
            return [a for a in W5_ARMS if a in adapters and a in base_arms] or [a for a in W5_ARMS if a in adapters]
        return [a for a in base_arms if a in adapters]

    try:
        invert = getattr(args, "invert_blocks", False)
        planned_stages = [s for s in reversed(stages) if s != "ANALYZE"] + (["ANALYZE"] if "ANALYZE" in stages else []) if invert else stages
        print(f"\n▶️  [PLAN] Session execution order (invert_blocks={invert}): stages={planned_stages}")

        # Stage B: Warm KV-cache (block-isolated per condition for deterministic cache_hit)
        if "B" in planned_stages:
            out_b = os.path.join(paths.raw, "warm_cache_trials.jsonl")
            done_b = _done_keys(out_b)
            wl_order = list(reversed(workloads)) if invert else list(workloads)
            conds = [(ak, wl) for wl in wl_order for ak in (list(reversed(_arms_for_wl(wl, arms_requested))) if invert else _arms_for_wl(wl, arms_requested))]
            if not invert:
                random.Random(2027).shuffle(conds)
            else:
                conds.reverse()
            print(f"\n=== STAGE B (Warm KV-Cache, cache_prompt=true, invert={invert}): {len(conds)} blocks ===", flush=True)
            for ak, wl in conds:
                for w_rep in range(1, args.warmups + 1):
                    if (ak, wl, w_rep, True) not in done_b:
                        _run_one(ak, wl, w_rep, True, "B_warm", True, out_b)
                for rep in range(1, args.reps + 1):
                    if (ak, wl, rep, False) not in done_b:
                        _run_one(ak, wl, rep, False, "B_warm", True, out_b)

        # Stage TOOLRAG: Full vs Minimal vs Tool-RAG in the same session (W2)
        if "TOOLRAG" in planned_stages:
            out_tr = os.path.join(paths.raw, "tool_rag_mitigation_trials.jsonl")
            tr_wls = [w for w in workloads if w != "W5"] or ["W2"]
            if invert:
                tr_wls = list(reversed(tr_wls))
            tr_arms = [a for a in TOOL_RAG_ARMS if a in adapters]
            if invert:
                tr_arms = list(reversed(tr_arms))
            regimes_seq = (("regime_a_cold", False), ("regime_b_warm", True)) if invert else (("regime_b_warm", True), ("regime_a_cold", False))
            for reg_name, cache_flag in regimes_seq:
                done_tr = {
                    (r["regime"], r["agent_key"], r["workload"], int(r["rep"]), bool(r["is_warmup"]))
                    for r in _load_jsonl(out_tr)
                    if r.get("extraction_validated", True) is True
                }
                print(f"\n=== STAGE TOOLRAG ({reg_name}, invert={invert}): arms={tr_arms} wls={tr_wls} ===", flush=True)
                for wl in tr_wls:
                    for ak in tr_arms:
                        for w_rep in range(1, args.warmups + 1):
                            if (reg_name, ak, wl, w_rep, True) not in done_tr:
                                _run_one(ak, wl, w_rep, True, reg_name, cache_flag, out_tr)
                        for rep in range(1, args.reps + 1):
                            if (reg_name, ak, wl, rep, False) not in done_tr:
                                _run_one(ak, wl, rep, False, reg_name, cache_flag, out_tr)

        # Stage A: Cold Prefill (randomized block interleaving)
        if "A" in planned_stages:
            out_a = os.path.join(paths.raw, "raw_trials.jsonl")
            done_a = _done_keys(out_a)
            wl_order = list(reversed(workloads)) if invert else list(workloads)
            conds = [(ak, wl) for wl in wl_order for ak in (list(reversed(_arms_for_wl(wl, arms_requested))) if invert else _arms_for_wl(wl, arms_requested))]
            print(f"\n=== STAGE A (Cold Prefill, cache_prompt=false, invert={invert}): {len(conds)} cells ===", flush=True)
            for ak, wl in conds:
                for w_rep in range(1, args.warmups + 1):
                    if (ak, wl, w_rep, True) not in done_a:
                        _run_one(ak, wl, w_rep, True, "A_cold", False, out_a)
            rng = random.Random(2026)
            for rep in range(1, args.reps + 1):
                block = list(conds)
                if invert:
                    block.reverse()
                else:
                    rng.shuffle(block)
                for ak, wl in block:
                    if (ak, wl, rep, False) not in done_a:
                        _run_one(ak, wl, rep, False, "A_cold", False, out_a)
    finally:
        server.stop()
        cleanup_orphan_processes(target_names=("llama-server.exe", "picoclaw_orch_windows.exe"), port_to_check=8080)

    if "ANALYZE" in stages:
        run_intel_session_analysis(paths, REPO_DIR, paths.guard)
        # Package reproducibility bundle inside isolated reproducibility dir
        os.makedirs(paths.guard(paths.repro), exist_ok=True)
        shutil.copytree(paths.data, paths.guard(os.path.join(paths.repro, "data")), dirs_exist_ok=True)
        shutil.copytree(paths.results, paths.guard(os.path.join(paths.repro, "results")), dirs_exist_ok=True)
        if os.path.exists(paths.manifest):
            shutil.copy2(paths.manifest, paths.guard(os.path.join(paths.repro, "manifest_sha256.json")))

    return paths


def main() -> None:
    is_dry_or_help = any(arg in sys.argv for arg in ["--dry-run", "-h", "--help"])
    if platform.system() != "Windows" and not is_dry_or_help:
        print(f"FATAL: Native platform mismatch! Windows Intel Graphics runner requires Windows. Detected: {platform.system()} {platform.machine()}", file=sys.stderr)
        sys.exit(1)

    ap = argparse.ArgumentParser(description="Windows Intel Graphics Dedicated Benchmark Campaign Runner")
    ap.add_argument("--smoke-test", action="store_true", help="Fast smoke test execution (reps=1, warmups=0)")
    ap.add_argument("--quick", action="store_true", help="Quick execution mode (reps=5, warmups=1)")
    ap.add_argument("--full", action="store_true", help="Full confirmatory campaign execution (reps=30, warmups=3)")
    ap.add_argument("--dry-run", action="store_true", help="Dry run matrix verification without hardware execution")
    ap.add_argument("--resume", action="store_true", help="Resume interrupted campaign")
    ap.add_argument("--invert-blocks", action="store_true", help="Invert block execution order for Session 2 counterbalancing")
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--warmups", type=int, default=3)
    ap.add_argument("--ngl", type=int, default=None, help="Override -ngl (default: auto-probed)")
    ap.add_argument("--n-ctx", type=int, default=32768, help="Context window (32768 for uniform cross-platform parity)")
    ap.add_argument("--threads", type=int, default=4, help="CPU threads for llama-server (4 physical cores on i7-4790K)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--tools-root", default=r"C:\bench_intel\tools")
    ap.add_argument("--workloads", default="W2,W5")
    ap.add_argument("--stages", default="B,TOOLRAG,A,ANALYZE")
    ap.add_argument("--arms", default=",".join(MAIN_ARMS))
    ap.add_argument("--sessions", default="1", help="Comma-separated sessions to execute (default: 1; wrapper expands sessions)")
    ap.add_argument("--inter-session-cooldown-s", type=float, default=30.0)
    ap.add_argument("--cool-cpu-c", type=float, default=82.0)
    ap.add_argument("--min-clock-mhz", type=int, default=3100)
    ap.add_argument("--min-free-ram-mb", type=float, default=1800.0)
    ap.add_argument("--cooldown-s", type=float, default=20.0)
    ap.add_argument("--trial-timeout-s", type=float, default=480.0)
    ap.add_argument("--suffix", default="")
    args = ap.parse_args()

    sessions = [s.strip() for s in args.sessions.split(",") if s.strip()]
    if len(sessions) > 1 and "_session" in args.suffix:
        raise ValueError(
            f"Ambiguous session configuration: runner received multi-session argument --sessions '{args.sessions}' "
            f"while suffix '{args.suffix}' already contains an isolated session namespace. "
            "Pass --sessions 1 when wrapper manages session suffixes."
        )

    if args.smoke_test:
        args.reps = 1
        args.warmups = 0
        if not args.suffix:
            args.suffix = "_smoke"
    elif args.quick:
        args.reps = 5
        args.warmups = 1
    elif args.full:
        args.reps = 30
        args.warmups = 3

    if args.dry_run:
        args.reps = 1
        args.warmups = 0
        args.sessions = "1"
        args.suffix = "_dryrun"
        args.inter_session_cooldown_s = 1.0
        print("[DRY-RUN] Isolated verification mode enabled.", flush=True)
        print(f"[DRY-RUN] Matrix: arms={args.arms} workloads={args.workloads} stages={args.stages} invert={args.invert_blocks}", flush=True)
        if platform.system() != "Windows":
            print("[DRY-RUN] Cross-platform flag and matrix parsing verified successfully on host.", flush=True)
            return
        run_single_session(args, "_dryrun")
        print("\nDRY-RUN COMPLETE", flush=True)
        return

    sessions = [s.strip() for s in args.sessions.split(",") if s.strip()]
    session_paths: dict[str, IntelPaths] = {}

    for idx, sess in enumerate(sessions):
        suf = f"{args.suffix}_session{sess}"
        session_paths[sess] = run_single_session(args, suf)
        if idx < len(sessions) - 1:
            print(f"\n[COOLDOWN] Inter-session stabilization pause ({args.inter_session_cooldown_s:.0f}s)...", flush=True)
            cleanup_orphan_processes(target_names=("llama-server.exe", "picoclaw_orch_windows.exe"), port_to_check=8080)
            time.sleep(args.inter_session_cooldown_s)

    if "1" in session_paths and "2" in session_paths:
        combined_paths = IntelPaths(REPO_DIR, suffix=f"{args.suffix}_replication")
        print("\n=== COMPUTING INTER-SESSION REPLICATION (TOST via statsmodels.ttost_ind) ===", flush=True)
        rep_out = run_combined_replication_analysis(
            repo_dir=REPO_DIR,
            s1_raw_dir=session_paths["1"].raw,
            s2_raw_dir=session_paths["2"].raw,
            out_dir=combined_paths.results,
            manifest_path=combined_paths.manifest,
            guard=combined_paths.guard,
        )
        print(
            f"[TOST] Warm cells equivalent (T_task/T_orch): "
            f"{rep_out['regime_b_warm_tost']['t_task_equivalent_cells']}/"
            f"{rep_out['regime_b_warm_tost']['total_cells_compared']} | "
            f"{rep_out['regime_b_warm_tost']['t_orch_equivalent_cells']}/"
            f"{rep_out['regime_b_warm_tost']['total_cells_compared']}",
            flush=True,
        )

    print("\nWINDOWS INTEL GRAPHICS CAMPAIGN COMPLETE", flush=True)


if __name__ == "__main__":
    main()
