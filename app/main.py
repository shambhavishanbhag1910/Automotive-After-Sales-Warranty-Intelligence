from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException

from app.agents.graph import WarrantyInvestigationGraph
from app.config import get_settings
from app.db import get_engine
from app.schemas import AgentRunResponse, HumanReviewRequest
from app.services.data_loader import database_has_claims, load_csv_folder_to_database
from app.services.kpi_service import get_kpis
from app.services.repository import WarrantyRepository

app = FastAPI(
    title="Agentic AI Warranty Intelligence Platform",
    description="Automotive after sales warranty investigation using LangGraph style agents, RAG retrieval, and human review.",
    version="0.1.0",
)

engine = get_engine()
repo = WarrantyRepository(engine)


@app.on_event("startup")
def startup_event() -> None:
    settings = get_settings()
    if not database_has_claims(engine):
        load_csv_folder_to_database(engine, Path(settings.sample_data_dir))


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "warranty-agentic-ai"}


@app.get("/kpis")
def kpis() -> Dict[str, Any]:
    return get_kpis(engine)


@app.get("/claims")
def list_claims(limit: int = 50) -> List[Dict[str, Any]]:
    return repo.list_claims(limit=limit)


@app.get("/claims/{claim_id}")
def get_claim(claim_id: str) -> Dict[str, Any]:
    claim = repo.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim not found: {claim_id}")
    return claim


@app.post("/claims/{claim_id}/run-agent", response_model=AgentRunResponse)
def run_agent(claim_id: str) -> Dict[str, Any]:
    if not repo.get_claim(claim_id):
        raise HTTPException(status_code=404, detail=f"Claim not found: {claim_id}")
    graph = WarrantyInvestigationGraph(repo)
    result = graph.run(claim_id)
    return {
        "claim_id": result["claim_id"],
        "vin": result["vin"],
        "final_recommended_action": result.get("final_recommended_action", "Review required"),
        "human_review_required": bool(result.get("human_review_required", True)),
        "confidence_score": float(result.get("confidence_score", 0.0)),
        "severity_index": float(result.get("severity_index", 0.0)),
        "root_cause_hypothesis": result.get("root_cause_hypothesis", ""),
        "supplier_recovery_result": result.get("supplier_recovery_result", {}),
        "missing_evidence": result.get("missing_evidence", []),
        "evidence_packet": result.get("evidence_packet", ""),
        "trace": result.get("trace", []),
    }


@app.get("/claims/{claim_id}/evidence-packet")
def get_evidence_packet(claim_id: str) -> Dict[str, Any]:
    packet = repo.get_evidence_packet(claim_id)
    if not packet:
        # Generate on demand for convenience.
        graph = WarrantyInvestigationGraph(repo)
        graph.run(claim_id)
        packet = repo.get_evidence_packet(claim_id)
    if not packet:
        raise HTTPException(status_code=404, detail=f"Evidence packet not found for claim: {claim_id}")
    return packet


@app.post("/claims/{claim_id}/human-review")
def save_human_review(claim_id: str, request: HumanReviewRequest) -> Dict[str, str]:
    if not repo.get_claim(claim_id):
        raise HTTPException(status_code=404, detail=f"Claim not found: {claim_id}")
    repo.save_human_review(
        claim_id=claim_id,
        reviewer_role=request.reviewer_role,
        human_decision=request.human_decision,
        override_flag=request.override_flag,
        override_reason=request.override_reason,
        learning_label=request.learning_label,
    )
    return {"status": "saved", "claim_id": claim_id}
