from __future__ import annotations

from typing import Any, Dict, List


def format_money(value: Any) -> str:
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "$0.00"


def build_evidence_packet(state: Dict[str, Any]) -> str:
    claim = state.get("claim_data", {}) or {}
    vehicle = state.get("vehicle_data", {}) or {}
    part = state.get("part_data", {}) or {}
    dealer = state.get("dealer_data", {}) or {}
    supplier = state.get("supplier_data", {}) or {}
    fault_codes: List[Dict[str, Any]] = state.get("fault_codes", []) or []
    service_history: List[Dict[str, Any]] = state.get("service_history", []) or []
    knowledge = state.get("knowledge_matches", []) or []
    missing = state.get("missing_evidence", []) or []

    fault_summary = "\n".join(
        [f"- {f.get('dtc_code')}: {f.get('dtc_description')} | severity: {f.get('severity')} | occurrence: {f.get('occurrence_count')}" for f in fault_codes[:5]]
    ) or "- No fault code found for this repair order."

    service_summary = "\n".join(
        [f"- {s.get('visit_date')}: {s.get('customer_complaint')} | diagnosis: {s.get('diagnosis')} | outcome: {s.get('repair_outcome')}" for s in service_history[:5]]
    ) or "- No prior service history found."

    knowledge_summary = "\n".join(
        [f"- {k.get('_source_table', 'knowledge')}: {k.get('tsb_id') or k.get('campaign_id') or k.get('rule_id') or k.get('part_number') or k.get('dtc_code')} | score: {k.get('retrieval_score')}" for k in knowledge[:6]]
    ) or "- No relevant knowledge article retrieved."

    missing_summary = "\n".join([f"- {item}" for item in missing]) or "- No major missing evidence identified."

    return f"""# Evidence Packet: {claim.get('claim_id')}

## 1. Claim Summary
- VIN: {claim.get('vin')}
- Repair order: {claim.get('repair_order_id')}
- Part: {claim.get('part_name')} ({claim.get('part_number')})
- System: {claim.get('system')}
- Claim amount: {format_money(claim.get('claim_amount_usd'))}
- Mileage at claim: {claim.get('mileage_at_claim')}
- Months in service: {claim.get('months_in_service')}
- Dealer: {dealer.get('dealer_name', claim.get('dealer_id'))}
- Current claim status: {claim.get('claim_status')}

## 2. Customer Complaint, Cause, and Correction
- Complaint: {claim.get('complaint')}
- Cause: {claim.get('cause')}
- Correction: {claim.get('correction')}

## 3. Vehicle Context
- Make and model: {vehicle.get('make')} {vehicle.get('model')} {vehicle.get('model_year')}
- Engine family: {vehicle.get('engine_family')}
- Application: {vehicle.get('application')}
- Fleet segment: {vehicle.get('fleet_segment')}
- Plant: {vehicle.get('plant')}

## 4. Fault Code Evidence
{fault_summary}

## 5. Service History Evidence
{service_summary}

## 6. Retrieved Technical and Warranty Knowledge
{knowledge_summary}

## 7. Part and Supplier Context
- Supplier: {supplier.get('supplier_name', part.get('supplier_name'))}
- Supplier quality rating: {supplier.get('supplier_quality_rating')}
- Unit cost: {format_money(part.get('unit_cost_usd'))}
- Warranty coverage: {part.get('warranty_coverage_months')} months / {part.get('warranty_coverage_miles')} miles
- Failure notes: {part.get('failure_mode_notes')}

## 8. Agent Reasoning Summary
- Severity index: {state.get('severity_index')}
- Confidence score: {state.get('confidence_score')}
- Human review required: {state.get('human_review_required')}
- Root cause hypothesis: {state.get('root_cause_hypothesis')}
- Supplier recovery: {state.get('supplier_recovery_result', {}).get('recommendation')}

## 9. Missing Evidence Checklist
{missing_summary}

## 10. Recommended Next Action
{state.get('final_recommended_action')}
"""
