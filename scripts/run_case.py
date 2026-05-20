from pathlib import Path
import sys
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.graph import WarrantyInvestigationGraph
from app.db import get_engine
from app.services.data_loader import database_has_claims, load_csv_folder_to_database
from app.config import get_settings
from app.services.repository import WarrantyRepository


def main() -> None:
    claim_id = sys.argv[1] if len(sys.argv) > 1 else "C0001"
    engine = get_engine()
    settings = get_settings()
    if not database_has_claims(engine):
        load_csv_folder_to_database(engine, Path(settings.sample_data_dir))
    repo = WarrantyRepository(engine)
    graph = WarrantyInvestigationGraph(repo)
    result = graph.run(claim_id)
    output = {
        "claim_id": result.get("claim_id"),
        "vin": result.get("vin"),
        "severity_index": result.get("severity_index"),
        "confidence_score": result.get("confidence_score"),
        "human_review_required": result.get("human_review_required"),
        "final_recommended_action": result.get("final_recommended_action"),
        "root_cause_hypothesis": result.get("root_cause_hypothesis"),
        "missing_evidence": result.get("missing_evidence"),
        "supplier_recovery_result": result.get("supplier_recovery_result"),
        "trace": result.get("trace"),
    }
    print(json.dumps(output, indent=2, default=str))
    print("\n--- Evidence Packet Preview ---\n")
    print(result.get("evidence_packet", ""))


if __name__ == "__main__":
    main()
