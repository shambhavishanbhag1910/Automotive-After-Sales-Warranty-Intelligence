from __future__ import annotations

from typing import Any, Dict
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


def get_kpis(engine: Engine) -> Dict[str, Any]:
    with engine.connect() as conn:
        claims = pd.read_sql_query(text("SELECT * FROM claims"), conn)
        agent_cases = pd.read_sql_query(text("SELECT * FROM agent_cases"), conn)

    total_claims = len(claims)
    total_cost = float(claims["claim_amount_usd"].sum()) if total_claims else 0.0
    high_risk_claims = int((claims["risk_score"] >= 75).sum()) if total_claims else 0
    repeat_claims = int((claims["repeat_repair_flag"].astype(str).str.upper() == "Y").sum()) if total_claims else 0
    supplier_recovery = int(claims["recommended_action"].astype(str).str.contains("supplier", case=False, na=False).sum()) if total_claims else 0
    avg_severity = float(claims["severity_index"].mean()) if total_claims else 0.0
    evidence_ready = int(agent_cases["evidence_packet_status"].astype(str).str.contains("Ready|Sent", case=False, na=False).sum()) if len(agent_cases) else 0

    top_parts = (
        claims.groupby("part_name", as_index=False)
        .agg(claim_count=("claim_id", "count"), total_cost=("claim_amount_usd", "sum"), avg_risk=("risk_score", "mean"))
        .sort_values(["total_cost", "claim_count"], ascending=False)
        .head(5)
        .to_dict(orient="records")
    )

    return {
        "total_claims": total_claims,
        "total_claim_amount_usd": round(total_cost, 2),
        "average_claim_amount_usd": round(total_cost / total_claims, 2) if total_claims else 0,
        "high_risk_claims": high_risk_claims,
        "repeat_repair_claims": repeat_claims,
        "supplier_recovery_opportunities": supplier_recovery,
        "average_severity_index": round(avg_severity, 3),
        "evidence_packets_ready_or_sent": evidence_ready,
        "top_parts_by_cost": top_parts,
    }
