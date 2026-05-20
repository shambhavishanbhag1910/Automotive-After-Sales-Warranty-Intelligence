from __future__ import annotations

from typing import Any, Dict

from app.agents.nodes import WarrantyAgentNodes
from app.agents.state import WarrantyCaseState
from app.services.repository import WarrantyRepository

try:
    from langgraph.graph import END, StateGraph
    LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover
    END = "END"
    StateGraph = None
    LANGGRAPH_AVAILABLE = False


class WarrantyInvestigationGraph:
    """Wrapper around the warranty investigation graph.

    If LangGraph is installed, the workflow uses StateGraph. If not, the same nodes
    run sequentially so that the demo remains easy to execute.
    """

    def __init__(self, repo: WarrantyRepository):
        self.repo = repo
        self.nodes = WarrantyAgentNodes(repo)
        self.graph = self._build_graph() if LANGGRAPH_AVAILABLE else None

    def _build_graph(self):
        workflow = StateGraph(WarrantyCaseState)
        workflow.add_node("claim_intake", self.nodes.claim_intake_node)
        workflow.add_node("data_enrichment", self.nodes.data_enrichment_node)
        workflow.add_node("data_quality", self.nodes.data_quality_node)
        workflow.add_node("vin_history", self.nodes.vin_history_node)
        workflow.add_node("fault_code", self.nodes.fault_code_node)
        workflow.add_node("knowledge_retrieval", self.nodes.knowledge_retrieval_node)
        workflow.add_node("warranty_rule", self.nodes.warranty_rule_node)
        workflow.add_node("severity_scoring", self.nodes.severity_scoring_node)
        workflow.add_node("root_cause", self.nodes.root_cause_node)
        workflow.add_node("supplier_recovery", self.nodes.supplier_recovery_node)
        workflow.add_node("decision", self.nodes.decision_node)
        workflow.add_node("evidence_packet", self.nodes.evidence_packet_node)

        workflow.set_entry_point("claim_intake")
        workflow.add_edge("claim_intake", "data_enrichment")
        workflow.add_edge("data_enrichment", "data_quality")
        workflow.add_edge("data_quality", "vin_history")
        workflow.add_edge("vin_history", "fault_code")
        workflow.add_edge("fault_code", "knowledge_retrieval")
        workflow.add_edge("knowledge_retrieval", "warranty_rule")
        workflow.add_edge("warranty_rule", "severity_scoring")
        workflow.add_edge("severity_scoring", "root_cause")
        workflow.add_edge("root_cause", "supplier_recovery")
        workflow.add_edge("supplier_recovery", "decision")
        workflow.add_edge("decision", "evidence_packet")
        workflow.add_edge("evidence_packet", END)
        return workflow.compile()

    def run(self, claim_id: str) -> Dict[str, Any]:
        initial_state: WarrantyCaseState = {"claim_id": claim_id, "trace": []}
        if self.graph is not None:
            result = self.graph.invoke(initial_state)
        else:  # pragma: no cover
            result = initial_state
            for node in [
                self.nodes.claim_intake_node,
                self.nodes.data_enrichment_node,
                self.nodes.data_quality_node,
                self.nodes.vin_history_node,
                self.nodes.fault_code_node,
                self.nodes.knowledge_retrieval_node,
                self.nodes.warranty_rule_node,
                self.nodes.severity_scoring_node,
                self.nodes.root_cause_node,
                self.nodes.supplier_recovery_node,
                self.nodes.decision_node,
                self.nodes.evidence_packet_node,
            ]:
                result = node(result)
        return dict(result)
