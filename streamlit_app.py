from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from app.agents.graph import WarrantyInvestigationGraph
from app.config import get_settings
from app.db import get_engine
from app.services.data_loader import database_has_claims, load_csv_folder_to_database
from app.services.kpi_service import get_kpis
from app.services.repository import WarrantyRepository

st.set_page_config(page_title="Warranty Intelligence", layout="wide")

engine = get_engine()
settings = get_settings()
if not database_has_claims(engine):
    load_csv_folder_to_database(engine, Path(settings.sample_data_dir))
repo = WarrantyRepository(engine)

st.title("Agentic AI Warranty Intelligence Platform")
st.caption("Automotive after sales claim investigation demo")

kpis = get_kpis(engine)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Claims", kpis["total_claims"])
col2.metric("Total Warranty Cost", f"${kpis['total_claim_amount_usd']:,.0f}")
col3.metric("High Risk Claims", kpis["high_risk_claims"])
col4.metric("Repeat Repairs", kpis["repeat_repair_claims"])

st.subheader("Claims Workbench")
claims = repo.list_claims(limit=100)
claims_df = pd.DataFrame(claims)
st.dataframe(claims_df, use_container_width=True)

claim_ids = claims_df["claim_id"].tolist() if not claims_df.empty else []
selected_claim = st.selectbox("Select claim to investigate", claim_ids)

if selected_claim:
    if st.button("Run Agent Investigation", type="primary"):
        graph = WarrantyInvestigationGraph(repo)
        result = graph.run(selected_claim)
        st.session_state["last_result"] = result

result = st.session_state.get("last_result")
if result:
    st.subheader("Agent Recommendation")
    a, b, c = st.columns(3)
    a.metric("Severity Index", result.get("severity_index"))
    b.metric("Confidence", result.get("confidence_score"))
    c.metric("Human Review", "Yes" if result.get("human_review_required") else "No")

    st.write("**Recommended next action:**", result.get("final_recommended_action"))
    st.write("**Root cause hypothesis:**", result.get("root_cause_hypothesis"))

    st.write("**Missing evidence:**")
    st.write(result.get("missing_evidence") or ["No major evidence gap"])

    st.write("**Agent trace:**")
    for step in result.get("trace", []):
        st.write(f"- {step}")

    st.subheader("Evidence Packet")
    st.markdown(result.get("evidence_packet", ""))
