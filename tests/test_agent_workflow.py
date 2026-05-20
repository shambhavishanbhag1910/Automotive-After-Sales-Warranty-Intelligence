from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.graph import WarrantyInvestigationGraph
from app.config import get_settings
from app.db import get_engine
from app.services.data_loader import database_has_claims, load_csv_folder_to_database
from app.services.repository import WarrantyRepository


def test_agent_workflow_generates_evidence_packet():
    engine = get_engine()
    settings = get_settings()
    if not database_has_claims(engine):
        load_csv_folder_to_database(engine, Path(settings.sample_data_dir))
    repo = WarrantyRepository(engine)
    graph = WarrantyInvestigationGraph(repo)
    result = graph.run("C0001")
    assert result["claim_id"] == "C0001"
    assert result["evidence_packet"]
    assert "Evidence Packet" in result["evidence_packet"]
    assert result["final_recommended_action"]
    assert isinstance(result["missing_evidence"], list)
