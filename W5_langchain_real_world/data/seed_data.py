#!/usr/bin/env python3
"""
W5_langchain_real_world/data/seed_data.py
Seeds the local document and SQLite database for the real-world cross-domain workload W5.
"""

import os
import sqlite3

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

POLICY_TEXT = """# ENTERPRISE INFRASTRUCTURE GOVERNANCE AND AI POLICY (REVISION 2026.4)

## 1. SCOPE AND JURISDICTION
This governance framework defines operational Service Level Agreements (SLAs), capital allocation thresholds, and security compliance standards for all autonomous AI services and backend workloads deployed across enterprise infrastructure.

## 2. SERVICE LEVEL AGREEMENTS (SLAS) AND LATENCY LIMITS
2.1 Tier-1 Mission-Critical Services:
- Maximum permissible P99 latency is 45.0 ms.
- Maximum allowable error rate is 0.05% (5 errors per 10,000 requests).
- Infrastructure requirement: High-priority cluster allocation with automated failover.

2.2 Tier-2 Standard Enterprise Services:
- Maximum permissible P99 latency is 120.0 ms.
- Maximum allowable error rate is 0.20%.
- Target uptime: 99.9% availability during business hours.

2.3 Tier-3 Exploratory and Batch Workloads:
- Maximum permissible P99 latency is 500.0 ms.
- Error tolerance up to 1.00%.

## 3. BUDGET ALLOCATION AND OVERRUN THRESHOLDS
3.1 Approved Project Budget Variance:
- Any project where `current_spend_usd` exceeds `allocated_budget_usd` by more than 5.0% triggers an immediate Governance Freeze.
- Projects operating within budget (spend <= allocation) are eligible for routine quarterly resource expansion.

3.2 Cost Recovery and Clawback:
- Teams operating projects with > 10% budget deficit without pre-authorization will have subsequent quarterly compute credits throttled by 25%.

## 4. COMPLIANCE AUDIT AND DATA PRIVACY
4.1 Active Violation Status:
- Projects marked with compliance status 'NON_COMPLIANT' or having violations_count >= 1 must be quarantined from accessing customer-identifiable datasets.
- Mandatory remediation window is 14 business days from audit notification.

4.2 Required Reporting Format:
- All cross-domain operational assessments must explicitly correlate financial spend variance with observed telemetry performance and compliance status.
"""

def init_db(db_path: str):
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE projects (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        tier TEXT NOT NULL,
        owner_team TEXT NOT NULL,
        allocated_budget_usd REAL NOT NULL,
        current_spend_usd REAL NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE service_telemetry (
        id INTEGER PRIMARY KEY,
        project_id INTEGER NOT NULL,
        endpoint TEXT NOT NULL,
        p99_latency_ms REAL NOT NULL,
        error_rate_pct REAL NOT NULL,
        daily_requests INTEGER NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    """)

    cur.execute("""
    CREATE TABLE compliance_audit (
        id INTEGER PRIMARY KEY,
        project_id INTEGER NOT NULL,
        last_audit_date TEXT NOT NULL,
        compliance_status TEXT NOT NULL,
        violations_count INTEGER NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    """)

    projects = [
        (1, "Alpha-Neural-Gateway", "Tier-1", "Core-Inference", 150000.0, 162000.0), # Over budget (+8%), latency 38ms (OK)
        (2, "Beta-Vector-Search", "Tier-2", "Search-Platform", 80000.0, 74500.0),    # Under budget, latency 135ms (Breach SLA >120)
        (3, "Gamma-Tool-Router", "Tier-1", "Agent-Systems", 110000.0, 108000.0),    # Under budget, latency 42ms (OK), compliance violation=1
        (4, "Delta-Batch-Analytics", "Tier-3", "Data-Pipelines", 45000.0, 49000.0), # Over budget (+8.8%), latency 310ms (OK)
        (5, "Epsilon-Embeddings-Cache", "Tier-2", "Platform-Infra", 95000.0, 92000.0) # Under budget, latency 85ms (OK), Compliant
    ]
    cur.executemany("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)", projects)

    telemetry = [
        (1, 1, "/v1/infer/stream", 38.4, 0.02, 1250000),
        (2, 2, "/v1/vectors/knn", 135.8, 0.12, 450000),
        (3, 3, "/v1/tools/dispatch", 42.1, 0.01, 890000),
        (4, 4, "/v1/batch/aggregate", 310.5, 0.45, 120000),
        (5, 5, "/v1/cache/lookup", 85.2, 0.03, 3100000)
    ]
    cur.executemany("INSERT INTO service_telemetry VALUES (?, ?, ?, ?, ?, ?)", telemetry)

    audits = [
        (1, 1, "2026-10-15", "COMPLIANT", 0),
        (2, 2, "2026-10-20", "COMPLIANT", 0),
        (3, 3, "2026-11-01", "NON_COMPLIANT", 1), # Data retention policy breach
        (4, 4, "2026-09-30", "COMPLIANT", 0),
        (5, 5, "2026-10-28", "COMPLIANT", 0)
    ]
    cur.executemany("INSERT INTO compliance_audit VALUES (?, ?, ?, ?, ?)", audits)

    conn.commit()
    conn.close()

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    doc_path = os.path.join(DATA_DIR, "governance_policy.txt")
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(POLICY_TEXT.strip() + "\n")
    
    db_path = os.path.join(DATA_DIR, "analytics.db")
    init_db(db_path)
    print(f"✔ Seeded policy document: {doc_path}")
    print(f"✔ Seeded SQLite database: {db_path}")

if __name__ == "__main__":
    main()
