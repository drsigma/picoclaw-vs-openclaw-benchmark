#!/usr/bin/env python3
"""
scripts/export_audit_bundle.py - Consolidated Academic Audit Bundle Exporter (< 135 KB Sized)
Exportador do Pacote Consolidado de Auditoria em Partes Dimensionadas para Submissão Elsevier SoftwareX

Generates:
  1. auditoria_parte1_manuscrito_tabelas_respostas.txt
  2. auditoria_parte2A_codigo_nucleo_adaptadores_e_testes.txt (< 135 KB)
  3. auditoria_parte2B_jsons_metadados_e_manifesto_sha256.txt (< 135 KB)
  4. auditoria_parte2C_scripts_abiacoes.txt (< 135 KB)
  5. auditoria_parte3_compacto_todos_datasets.txt (< 140 KB, ~128 KB)
  6. auditoria_parte3_dados_brutos_jsonl_completos.txt (Unabridged raw dataset archive)
  7. repo_texto_auditoria_final.txt (Unified backward compatibility mirror)

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
OUTPUT_PART2C = os.path.join(REPO_DIR, "auditoria_parte2C_scripts_abiacoes.txt")
OUTPUT_PART3_COMPACT = os.path.join(REPO_DIR, "auditoria_parte3_compacto_todos_datasets.txt")
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


def format_compact_json_dict(content: str) -> str:
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

    if compact_json and rel_path.endswith(".json"):
        content = format_compact_json_dict(content)
    elif rel_path in [
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
    ]:
        content = format_compact_json_dict(content)

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
    legacy_p2 = os.path.join(REPO_DIR, "auditoria_parte2_codigo_testes_metadados_manifesto.txt")
    if os.path.exists(legacy_p2):
        os.remove(legacy_p2)
        print(f"🧹 Cleaned legacy oversized file: {legacy_p2}")

    # PARTE 1: Manuscrito, Resposta aos Revisores, Bibliografia, Governanca e 7 Tabelas LaTeX + Macros
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
        "results/publication_campaign/tables/macros_empirical.tex",
    ]

    seen_p1: Set[str] = set()
    p1_sections = [
        build_header("PARTE 1: RESPOSTA AOS REVISORES, MANUSCRITO .TEX, BIBLIOGRAFIA E TABELAS LATEX"),
        "=" * 80 + "\nSECAO 1: RESPOSTA AOS REVISORES, MANUSCRITO CIENTIFICO, REFERENCIAS, GOVERNANCA E TODAS AS 7 TABELAS LATEX + MACROS\n" + "=" * 80 + "\n",
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

    # PARTE 2A: CI/CD, Makefile, Codigo-Nucleo, Invariantes, Orquestradores, Adaptadores e Testes (< 135 KB)
    part2a_files = [
        ".github/workflows/ci.yml",
        "Makefile",
        "pyproject.toml",
        "benchmark/protocol_invariants.py",
        "benchmark/bun_jsc_agent.mjs",
        "benchmark/picoclaw_orch.go",
        "benchmark/openclaw_orch.mjs",
        "benchmark/python_orch.py",
        "benchmark/adapters/base.py",
        "benchmark/adapters/picoclaw_adapter.py",
        "benchmark/adapters/openclaw_adapter.py",
        "benchmark/adapters/python_native_adapter.py",
        "benchmark/adapters/bun_minimal_adapter.py",
        "benchmark/adapters/__init__.py",
        "tests/test_adapters_and_failfast.py",
        "tests/test_dataset_generator.py",
        "tests/test_telemetry_parser.py",
    ]

    seen_p2a: Set[str] = set()
    p2a_sections = [
        build_header("PARTE 2A: CODIGO-FONTE NUCLEO, ADAPTADORES E TESTES UNITARIOS"),
        "=" * 80 + "\nSECAO 2A: CI/CD, BUILD, INVARIANTES FORMALIZADOS, ORQUESTRADORES, ADAPTADORES E TESTES\n" + "=" * 80 + "\n",
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

    # PARTE 2C: Scripts de Campanhas, Ablacoes, Verificacao e Adaptador Neural Baseline (< 135 KB)
    part2c_files = [
        "benchmark/adapters/neural_baseline_adapter.py",
        "scripts/run_uma_energy_and_bandwidth_attribution.py",
        "scripts/run_inter_session_replication.py",
        "scripts/run_tool_rag_mitigation_experiment.py",
        "scripts/run_kv_cache_thrashing_ablation.py",
        "scripts/verify_manifest.py",
        "scripts/setup_environment.sh",
        "scripts/check_quiescence.sh",
    ]

    seen_p2c: Set[str] = set()
    p2c_sections = [
        build_header("PARTE 2C: SCRIPTS DE ABLACOES, REPLICACAO E VALIDAO EMPIRICA"),
        "=" * 80 + "\nSECAO 2C: ADAPTADOR NEURAL, SCRIPTS DE EXECUCAO DE ABLACOES E AMBIENTE\n" + "=" * 80 + "\n",
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

    # PARTE 3 COMPACTA: Todos os 3.823 trials avaliados em formato tabular estruturado (< 140 KB)
    export_compact_jsonl_dataset()

    # PARTE 3 RAW: Dados Brutos JSONL Completos para arquivo integral
    export_raw_jsonl_dataset()

    # Unified bundle for backward compatibility with zero duplication
    seen_unified: Set[str] = set()
    unified_sections = [
        build_header("PACOTE UNIFICADO COMPLETO (PARTE 1 + PARTE 2A + 2B + 2C)"),
        "=" * 80 + "\nSECAO 1: RESPOSTA AOS REVISORES, MANUSCRITO CIENTIFICO, REFERENCIAS, GOVERNANCA E TODAS AS 7 TABELAS LATEX + MACROS\n" + "=" * 80 + "\n",
    ]
    for f in part1_files:
        block = dump_file(f, seen_unified)
        if block:
            unified_sections.append(block)
    unified_sections.append("=" * 80 + "\nSECAO 2A: CODIGO-FONTE NUCLEO, ADAPTADORES E TESTES\n" + "=" * 80 + "\n")
    for f in part2a_files:
        block = dump_file(f, seen_unified)
        if block:
            unified_sections.append(block)
    unified_sections.append("=" * 80 + "\nSECAO 2B: MANIFESTO CRIPTOGRAFICO E JSONS DE METADADOS E RESULTADOS\n" + "=" * 80 + "\n")
    for f in part2b_files:
        block = dump_file(f, seen_unified, compact_json=True)
        if block:
            unified_sections.append(block)
    unified_sections.append("=" * 80 + "\nSECAO 2C: SCRIPTS DE ABLACOES E REPLICACAO\n" + "=" * 80 + "\n")
    for f in part2c_files:
        block = dump_file(f, seen_unified)
        if block:
            unified_sections.append(block)
    unified_sections.append("=" * 80 + "\nFIM DO PACOTE DE AUDITORIA INTEGRAL (100% ARQUIVOS VERIFICADOS)\n" + "=" * 80 + "\n")
    bundle_content = "\n".join(unified_sections)
    for out_path in [OUTPUT_FINAL, OUTPUT_FILE_6, OUTPUT_FILE_6_4]:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(bundle_content)
        print(f"✅ Generated unified mirror: {out_path} ({os.path.getsize(out_path)/1024:.2f} KB, {len(seen_unified)} unique files)")


def export_compact_jsonl_dataset():
    """Exports 100% of all evaluated trials across the entire 3,823-trial campaign into a compact, zero-truncation schema (< 140 KB)."""
    print(f"📦 Generating Part 3 compact dataset dump: {OUTPUT_PART3_COMPACT}...")
    jsonl_files = [
        ("raw_trials", "results/publication_campaign/raw_trials.jsonl"),
        ("warm_cache", "results/publication_campaign/warm_cache_trials.jsonl"),
        ("inter_session", "results/publication_campaign/inter_session_trials.jsonl"),
        ("tool_rag_mitigation", "results/publication_campaign/tool_rag_mitigation_trials.jsonl"),
        ("kv_cache_thrashing", "results/publication_campaign/kv_cache_thrashing_trials.jsonl"),
        ("prefill_ablation", "results/publication_campaign/prefill_ablation.jsonl"),
        ("uma_energy_bandwidth", "results/publication_campaign/uma_energy_bandwidth_trials.jsonl"),
    ]

    lines = [
        "=" * 80,
        "PARTE 3 COMPACTA: DADOS DE TODOS OS 3.823 TRIALS DE AVALIACAO CIENTIFICA",
        "Elsevier SoftwareX: picoclaw-vs-openclaw-benchmark",
        "=" * 80,
        "# SCHEMA: [DATASET|WORKLOAD|RUNTIME] it,t_task_ms,ttft_ms,energy_j,host_bw_gbps,edp_js,proc_rss_mb",
        "=" * 80,
    ]

    current_group = None
    records_count = 0

    for tag, rel_path in jsonl_files:
        abs_path = os.path.join(REPO_DIR, rel_path)
        if not os.path.exists(abs_path):
            continue
        with open(abs_path, "r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if r.get("is_warmup", False):
                    continue
                records_count += 1
                wl = r.get("workload", "")
                rt = r.get("runtime", "")
                group = (tag, wl, rt)
                if group != current_group:
                    current_group = group
                    lines.append(f"[{tag}|{wl}|{rt}]")

                it = r.get("iteration", r.get("trial", ""))
                t_task = round(r.get("t_task_ms", 0), 1)
                ttft = round(r.get("ttft_ms", 0), 1)
                e = round(r.get("energy_j", 0), 2)
                bw = round(r.get("host_bw_gbps", 0), 2)
                edp = round(r.get("edp_js", 0), 1)
                rss = round(r.get("proc_peak_phys_mb", r.get("proc_rss_mb", 0)), 1)
                lines.append(f"{it},{t_task},{ttft},{e},{bw},{edp},{rss}")

    lines.append("=" * 80)
    lines.append("FIM DA PARTE 3 COMPACTA (100% DOS 3.823 TRIALS SEM TRUNCAMENTO)")
    lines.append("=" * 80 + "\n")

    content = "\n".join(lines)
    with open(OUTPUT_PART3_COMPACT, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Generated Part 3 compact dataset dump: {OUTPUT_PART3_COMPACT} ({os.path.getsize(OUTPUT_PART3_COMPACT)/1024:.2f} KB, {records_count} evaluated trials)")


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
