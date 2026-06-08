## Project Status

### Implemented
- LangGraph-based workflow orchestration
- Warranty-claim intake and enrichment
- VIN-history and repeat-repair analysis
- Fault-code severity interpretation
- TF-IDF retrieval baseline
- Warranty-rule validation
- Supplier-recovery recommendation baseline
- Human-review endpoint
- Evidence-packet generation
- FastAPI backend
- Streamlit analyst dashboard
- Dockerized local setup

### In Progress
- Conditional LangGraph routing
- Semantic retrieval using Qdrant
- Grounded LLM explanation layer
- Golden-case evaluation
- Langfuse observability
- CI/CD workflow

# Agentic AI Warranty Intelligence Platform for Automotive After Sales

This is a runnable MVP for an **automotive after sales Agentic AI project**. It uses a production style workflow for warranty claim investigation, VIN history review, fault code interpretation, warranty rule validation, TSB and recall retrieval, supplier recovery recommendation, human review, and evidence packet generation.

The project is designed for interview explanation, portfolio demo, and extension into a real enterprise system.

## What this project demonstrates

1. Agentic workflow using LangGraph style orchestration
2. FastAPI backend with production style endpoints
3. SQLite local setup by default, with optional PostgreSQL support
4. CSV based data ingestion from a realistic warranty demo dataset
5. Rule based agent reasoning that works without an LLM key
6. RAG style retrieval over TSB, recall, warranty rule, fault code, and parts knowledge
7. Evidence packet generation for warranty analyst review
8. Streamlit dashboard for quick demo
9. Docker and docker compose setup
10. Pytest smoke tests

## Business flow

```text
Warranty claim
  -> Data quality check
  -> VIN history analysis
  -> Fault code interpretation
  -> TSB and recall retrieval
  -> Warranty rule validation
  -> Root cause hypothesis
  -> Supplier recovery check
  -> Human review decision
  -> Evidence packet
```

## Project structure

```text
agentic-automotive-warranty-intelligence/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── schemas.py
│   ├── agents/
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   └── state.py
│   ├── rag/
│   │   └── simple_retriever.py
│   └── services/
│       ├── data_loader.py
│       ├── evidence_packet.py
│       ├── kpi_service.py
│       └── repository.py
├── data/sample/
├── scripts/
│   ├── init_db.py
│   └── run_case.py
├── tests/
├── streamlit_app.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Quick start

### 1. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create environment file

```bash
cp .env.example .env
```

### 4. Load the demo dataset

```bash
python scripts/init_db.py
```

This creates a local SQLite database at:

```text
data/warranty_ai.db
```

### 5. Run one agent case from command line

```bash
python scripts/run_case.py C0001
```

Try these claim IDs also:

```bash
python scripts/run_case.py C0002
python scripts/run_case.py C0010
python scripts/run_case.py C0016
```

### 6. Start FastAPI

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

```text
http://localhost:8000/docs
```

### 7. Run Streamlit dashboard

Open a second terminal and run:

```bash
streamlit run streamlit_app.py
```

## Main API endpoints

```text
GET  /health
GET  /kpis
GET  /claims
GET  /claims/{claim_id}
POST /claims/{claim_id}/run-agent
GET  /claims/{claim_id}/evidence-packet
POST /claims/{claim_id}/human-review
```

## Example API call

```bash
curl -X POST http://localhost:8000/claims/C0001/run-agent
```

## Optional PostgreSQL setup

For local demo, SQLite is enough. For production style deployment, set PostgreSQL in `.env`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/warranty_ai
```

Then install PostgreSQL driver:

```bash
pip install psycopg2-binary
```

Then run:

```bash
python scripts/init_db.py
```

## Docker run

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000/docs
```

## How to explain this project in an interview

This project simulates a real automotive OEM after sales warranty intelligence process. The system takes a warranty claim as input and uses multiple specialized agents to inspect the VIN history, service history, fault codes, warranty eligibility, technical service bulletins, recalls, dealer quality, part supplier details, and missing evidence. It then creates a root cause hypothesis, recommends whether the claim should be approved, held, escalated to engineering, or prepared for supplier recovery, and generates a structured evidence packet for human review.

The first version runs using deterministic business logic so that the demo is explainable and stable. An LLM can be added later for richer natural language reasoning, but the production control points remain the same: structured state, conditional routing, human approval, audit trail, evaluation, and monitoring.

## Recommended next enhancements

1. Add OpenAI or Azure OpenAI for natural language root cause explanation
2. Replace simple keyword retriever with pgvector or Pinecone
3. Add authentication with Microsoft Entra ID
4. Add role based access control for warranty analyst, dealer, supplier quality, and warranty manager
5. Add LangSmith or OpenTelemetry for graph tracing and observability
6. Add CI CD deployment to AWS ECS, Azure Container Apps, or Kubernetes
7. Add PDF evidence packet export
8. Add model evaluation using golden cases from `agent_cases.csv`
