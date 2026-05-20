from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime

from app.agents.state import WarrantyCaseState
from app.rag.simple_retriever import SimpleKnowledgeRetriever
from app.services.evidence_packet import build_evidence_packet
from app.services.repository import WarrantyRepository


HIGH_SEVERITY_DTC = {"Critical", "High"}


def append_trace(state: WarrantyCaseState, message: str) -> None:
    trace = state.get("trace", [])
    trace.append(message)
    state["trace"] = trace


class WarrantyAgentNodes:
    def __init__(self, repo: WarrantyRepository):
        self.repo = repo
        self.retriever = SimpleKnowledgeRetriever(repo.get_all_knowledge_rows())

    def claim_intake_node(self, state: WarrantyCaseState) -> WarrantyCaseState:
        claim_id = state["claim_id"]
        claim = self.repo.get_claim(claim_id)
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")
        state["claim_data"] = claim
        state["vin"] = claim["vin"]
        append_trace(state, "Claim Intake Agent loaded the warranty claim and basic complaint details.")
        return state

    def data_enrichment_node(self, state: WarrantyCaseState) -> WarrantyCaseState:
        claim = state["claim_data"]
        vehicle = self.repo.get_vehicle(claim["vin"]) or {}
        part = self.repo.get_part(claim["part_number"]) or {}
        dealer = self.repo.get_dealer(claim["dealer_id"]) or {}
        supplier = self.repo.get_supplier(part.get("supplier_id", "")) or {}
        service_history = self.repo.get_service_history(claim["vin"])
        fault_codes = self.repo.get_fault_codes_by_repair_order(claim["repair_order_id"])

        state["vehicle_data"] = vehicle
        state["part_data"] = part
        state["dealer_data"] = dealer
        state["supplier_data"] = supplier
        state["service_history"] = service_history
        state["fault_codes"] = fault_codes
        append_trace(state, "Data Enrichment Agent joined vehicle, part, dealer, supplier, service history, and fault code context.")
        return state

    def data_quality_node(self, state: WarrantyCaseState) -> WarrantyCaseState:
        claim = state.get("claim_data", {})
        required_fields = ["claim_id", "vin", "repair_order_id", "part_number", "complaint", "cause", "correction"]
        missing = [field for field in required_fields if not claim.get(field)]

        if not state.get("fault_codes"):
            missing.append("Fault code details for repair order")
        if not state.get("service_history"):
            missing.append("Service history for VIN")

        cause_text = str(claim.get("cause", "")).lower()
        correction_text = str(claim.get("correction", "")).lower()
        if "not fully documented" in cause_text or "not documented" in cause_text:
            missing.append("Detailed technician diagnostic notes")
        if "replaced" in correction_text and "test" not in correction_text and "inspection" not in correction_text:
            missing.append("Before and after test result for replaced part")

        state["missing_evidence"] = list(dict.fromkeys(missing))
        state["data_quality_result"] = {
            "missing_evidence_count": len(state["missing_evidence"]),
            "status": "Incomplete" if missing else "Complete",
        }
        append_trace(state, "Data Quality Agent checked mandatory claim evidence and diagnostic completeness.")
        return state

    def vin_history_node(self, state: WarrantyCaseState) -> WarrantyCaseState:
        claim = state["claim_data"]
        service_history = state.get("service_history", [])
        same_part_visits = [
            row for row in service_history
            if str(row.get("part_replaced", "")).lower() == str(claim.get("part_name", "")).lower()
        ]
        repeat_repair = claim.get("repeat_repair_flag") == "Y" or len(same_part_visits) > 1
        state["vin_history_result"] = {
            "service_visit_count": len(service_history),
            "same_part_visit_count": len(same_part_visits),
            "repeat_repair_detected": repeat_repair,
        }
        append_trace(state, "VIN History Agent checked repeat repair and prior service events.")
        return state

    def fault_code_node(self, state: WarrantyCaseState) -> WarrantyCaseState:
        fault_codes = state.get("fault_codes", [])
        critical_codes = [f for f in fault_codes if str(f.get("severity")) in HIGH_SEVERITY_DTC]
        high_occurrence = [f for f in fault_codes if int(f.get("occurrence_count") or 0) >= 5]
        state["fault_code_result"] = {
            "fault_code_count": len(fault_codes),
            "critical_fault_code_count": len(critical_codes),
            "high_occurrence_count": len(high_occurrence),
            "primary_fault_code": fault_codes[0].get("dtc_code") if fault_codes else None,
        }
        append_trace(state, "Fault Code Agent interpreted DTC severity and occurrence frequency.")
        return state

    def knowledge_retrieval_node(self, state: WarrantyCaseState) -> WarrantyCaseState:
        claim = state["claim_data"]
        query = " ".join([
            str(claim.get("part_name", "")),
            str(claim.get("system", "")),
            str(claim.get("complaint", "")),
            str(claim.get("cause", "")),
            str(claim.get("dtc_primary", "")),
        ])
        matches = self.retriever.search(query, top_k=8)
        state["knowledge_matches"] = matches
        append_trace(state, "Knowledge Retrieval Agent searched TSB, recall, warranty rule, parts, and fault code knowledge.")
        return state

    def warranty_rule_node(self, state: WarrantyCaseState) -> WarrantyCaseState:
        claim = state["claim_data"]
        part = state.get("part_data", {})
        mileage = float(claim.get("mileage_at_claim") or 0)
        months = float(claim.get("months_in_service") or 0)
        coverage_miles = float(part.get("warranty_coverage_miles") or 100000)
        coverage_months = float(part.get("warranty_coverage_months") or 36)
        within_coverage = mileage <= coverage_miles and months <= coverage_months and claim.get("policy_eligible") == "Y"
        requires_human = False
        reasons: List[str] = []

        if not within_coverage:
            requires_human = True
            reasons.append("Claim is outside standard warranty coverage or policy eligibility is not clear")
        if state.get("vin_history_result", {}).get("repeat_repair_detected"):
            requires_human = True
            reasons.append("Repeat repair detected")
        if state.get("data_quality_result", {}).get("status") == "Incomplete":
            requires_human = True
            reasons.append("Claim evidence is incomplete")
        if float(claim.get("claim_amount_usd") or 0) >= 2000:
            requires_human = True
            reasons.append("High dollar claim")

        state["warranty_rule_result"] = {
            "within_coverage": within_coverage,
            "human_approval_required": requires_human,
            "reasons": reasons,
        }
        append_trace(state, "Warranty Rule Agent validated coverage, repeat repair, claim value, and evidence rules.")
        return state

    def severity_scoring_node(self, state: WarrantyCaseState) -> WarrantyCaseState:
        claim = state["claim_data"]
        claim_amount = float(claim.get("claim_amount_usd") or 0)
        risk_score = float(claim.get("risk_score") or 0)
        mileage = float(claim.get("mileage_at_claim") or 0)
        repeat = state.get("vin_history_result", {}).get("repeat_repair_detected", False)
        critical_faults = state.get("fault_code_result", {}).get("critical_fault_code_count", 0)
        missing_count = len(state.get("missing_evidence", []))

        score = 0.0
        score += min(claim_amount / 3000, 1.0) * 0.25
        score += min(risk_score / 100, 1.0) * 0.25
        score += 0.20 if repeat else 0.0
        score += 0.15 if critical_faults else 0.0
        score += 0.10 if mileage < 50000 else 0.03
        score += min(missing_count / 5, 1.0) * 0.05

        severity = round(min(score, 1.0), 2)
        confidence = round(max(0.55, 0.95 - (missing_count * 0.06)), 2)
        state["severity_index"] = severity
        state["confidence_score"] = confidence
        append_trace(state, "Severity Scoring Agent calculated severity index and confidence score.")
        return state

    def root_cause_node(self, state: WarrantyCaseState) -> WarrantyCaseState:
        claim = state["claim_data"]
        part_name = claim.get("part_name")
        cause = claim.get("cause")
        complaint = claim.get("complaint")
        fault_codes = state.get("fault_codes", [])
        dtc_text = ", ".join([f"{f.get('dtc_code')} {f.get('dtc_description')}" for f in fault_codes[:3]])
        repeat_text = "Repeat repair is present. " if state.get("vin_history_result", {}).get("repeat_repair_detected") else "No repeat repair was confirmed. "
        evidence_text = "Evidence is incomplete, so the recommendation should remain under human review. " if state.get("missing_evidence") else "Evidence looks sufficiently complete for initial decisioning. "

        hypothesis = (
            f"Likely issue around {part_name}. Customer complaint states: {complaint}. "
            f"Dealer stated cause: {cause}. Fault code context: {dtc_text or 'No DTC available'}. "
            f"{repeat_text}{evidence_text}The agent recommends validating diagnostic test results before final claim disposition."
        )
        state["root_cause_hypothesis"] = hypothesis
        append_trace(state, "Root Cause Agent created a warranty analyst style hypothesis from complaint, DTC, repair history, and evidence gaps.")
        return state

    def supplier_recovery_node(self, state: WarrantyCaseState) -> WarrantyCaseState:
        part = state.get("part_data", {})
        supplier = state.get("supplier_data", {})
        claim = state["claim_data"]
        severity = state.get("severity_index", 0.0)
        repeat = state.get("vin_history_result", {}).get("repeat_repair_detected", False)
        low_mileage = float(claim.get("mileage_at_claim") or 0) < 60000
        missing_count = len(state.get("missing_evidence", []))

        recovery_possible = severity >= 0.6 or repeat or low_mileage
        if recovery_possible and missing_count <= 2:
            recommendation = "Prepare supplier recovery packet"
        elif recovery_possible:
            recommendation = "Potential supplier recovery, but collect missing failed part and diagnostic evidence first"
        else:
            recommendation = "Supplier recovery not recommended at this stage"

        state["supplier_recovery_result"] = {
            "supplier_id": part.get("supplier_id"),
            "supplier_name": supplier.get("supplier_name", part.get("supplier_name")),
            "recovery_possible": recovery_possible,
            "recommendation": recommendation,
        }
        append_trace(state, "Supplier Recovery Agent checked low mileage, repeat repair, severity, and evidence completeness.")
        return state

    def decision_node(self, state: WarrantyCaseState) -> WarrantyCaseState:
        warranty = state.get("warranty_rule_result", {})
        supplier = state.get("supplier_recovery_result", {})
        severity = state.get("severity_index", 0.0)
        missing = state.get("missing_evidence", [])

        human_review_required = bool(warranty.get("human_approval_required")) or severity >= 0.65 or len(missing) > 0

        if len(missing) >= 3:
            action = "Hold claim and request missing diagnostic evidence from dealer"
        elif supplier.get("recovery_possible") and severity >= 0.6:
            action = "Prepare evidence packet for supplier recovery review"
        elif not warranty.get("within_coverage", True):
            action = "Route to warranty analyst for policy exception review"
        elif severity >= 0.7:
            action = "Escalate to engineering and warranty manager for high severity review"
        else:
            action = "Approve for normal warranty processing after analyst confirmation"

        state["human_review_required"] = human_review_required
        state["final_recommended_action"] = action
        append_trace(state, "Decision Router selected the next best action and human review requirement.")
        return state

    def evidence_packet_node(self, state: WarrantyCaseState) -> WarrantyCaseState:
        packet = build_evidence_packet(state)
        state["evidence_packet"] = packet
        self.repo.save_evidence_packet(
            claim_id=state["claim_id"],
            evidence_packet=packet,
            final_action=state.get("final_recommended_action", "Review required"),
            confidence=float(state.get("confidence_score", 0.0)),
            severity=float(state.get("severity_index", 0.0)),
        )
        self.repo.save_audit_log(state["claim_id"], "agent_run_completed", dict(state))
        append_trace(state, "Evidence Packet Agent generated and stored the final evidence packet.")
        return state
