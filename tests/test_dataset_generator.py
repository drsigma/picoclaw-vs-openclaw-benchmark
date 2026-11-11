"""
Unit Tests for Deterministic Workload Datasets
Testes Unitários para Datasets Determinísticos dos Workloads

Author / Autor: Rafael Paniccia Cassetta (UFABC)
"""

import json
import os

import numpy as np

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_DIR, "data", "workload_data")


def test_mock_files_directory_structure():
    """Verify mock_files contains exactly 50 synthetic deterministic files."""
    mock_dir = os.path.join(DATA_DIR, "mock_files")
    assert os.path.exists(mock_dir), f"Directory {mock_dir} does not exist"
    files = [f for f in os.listdir(mock_dir) if not f.startswith(".")]
    assert len(files) == 50, f"Expected 50 mock files, found {len(files)}"
    for f in files:
        full_p = os.path.join(mock_dir, f)
        assert os.path.getsize(full_p) > 0, f"File {f} is empty"


def test_system_logs_schema_and_record_count():
    """Verify system_logs.jsonl contains 750 valid JSON lines with required fields."""
    log_file = os.path.join(DATA_DIR, "system_logs.jsonl")
    assert os.path.exists(log_file), f"Log file {log_file} does not exist"

    count = 0
    with open(log_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            count += 1
            record = json.loads(line)
            assert "timestamp" in record, f"Line {idx} missing timestamp"
            assert "subsystem" in record, f"Line {idx} missing subsystem"
            assert "level" in record, f"Line {idx} missing level"
            assert "latency_ms" in record, f"Line {idx} missing latency_ms"
            assert isinstance(record["latency_ms"], (int, float)), f"Line {idx} latency_ms not numeric"

    assert count == 750, f"Expected 750 log entries, counted {count}"


def test_rag_chunks_count_and_format():
    """Verify rag_chunks_10k.json contains valid text chunks with index keys."""
    rag_file = os.path.join(DATA_DIR, "rag_chunks_10k.json")
    assert os.path.exists(rag_file), f"RAG chunks file {rag_file} does not exist"

    with open(rag_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    assert len(chunks) >= 100, f"Expected at least 100 chunks, found {len(chunks)}"
    assert "0" in chunks, "Index 0 missing in chunks"
    assert isinstance(chunks["0"], str) and len(chunks["0"]) > 50


def test_embedding_head_matrix_dimensions():
    """Verify embedding_head_100k.npz contains the dense projection matrix."""
    emb_file = os.path.join(DATA_DIR, "embedding_head_100k.npz")
    assert os.path.exists(emb_file), f"Embedding weights {emb_file} missing"

    data = np.load(emb_file)
    assert len(data.files) > 0
    key = data.files[0]
    mat = data[key]
    assert mat.dtype in (np.float32, np.float64)
    assert mat.size >= 98000, f"Matrix size {mat.size} below expected ~98k parameters"
