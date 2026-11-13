#!/usr/bin/env python3
"""
scripts/export_audit_bundle.py - Consolidated Academic Audit Bundle Exporter
Exportador do Pacote Consolidado de Auditoria para Submissão Elsevier SoftwareX

Generates repo_texto_auditoria_final.txt (and mirrors) containing 100% integral contents:
manuscript, governance, all 6 LaTeX tables and macros, consolidated results JSONs,
and full unabridged production source code and test suite (ZERO truncation).

Author: Rafael Paniccia Cassetta (UFABC)
"""

import datetime
import hashlib
import json
import os
import subprocess
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


def format_compact_spearman(content: str) -> str:
    try:
        data = json.loads(content)
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


def format_compact_pca(content: str) -> str:
    try:
        data = json.loads(content)
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
    """Reads and returns 100% full content of the specified file with SHA-256 header (ZERO truncation)."""
    abs_path = os.path.join(REPO_DIR, rel_path)
    if not os.path.exists(abs_path):
        return f"=== FILE: {rel_path} (MISSING) ===\n\n"

    sha = compute_sha256(abs_path)
    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if rel_path in [
        "results/publication_campaign/hyperfine_cold_start.json",
        "results/publication_campaign/hyperfine_agent_init.json",
    ]:
        content = format_compact_hyperfine(content)
    elif rel_path == "results/publication_campaign/spearman_correlation_matrix.json":
        content = format_compact_spearman(content)
    elif rel_path == "results/publication_campaign/pca_variance_decomposition.json":
        content = format_compact_pca(content)

    return f"================================================================================\nFILE: {rel_path}\nSHA-256: {sha}\n================================================================================\n{content}\n\n"


def generate_bundle():
    print(f"📦 Generating unabridged audit bundle: {OUTPUT_FINAL}...")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    git_head = get_cmd_output(["git", "rev-parse", "HEAD"])
    git_status = get_cmd_output(["git", "status", "--short"])
    sw_vers = get_cmd_output(["sw_vers"])
    sysctl_cpu = get_cmd_output(["sysctl", "-n", "machdep.cpu.brand_string"])

    header = f"""================================================================================
PACOTE COMPLETO DE AUDITORIA E REPRODUCIBILIDADE CIENTIFICA INTEGRAL
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

    sections = [header]

    # SECAO 1: ARTIGO, BIBLIOGRAFIA, LICENCAS, CI/CD E GOVERNANCA (100% INTEGRAL)
    sections.append("=" * 80 + "\nSECAO 1: MANUSCRITO CIENTIFICO, REFERENCIAS, CITACAO, GOVERNANCA E LICENCAS (100% INTEGRAL)\n" + "=" * 80 + "\n")
    priority_docs = [
        "paper/softwarex_manuscript.tex",
        "references.bib",
        "paper/HIGHLIGHTS.md",
        "paper/COVER_LETTER.md",
        "CITATION.cff",
        "LICENSE",
        "DATA_LICENSE",
        ".github/workflows/ci.yml",
        "Makefile",
        "pyproject.toml",
    ]
    for doc in priority_docs:
        sections.append(dump_file(doc))

    # SECAO 2: TODAS AS 6 TABELAS LATEX E MACROS (100% INTEGRAL)
    sections.append("=" * 80 + "\nSECAO 2: TODAS AS 6 TABELAS LATEX E MACROS (100% INTEGRAL)\n" + "=" * 80 + "\n")
    latex_tables = [
        "results/publication_campaign/tables/table_journal_ablation.tex",
        "results/publication_campaign/tables/table_warm_cache.tex",
        "results/publication_campaign/tables/table_prefill_ablation.tex",
        "results/publication_campaign/tables/table_spearman_correlation.tex",
        "results/publication_campaign/tables/table_pca_loadings.tex",
        "results/publication_campaign/tables/table_energy_bandwidth_deconvolution.tex",
        "results/publication_campaign/tables/macros_empirical.tex",
    ]
    for lt in latex_tables:
        sections.append(dump_file(lt))

    # SECAO 3: TODO O CODIGO-FONTE DE PRODUCAO E TESTES (100% INTEGRAL SEM TRUNCAMENTO)
    sections.append("=" * 80 + "\nSECAO 3: TODO O CODIGO-FONTE DE PRODUCAO E TESTES (100% INTEGRAL - ZERO TRUNCAMENTO)\n" + "=" * 80 + "\n")
    source_files = [
        # Benchmark & Adapters
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
        "scripts/run_warm_cache_campaign.py",
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
    ]
    for sf in source_files:
        sections.append(dump_file(sf))

    # SECAO 4: DOCUMENTACAO GERAL, METADADOS E TABELAS ESTATICAS
    sections.append("=" * 80 + "\nSECAO 4: DOCUMENTACAO GERAL, METADADOS E JSONS DE RESULTADOS (COMPACTADOS SEM PERDA)\n" + "=" * 80 + "\n")
    doc_and_meta_files = [
        "README.md",
        "tutorial/README.md",
        "results/publication_campaign/campaign_metadata.json",
        "results/publication_campaign/prefill_regression_fit.json",
        "results/publication_campaign/uma_energy_bandwidth_attribution.json",
        "results/publication_campaign/inter_session_replication.json",
        "results/publication_campaign/pca_variance_decomposition.json",
        "results/publication_campaign/spearman_correlation_matrix.json",
        "results/publication_campaign/summary_statistics.json",
        "results/publication_campaign/warm_cache_summary.json",
        "results/publication_campaign/statistical_tests.json",
        "results/publication_campaign/warm_cache_statistical_tests.json",
        "results/publication_campaign/hyperfine_cold_start.json",
        "results/publication_campaign/hyperfine_agent_init.json",
        "data/manifest_sha256.json",
    ]
    for dmf in doc_and_meta_files:
        sections.append(dump_file(dmf))

    bundle_content = "\n".join(sections)
    for out_path in [OUTPUT_FINAL, OUTPUT_FILE_6, OUTPUT_FILE_6_4]:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(bundle_content)
        print(f"✅ Generated bundle: {out_path} ({len(bundle_content)} characters, {os.path.getsize(out_path)} bytes)")

    # Export complete raw JSONL dataset dump without truncation
    export_raw_jsonl_dataset()


def export_raw_jsonl_dataset():
    print(f"📦 Generating full untruncated JSONL dataset dump: {OUTPUT_RAW_JSONL}...")
    jsonl_files = [
        "results/publication_campaign/raw_trials.jsonl",
        "results/publication_campaign/warm_cache_trials.jsonl",
        "results/publication_campaign/prefill_ablation.jsonl",
        "results/publication_campaign/uma_energy_bandwidth_trials.jsonl",
    ]
    parts = [
        "================================================================================",
        "DADOS BRUTOS COMPLETOS (100% REGISTROS JSONL) - REVISAO 6",
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
        parts.append("")

    content = "\n".join(parts)
    with open(OUTPUT_RAW_JSONL, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Generated complete raw JSONL dump: {OUTPUT_RAW_JSONL} ({len(parts)} lines, {os.path.getsize(OUTPUT_RAW_JSONL)} bytes)")


if __name__ == "__main__":
    generate_bundle()
