#!/usr/bin/env python3
"""
Deterministic Synthetic Workload Dataset Generator for W1, W2, W3, W4
Course: CCM313-EEI203 - Performance Analysis of Networks and Systems (UFABC)
"""
import json
import os
import random
import numpy as np

BASE_DIR = "/Users/rafael/.gemini/antigravity/scratch/picoclaw_vs_openclaw/workload_data"
MOCK_DIR = os.path.join(BASE_DIR, "mock_files")
LOG_FILE = os.path.join(BASE_DIR, "system_logs.jsonl")
EMBED_FILE = os.path.join(BASE_DIR, "embedding_head_100k.npz")
DOCS_FILE = os.path.join(BASE_DIR, "rag_chunks_10k.json")


def main():
    rng = random.Random(42)
    np_rng = np.random.default_rng(42)
    os.makedirs(MOCK_DIR, exist_ok=True)

    # 1. W2 Tool 1 dataset: 50 mock files in mock_files/
    for i in range(50):
        fname = os.path.join(MOCK_DIR, f"service_node_{i:02d}.conf")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(
                f"# Node Configuration {i:02d}\n"
                f"node_id=node-{i:02d}\n"
                f"cluster_role={'primary' if i % 5 == 0 else 'worker'}\n"
                f"memory_limit_mb={512 + (i * 16)}\n"
                f"status=ACTIVE\n"
            )

    # 2. W2 Tool 2 & Tool 3 dataset: ~100 KB JSONL log file with 500 target metric records
    records = []
    for i in range(750):
        is_target = i < 500
        val = round(rng.gauss(42.5, 8.75), 4) if is_target else round(rng.gauss(10.0, 2.0), 4)
        rec = {
            "seq": i,
            "timestamp": f"2026-10-25T18:{(i // 60) % 60:02d}:{i % 60:02d}.000Z",
            "subsystem": "UMA_BUS_CONTROLLER" if is_target else "IDLE_DAEMON",
            "level": "WARN" if is_target else "INFO",
            "latency_ms": val,
            "payload": f"bus_tx_id={100000 + i} coherence_state=SHARED_CLEAN cache_line=64B",
        }
        records.append(json.dumps(rec))

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(records) + "\n")

    # 3. W3 Vector RAG dataset: 100k-parameter projection layer (256x384 + 384 = 98,688 params)
    # and 10,000 document chunks (normalized 384-dim embeddings)
    w_proj = np_rng.standard_normal((256, 384), dtype=np.float32) * 0.05
    b_proj = np_rng.standard_normal((384,), dtype=np.float32) * 0.01
    doc_Matrix = np_rng.standard_normal((10000, 384), dtype=np.float32)
    norms = np.linalg.norm(doc_Matrix, axis=1, keepdims=True) + 1e-8
    doc_Matrix = doc_Matrix / norms

    np.savez(
        EMBED_FILE,
        w_proj=w_proj,
        b_proj=b_proj,
        doc_embeddings=doc_Matrix,
    )

    # Save metadata for top chunks so RAG injection produces ~1,280 retrieved context tokens
    sample_chunks = {}
    topics = [
        "Apple M4 Unified Memory Architecture LPDDR5X 120 GB/s bandwidth zero-copy tensor dispatch",
        "Go 1.23 concurrent tri-color mark-sweep garbage collector low-latency goroutine scheduling",
        "Node.js V8 generational scavenger and mark-compact garbage collection pauses in TypeScript",
        "Quantized GGUF Q4_K_M neural inference prefill and decode bandwidth scaling on Metal GPU",
        "POSIX local loopback IPC socket serialization and JSON schema validation overhead in agents",
    ]
    for idx in range(100):
        t = topics[idx % len(topics)]
        sample_chunks[str(idx)] = (
            f"[Chunk #{idx:04d}] Technical Reference: {t}. "
            + ("Empirical telemetry confirms cache-line coherence across performance and efficiency cores " * 14)
        )
    with open(DOCS_FILE, "w", encoding="utf-8") as f:
        json.dump(sample_chunks, f, indent=2)

    log_size_kb = os.path.getsize(LOG_FILE) / 1024.0
    embed_size_mb = os.path.getsize(EMBED_FILE) / (1024.0 * 1024.0)
    print(f"Created 50 mock files in {MOCK_DIR}")
    print(f"Created JSON log file: {LOG_FILE} ({log_size_kb:.1f} KB, {len(records)} lines, 500 target points)")
    print(f"Created 100k-param projection head + 10,000x384 vector matrix: {EMBED_FILE} ({embed_size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
