#!/usr/bin/env python3
"""
export_audit_chunks.py
Exporta o pacote de auditoria completo fatiado em blocos de no máximo
CHUNK_SIZE caracteres (sem quebrar palavras), para consumo modular por
um Avaliador IA com janela de contexto limitada.
"""

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Configuração ─────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
MAX_CHARS_PER_FILE = 10_000  # limite estrito de chars por arquivo (incluindo rodapé)
OUTPUT_DIR = REPO_ROOT / "audit_export_chunks"
PYTEST_LOG = Path("/tmp/pytest_audit_output.txt")

# Arquivos a incluir: (rótulo de cabeçalho, caminho relativo ao REPO_ROOT)
FILES = [
    (
        "RELATÓRIO DE AUDITORIA CROSS-PLATFORM (Linux x86_64 vs Darwin ARM64)",
        "results/publication_campaign_linux_x86_64/cross_platform_audit_report.md",
    ),
    (
        "TABELA 1 — SUMÁRIO MASTER (Mac Mini M4 / darwin-aarch64)",
        "results/publication_campaign/tables/table_journal_ablation.tex",
    ),
    (
        "TABELA 1 — SUMÁRIO MASTER (Linux x86_64)",
        "results/publication_campaign_linux_x86_64/tables/table1_master_summary.tex",
    ),
    (
        "MANIFESTO SHA-256 — darwin-aarch64 (Mac Mini M4)",
        "data/manifest_sha256.json",
    ),
    (
        "MANIFESTO SHA-256 — linux_x86_64 (Dell G15)",
        "data/manifest_sha256_linux_x86_64.json",
    ),
]

# ─── Montagem do corpus ────────────────────────────────────────────────────────
def border(label: str) -> str:
    return f"\n=== {label} ===\n\n"


def build_corpus() -> str:
    parts: list[str] = []

    # Cabeçalho global
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        head_commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except Exception:
        head_commit = "main"
    parts.append(
        border("PACOTE DE AUDITORIA — picoclaw-vs-openclaw-benchmark")
        + f"Gerado em : {ts}\n"
        + "Repositório: picoclaw-vs-openclaw-benchmark\n"
        + f"Commit HEAD: {head_commit} (main)\n\n"
    )

    # Arquivos do repositório
    for label, rel_path in FILES:
        abs_path = REPO_ROOT / rel_path
        parts.append(border(label))
        if abs_path.exists():
            content = abs_path.read_text(encoding="utf-8", errors="replace").strip()
            parts.append(content)
            parts.append("\n\n")
        else:
            parts.append(f"[ARQUIVO NÃO ENCONTRADO: {rel_path}]\n\n")

    # Log do pytest
    parts.append(border("LOG PYTEST — tests/test_artifact_consistency.py"))
    if PYTEST_LOG.exists():
        content = PYTEST_LOG.read_text(encoding="utf-8", errors="replace").strip()
        parts.append(content)
        parts.append("\n")
    else:
        parts.append("[Log do pytest não encontrado em /tmp/pytest_audit_output.txt]\n")

    return "".join(parts)


# ─── Fatiamento (word-safe) ────────────────────────────────────────────────────
def chunk_text(text: str, max_file_size: int = MAX_CHARS_PER_FILE) -> list[str]:
    """Divide texto em blocos garantindo que cada bloco + rodapé <= max_file_size chars sem quebrar palavras."""
    # Reservar 25 caracteres para o rodapé de paginação
    effective_chunk_size = max_file_size - 25
    chunks: list[str] = []
    start = 0
    total = len(text)
    while start < total:
        end = start + effective_chunk_size
        if end >= total:
            chunks.append(text[start:])
            break
        # Recua até o último espaço/newline para não cortar palavra
        cut = text.rfind(" ", start, end)
        nl_cut = text.rfind("\n", start, end)
        cut = max(cut, nl_cut)
        if cut <= start:          # palavra gigante — corta forçado
            cut = end
        else:
            cut += 1              # inclui o delimitador no bloco anterior
        chunks.append(text[start:cut])
        start = cut
    return chunks


# ─── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("▶  Montando corpus de auditoria...")
    corpus = build_corpus()
    print(f"   Corpus total : {len(corpus):,} caracteres")

    print(f"▶  Fatiando em blocos (limite total estrito <= {MAX_CHARS_PER_FILE:,} chars)...")
    chunks = chunk_text(corpus, MAX_CHARS_PER_FILE)
    print(f"   Total de partes : {len(chunks)}")

    # Limpa arquivos antigos
    for old in OUTPUT_DIR.glob("audit_part_*.txt"):
        old.unlink()

    summary_rows: list[tuple[str, int, int, int]] = []

    for i, chunk in enumerate(chunks, start=1):
        filename = OUTPUT_DIR / f"audit_part_{i}.txt"
        footer = f"\n\n--- Parte {i} de {len(chunks)} ---\n"
        content = chunk + footer
        filename.write_text(content, encoding="utf-8")
        lines = content.count("\n")
        chars = len(content)
        size_b = filename.stat().st_size
        summary_rows.append((filename.name, size_b, lines, chars))

    # ─── Relatório ───────────────────────────────────────────────────────────
    print()
    print(f"{'Arquivo':<25} {'Tamanho (KB)':>13} {'Linhas':>8} {'Caracteres':>12} {'<= 10.000?':>12}")
    print("-" * 74)
    all_ok = True
    for name, size_b, lines, chars in summary_rows:
        kb = size_b / 1024
        ok = "✅ SIM" if chars <= MAX_CHARS_PER_FILE else "❌ NÃO"
        if chars > MAX_CHARS_PER_FILE:
            all_ok = False
        print(f"{name:<25} {kb:>12.2f} {lines:>8,} {chars:>12,} {ok:>12}")

    print()
    if all_ok:
        print("✅  TODOS os arquivos respeitam rigorosamente o limite de <= 10.000 caracteres.")
    else:
        print("❌  ERRO: algum arquivo ultrapassou 10.000 caracteres!")
        sys.exit(1)

    print()
    print("📁  Pasta de exportação:")
    print(f"    {OUTPUT_DIR.resolve()}")
    print()
    print(f"📋  Total de partes : {len(chunks)}")
    print(f"    Corpus completo : {len(corpus):,} chars")
    print("    Pronto para enviar ao Avaliador IA parte a parte.")


if __name__ == "__main__":
    main()
