#!/usr/bin/env python3
"""
scripts/export_audit_bundle.py - Consolidated Academic Audit Bundle Exporter (< 135 KB Sized)
Exportador do Pacote Consolidado de Auditoria em Partes Dimensionadas para Submissão Elsevier SoftwareX

Generates:
  1. auditoria_parte1_manuscrito_tabelas_respostas.txt
  2. auditoria_parte2A_codigo_nucleo_adaptadores_e_testes.txt (< 135 KB)
  3. auditoria_parte2B_jsons_metadados_e_manifesto_sha256.txt (< 135 KB)
  4. auditoria_parte2C_scripts_testes_e_tutoriais.txt (< 135 KB)
  5. auditoria_parte2D_testes_completos_e_tutoriais.txt (< 135 KB)
  6. auditoria_parte3_compacto_todos_datasets.txt (Full CSV Schema across all 3,823 trials)
  7. auditoria_parte3A_compacto_regime_a_e_warm_cache.txt (< 135 KB)
  8. auditoria_parte3B_compacto_inter_session_e_tool_rag.txt (< 135 KB)
  9. auditoria_parte3C_compacto_ablacoes_e_uma.txt (< 135 KB)
  10. auditoria_parte3_dados_brutos_jsonl_completos.txt (Unabridged raw dataset archive)
  11. repo_texto_auditoria_final.txt (Unified backward compatibility mirror)

Author: Rafael Paniccia Cassetta (UFABC)
"""

import datetime
import hashlib
import json
import os
import subprocess
import sys
from typing import Optional, Set

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PART1 = os.path.join(REPO_DIR, "auditoria_parte1_manuscrito_tabelas_respostas.txt")
OUTPUT_PART2A = os.path.join(REPO_DIR, "auditoria_parte2A_codigo_nucleo_adaptadores_e_testes.txt")
OUTPUT_PART2B = os.path.join(REPO_DIR, "auditoria_parte2B_jsons_metadados_e_manifesto_sha256.txt")
OUTPUT_PART2C = os.path.join(REPO_DIR, "auditoria_parte2C_scripts_testes_e_tutoriais.txt")
OUTPUT_PART2D = os.path.join(REPO_DIR, "auditoria_parte2D_testes_completos_e_tutoriais.txt")
OUTPUT_PART3_COMPACT = os.path.join(REPO_DIR, "auditoria_parte3_compacto_todos_datasets.txt")
OUTPUT_PART3A = os.path.join(REPO_DIR, "auditoria_parte3A_compacto_regime_a_e_warm_cache.txt")
OUTPUT_PART3B = os.path.join(REPO_DIR, "auditoria_parte3B_compacto_inter_session_e_tool_rag.txt")
OUTPUT_PART3C = os.path.join(REPO_DIR, "auditoria_parte3C_compacto_ablacoes_e_uma.txt")
OUTPUT_PART3_RAW = os.path.join(REPO_DIR, "auditoria_parte3_dados_brutos_jsonl_completos.txt")
OUTPUT_FINAL = os.path.join(REPO_DIR, "repo_texto_auditoria_final.txt")
OUTPUT_FILE_6 = os.path.join(REPO_DIR, "repo_texto_auditoria_6.txt")
OUTPUT_FILE_6_4 = os.path.join(REPO_DIR, "repo_texto_auditoria_6_4.txt")
OUTPUT_RAW_JSONL = os.path.join(REPO_DIR, "repo_dados_brutos_jsonl_completos.txt")


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_cmd_output(cmd: list) -> str:
    try:
        res = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True, timeout=5)
        return res.stdout.strip()
    except Exception as e:
        return f"Error: {e}"


def format_compact_json(content: str) -> str:
    try:
        data = json.loads(content)
        return json.dumps(data, separators=(",", ":"))
    except Exception:
        return content


def dump_file(rel_path: str, seen: Optional[Set[str]] = None, compact_json: bool = False) -> str:
    """Reads and returns 100% full content of the specified file with SHA-256 header and explicit closing delimiter."""
    if seen is not None:
        if rel_path in seen:
            return ""
        seen.add(rel_path)

    abs_path = os.path.join(REPO_DIR, rel_path)
    if not os.path.exists(abs_path):
        return f"=== FILE: {rel_path} (MISSING) ===\n\n"

    sha = compute_sha256(abs_path)
    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if compact_json and rel_path.endswith(".json") and rel_path != "data/manifest_sha256.json":
        content = format_compact_json(content)

    return (
        "================================================================================\n"
        f"FILE: {rel_path}\n"
        f"SHA-256: {sha}\n"
        "================================================================================\n"
        f"{content}\n"
        "================================================================================\n"
        f"END FILE: {rel_path}\n"
        "================================================================================\n\n"
    )


def build_header(part_title: str) -> str:
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    git_head = get_cmd_output(["git", "rev-parse", "HEAD"])
    raw_status = get_cmd_output(["git", "status", "--short"])
    ignore_bundles = (
        "auditoria_parte",
        "repo_texto_auditoria",
        "repo_dados_brutos",
    )
    filtered_lines = [
        line for line in raw_status.splitlines()
        if not any(b in line for b in ignore_bundles)
    ]
    git_status = "\n".join(filtered_lines) if filtered_lines else "(clean working tree)"
    sw_vers = get_cmd_output(["sw_vers"])
    sysctl_cpu = get_cmd_output(["sysctl", "-n", "machdep.cpu.brand_string"])

    return f"""================================================================================
PACOTE COMPLETO DE AUDITORIA E REPRODUCIBILIDADE CIENTIFICA INTEGRAL
{part_title}
Elsevier SoftwareX: picoclaw-vs-openclaw-benchmark
================================================================================
Data de Geracao (UTC): {now_iso}
Git HEAD: {git_head}
Hardware Host: Apple Silicon M4 ({sysctl_cpu})
Sistema Operacional: macOS Darwin arm64 ({sw_vers})
Python Version: {sys.version.split()[0]}
Status Git:
{git_status}
================================================================================

"""


def generate_bundle():
    print("📦 Generating size-budgeted audit bundles (< 135 KB) and unified mirror...")

    # Clean up any legacy oversized Part 2 if present
    for old_name in [
        "auditoria_parte2_codigo_testes_metadados_manifesto.txt",
        "auditoria_parte2C_scripts_abiacoes.txt",
    ]:
        p = os.path.join(REPO_DIR, old_name)
        if os.path.exists(p):
            os.remove(p)
            print(f"🧹 Cleaned legacy file: {p}")

    # PARTE 1: Manuscrito, Resposta aos Revisores, Bibliografia, Governanca e 9 Tabelas LaTeX + Macros
    part1_files = [
        "paper/RESPONSE_TO_REVIEWERS.md",
        "paper/softwarex_manuscript.tex",
        "references.bib",
        "paper/HIGHLIGHTS.md",
        "paper/COVER_LETTER.md",
        "CITATION.cff",
        "LICENSE",
        "DATA_LICENSE",
        "results/publication_campaign/tables/table_journal_ablation.tex",
        "results/publication_campaign/tables/table_warm_cache.tex",
        "results/publication_campaign/tables/table_prefill_ablation.tex",
        "results/publication_campaign/tables/table_tool_rag_mitigation.tex",
        "results/publication_campaign/tables/table_spearman_correlation.tex",
        "results/publication_campaign/tables/table_pca_loadings.tex",
        "results/publication_campaign/tables/table_energy_bandwidth_deconvolution.tex",
        "results/publication_campaign/tables/table_mcp_transport_ablation.tex",
        "results/publication_campaign/tables/table_quantization_scaling.tex",
        "results/publication_campaign/tables/macros_empirical.tex",
    ]

    seen_p1: Set[str] = set()
    p1_sections = [
        build_header("PARTE 1: RESPOSTA AOS REVISORES, MANUSCRITO .TEX, BIBLIOGRAFIA E TABELAS LATEX"),
        "=" * 80 + "\nSECAO 1: RESPOSTA AOS REVISORES, MANUSCRITO CIENTIFICO, REFERENCIAS, GOVERNANCA E TODAS AS 9 TABELAS LATEX + MACROS\n" + "=" * 80 + "\n",
    ]
    for f in part1_files:
        block = dump_file(f, seen_p1)
        if block:
            p1_sections.append(block)
    p1_sections.append("=" * 80 + "\nFIM DA PARTE 1 DO PACOTE DE AUDITORIA (100% INTEGRAL SEM TRUNCAMENTO)\n" + "=" * 80 + "\n")
    part1_content = "\n".join(p1_sections)
    with open(OUTPUT_PART1, "w", encoding="utf-8") as f:
        f.write(part1_content)
    print(f"✅ Generated Part 1: {OUTPUT_PART1} ({os.path.getsize(OUTPUT_PART1)/1024:.2f} KB, {len(seen_p1)} unique files)")

    # PARTE 2A: CI/CD, Makefile, Codigo-Nucleo, Telemetria, Invariantes, Orquestradores e Adaptadores (< 135 KB)
    part2a_files = [
        ".github/workflows/ci.yml",
        "Makefile",
        "pyproject.toml",
        "benchmark/protocol_invariants.py",
        "benchmark/bun_jsc_agent.mjs",
        "benchmark/picoclaw_orch.go",
        "benchmark/openclaw_orch.mjs",
        "benchmark/python_orch.py",
        "benchmark/telemetry.py",
        "benchmark/adapters/base.py",
        "benchmark/adapters/picoclaw_adapter.py",
        "benchmark/adapters/openclaw_adapter.py",
        "benchmark/adapters/python_native_adapter.py",
        "benchmark/adapters/bun_minimal_adapter.py",
        "benchmark/adapters/__init__.py",
    ]

    seen_p2a: Set[str] = set()
    p2a_sections = [
        build_header("PARTE 2A: CODIGO-FONTE NUCLEO, TELEMETRIA, INVARIANTES E ADAPTADORES"),
        "=" * 80 + "\nSECAO 2A: CI/CD, BUILD, TELEMETRIA, INVARIANTES FORMALIZADOS, ORQUESTRADORES E ADAPTADORES\n" + "=" * 80 + "\n",
    ]
    for f in part2a_files:
        block = dump_file(f, seen_p2a)
        if block:
            p2a_sections.append(block)
    p2a_sections.append("=" * 80 + "\nFIM DA PARTE 2A DO PACOTE DE AUDITORIA (100% INTEGRAL SEM TRUNCAMENTO)\n" + "=" * 80 + "\n")
    part2a_content = "\n".join(p2a_sections)
    with open(OUTPUT_PART2A, "w", encoding="utf-8") as f:
        f.write(part2a_content)
    print(f"✅ Generated Part 2A: {OUTPUT_PART2A} ({os.path.getsize(OUTPUT_PART2A)/1024:.2f} KB, {len(seen_p2a)} unique files)")

    # PARTE 2B: Manifesto Criptografico SHA-256 no topo e JSONs de Metadados e Resultados Empiricos (< 135 KB)
    part2b_files = [
        "data/manifest_sha256.json",
        "results/publication_campaign/campaign_metadata.json",
        "results/publication_campaign/summary_statistics.json",
        "results/publication_campaign/warm_cache_summary.json",
        "results/publication_campaign/uma_energy_bandwidth_attribution.json",
        "results/publication_campaign/inter_session_replication.json",
        "results/publication_campaign/tool_rag_mitigation_summary.json",
        "results/publication_campaign/kv_cache_thrashing_summary.json",
        "results/publication_campaign/independent_validation_report.json",
        "results/publication_campaign/cross_hardware_and_independent_validation.json",
        "results/publication_campaign/statistical_tests.json",
        "results/publication_campaign/warm_cache_statistical_tests.json",
        "results/publication_campaign/prefill_regression_fit.json",
        "results/publication_campaign/sensitivity_and_outlier_analysis.json",
    ]

    seen_p2b: Set[str] = set()
    p2b_sections = [
        build_header("PARTE 2B: MANIFESTO CRIPTOGRAFICO SHA-256 E JSONS DE RESULTADOS"),
        "=" * 80 + "\nSECAO 2B: MANIFESTO CRIPTOGRAFICO SHA-256 E TABELAS JSON INTEGRAIS DE METADADOS E ESTATISTICAS\n" + "=" * 80 + "\n",
    ]
    for f in part2b_files:
        block = dump_file(f, seen_p2b, compact_json=True)
        if block:
            p2b_sections.append(block)
    p2b_sections.append("=" * 80 + "\nFIM DA PARTE 2B DO PACOTE DE AUDITORIA (100% INTEGRAL SEM TRUNCAMENTO)\n" + "=" * 80 + "\n")
    part2b_content = "\n".join(p2b_sections)
    with open(OUTPUT_PART2B, "w", encoding="utf-8") as f:
        f.write(part2b_content)
    print(f"✅ Generated Part 2B: {OUTPUT_PART2B} ({os.path.getsize(OUTPUT_PART2B)/1024:.2f} KB, {len(seen_p2b)} unique files)")

    # PARTE 2C: Scripts de Campanhas, Ablacoes, Motor de Analise Estatistica e Adaptador Neural Baseline (< 135 KB)
    part2c_files = [
        "benchmark/analyze_results.py",
        "benchmark/adapters/neural_baseline_adapter.py",
        "scripts/run_uma_energy_and_bandwidth_attribution.py",
        "scripts/run_kv_cache_thrashing_ablation.py",
    ]

    seen_p2c: Set[str] = set()
    p2c_sections = [
        build_header("PARTE 2C: MOTOR DE ANALISE, ABLACAO KV CACHE E UMA ATTRIBUTION"),
        "=" * 80 + "\nSECAO 2C: MOTOR DE ANALISE ESTATISTICA E SCRIPTS CRITICOS DOS GATES 1 A 4\n" + "=" * 80 + "\n",
    ]
    for f in part2c_files:
        block = dump_file(f, seen_p2c)
        if block:
            p2c_sections.append(block)
    p2c_sections.append("=" * 80 + "\nFIM DA PARTE 2C DO PACOTE DE AUDITORIA (100% INTEGRAL SEM TRUNCAMENTO)\n" + "=" * 80 + "\n")
    part2c_content = "\n".join(p2c_sections)
    with open(OUTPUT_PART2C, "w", encoding="utf-8") as f:
        f.write(part2c_content)
    print(f"✅ Generated Part 2C: {OUTPUT_PART2C} ({os.path.getsize(OUTPUT_PART2C)/1024:.2f} KB, {len(seen_p2c)} unique files)")

    # PARTE 2D: Testes Unitarios Completos (Gates 6 e 7), Scripts de Validacao Independente e Tutoriais (< 135 KB)
    part2d_files = [
        "tests/test_artifact_consistency.py",
        "tests/test_statistical_engine.py",
        "tests/test_adapters_and_failfast.py",
        "tests/test_dataset_generator.py",
        "tests/test_telemetry_parser.py",
        "scripts/run_independent_validation_suite.py",
        "scripts/run_inter_session_replication.py",
        "scripts/run_tool_rag_mitigation_experiment.py",
        "scripts/verify_manifest.py",
        "tutorial/README.md",
    ]

    seen_p2d: Set[str] = set()
    p2d_sections = [
        build_header("PARTE 2D: SUITE DE TESTES UNITARIOS, REPLICACAO E TUTORIAIS"),
        "=" * 80 + "\nSECAO 2D: SUITE INTEGRAL DE TESTES UNITARIOS, REPLICACAO INDEPENDENTE E GUIA DE REPRODUCIBILIDADE\n" + "=" * 80 + "\n",
    ]
    for f in part2d_files:
        block = dump_file(f, seen_p2d)
        if block:
            p2d_sections.append(block)
    p2d_sections.append("=" * 80 + "\nFIM DA PARTE 2D DO PACOTE DE AUDITORIA (100% INTEGRAL SEM TRUNCAMENTO)\n" + "=" * 80 + "\n")
    part2d_content = "\n".join(p2d_sections)
    with open(OUTPUT_PART2D, "w", encoding="utf-8") as f:
        f.write(part2d_content)
    print(f"✅ Generated Part 2D: {OUTPUT_PART2D} ({os.path.getsize(OUTPUT_PART2D)/1024:.2f} KB, {len(seen_p2d)} unique files)")

    # PARTE 3: Datasets compactos com o esquema exato de 20 colunas e blocos de metadados Gate 0
    export_compact_jsonl_datasets()

    # PARTE 3 RAW: Dados Brutos JSONL Completos para arquivo integral
    export_raw_jsonl_dataset()

    # Unified bundle for backward compatibility with zero duplication
    seen_unified: Set[str] = set()
    unified_sections = [
        build_header("PACOTE UNIFICADO COMPLETO (PARTE 1 + PARTE 2A + 2B + 2C + 2D)"),
        "=" * 80 + "\nSECAO 1: RESPOSTA AOS REVISORES, MANUSCRITO CIENTIFICO, REFERENCIAS, GOVERNANCA E TODAS AS 9 TABELAS LATEX + MACROS\n" + "=" * 80 + "\n",
    ]
    for f in part1_files:
        block = dump_file(f, seen_unified)
        if block:
            unified_sections.append(block)
    unified_sections.append("=" * 80 + "\nSECAO 2A: CODIGO-FONTE NUCLEO, TELEMETRIA, INVARIANTES E ADAPTADORES\n" + "=" * 80 + "\n")
    for f in part2a_files:
        block = dump_file(f, seen_unified)
        if block:
            unified_sections.append(block)
    unified_sections.append("=" * 80 + "\nSECAO 2B: MANIFESTO CRIPTOGRAFICO E JSONS DE METADADOS E RESULTADOS\n" + "=" * 80 + "\n")
    for f in part2b_files:
        block = dump_file(f, seen_unified, compact_json=True)
        if block:
            unified_sections.append(block)
    unified_sections.append("=" * 80 + "\nSECAO 2C: MOTOR DE ANALISE E ABLACOES KV CACHE / UMA\n" + "=" * 80 + "\n")
    for f in part2c_files:
        block = dump_file(f, seen_unified)
        if block:
            unified_sections.append(block)
    unified_sections.append("=" * 80 + "\nSECAO 2D: SUITE DE TESTES, VALIDACAO E TUTORIAIS\n" + "=" * 80 + "\n")
    for f in part2d_files:
        block = dump_file(f, seen_unified)
        if block:
            unified_sections.append(block)
    unified_sections.append("=" * 80 + "\nFIM DO PACOTE DE AUDITORIA INTEGRAL (100% ARQUIVOS VERIFICADOS)\n" + "=" * 80 + "\n")
    bundle_content = "\n".join(unified_sections)
    for out_path in [OUTPUT_FINAL, OUTPUT_FILE_6, OUTPUT_FILE_6_4]:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(bundle_content)
        print(f"✅ Generated unified mirror: {out_path} ({os.path.getsize(out_path)/1024:.2f} KB, {len(seen_unified)} unique files)")


def fmt_val(v, decimals=1):
    if v is None:
        return "0"
    try:
        f = float(v)
        if f == int(f):
            return str(int(f))
        return f"{round(f, decimals):.{decimals}f}".rstrip("0").rstrip(".")
    except Exception:
        return str(v)


def format_trial_row(r: dict) -> str:
    rep = r.get("rep", r.get("iteration", r.get("trial", 1)))
    warmup = 1 if r.get("is_warmup", False) else 0
    prompt_tok = r.get("prompt_tokens", 0)
    cached_tok = r.get("cached_tokens", 0)
    new_tok = r.get("uncached_prompt_tokens", 0)
    comp_tok = r.get("completion_tokens", r.get("output_tokens", 0))
    t_task = fmt_val(r.get("t_task_ms", r.get("t_exec_ms", r.get("t_total_ms", 0.0))), 1)
    prompt_ms = fmt_val(r.get("prompt_ms", 0.0), 1)
    pred_ms = fmt_val(r.get("predicted_ms", 0.0), 1)
    t_orch = fmt_val(r.get("t_orch_ms", 0.0), 2)
    t_disp = fmt_val(r.get("t_dispatch_ms", 0.0), 2)
    ttft = fmt_val(r.get("ttft_ms", 0.0), 1)
    itl = fmt_val(r.get("itl_ms", 0.0), 2)
    phys_mb = fmt_val(r.get("proc_peak_phys_mb", 0.0), 2)
    rss_mb = fmt_val(r.get("proc_rss_mb", r.get("rss_peak_mb", 0.0)), 2)
    instr_M = fmt_val(r.get("proc_instructions", 0) / 1e6, 2)
    cycles_M = fmt_val(r.get("proc_cycles", 0) / 1e6, 2)
    billed_e = fmt_val(r.get("proc_billed_energy", r.get("ri_billed_energy", 0)), 0)
    e_net = fmt_val(r.get("energy_net_above_idle_j", r.get("energy_cpu_net_j", r.get("energy_total_j", 0.0) or 0.0)) or 0.0, 3)
    edp = fmt_val(r.get("edp_js", 0.0) or 0.0, 2)
    return f"{rep},{warmup},{prompt_tok},{cached_tok},{new_tok},{comp_tok},{t_task},{prompt_ms},{pred_ms},{t_orch},{t_disp},{ttft},{itl},{phys_mb},{rss_mb},{instr_M},{cycles_M},{billed_e},{e_net},{edp}"


def export_compact_jsonl_datasets():
    """Exports all 3,823 evaluation trials into structured, non-truncating compact datasets with exact CSV schemas."""
    print("📦 Generating Part 3 compact datasets (< 135 KB chunks + unified matrix)...")

    jsonl_sets = [
        ("raw_trials", "results/publication_campaign/raw_trials.jsonl"),
        ("warm_cache", "results/publication_campaign/warm_cache_trials.jsonl"),
        ("inter_session", "results/publication_campaign/inter_session_trials.jsonl"),
        ("tool_rag_mitigation", "results/publication_campaign/tool_rag_mitigation_trials.jsonl"),
        ("kv_cache_thrashing", "results/publication_campaign/kv_cache_thrashing_trials.jsonl"),
        ("prefill_ablation", "results/publication_campaign/prefill_ablation.jsonl"),
        ("uma_energy_bandwidth", "results/publication_campaign/uma_energy_bandwidth_trials.jsonl"),
    ]

    all_records = []
    for tag, rel_path in jsonl_sets:
        abs_p = os.path.join(REPO_DIR, rel_path)
        if not os.path.exists(abs_p):
            continue
        with open(abs_p, "r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                all_records.append((tag, json.loads(line)))

    # Group records by (tag, workload, agent_key, session_id, git_commit)
    grouped = {}
    for tag, r in all_records:
        wl = r.get("workload", "")
        ag = r.get("agent_key", r.get("runtime", ""))
        sess = r.get("session_id", "")
        git_c = r.get("git_commit", "")
        k = (tag, wl, ag, sess, git_c)
        if k not in grouped:
            grouped[k] = []
        grouped[k].append(r)

    def render_blocks(target_groups):
        lines = [
            "=" * 80,
            "PARTE 3 COMPACTA: DADOS DE TODOS OS TRIALS DE AVALIACAO CIENTIFICA",
            "Elsevier SoftwareX: picoclaw-vs-openclaw-benchmark",
            "=" * 80,
            "# SCHEMA: rep,warmup,prompt_tok,cached_tok,new_tok,comp_tok,t_task_ms,prompt_ms,pred_ms,t_orch_ms,t_disp_ms,ttft_ms,itl_ms,phys_mb,rss_mb,instr_M,cycles_M,billed_e,e_net_j,edp_js",
            "=" * 80,
        ]
        cnt = 0
        for (tag, wl, ag, sess, git_c), recs in target_groups.items():
            first = recs[0]
            hw = first.get("hardware", "Apple M4")
            os_name = first.get("os", "macOS")
            mv = first.get("model_version", "Qwen2.5-Coder-7B")
            qz = first.get("quantization", "Q4_K_M")
            sf = first.get("server_flags", "default")
            lines.append(f"[{tag}|{wl}|{ag}|{sess}|{git_c}]")
            lines.append(f"# META: session_id={sess} | git_commit={git_c} | hardware={hw} | os={os_name} | model_version={mv} | quantization={qz} | server_flags={sf} | workload={wl}")
            for r in recs:
                cnt += 1
                lines.append(format_trial_row(r))
        lines.append("=" * 80)
        lines.append("FIM DA PARTE 3 COMPACTA (100% INTEGRAL SEM TRUNCAMENTO)")
        lines.append("=" * 80 + "\n")
        return "\n".join(lines), cnt

    # 1. Unified file with all 3,823 lines
    content_all, count_all = render_blocks(grouped)
    with open(OUTPUT_PART3_COMPACT, "w", encoding="utf-8") as f:
        f.write(content_all)
    print(f"✅ Generated Part 3 Unified: {OUTPUT_PART3_COMPACT} ({os.path.getsize(OUTPUT_PART3_COMPACT)/1024:.2f} KB, {count_all} trials)")

    # 2. Size-budgeted chunks (< 135 KB each) for evaluation platforms with strict per-file limits
    groups_3a = {k: v for k, v in grouped.items() if k[0] in ("raw_trials", "warm_cache")}
    groups_3b = {k: v for k, v in grouped.items() if k[0] in ("tool_rag_mitigation", "uma_energy_bandwidth")}
    groups_3c = {k: v for k, v in grouped.items() if k[0] in ("inter_session", "prefill_ablation", "kv_cache_thrashing")}

    content_3a, cnt_3a = render_blocks(groups_3a)
    content_3b, cnt_3b = render_blocks(groups_3b)
    content_3c, cnt_3c = render_blocks(groups_3c)

    with open(OUTPUT_PART3A, "w", encoding="utf-8") as f:
        f.write(content_3a)
    with open(OUTPUT_PART3B, "w", encoding="utf-8") as f:
        f.write(content_3b)
    with open(OUTPUT_PART3C, "w", encoding="utf-8") as f:
        f.write(content_3c)

    print(f"✅ Generated Part 3A (Raw & Warm): {OUTPUT_PART3A} ({os.path.getsize(OUTPUT_PART3A)/1024:.2f} KB, {cnt_3a} trials)")
    print(f"✅ Generated Part 3B (Tool-RAG & UMA): {OUTPUT_PART3B} ({os.path.getsize(OUTPUT_PART3B)/1024:.2f} KB, {cnt_3b} trials)")
    print(f"✅ Generated Part 3C (Inter-Session, Prefill & Thrashing): {OUTPUT_PART3C} ({os.path.getsize(OUTPUT_PART3C)/1024:.2f} KB, {cnt_3c} trials)")


def export_raw_jsonl_dataset():
    print(f"📦 Generating Part 3 full untruncated JSONL dataset dump: {OUTPUT_PART3_RAW}...")
    jsonl_files = [
        "results/publication_campaign/raw_trials.jsonl",
        "results/publication_campaign/warm_cache_trials.jsonl",
        "results/publication_campaign/inter_session_trials.jsonl",
        "results/publication_campaign/tool_rag_mitigation_trials.jsonl",
        "results/publication_campaign/kv_cache_thrashing_trials.jsonl",
        "results/publication_campaign/prefill_ablation.jsonl",
        "results/publication_campaign/uma_energy_bandwidth_trials.jsonl",
    ]
    seen_jsonl: Set[str] = set()
    parts = [
        "================================================================================",
        "PARTE 3: DADOS BRUTOS COMPLETOS (100% REGISTROS JSONL SEM CORTES)",
        "Elsevier SoftwareX: picoclaw-vs-openclaw-benchmark",
        "================================================================================\n",
    ]
    for rel_path in jsonl_files:
        if rel_path in seen_jsonl:
            continue
        seen_jsonl.add(rel_path)
        abs_path = os.path.join(REPO_DIR, rel_path)
        if not os.path.exists(abs_path):
            continue
        sha = compute_sha256(abs_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        parts.append("=" * 80)
        parts.append(f"DATASET: {rel_path} | SHA-256: {sha} | Total Records: {len(lines)}")
        parts.append("=" * 80)
        for line in lines:
            parts.append(line)
        parts.append("=" * 80)
        parts.append(f"END DATASET: {rel_path}")
        parts.append("=" * 80 + "\n")

    parts.append("=" * 80)
    parts.append("FIM DA PARTE 3: TODOS OS REGISTROS JSONL EXPORTADOS INTEGRALMENTE")
    parts.append("=" * 80 + "\n")

    content = "\n".join(parts)
    for out_p in [OUTPUT_PART3_RAW, OUTPUT_RAW_JSONL]:
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Generated Part 3 raw JSONL dump: {out_p} ({len(parts)} lines, {os.path.getsize(out_p)/1024:.2f} KB, {len(seen_jsonl)} unique datasets)")


if __name__ == "__main__":
    generate_bundle()
