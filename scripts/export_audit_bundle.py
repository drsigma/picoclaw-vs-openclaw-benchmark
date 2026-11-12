#!/usr/bin/env python3
"""
scripts/export_audit_bundle.py - Consolidated Academic Audit Bundle Exporter
Exportador do Pacote Consolidado de Auditoria para Submissão Elsevier SoftwareX

Generates repo_texto_auditoria_6.txt containing full audit proofs, file contents,
cryptographic SHA-256 signatures, licenses, CI workflow, and telemetry summaries.
Ordered with manuscript, tables, and licenses upfront to guarantee complete AI context visibility.

Author: Rafael Paniccia Cassetta (UFABC)
"""

import datetime
import hashlib
import os
import subprocess
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(REPO_DIR, "repo_texto_auditoria_6.txt")
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


def get_jsonl_summary(rel_path: str) -> str:
    abs_path = os.path.join(REPO_DIR, rel_path)
    if not os.path.exists(abs_path):
        return f"[FILE MISSING: {rel_path}]\n"

    sha = compute_sha256(abs_path)
    size_bytes = os.path.getsize(abs_path)

    with open(abs_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    n_lines = len(lines)
    first_3 = lines[:3]
    last_3 = lines[-3:] if n_lines >= 3 else lines

    out = [
        f"--- File: {rel_path} ---",
        f"SHA-256: {sha}",
        f"Size: {size_bytes} bytes | Line Count: {n_lines} records",
        "First 3 records:",
    ]
    for r in first_3:
        out.append(f"  {r}")
    if n_lines > 3:
        out.append("Last 3 records:")
        for r in last_3:
            out.append(f"  {r}")
    out.append("")
    return "\n".join(out)


def dump_file(rel_path: str) -> str:
    abs_path = os.path.join(REPO_DIR, rel_path)
    if not os.path.exists(abs_path):
        return f"=== FILE: {rel_path} (MISSING) ===\n\n"

    sha = compute_sha256(abs_path)
    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    return f"================================================================================\nFILE: {rel_path}\nSHA-256: {sha}\n================================================================================\n{content}\n\n"


def generate_bundle():
    print(f"📦 Generating prioritized audit bundle: {OUTPUT_FILE}...")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    git_head = get_cmd_output(["git", "rev-parse", "HEAD"])
    git_status = get_cmd_output(["git", "status", "--short"])
    sw_vers = get_cmd_output(["sw_vers"])
    sysctl_cpu = get_cmd_output(["sysctl", "-n", "machdep.cpu.brand_string"])

    header = f"""================================================================================
PACOTE COMPLETO DE AUDITORIA E REPRODUCIBILIDADE CIENTIFICA - REVISAO 6
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

    # SECAO 1: MANUSCRITO, BIBLIOGRAFIA, LICENCAS, CI/CD E DOCUMENTACAO
    sections.append("=" * 80 + "\nSECAO 1: MANUSCRITO CIENTIFICO, REFERENCIAS, CITACAO, GOVERNANCA E LICENCAS\n" + "=" * 80 + "\n")
    priority_docs = [
        "paper/softwarex_manuscript.tex",
        "references.bib",
        "CITATION.cff",
        "LICENSE",
        "DATA_LICENSE",
        ".github/workflows/ci.yml",
        "README.md",
        "paper/COVER_LETTER.md",
        "paper/HIGHLIGHTS.md",
        "tutorial/README.md",
    ]
    for doc in priority_docs:
        sections.append(dump_file(doc))

    # SECAO 2: TABELAS LATEX E RESUMOS ESTATISTICOS CONSOLIDADOS
    sections.append("=" * 80 + "\nSECAO 2: TABELAS LATEX E RESUMOS ESTATISTICOS CONSOLIDADOS\n" + "=" * 80 + "\n")
    meta_files = [
        "results/publication_campaign/tables/table_journal_ablation.tex",
        "results/publication_campaign/tables/table_warm_cache.tex",
        "results/publication_campaign/tables/table_prefill_ablation.tex",
        "results/publication_campaign/tables/table_spearman_correlation.tex",
        "results/publication_campaign/tables/table_pca_loadings.tex",
        "results/publication_campaign/tables/macros_empirical.tex",
        "results/publication_campaign/campaign_metadata.json",
        "results/publication_campaign/prefill_regression_fit.json",
        "results/publication_campaign/spearman_correlation_matrix.json",
        "results/publication_campaign/pca_variance_decomposition.json",
        "results/publication_campaign/summary_statistics.json",
        "results/publication_campaign/warm_cache_summary.json",
        "results/publication_campaign/warm_cache_statistical_tests.json",
        "results/publication_campaign/inter_session_replication.json",
        "results/publication_campaign/hyperfine_cold_start.json",
        "results/publication_campaign/hyperfine_agent_init.json",
        "results/publication_campaign/llama_server_publication.log",
        "results/publication_campaign/powermetrics_publication_sample.txt",
        "results/publication_campaign/tables/table_energy_bandwidth_deconvolution.tex",
        "results/publication_campaign/uma_energy_bandwidth_attribution.json",
        "data/manifest_sha256.json",
    ]
    for mf in meta_files:
        sections.append(dump_file(mf))

    # SECAO 3: RESUMO AUDITAVEL DE DADOS BRUTOS FISICOS (JSONL HASHES & SAMPLES)
    sections.append("=" * 80 + "\nSECAO 3: RESUMO AUDITAVEL DE DADOS BRUTOS FISICOS (JSONL HASHES & SAMPLES)\n" + "=" * 80 + "\n")
    jsonl_files = [
        "results/publication_campaign/raw_trials.jsonl",
        "results/publication_campaign/warm_cache_trials.jsonl",
        "results/publication_campaign/prefill_ablation.jsonl",
        "results/publication_campaign/uma_energy_bandwidth_trials.jsonl",
    ]
    for jf in jsonl_files:
        sections.append(get_jsonl_summary(jf))

    # SECAO 4: CODIGO-FONTE DOS ORQUESTRADORES, ADAPTADORES E SCRIPTS
    sections.append("=" * 80 + "\nSECAO 4: CODIGO-FONTE DOS ORQUESTRADORES, ADAPTADORES E SCRIPTS\n" + "=" * 80 + "\n")
    code_files = [
        "benchmark/adapters/base.py",
        "benchmark/adapters/picoclaw_adapter.py",
        "benchmark/adapters/openclaw_adapter.py",
        "benchmark/adapters/python_native_adapter.py",
        "benchmark/adapters/neural_baseline_adapter.py",
        "benchmark/adapters/bun_minimal_adapter.py",
        "benchmark/adapters/__init__.py",
        "benchmark/picoclaw_orch.go",
        "benchmark/openclaw_orch.mjs",
        "benchmark/python_orch.py",
        "benchmark/telemetry.py",
        "benchmark/run_unified_benchmark.py",
        "benchmark/analyze_results.py",
        "scripts/run_prefill_ablation.py",
        "scripts/run_warm_cache_campaign.py",
        "scripts/run_regime_a_equalized_update.py",
        "scripts/run_inter_session_replication.py",
        "scripts/run_uma_energy_and_bandwidth_attribution.py",
        "scripts/export_audit_bundle.py",
        "scripts/verify_manifest.py",
        "Makefile",
        "pyproject.toml",
    ]
    for cf in code_files:
        sections.append(dump_file(cf))

    # SECAO 5: SUITE DE TESTES UNITARIOS
    sections.append("=" * 80 + "\nSECAO 5: SUITE DE TESTES UNITARIOS\n" + "=" * 80 + "\n")
    test_files = [
        "tests/test_adapters_and_failfast.py",
        "tests/test_artifact_consistency.py",
        "tests/test_statistical_engine.py",
        "tests/test_telemetry_parser.py",
        "tests/test_dataset_generator.py",
    ]
    for tf in test_files:
        sections.append(dump_file(tf))

    bundle_content = "\n".join(sections)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(bundle_content)

    print(f"✅ Generated prioritized audit bundle: {OUTPUT_FILE} ({len(bundle_content)} characters, {os.path.getsize(OUTPUT_FILE)} bytes)")

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
