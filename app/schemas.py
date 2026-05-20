from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ClaimSummary(BaseModel):
    claim_id: str
    vin: str
    part_name: Optional[str] = None
    system: Optional[str] = None
    claim_amount_usd: Optional[float] = None
    risk_score: Optional[float] = None
    severity_index: Optional[float] = None
    recommended_action: Optional[str] = None


class AgentRunResponse(BaseModel):
    claim_id: str
    vin: str
    final_recommended_action: str
    human_review_required: bool
    confidence_score: float
    severity_index: float
    root_cause_hypothesis: str
    supplier_recovery_result: Dict[str, Any]
    missing_evidence: List[str]
    evidence_packet: str
    trace: List[str]


class HumanReviewRequest(BaseModel):
    reviewer_role: str
    human_decision: str
    override_flag: str = "N"
    override_reason: str = "No override"
    learning_label: str = "Accepted"
