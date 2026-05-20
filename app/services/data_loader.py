from __future__ import annotations

from pathlib import Path
from typing import Dict
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

REQUIRED_CSV_FILES = [
    "claims.csv",
    "vehicle_master.csv",
    "service_history.csv",
    "fault_codes.csv",
    "parts_master.csv",
    "dealers.csv",
    "suppliers.csv",
    "recalls_campaigns.csv",
    "tsb_knowledge.csv",
    "warranty_rules.csv",
    "agent_cases.csv",
    "human_review_feedback.csv",
    "data_dictionary.csv",
]


def load_csv_folder_to_database(engine: Engine, data_dir: Path) -> Dict[str, int]:
    """Load all demo CSV files into database tables.

    This function intentionally uses pandas.to_sql for easy local use. In enterprise setup,
    replace this with Alembic migrations and controlled ETL jobs.
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    loaded_counts: Dict[str, int] = {}
    for file_name in REQUIRED_CSV_FILES:
        file_path = data_dir / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Required CSV missing: {file_path}")
        table_name = file_name.replace(".csv", "")
        df = pd.read_csv(file_path)
        df.to_sql(table_name, con=engine, if_exists="replace", index=False)
        loaded_counts[table_name] = len(df)

    create_support_tables(engine)
    return loaded_counts


def create_support_tables(engine: Engine) -> None:
    """Create simple support tables for audit and human review outputs.

    SQLite is used by default. PostgreSQL is also supported when DATABASE_URL is
    changed, but for enterprise usage you should replace this with Alembic
    migrations.
    """
    dialect = engine.dialect.name
    id_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if dialect == "sqlite" else "SERIAL PRIMARY KEY"

    with engine.begin() as conn:
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS agent_audit_log (
            id {id_type},
            claim_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_payload TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS generated_evidence_packets (
            claim_id TEXT PRIMARY KEY,
            evidence_packet TEXT NOT NULL,
            final_recommended_action TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            severity_index REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS human_review_decisions (
            id {id_type},
            claim_id TEXT NOT NULL,
            reviewer_role TEXT NOT NULL,
            human_decision TEXT NOT NULL,
            override_flag TEXT NOT NULL,
            override_reason TEXT NOT NULL,
            learning_label TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))


def database_has_claims(engine: Engine) -> bool:
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM claims"))
            return result.scalar_one() > 0
    except Exception:
        return False
