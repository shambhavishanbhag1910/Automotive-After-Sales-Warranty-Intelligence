from __future__ import annotations

from typing import Any, Dict, List, Optional
import json
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


class WarrantyRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    def _read_one(self, sql: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self.engine.connect() as conn:
            df = pd.read_sql_query(text(sql), conn, params=params)
        if df.empty:
            return None
        return df.iloc[0].where(pd.notnull(df.iloc[0]), None).to_dict()

    def _read_many(self, sql: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            df = pd.read_sql_query(text(sql), conn, params=params or {})
        if df.empty:
            return []
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient="records")

    def get_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        return self._read_one("SELECT * FROM claims WHERE claim_id = :claim_id", {"claim_id": claim_id})

    def list_claims(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._read_many("""
            SELECT claim_id, vin, part_name, system, claim_amount_usd, risk_score, severity_index, recommended_action
            FROM claims
            ORDER BY risk_score DESC, claim_amount_usd DESC
            LIMIT :limit
        """, {"limit": limit})

    def get_vehicle(self, vin: str) -> Optional[Dict[str, Any]]:
        return self._read_one("SELECT * FROM vehicle_master WHERE vin = :vin", {"vin": vin})

    def get_service_history(self, vin: str) -> List[Dict[str, Any]]:
        return self._read_many("""
            SELECT * FROM service_history
            WHERE vin = :vin
            ORDER BY visit_date DESC
        """, {"vin": vin})

    def get_fault_codes_by_repair_order(self, repair_order_id: str) -> List[Dict[str, Any]]:
        return self._read_many("""
            SELECT * FROM fault_codes
            WHERE repair_order_id = :repair_order_id
            ORDER BY severity DESC, occurrence_count DESC
        """, {"repair_order_id": repair_order_id})

    def get_fault_codes_by_vin(self, vin: str) -> List[Dict[str, Any]]:
        return self._read_many("""
            SELECT * FROM fault_codes
            WHERE vin = :vin
            ORDER BY last_detected_date DESC, occurrence_count DESC
        """, {"vin": vin})

    def get_part(self, part_number: str) -> Optional[Dict[str, Any]]:
        return self._read_one("SELECT * FROM parts_master WHERE part_number = :part_number", {"part_number": part_number})

    def get_dealer(self, dealer_id: str) -> Optional[Dict[str, Any]]:
        return self._read_one("SELECT * FROM dealers WHERE dealer_id = :dealer_id", {"dealer_id": dealer_id})

    def get_supplier(self, supplier_id: str) -> Optional[Dict[str, Any]]:
        return self._read_one("SELECT * FROM suppliers WHERE supplier_id = :supplier_id", {"supplier_id": supplier_id})

    def get_related_tsb(self, component: str, make: Optional[str] = None, model: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._read_many("""
            SELECT * FROM tsb_knowledge
            WHERE lower(component) LIKE lower(:component)
               OR lower(symptom) LIKE lower(:component)
               OR lower(document_text) LIKE lower(:component)
            LIMIT 5
        """, {"component": f"%{component}%"})

    def get_related_recalls(self, component: str, make: Optional[str] = None, model: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._read_many("""
            SELECT * FROM recalls_campaigns
            WHERE lower(component) LIKE lower(:component)
               OR lower(defect_summary) LIKE lower(:component)
            LIMIT 5
        """, {"component": f"%{component}%"})

    def get_warranty_rules(self) -> List[Dict[str, Any]]:
        return self._read_many("SELECT * FROM warranty_rules ORDER BY priority DESC")

    def get_all_knowledge_rows(self) -> List[Dict[str, Any]]:
        docs: List[Dict[str, Any]] = []
        for table in ["tsb_knowledge", "recalls_campaigns", "warranty_rules", "parts_master", "fault_codes"]:
            rows = self._read_many(f"SELECT * FROM {table} LIMIT 500")
            for row in rows:
                row["_source_table"] = table
                docs.append(row)
        return docs

    def save_audit_log(self, claim_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO agent_audit_log (claim_id, event_type, event_payload)
                VALUES (:claim_id, :event_type, :event_payload)
            """), {
                "claim_id": claim_id,
                "event_type": event_type,
                "event_payload": json.dumps(payload, default=str),
            })

    def save_evidence_packet(self, claim_id: str, evidence_packet: str, final_action: str, confidence: float, severity: float) -> None:
        if self.engine.dialect.name == "sqlite":
            sql = """
                INSERT OR REPLACE INTO generated_evidence_packets
                (claim_id, evidence_packet, final_recommended_action, confidence_score, severity_index)
                VALUES (:claim_id, :evidence_packet, :final_action, :confidence, :severity)
            """
        else:
            sql = """
                INSERT INTO generated_evidence_packets
                (claim_id, evidence_packet, final_recommended_action, confidence_score, severity_index)
                VALUES (:claim_id, :evidence_packet, :final_action, :confidence, :severity)
                ON CONFLICT (claim_id) DO UPDATE SET
                    evidence_packet = EXCLUDED.evidence_packet,
                    final_recommended_action = EXCLUDED.final_recommended_action,
                    confidence_score = EXCLUDED.confidence_score,
                    severity_index = EXCLUDED.severity_index,
                    created_at = CURRENT_TIMESTAMP
            """
        with self.engine.begin() as conn:
            conn.execute(text(sql), {
                "claim_id": claim_id,
                "evidence_packet": evidence_packet,
                "final_action": final_action,
                "confidence": confidence,
                "severity": severity,
            })

    def get_evidence_packet(self, claim_id: str) -> Optional[Dict[str, Any]]:
        return self._read_one("""
            SELECT * FROM generated_evidence_packets WHERE claim_id = :claim_id
        """, {"claim_id": claim_id})

    def save_human_review(self, claim_id: str, reviewer_role: str, human_decision: str, override_flag: str, override_reason: str, learning_label: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO human_review_decisions
                (claim_id, reviewer_role, human_decision, override_flag, override_reason, learning_label)
                VALUES (:claim_id, :reviewer_role, :human_decision, :override_flag, :override_reason, :learning_label)
            """), {
                "claim_id": claim_id,
                "reviewer_role": reviewer_role,
                "human_decision": human_decision,
                "override_flag": override_flag,
                "override_reason": override_reason,
                "learning_label": learning_label,
            })
