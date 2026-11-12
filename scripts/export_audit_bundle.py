#!/usr/bin/env python3
"""
scripts/export_audit_bundle.py - Consolidated Academic Audit Bundle Exporter
Exportador do Pacote Consolidado de Auditoria para Submissão Elsevier SoftwareX

Generates repo_texto_auditoria_6.txt containing full audit proofs, file contents,
cryptographic SHA-256 signatures, licenses, CI workflow, and telemetry summaries.

Author: Rafael Paniccia Cassetta (UFABC)
"""

import datetime
import hashlib
import os
import subprocess
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(REPO_DIR, "repo_texto_auditoria_6.txt")


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
    print(f"📦 Generating audit bundle: {OUTPUT_FILE}...")

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

    # 1. Dataset Verification & Samples
    sections.append("=" * 80 + "\nSECAO 1: DADOS BRUTOS FISICOS (JSONL SUMMARIES & HASHES)\n" + "=" * 80 + "\n")
    jsonl_files = [
        "results/publication_campaign/raw_trials.jsonl",
        "results/publication_campaign/warm_cache_trials.jsonl",
        "results/publication_campaign/prefill_ablation.jsonl",
        "results/exploratory_campaigns/raw_trials_pre_w2_fix.jsonl",
    ]
    for jf in jsonl_files:
        sections.append(get_jsonl_summary(jf))

    # 2. Key Metadata & Tables
    sections.append("=" * 80 + "\nSECAO 2: TABELAS LATEX E RESUMOS ESTATISTICOS\n" + "=" * 80 + "\n")
    meta_files = [
        "results/publication_campaign/tables/table_journal_ablation.tex",
        "results/publication_campaign/tables/table_warm_cache.tex",
        "results/publication_campaign/tables/table_prefill_ablation.tex",
        "results/publication_campaign/tables/table_spearman_correlation.tex",
        "results/publication_campaign/tables/macros_empirical.tex",
        "results/publication_campaign/prefill_regression_fit.json",
        "results/publication_campaign/spearman_correlation_matrix.json",
        "results/publication_campaign/summary_statistics.json",
        "results/publication_campaign/warm_cache_summary.json",
        "data/manifest_sha256.json",
    ]
    for mf in meta_files:
        sections.append(dump_file(mf))

    # 3. Governance, CI & Legal
    sections.append("=" * 80 + "\nSECAO 3: GOVERNANCA, LICENCAS E CI/CD\n" + "=" * 80 + "\n")
    gov_files = [
        "LICENSE",
        "DATA_LICENSE",
        ".github/workflows/ci.yml",
        ".gitignore",
        "Makefile",
        "pyproject.toml",
    ]
    for gf in gov_files:
        sections.append(dump_file(gf))

    # 4. Source Code & Adapters
    sections.append("=" * 80 + "\nSECAO 4: CODIGO-FONTE DOS ORQUESTRADORES E ADAPTADORES\n" + "=" * 80 + "\n")
    code_files = [
        "benchmark/adapters/base.py",
        "benchmark/adapters/picoclaw_adapter.py",
        "benchmark/adapters/openclaw_adapter.py",
        "benchmark/adapters/python_adapter.py",
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
        "scripts/verify_manifest.py",
    ]
    for cf in code_files:
        sections.append(dump_file(cf))

    # 5. Tests
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

    # 6. Documentation & Manuscript
    sections.append("=" * 80 + "\nSECAO 6: MANUSCRITO E DOCUMENTACAO DE SUBMISSAO\n" + "=" * 80 + "\n")
    doc_files = [
        "paper/softwarex_manuscript.tex",
        "references.bib",
        "paper/COVER_LETTER.md",
        "paper/HIGHLIGHTS.md",
        "README.md",
        "tutorial/README.md",
    ]
    for df in doc_files:
        sections.append(dump_file(df))

    bundle_content = "\n".join(sections)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(bundle_content)

    print(f"✅ Generated audit bundle: {OUTPUT_FILE} ({len(bundle_content)} characters, {os.path.getsize(OUTPUT_FILE)} bytes)")


if __name__ == "__main__":
    generate_bundle()
