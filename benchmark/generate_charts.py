#!/usr/bin/env python3
"""
Generates high-resolution (300 DPI) charts, figures, and architectural diagrams
for the CCM313-EEI203 System Testing & Performance Evaluation Report.
"""
import json
import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH_DIR = os.path.join(REPO_DIR, "benchmark")
FIG_DIR = os.path.join(REPO_DIR, "figures")
DATA_DIR = os.path.join(REPO_DIR, "data")
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.labelweight": "bold",
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 300,
})

COLOR_PICO = "#0D9488"     # Teal (PicoClaw Go)
COLOR_OPEN = "#E11D48"     # Crimson/Rose (OpenClaw Node.js/TS)
COLOR_NEURAL = "#3B82F6"   # Blue (Neural Inference)
COLOR_ORCH = "#F59E0B"     # Amber (Orchestration Overhead)


def draw_architecture_diagram():
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 65)
    ax.axis("off")

    # Outer Hardware Box
    outer = patches.FancyBboxPatch(
        (2, 2), 96, 60, boxstyle="round,pad=0.8",
        edgecolor="#1E293B", facecolor="#F8FAFC", linewidth=2.0
    )
    ax.add_patch(outer)
    ax.text(
        50, 59.5,
        "HOST TESTBED: APPLE MAC MINI M4 (10-Core CPU [4P+6E] | 10-Core Metal GPU | 24 GB Unified LPDDR5X @ 120 GB/s)",
        ha="center", va="center", fontsize=10.5, fontweight="bold", color="#0F172A"
    )

    def add_box(x, y, w, h, title, lines, bg="#FFFFFF", border="#334155", title_color="#0F172A"):
        b = patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.5",
            edgecolor=border, facecolor=bg, linewidth=1.6
        )
        ax.add_patch(b)
        ax.text(x + w / 2, y + h - 2.1, title, ha="center", va="center", fontsize=9.5, fontweight="bold", color=title_color)
        for idx, line in enumerate(lines):
            ax.text(x + 1.5, y + h - 4.8 - idx * 2.2, line, ha="left", va="center", fontsize=8.2, color="#1E293B")

    # Top Left: Workload Driver
    add_box(
        5, 42, 42, 14,
        "1. WORKLOAD DRIVER & HARNESS (Python 3.12.3)",
        [
            "• Asynchronous HTTP/SSE Streaming Driver (aiohttp / urllib)",
            "• High-Precision POSIX Monotonic Clocks (clock_gettime_ns)",
            "• Randomized Full Factorial Scheduler (16 Treatments, n=30)",
            "• Thermal & Cooldown Enforcer (caffeinate -dims active)"
        ],
        bg="#EFF6FF", border="#2563EB", title_color="#1D4ED8"
    )

    # Top Right: Telemetry & Profiling
    add_box(
        53, 42, 42, 14,
        "2. HARDWARE TELEMETRY & PROFILERS (Darwin 25G83)",
        [
            "• hyperfine v2.0.0: Process Cold-Start & Warm Cache Timing",
            "• Darwin libproc RUSAGE_INFO_V4: Kernel RSS & Phys Footprint",
            "• Hardware PMCs: ri_instructions, ri_cycles, ri_billed_energy",
            "• powermetrics: Blocked in user-space (requires euid=0 root)"
        ],
        bg="#FEF3C7", border="#D97706", title_color="#B45309"
    )

    # Middle Left: Condition A1 (OpenClaw)
    add_box(
        5, 22, 42, 15,
        "3A. FACTOR A1: OpenClaw v2026.10.7 (Node.js v26.12.1)",
        [
            "• Google V8 JIT Engine + Generational Garbage Collector",
            "• Dynamic ESM Module Graph (497 npm packages + node:sqlite)",
            "• Default CLI Prompt: 40,799 chars (16,369 tokens, 54 tools)",
            "• Equalized Benchmark Worker: openclaw_orch.mjs"
        ],
        bg="#FFE4E6", border="#E11D48", title_color="#BE123C"
    )

    # Middle Right: Condition A2 (PicoClaw)
    add_box(
        53, 22, 42, 15,
        "3B. FACTOR A2: PicoClaw v0.3.1 (Native Go 1.23.2)",
        [
            "• Statically Compiled Mach-O ARM64 Binary (Zero External Deps)",
            "• Concurrent Goroutines + Non-Generational Tri-Color Sweep GC",
            "• Ultra-Fast Cold Launch (9.6 ms) & Minimal Idle RSS (14.2 MB)",
            "• Equalized Benchmark Worker: picoclaw_orch (7.9 MB binary)"
        ],
        bg="#CCFBF1", border="#0D9488", title_color="#0F766E"
    )

    # Bottom Left: Synthetic Workloads (W1-W4)
    add_box(
        5, 4.5, 42, 13,
        "4. SYNTHETIC WORKLOAD TIERS (Factor B: W1–W4)",
        [
            "• W1 (Low): Single-Turn Reflection (128 prompt -> 64 out, 0 tools)",
            "• W2 (Med): 3-Tool Chain (list_dir [50], grep_logs [147KB], calc_stats)",
            "• W3 (High): Vector RAG (100k-param 384d head + 10,000 doc chunks)",
            "• W4 (Stress): 10-Turn Autonomous ReAct Loop (512 -> 2,048 tokens)"
        ],
        bg="#F3E8FF", border="#7C3AED", title_color="#6D28D9"
    )

    # Bottom Right: Local Neural Serving Engine
    add_box(
        53, 4.5, 42, 13,
        "5. EQUALIZED NEURAL ENGINE (llama.cpp b11887 Metal)",
        [
            "• Server Endpoint: http://127.0.0.1:8080/v1/chat/completions",
            "• Model: Llama-3.2-3B-Instruct Quantized GGUF Q4_K_M (1.92 GB)",
            "• Hardware Offload: Apple M4 10-Core Metal GPU (ngl=99, 46.3 tok/s)",
            "• Deterministic Decoding: temp = 0.0, top_p = 1.0, seed = 42"
        ],
        bg="#ECFDF5", border="#059669", title_color="#047857"
    )

    # Arrows
    arrow_kw = dict(arrowstyle="->,head_width=0.35,head_length=0.45", lw=1.6, color="#334155")
    ax.annotate("", xy=(26, 37.3), xytext=(26, 41.8), arrowprops=arrow_kw)
    ax.annotate("", xy=(74, 37.3), xytext=(35, 41.8), arrowprops=arrow_kw)
    ax.annotate("", xy=(26, 37.3), xytext=(65, 41.8), arrowprops=dict(arrowstyle="->", lw=1.3, ls="--", color="#B45309"))
    ax.annotate("", xy=(74, 37.3), xytext=(74, 41.8), arrowprops=dict(arrowstyle="->", lw=1.3, ls="--", color="#B45309"))
    ax.annotate("", xy=(26, 17.8), xytext=(26, 21.8), arrowprops=arrow_kw)
    ax.annotate("", xy=(26, 17.8), xytext=(65, 21.8), arrowprops=arrow_kw)
    ax.annotate("", xy=(74, 17.8), xytext=(35, 21.8), arrowprops=arrow_kw)
    ax.annotate("", xy=(74, 17.8), xytext=(74, 21.8), arrowprops=arrow_kw)

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig1_architecture_topology.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    return out


def plot_exp1_startup_memory(data):
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2))

    # Subplot A: Cold-Start Latency (hyperfine n=30)
    ax = axes[0]
    categories = ["CLI Version Probe\n(--version / version)", "Agent Subcommand Init\n(agent --help)"]
    pico_means = [
        data["cold_start_cli_version_ms"]["picoclaw"]["mean"],
        data["cold_start_agent_init_ms"]["picoclaw"]["mean"],
    ]
    pico_cis = [
        data["cold_start_cli_version_ms"]["picoclaw"]["ci95_half"],
        data["cold_start_agent_init_ms"]["picoclaw"]["ci95_half"],
    ]
    open_means = [
        data["cold_start_cli_version_ms"]["openclaw"]["mean"],
        data["cold_start_agent_init_ms"]["openclaw"]["mean"],
    ]
    open_cis = [
        data["cold_start_cli_version_ms"]["openclaw"]["ci95_half"],
        data["cold_start_agent_init_ms"]["openclaw"]["ci95_half"],
    ]

    x = np.arange(len(categories))
    w = 0.34
    b1 = ax.bar(x - w / 2, pico_means, w, yerr=pico_cis, capsize=4, label="PicoClaw v0.3.1 (Go)", color=COLOR_PICO, edgecolor="#0F172A")
    b2 = ax.bar(x + w / 2, open_means, w, yerr=open_cis, capsize=4, label="OpenClaw v2026.10.7 (Node.js)", color=COLOR_OPEN, edgecolor="#0F172A")
    ax.set_ylabel("Cold-Start Latency T_cold (ms)")
    ax.set_title("(a) Process Cold-Start Latency (hyperfine, n=30)")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylim(0, max(open_means) * 1.25)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")

    for bar, ci in zip(b1, pico_cis):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + ci + 4, f"{h:.1f} ms", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0F766E")
    for bar, ci in zip(b2, open_cis):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + ci + 4, f"{h:.1f} ms", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#BE123C")

    # Subplot B: Memory Footprint (RSS_idle vs RSS_peak across W1-W4)
    ax2 = axes[1]
    tiers = ["Idle Baseline", "W1 (Low)", "W2 (Med)", "W3 (RAG)", "W4 (ReAct)"]
    t_open_keys = ["T9", "T11", "T13", "T15"]
    t_pico_keys = ["T10", "T12", "T14", "T16"]
    pico_rss = [data["treatments"]["T10"]["rss_idle_mb"]["mean"]] + [data["treatments"][k]["rss_peak_mb"]["mean"] for k in t_pico_keys]
    open_rss = [data["treatments"]["T9"]["rss_idle_mb"]["mean"]] + [data["treatments"][k]["rss_peak_mb"]["mean"] for k in t_open_keys]

    x2 = np.arange(len(tiers))
    b3 = ax2.bar(x2 - w / 2, pico_rss, w, label="PicoClaw RSS (MB)", color=COLOR_PICO, edgecolor="#0F172A")
    b4 = ax2.bar(x2 + w / 2, open_rss, w, label="OpenClaw RSS (MB)", color=COLOR_OPEN, edgecolor="#0F172A")
    ax2.set_ylabel("Resident Set Size RSS (MB)")
    ax2.set_title("(b) Resident Memory Scaling Across Workload Tiers")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(tiers, rotation=12)
    ax2.set_ylim(0, max(open_rss) * 1.22)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)
    ax2.legend(loc="upper left")

    for bar in b3:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h + 5, f"{h:.1f}", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#0F766E")
    for bar in b4:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h + 5, f"{h:.0f}", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#BE123C")

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig2_exp1_cold_start_rss.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    return out


def plot_exp2_latency_overhead(data):
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4))

    # Subplot A: Orchestration Overhead T_orch (ms) across Cold & Warm for W1-W4
    ax = axes[0]
    labels = ["W1\nCold", "W1\nWarm", "W2\nCold", "W2\nWarm", "W3\nCold", "W3\nWarm", "W4\nCold", "W4\nWarm"]
    open_ids = ["T1", "T9", "T3", "T11", "T5", "T13", "T7", "T15"]
    pico_ids = ["T2", "T10", "T4", "T12", "T6", "T14", "T8", "T16"]

    open_orch = [data["treatments"][k]["t_orch_ms"]["mean"] for k in open_ids]
    pico_orch = [data["treatments"][k]["t_orch_ms"]["mean"] for k in pico_ids]

    x = np.arange(len(labels))
    w = 0.36
    ax.bar(x - w / 2, pico_orch, w, label="PicoClaw T_orch (ms)", color=COLOR_PICO, edgecolor="#0F172A")
    ax.bar(x + w / 2, open_orch, w, label="OpenClaw T_orch (ms)", color=COLOR_OPEN, edgecolor="#0F172A")
    ax.set_ylabel("Isolated Orchestrator Overhead T_orch (ms)")
    ax.set_title("(a) Decoupled Agent Orchestration Latency (T_task - T_neural)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")

    # Subplot B: Orchestration Overhead Ratio Phi_orch (%)
    ax2 = axes[1]
    open_phi = [data["treatments"][k]["phi_orch_pct"]["mean"] for k in open_ids]
    pico_phi = [data["treatments"][k]["phi_orch_pct"]["mean"] for k in pico_ids]

    b1 = ax2.bar(x - w / 2, pico_phi, w, label="PicoClaw Φ_orch (%)", color=COLOR_PICO, edgecolor="#0F172A")
    b2 = ax2.bar(x + w / 2, open_phi, w, label="OpenClaw Φ_orch (%)", color=COLOR_OPEN, edgecolor="#0F172A")
    ax2.set_ylabel("Orchestration Overhead Ratio Φ_orch (%)")
    ax2.set_title("(b) Orchestration Overhead Share of Total Latency (%)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.set_ylim(0, max(open_phi) * 1.25)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right")

    for bar in b1:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h + 0.4, f"{h:.1f}%", ha="center", va="bottom", fontsize=7.2, color="#0F766E", fontweight="bold")
    for bar in b2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h + 0.4, f"{h:.1f}%", ha="center", va="bottom", fontsize=7.2, color="#BE123C", fontweight="bold")

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig3_exp2_latency_overhead.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    return out


def plot_exp3_energy_edp(data):
    pm_path = os.path.join(DATA_DIR, "powermetrics_parsed.json")
    if not os.path.exists(pm_path):
        pm_path = os.path.join(BENCH_DIR, "powermetrics_parsed.json")
    has_pm = os.path.exists(pm_path)
    if has_pm:
        with open(pm_path, "r") as f:
            pm = json.load(f)
        fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.9))
        ax0 = axes[0]
        t_idle = np.cumsum([s["elapsed_ms"] / 1000.0 for s in pm["idle"]["samples"]])
        p_idle = [s["combined_mw"] / 1000.0 for s in pm["idle"]["samples"]]
        t_pico = np.cumsum([s["elapsed_ms"] / 1000.0 for s in pm["picoclaw"]["samples"][:24]])
        p_pico = [s["combined_mw"] / 1000.0 for s in pm["picoclaw"]["samples"][:24]]
        t_open = np.cumsum([s["elapsed_ms"] / 1000.0 for s in pm["openclaw"]["samples"][:24]])
        p_open = [s["combined_mw"] / 1000.0 for s in pm["openclaw"]["samples"][:24]]

        ax0.plot(t_pico, p_pico, "-o", markersize=3.5, linewidth=1.8, color=COLOR_PICO, label="PicoClaw + Metal GPU (W)")
        ax0.plot(t_open, p_open, "-s", markersize=3.5, linewidth=1.6, color=COLOR_OPEN, alpha=0.85, label="OpenClaw + Metal GPU (W)")
        ax0.plot(t_idle, p_idle, "--", linewidth=1.6, color="#475569", label="Idle Baseline (~1.46 W)")
        ax0.set_xlabel("Elapsed Time (s, 100 ms SMC samples)")
        ax0.set_ylabel("Combined SoC Power (Watts)")
        ax0.set_title("(a) Real sudo powermetrics Trace (M4)")
        ax0.set_ylim(0, 19.5)
        ax0.grid(True, linestyle="--", alpha=0.5)
        ax0.legend(loc="upper right", fontsize=7.5)
        ax = axes[1]
        ax2 = axes[2]
        sub_b = "(b) Cumulative SoC Energy E_pkg (J)"
        sub_c = "(c) Energy-Delay Product EDP (J·s)"
    else:
        fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.2))
        ax = axes[0]
        ax2 = axes[1]
        sub_b = "(a) Cumulative SoC Energy Consumption (Cold Start)"
        sub_c = "(b) Energy-Delay Product (EDP = E_pkg × T_task)"

    tiers = ["W1 (Refl.)", "W2 (Tools)", "W3 (RAG)", "W4 (ReAct)"]
    open_cold = ["T1", "T3", "T5", "T7"]
    pico_cold = ["T2", "T4", "T6", "T8"]

    open_e = [data["treatments"][k]["e_pkg_j"]["mean"] for k in open_cold]
    pico_e = [data["treatments"][k]["e_pkg_j"]["mean"] for k in pico_cold]
    open_edp = [data["treatments"][k]["edp_js"]["mean"] for k in open_cold]
    pico_edp = [data["treatments"][k]["edp_js"]["mean"] for k in pico_cold]

    x = np.arange(len(tiers))
    w = 0.35
    ax.bar(x - w / 2, pico_e, w, label="PicoClaw E_pkg (J)", color=COLOR_PICO, edgecolor="#0F172A")
    ax.bar(x + w / 2, open_e, w, label="OpenClaw E_pkg (J)", color=COLOR_OPEN, edgecolor="#0F172A")
    ax.set_ylabel("SoC Package Energy E_pkg (Joules)")
    ax.set_title(sub_b)
    ax.set_xticks(x)
    ax.set_xticklabels(tiers, rotation=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(fontsize=8)

    ax2.bar(x - w / 2, pico_edp, w, label="PicoClaw EDP (J·s)", color=COLOR_PICO, edgecolor="#0F172A")
    ax2.bar(x + w / 2, open_edp, w, label="OpenClaw EDP (J·s)", color=COLOR_OPEN, edgecolor="#0F172A")
    ax2.set_yscale("log")
    ax2.set_ylabel("Energy-Delay Product EDP (J·s, log scale)")
    ax2.set_title(sub_c)
    ax2.set_xticks(x)
    ax2.set_xticklabels(tiers, rotation=10)
    ax2.grid(axis="y", linestyle="--", alpha=0.5, which="both")
    ax2.legend(fontsize=8)

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig4_exp3_energy_edp.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    return out


def plot_exp4_tools_and_prompt_bloat(data):
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.3))

    # Subplot A: Tool Dispatch Throughput R_tool (ops/sec) in W2 and W4
    ax = axes[0]
    conds = ["W2 (3 Tools)\nCold", "W2 (3 Tools)\nWarm", "W4 (10 Tools)\nCold", "W4 (10 Tools)\nWarm"]
    open_k = ["T3", "T11", "T7", "T15"]
    pico_k = ["T4", "T12", "T8", "T16"]

    open_rt = [data["treatments"][k]["r_tool_ops_sec"]["mean"] for k in open_k]
    pico_rt = [data["treatments"][k]["r_tool_ops_sec"]["mean"] for k in pico_k]

    x = np.arange(len(conds))
    w = 0.35
    b1 = ax.bar(x - w / 2, pico_rt, w, label="PicoClaw R_tool (ops/s)", color=COLOR_PICO, edgecolor="#0F172A")
    b2 = ax.bar(x + w / 2, open_rt, w, label="OpenClaw R_tool (ops/s)", color=COLOR_OPEN, edgecolor="#0F172A")
    ax.set_ylabel("Tool Dispatch Throughput R_tool (ops/sec)")
    ax.set_title("(a) Tool-Calling Serialization & Dispatch Throughput")
    ax.set_xticks(x)
    ax.set_xticklabels(conds)
    ax.set_ylim(0, max(pico_rt) * 1.25)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend()

    for bar in b1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 15, f"{h:.0f}", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#0F766E")
    for bar in b2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 15, f"{h:.0f}", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#BE123C")

    # Subplot B: System Testing Discovery - Default CLI Prompt Token Overhead vs Context Limit
    ax2 = axes[1]
    configs = [
        "Equalized W1\nBenchmark",
        "PicoClaw Default\n(15 Tools)",
        "OpenClaw Default\n(54 Tools + Soul)"
    ]
    prompt_tokens = [128, 4657, 16369]
    colors = [COLOR_NEURAL, COLOR_PICO, COLOR_OPEN]
    bars = ax2.bar(configs, prompt_tokens, width=0.5, color=colors, edgecolor="#0F172A")
    ax2.axhline(4096, color="#DC2626", linestyle="--", linewidth=1.8, label="Work Plan Context Limit (4,096 tok)")
    ax2.set_ylabel("Initial Turn Prompt Tokens Sent to LLM")
    ax2.set_title("(b) System Testing Finding: Default Prompt Token Bloat")
    ax2.set_ylim(0, 19500)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)
    ax2.legend(loc="upper left")

    for bar in bars:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h + 350, f"{h:,} tok", ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig5_exp4_tools_and_bloat.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    return out


def plot_pmc_hardware_counters(data):
    fig, axes = plt.subplots(1, 3, figsize=(10.6, 3.8))
    pmc = data["hyperfine_pmc_30runs"]
    ru = data["rusage_v4_telemetry"]

    # Panel A: Instructions Retired (Millions)
    ax = axes[0]
    cats = ["Agent Init\n(hyperfine n=30)", "W2 Orchestrator\n(RUSAGE_INFO_V4)"]
    p_inst = [pmc["picoclaw_instructions"]["mean"] / 1e6, ru["picoclaw_orch_w2"]["instructions"] / 1e6]
    o_inst = [pmc["openclaw_instructions"]["mean"] / 1e6, ru["openclaw_orch_w2"]["instructions"] / 1e6]
    x = np.arange(len(cats))
    w = 0.35
    ax.bar(x - w / 2, p_inst, w, label="PicoClaw (Go)", color=COLOR_PICO, edgecolor="#0F172A")
    ax.bar(x + w / 2, o_inst, w, label="OpenClaw (Node.js)", color=COLOR_OPEN, edgecolor="#0F172A")
    ax.set_yscale("log")
    ax.set_ylabel("Instructions Retired (Millions, log)")
    ax.set_title("(a) Apple M4 PMC: Instructions")
    ax.set_xticks(x)
    ax.set_xticklabels(cats)
    ax.grid(axis="y", linestyle="--", alpha=0.5, which="both")
    ax.legend(loc="upper right", fontsize=8)

    # Panel B: CPU Cycles (Millions)
    ax2 = axes[1]
    p_cyc = [pmc["picoclaw_cycles"]["mean"] / 1e6, ru["picoclaw_orch_w2"]["cycles"] / 1e6]
    o_cyc = [pmc["openclaw_cycles"]["mean"] / 1e6, ru["openclaw_orch_w2"]["cycles"] / 1e6]
    ax2.bar(x - w / 2, p_cyc, w, label="PicoClaw (Go)", color=COLOR_PICO, edgecolor="#0F172A")
    ax2.bar(x + w / 2, o_cyc, w, label="OpenClaw (Node.js)", color=COLOR_OPEN, edgecolor="#0F172A")
    ax2.set_yscale("log")
    ax2.set_ylabel("CPU Cycles (Millions, log)")
    ax2.set_title("(b) Apple M4 PMC: CPU Cycles")
    ax2.set_xticks(x)
    ax2.set_xticklabels(cats)
    ax2.grid(axis="y", linestyle="--", alpha=0.5, which="both")

    # Panel C: Physical Memory Footprint vs Resident Set Size (MB)
    ax3 = axes[2]
    m_cats = ["Kernel RSS\n(hyperfine)", "Phys Footprint\n(RUSAGE_INFO_V4)"]
    p_mem = [pmc["picoclaw_rss_mb"]["mean"], ru["picoclaw_cli"]["peak_phys_mb"]]
    o_mem = [pmc["openclaw_rss_mb"]["mean"], ru["openclaw_cli"]["peak_phys_mb"]]
    x3 = np.arange(len(m_cats))
    b5 = ax3.bar(x3 - w / 2, p_mem, w, label="PicoClaw (Go)", color=COLOR_PICO, edgecolor="#0F172A")
    b6 = ax3.bar(x3 + w / 2, o_mem, w, label="OpenClaw (Node.js)", color=COLOR_OPEN, edgecolor="#0F172A")
    ax3.set_ylabel("Memory Footprint (MB)")
    ax3.set_title("(c) Kernel RSS vs Phys Footprint")
    ax3.set_xticks(x3)
    ax3.set_xticklabels(m_cats)
    ax3.set_ylim(0, 200)
    ax3.grid(axis="y", linestyle="--", alpha=0.5)

    for bar in b5:
        h = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width() / 2, h + 3, f"{h:.1f}", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#0F766E")
    for bar in b6:
        h = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width() / 2, h + 3, f"{h:.1f}", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#BE123C")

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig6_pmc_hardware_counters.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    return out


def main():
    res_path = os.path.join(DATA_DIR, "results_all.json")
    if not os.path.exists(res_path):
        res_path = os.path.join(BENCH_DIR, "results_all.json")
    with open(res_path, "r") as f:
        data = json.load(f)
    f1 = draw_architecture_diagram()
    f2 = plot_exp1_startup_memory(data)
    f3 = plot_exp2_latency_overhead(data)
    f4 = plot_exp3_energy_edp(data)
    f5 = plot_exp4_tools_and_prompt_bloat(data)
    f6 = plot_pmc_hardware_counters(data)
    print("Generated figures:")
    for p in [f1, f2, f3, f4, f5, f6]:
        print(" ", p)


if __name__ == "__main__":
    main()
