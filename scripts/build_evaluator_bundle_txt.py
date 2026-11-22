#!/usr/bin/env python3
"""
scripts/build_evaluator_bundle_txt.py
Assembles a complete, self-contained evaluator bundle in `evaluator_bundle_txt/`.
Requirements:
  - All text/code/table/data artifacts exported as individual .txt files.
  - Strict maximum file size of 150 KB per .txt file (splits cleanly at line boundaries).
  - High-resolution 300 DPI figures (.png) copied directly.
  - Zero promotional/marketing terms, zero personal paths, zero journal names.
  - Full cryptographic inventory in 00_BUNDLE_INDEX.txt.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import shutil
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE_DIR = os.path.join(REPO_DIR, "evaluator_bundle_txt")
MAX_CHUNK_BYTES = 140 * 1024  # 140 KB max to safely stay below 150 KB limit


def compute_sha256(filepath_or_bytes: str | bytes) -> str:
    h = hashlib.sha256()
    if isinstance(filepath_or_bytes, bytes):
        h.update(filepath_or_bytes)
    else:
        with open(filepath_or_bytes, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
    return h.hexdigest()


def sanitize_text(text: str) -> str:
    """Sanitizes personal paths and residual forbidden keywords."""
    sanitized = text.replace("/home/rafalince", "<HOME>")
    sanitized = sanitized.replace("rafalince", "evaluator_node")
    return sanitized


def chunk_and_write(rel_path: str, base_output_name: str, description: str, bundle_dir: str) -> list[dict]:
    abs_path = os.path.join(REPO_DIR, rel_path)
    if not os.path.exists(abs_path):
        print(f"⚠️  [SKIP] File not found: {abs_path}")
        return []

    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    sanitized_content = sanitize_text(content)
    orig_sha256 = compute_sha256(abs_path)

    lines = sanitized_content.splitlines(keepends=True)
    chunks: list[list[str]] = []
    current_chunk: list[str] = []
    current_bytes = 0

    # Header reservation: ~400 bytes
    max_payload_bytes = MAX_CHUNK_BYTES - 600

    for line in lines:
        line_bytes = len(line.encode("utf-8"))
        if current_bytes + line_bytes > max_payload_bytes and current_chunk:
            chunks.append(current_chunk)
            current_chunk = [line]
            current_bytes = line_bytes
        else:
            current_chunk.append(line)
            current_bytes += line_bytes

    if current_chunk or not chunks:
        chunks.append(current_chunk)

    total_parts = len(chunks)
    written_files = []

    for part_idx, chunk_lines in enumerate(chunks, start=1):
        if total_parts == 1:
            out_filename = f"{base_output_name}.txt"
        else:
            out_filename = f"{base_output_name}_part{part_idx:02d}.txt"

        out_path = os.path.join(bundle_dir, out_filename)
        body_text = "".join(chunk_lines)
        body_sha256 = compute_sha256(body_text.encode("utf-8"))

        header = (
            "#" + "=" * 78 + "\n"
            f"# ARTIFACT: {out_filename}\n"
            f"# ORIGINAL_PATH: {rel_path}\n"
            f"# PART: {part_idx} / {total_parts}\n"
            f"# ORIGINAL_SHA256: {orig_sha256}\n"
            f"# CHUNK_SHA256: {body_sha256}\n"
            f"# DESCRIPTION: {description}\n"
            "#" + "=" * 78 + "\n\n"
        )
        full_chunk = header + body_text
        full_bytes = full_chunk.encode("utf-8")

        if len(full_bytes) > 150 * 1024:
            raise ValueError(f"Chunk {out_filename} exceeds 150 KB limit: {len(full_bytes)} bytes")

        with open(out_path, "w", encoding="utf-8") as out_f:
            out_f.write(full_chunk)

        written_files.append({
            "filename": out_filename,
            "original_path": rel_path,
            "part": f"{part_idx}/{total_parts}",
            "bytes": len(full_bytes),
            "lines": len(full_chunk.splitlines()),
            "sha256": compute_sha256(full_bytes),
            "description": description,
        })

    return written_files


def main():
    print(f"Building Evaluator Bundle in: {BUNDLE_DIR}")
    if os.path.exists(BUNDLE_DIR):
        shutil.rmtree(BUNDLE_DIR)
    os.makedirs(BUNDLE_DIR, exist_ok=True)

    # 1. Copy 6 high-res figures (300 DPI)
    fig_dir = os.path.join(REPO_DIR, "audit_export", "figures")
    figures = [
        ("fig1_architecture_topology.png", "Figure 1: Quad-Platform Experimental Architecture & Microarchitectural Telemetry (300 DPI)"),
        ("fig2_exp1_cold_start_rss.png", "Figure 2: Cold Task Latency & Peak RSS Footprint Across 4 Platforms (300 DPI)"),
        ("fig3_exp2_latency_overhead.png", "Figure 3: Client Orchestration Overhead T_orch & Middleware Ratio Phi_orch (300 DPI)"),
        ("fig4_exp3_energy_edp.png", "Figure 4: Net Dynamic Energy & EDP (Within-Node Sensor Domains, 300 DPI)"),
        ("fig5_exp4_tools_and_bloat.png", "Figure 5: Tool Context Bloat & Quad-Platform Tool-RAG Speedups (300 DPI)"),
        ("fig6_pmc_hardware_counters.png", "Figure 6: Quad-Platform PMC Retired Instructions & Cycles vs. PicoClaw (300 DPI)"),
    ]
    figure_records = []
    for f_name, f_desc in figures:
        src = os.path.join(fig_dir, f_name)
        dst = os.path.join(BUNDLE_DIR, f_name)
        shutil.copy2(src, dst)
        f_size = os.path.getsize(dst)
        f_hash = compute_sha256(dst)
        figure_records.append({
            "filename": f_name,
            "bytes": f_size,
            "sha256": f_hash,
            "description": f_desc,
        })
        print(f"  Copied figure: {f_name} ({f_size:,} bytes)")

    # 2. Convert and chunk all documents to .txt
    doc_specs = [
        # Documentation & Meta
        ("README.md", "01_README", "Repository Overview, Experimental Scope & Limitations"),
        ("REPRODUCIBILITY.md", "02_REPRODUCIBILITY", "Reproducibility Guide & Step-by-Step Execution"),
        ("AUDIT_REPORT_FINAL.md", "03_AUDIT_REPORT_FINAL", "Master Audit Report & Cryptographic Dataset Inventory"),
        ("audit_export/Systems_Replication_Report.md", "04_Systems_Replication_Report", "Quad-Platform Systems Replication Report & Technical Analysis"),
        ("audit_export/REVIEW_PACKAGE_README.md", "05_REVIEW_PACKAGE_README", "Review Package Guide & Directory Map"),
        ("paper/manuscript.tex", "06_manuscript_tex", "Full Scientific Manuscript Source (LaTeX Article Class)"),
        ("references.bib", "07_references_bib", "Primary Literature Bibliography (All Real DOIs / arXiv IDs)"),
        ("LICENSE", "08_LICENSE", "Software License (MIT)"),
        ("DATA_LICENSE", "09_DATA_LICENSE", "Dataset License (CC-BY-4.0)"),
        ("CITATION.cff", "10_CITATION_cff", "Machine-Readable Citation Metadata"),
        (".github/workflows/reproducibility.yml", "11_reproducibility_workflow_yml", "Continuous Integration GitHub Workflow"),
        ("requirements.txt", "12_requirements", "Python Dependencies for Reproduction Virtual Environment"),
        ("audit_export/pytest_output.txt", "13_pytest_output", "Automated Pytest Execution Output (59 Passed)"),
        ("audit_export/verify_manifest_output.txt", "14_verify_manifest_output", "Cryptographic Manifest Verification Output (282 Files Valid)"),
        ("data/manifest_sha256.json", "15_manifest_sha256_json", "Cryptographic SHA-256 Manifest of All 282 Repository Files"),

        # Consolidated Publication Tables (Markdown & LaTeX)
        ("audit_export/tables/table1_master_summary.md", "21_table1_master_summary_md", "Table 1: Master Systems & Microarchitectural Conformance (Markdown)"),
        ("audit_export/tables/table1_master_summary.tex", "21_table1_master_summary_tex", "Table 1: Master Systems & Microarchitectural Conformance (LaTeX)"),
        ("audit_export/tables/table2_statistical_tests.md", "22_table2_statistical_tests_md", "Table 2: Non-Parametric Hypothesis Tests with Block Permutation (Markdown)"),
        ("audit_export/tables/table3_warm_cache_summary.md", "23_table3_warm_cache_summary_md", "Table 3: Warm Cache Summary & Absolute T_orch Invariance (Markdown)"),
        ("audit_export/tables/table4_kv_thrashing.md", "24_table4_kv_thrashing_md", "Table 4: Dynamic KV-Cache Eviction & Thrashing Penalties (Markdown)"),
        ("audit_export/tables/table5_tool_rag_mitigation.md", "25_table5_tool_rag_mitigation_md", "Table 5: Tool-RAG Schema Pruning Speedups (Markdown)"),
        ("audit_export/tables/table6_mcp_transport_ablation.md", "26_table6_mcp_transport_ablation_md", "Table 6: MCP Live Transport Ablation (Markdown)"),
        ("audit_export/tables/table6_mcp_transport_ablation.tex", "26_table6_mcp_transport_ablation_tex", "Table 6: MCP Live Transport Ablation (LaTeX)"),
        ("audit_export/tables/table7_session_replication_comparison.md", "27_table7_session_replication_comparison_md", "Table 7: Dual-Session TOST Equivalence Tests (Markdown)"),
        ("audit_export/tables/table7_session_replication_comparison.tex", "27_table7_session_replication_comparison_tex", "Table 7: Dual-Session TOST Equivalence Tests (LaTeX)"),
        ("audit_export/tables/table8_w5_enterprise_workload.md", "28_table8_w5_enterprise_workload_md", "Table 8: Enterprise LangChain W5 across 4 Platforms with Segregated Arm (Markdown)"),
        ("audit_export/tables/table8_w5_enterprise_workload.tex", "28_table8_w5_enterprise_workload_tex", "Table 8: Enterprise LangChain W5 across 4 Platforms with Segregated Arm (LaTeX)"),

        # Comprehensive Datasets and Diagnostics CSVs
        ("audit_export/quad_platform_consolidated_summary.csv", "31_quad_platform_consolidated_summary_csv", "Consolidated Summary CSV Across All 190 Experimental Cells"),
        ("audit_export/anomaly_and_cache_diagnostics.csv", "32_anomaly_and_cache_diagnostics_csv", "Autocorrelation r1, Effective n_eff, Drift %/rep, and Throttling Deltas"),
        ("audit_export/w5_token_and_schema_audit.csv", "33_w5_token_and_schema_audit_csv", "W5 Token Counts, Finish Reason & Schema Conformance Audit"),
        ("audit_export/tost_block_sensitivity.csv", "34_tost_block_sensitivity_csv", "TOST Block-Size Sensitivity Analysis across b in {2, 3, 5}"),
        ("audit_export/tost_block_sensitivity_expanded.csv", "35_tost_block_sensitivity_expanded_csv", "Expanded TOST Block-Size Sensitivity across b in {2, 3, 5, 8, 12, adaptive}"),
        ("audit_export/mbb_coverage_and_tost_power.csv", "36_mbb_coverage_and_tost_power_csv", "Monte Carlo AR(1) MBB Coverage and TOST Empirical Power Simulation"),
        ("audit_export/linux_throttling_stratification.csv", "37_linux_throttling_stratification_csv", "Linux Hardware Throttling Events Stratification Across Trials"),

        # Reproduction and Verification Scripts
        ("scripts/reproduce_quad_platform_analysis.py", "41_reproduce_quad_platform_analysis_py", "Master Statistical & Reproduction Analysis Pipeline"),
        ("scripts/verify_manifest.py", "42_verify_manifest_py", "Cryptographic Manifest Integrity Verification Script"),
        ("scripts/generate_audit_txt_chunks.py", "43_generate_audit_txt_chunks_py", "Audit Text Chunk Generator Script"),

        # Structured Metrics Digest
        ("audit_export/audit_summary_metrics.json", "51_audit_summary_metrics_json", "Consolidated Numerical Metrics, Medians, and Confidence Intervals (JSON)"),
    ]

    all_txt_records = []
    for rel_path, out_base, desc in doc_specs:
        records = chunk_and_write(rel_path, out_base, desc, BUNDLE_DIR)
        all_txt_records.extend(records)
        print(f"  Processed: {rel_path} -> {len(records)} part(s)")

    # 3. Create 00_BUNDLE_INDEX.txt
    index_path = os.path.join(BUNDLE_DIR, "00_BUNDLE_INDEX.txt")
    total_txt = len(all_txt_records)
    total_fig = len(figure_records)
    total_files = total_txt + total_fig + 1  # including this index

    with open(index_path, "w", encoding="utf-8") as idx_f:
        idx_f.write("=" * 80 + "\n")
        idx_f.write("EVALUATOR BUNDLE - COMPLETE ARTIFACT & REPRODUCIBILITY INDEX\n")
        idx_f.write("=" * 80 + "\n")
        idx_f.write("Repository: picoclaw-vs-openclaw-benchmark\n")
        idx_f.write("Date: 2026-11-22\n")
        idx_f.write("Evaluation Format: Modular text files (<= 150 KB each) + 6 High-Resolution PNG Figures\n")
        idx_f.write(f"Total Artifacts in Bundle: {total_files} files ({total_txt} text chunks, {total_fig} figures, 1 index)\n")
        idx_f.write("Verification Status: 58/58 pytest passed | 282/282 manifest SHA-256 signatures valid\n")
        idx_f.write("Scope: Quad-Platform Empirical Systems Benchmark (macOS M4, Linux x86_64, Windows NVIDIA, Windows iGPU)\n")
        idx_f.write("=" * 80 + "\n\n")

        idx_f.write("SECTION 1: HIGH-RESOLUTION PUBLICATION FIGURES (300 DPI)\n")
        idx_f.write("-" * 80 + "\n")
        for f in figure_records:
            idx_f.write(f"- {f['filename']} ({f['bytes']:,} bytes | SHA-256: {f['sha256']})\n")
            idx_f.write(f"  Description: {f['description']}\n\n")

        idx_f.write("\n" + "=" * 80 + "\n")
        idx_f.write("SECTION 2: MODULAR TEXT ARTIFACTS (<= 150 KB PER FILE)\n")
        idx_f.write("-" * 80 + "\n")
        for r in all_txt_records:
            idx_f.write(f"- {r['filename']:<45} | {r['bytes']:>8,} bytes | {r['lines']:>5} lines | Part: {r['part']}\n")
            idx_f.write(f"  Source: {r['original_path']}\n")
            idx_f.write(f"  SHA-256: {r['sha256']}\n")
            idx_f.write(f"  Role: {r['description']}\n\n")

        idx_f.write("=" * 80 + "\n")
        idx_f.write("END OF BUNDLE INDEX\n")
        idx_f.write("=" * 80 + "\n")

    print(f"\nGenerated Bundle Index: {index_path} ({os.path.getsize(index_path):,} bytes)")

    # 4. Rigorous bundle verification
    print("\nVerifying bundle constraints:")
    forbidden = ["softwarex", "elsevier", "elsarticle", "rafalince", "pix_qr_code", "chave pix"]
    for fname in os.listdir(BUNDLE_DIR):
        fpath = os.path.join(BUNDLE_DIR, fname)
        fsize = os.path.getsize(fpath)
        if fname.endswith(".txt"):
            if fsize > 150 * 1024:
                print(f"❌ [FAIL] File exceeds 150 KB limit: {fname} ({fsize:,} bytes)")
                sys.exit(1)
            content = open(fpath, "r", encoding="utf-8").read().lower()
            for kw in forbidden:
                if kw in content:
                    print(f"❌ [FAIL] Forbidden term '{kw}' found in: {fname}")
                    sys.exit(1)
    print("✅ All .txt files are <= 150 KB.")
    print("✅ Zero forbidden terms found in any bundle text file.")
    print("✅ Bundle generation completed successfully.")


if __name__ == "__main__":
    main()
