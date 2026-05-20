from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class WarrantyCaseState(TypedDict, total=False):
    claim_id: str
    vin: str
    trace: List[str]
    claim_data: Dict[str, Any]
    vehicle_data: Dict[str, Any]
    part_data: Dict[str, Any]
    dealer_data: Dict[str, Any]
    supplier_data: Dict[str, Any]
    service_history: List[Dict[str, Any]]
    fault_codes: List[Dict[str, Any]]
    knowledge_matches: List[Dict[str, Any]]
    data_quality_result: Dict[str, Any]
    warranty_rule_result: Dict[str, Any]
    root_cause_hypothesis: str
    supplier_recovery_result: Dict[str, Any]
    severity_index: float
    confidence_score: float
    missing_evidence: List[str]
    human_review_required: bool
    final_recommended_action: str
    evidence_packet: str
