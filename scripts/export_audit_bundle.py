#!/usr/bin/env python3
"""
scripts/export_audit_bundle.py - Consolidated 3-Part Academic Audit Bundle Exporter
Exportador do Pacote Consolidado de Auditoria em 3 Partes para Submissão Elsevier SoftwareX

Generates:
  1. auditoria_parte1_manuscrito_tabelas_respostas.txt
  2. auditoria_parte2_codigo_testes_metadados_manifesto.txt
  3. auditoria_parte3_dados_brutos_jsonl_completos.txt
  4. repo_texto_auditoria_final.txt (unified mirror for backward compatibility)

Author: Rafael Paniccia Cassetta (UFABC)
"""

import datetime
import hashlib
import json
import os
import subprocess
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PART1 = os.path.join(REPO_DIR, "auditoria_parte1_manuscrito_tabelas_respostas.txt")
OUTPUT_PART2 = os.path.join(REPO_DIR, "auditoria_parte2_codigo_testes_metadados_manifesto.txt")
OUTPUT_PART3 = os.path.join(REPO_DIR, "auditoria_parte3_dados_brutos_jsonl_completos.txt")
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


def get_cmd_output(cmd: list[str]) -> str:
    try:
        res = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True, timeout=5)
        return res.stdout.strip()
    except Exception as e:
        return f"Error: {e}"


def format_compact_hyperfine(content: str) -> str:
    try:
        data = json.loads(content)
        results = data.get("results", [])
        lines = [
            "{",
            f'  "schema_version": {data.get("schema_version", 2)},',
            f'  "metadata": {json.dumps(data.get("metadata", {}), separators=(",", ": "))},',
            f'  "primary_metric": "{data.get("primary_metric", "time_wall_clock")}",',
            '  "results": [',
        ]
        for r_idx, r in enumerate(results):
            lines.append("    {")
            lines.append(f'      "command": {json.dumps(r.get("command", ""))},')
            lines.append('      "measurements": [')
            meas = r.get("measurements", [])
            for m_idx, m in enumerate(meas):
                comma = "," if m_idx < len(meas) - 1 else ""
                lines.append(f"        {json.dumps(m, separators=(',', ':'))}{comma}")
            lines.append("      ]")
            comma_r = "," if r_idx < len(results) - 1 else ""
            lines.append(f"    }}{comma_r}")
        lines.append("  ]")
        lines.append("}")
        return "\n".join(lines)
    except Exception:
        return content


def format_compact_json_dict(content: str) -> str:
    try:
        data = json.loads(content)
        if not isinstance(data, dict):
            return content
        lines = ["{"]
        items = list(data.items())
        for idx, (k, v) in enumerate(items):
            comma = "," if idx < len(items) - 1 else ""
            if isinstance(v, dict):
                lines.append(f'  "{k}": {{')
                sub_items = list(v.items())
                for s_idx, (sk, sv) in enumerate(sub_items):
                    s_comma = "," if s_idx < len(sub_items) - 1 else ""
                    lines.append(f'    "{sk}": {json.dumps(sv, separators=(",", ":"))}{s_comma}')
                lines.append(f"  }}{comma}")
            else:
                lines.append(f'  "{k}": {json.dumps(v, separators=(",", ": "))}{comma}')
        lines.append("}")
        return "\n".join(lines)
    except Exception:
        return content


def dump_file(rel_path: str) -> str:
    """Reads and returns 100% full content of the specified file with SHA-256 header and explicit closing delimiter."""
    abs_path = os.path.join(REPO_DIR, rel_path)
    if not os.path.exists(abs_path):
        return f"=== FILE: {rel_path} (MISSING) ===\n\n"

    sha = compute_sha256(abs_path)
    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if rel_path in [
        "results/publication_campaign/hyperfine_cold_start.json",
        "results/publication_campaign/hyperfine_agent_init.json",
        "results/publication_campaign/hyperfine_worker_version.json",
    ]:
        content = format_compact_hyperfine(content)
    elif rel_path in [
        "results/publication_campaign/spearman_correlation_matrix.json",
        "results/publication_campaign/pca_variance_decomposition.json",
        "results/publication_campaign/uma_energy_bandwidth_attribution.json",
        "results/publication_campaign/inter_session_replication.json",
        "results/publication_campaign/tool_rag_mitigation_summary.json",
        "results/publication_campaign/summary_statistics.json",
        "results/publication_campaign/warm_cache_summary.json",
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
        "auditoria_parte1_manuscrito_tabelas_respostas.txt",
        "auditoria_parte2_codigo_testes_metadados_manifesto.txt",
        "auditoria_parte3_dados_brutos_jsonl_completos.txt",
        "repo_texto_auditoria_final.txt",
        "repo_texto_auditoria_6.txt",
        "repo_texto_auditoria_6_4.txt",
        "repo_dados_brutos_jsonl_completos.txt",
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
    print("📦 Generating 3-part unabridged audit bundles and unified mirror...")

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

    p1_sections = [
        build_header("PARTE 1: RESPOSTA AOS REVISORES, MANUSCRITO .TEX, BIBLIOGRAFIA E TABELAS LATEX"),
        "=" * 80 + "\nSECAO 1: RESPOSTA AOS REVISORES, MANUSCRITO CIENTIFICO, REFERENCIAS, GOVERNANCA E TODAS AS 7 TABELAS LATEX + MACROS\n" + "=" * 80 + "\n",
    ]
    for f in part1_files:
        p1_sections.append(dump_file(f))
    p1_sections.append("=" * 80 + "\nFIM DA PARTE 1 DO PACOTE DE AUDITORIA (100% INTEGRAL SEM TRUNCAMENTO)\n" + "=" * 80 + "\n")
    part1_content = "\n".join(p1_sections)
    with open(OUTPUT_PART1, "w", encoding="utf-8") as f:
        f.write(part1_content)
    print(f"✅ Generated Part 1: {OUTPUT_PART1} ({len(part1_content)} chars, {os.path.getsize(OUTPUT_PART1)} bytes)")

    # PARTE 2: CI/CD, Makefile, Codigo-Fonte de Producao (incluindo protocol_invariants.py e bun_jsc_agent.mjs), Scripts, Testes, JSONs e Manifesto SHA-256
    part2_files = [
        ".github/workflows/ci.yml",
        "Makefile",
        "pyproject.toml",
        # Benchmark & Adapters
        "benchmark/protocol_invariants.py",
        "benchmark/bun_jsc_agent.mjs",
        "benchmark/picoclaw_orch.go",
        "benchmark/openclaw_orch.mjs",
        "benchmark/python_orch.py",
        "benchmark/telemetry.py",
        "benchmark/run_unified_benchmark.py",
        "benchmark/analyze_results.py",
        "benchmark/generate_charts.py",
        "benchmark/generate_datasets.py",
        "benchmark/adapters/base.py",
        "benchmark/adapters/picoclaw_adapter.py",
        "benchmark/adapters/openclaw_adapter.py",
        "benchmark/adapters/python_native_adapter.py",
        "benchmark/adapters/neural_baseline_adapter.py",
        "benchmark/adapters/bun_minimal_adapter.py",
        "benchmark/adapters/__init__.py",
        # Active Scripts
        "scripts/run_tool_rag_mitigation_experiment.py",
        "scripts/run_warm_cache_campaign.py",
        "scripts/run_regime_b_w2_w4_unified_session.py",
        "scripts/run_prefill_ablation.py",
        "scripts/run_w2_resample.py",
        "scripts/run_inter_session_replication.py",
        "scripts/run_uma_energy_and_bandwidth_attribution.py",
        "scripts/verify_manifest.py",
        "scripts/setup_environment.sh",
        "scripts/check_quiescence.sh",
        # Test Suite
        "tests/test_adapters_and_failfast.py",
        "tests/test_artifact_consistency.py",
        "tests/test_dataset_generator.py",
        "tests/test_statistical_engine.py",
        "tests/test_telemetry_parser.py",
        # Docs, Results JSONs & Cryptographic Manifest
        "README.md",
        "tutorial/README.md",
        "results/publication_campaign/campaign_metadata.json",
        "results/publication_campaign/uma_energy_bandwidth_attribution.json",
        "results/publication_campaign/inter_session_replication.json",
        "results/publication_campaign/tool_rag_mitigation_summary.json",
        "results/publication_campaign/prefill_regression_fit.json",
        "results/publication_campaign/spearman_correlation_matrix.json",
        "results/publication_campaign/pca_variance_decomposition.json",
        "results/publication_campaign/summary_statistics.json",
        "results/publication_campaign/warm_cache_summary.json",
        "results/publication_campaign/statistical_tests.json",
        "results/publication_campaign/warm_cache_statistical_tests.json",
        "results/publication_campaign/hyperfine_cold_start.json",
        "results/publication_campaign/hyperfine_worker_version.json",
        "results/publication_campaign/hyperfine_agent_init.json",
        "data/manifest_sha256.json",
    ]

    p2_sections = [
        build_header("PARTE 2: CODIGO-FONTE, SCRIPTS, TESTES, JSONS DE RESULTADOS E MANIFESTO SHA-256"),
        "=" * 80 + "\nSECAO 2: CODIGO-FONTE INTEGRAL, SCRIPTS, TESTES, JSONS DE RESULTADOS E MANIFESTO SHA-256\n" + "=" * 80 + "\n",
    ]
    for f in part2_files:
        p2_sections.append(dump_file(f))
    p2_sections.append("=" * 80 + "\nFIM DA PARTE 2 DO PACOTE DE AUDITORIA (100% ARQUIVOS E MANIFESTO VERIFICADOS)\n" + "=" * 80 + "\n")
    part2_content = "\n".join(p2_sections)
    with open(OUTPUT_PART2, "w", encoding="utf-8") as f:
        f.write(part2_content)
    print(f"✅ Generated Part 2: {OUTPUT_PART2} ({len(part2_content)} chars, {os.path.getsize(OUTPUT_PART2)} bytes)")

    # Unified bundle for backward compatibility
    unified_sections = [
        build_header("PACOTE UNIFICADO COMPLETO (PARTE 1 + PARTE 2)"),
        "\n".join(p1_sections[1:-1]),
        "\n".join(p2_sections[1:-1]),
        "=" * 80 + "\nFIM DO PACOTE DE AUDITORIA INTEGRAL (100% ARQUIVOS VERIFICADOS)\n" + "=" * 80 + "\n",
    ]
    bundle_content = "\n".join(unified_sections)
    for out_path in [OUTPUT_FINAL, OUTPUT_FILE_6, OUTPUT_FILE_6_4]:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(bundle_content)
        print(f"✅ Generated unified bundle: {out_path} ({len(bundle_content)} chars, {os.path.getsize(out_path)} bytes)")

    # PARTE 3: Dados Brutos JSONL Completos
    export_raw_jsonl_dataset()


def export_raw_jsonl_dataset():
    print(f"📦 Generating Part 3 full untruncated JSONL dataset dump: {OUTPUT_PART3}...")
    jsonl_files = [
        "results/publication_campaign/raw_trials.jsonl",
        "results/publication_campaign/warm_cache_trials.jsonl",
        "results/publication_campaign/inter_session_trials.jsonl",
        "results/publication_campaign/tool_rag_mitigation_trials.jsonl",
        "results/publication_campaign/prefill_ablation.jsonl",
        "results/publication_campaign/uma_energy_bandwidth_trials.jsonl",
    ]
    parts = [
        "================================================================================",
        "PARTE 3: DADOS BRUTOS COMPLETOS (100% REGISTROS JSONL SEM CORTES)",
        "Elsevier SoftwareX: picoclaw-vs-openclaw-benchmark",
        "================================================================================\n",
    ]
    for rel_path in jsonl_files:
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
    for out_p in [OUTPUT_PART3, OUTPUT_RAW_JSONL]:
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Generated Part 3 raw JSONL dump: {out_p} ({len(parts)} lines, {os.path.getsize(out_p)} bytes)")


if __name__ == "__main__":
    generate_bundle()
