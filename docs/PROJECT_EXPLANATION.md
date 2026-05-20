# Project Explanation for Interview

## Project name
Agentic AI Warranty Intelligence Platform for Automotive After Sales

## Problem
Automobile OEM after sales teams review thousands of warranty claims. A warranty analyst must manually check the complaint, cause, correction, VIN history, mileage, fault codes, service history, warranty rules, part details, dealer behavior, recalls, technical service bulletins, and supplier responsibility. This creates slow decisions, inconsistent claim handling, weak evidence packets, and missed supplier recovery opportunities.

## Solution
This project creates an Agentic AI decision layer for warranty claim investigation. The claim moves through multiple specialized agents. Each agent performs one clear job and updates a shared case state. The final output is a decision recommendation and an evidence packet for human review.

## Agents

1. Claim Intake Agent
2. Data Enrichment Agent
3. Data Quality Agent
4. VIN History Agent
5. Fault Code Agent
6. Knowledge Retrieval Agent
7. Warranty Rule Agent
8. Severity Scoring Agent
9. Root Cause Agent
10. Supplier Recovery Agent
11. Decision Router
12. Evidence Packet Agent

## Why this is production style

1. It uses structured state across the workflow.
2. It separates business logic into agents.
3. It keeps human approval in the process.
4. It stores audit logs and generated evidence packets.
5. It can run without LLM dependency for stable demo.
6. It can be extended with OpenAI, Azure OpenAI, Gemini, or Claude.
7. It has FastAPI endpoints, database loading, Docker, tests, and dashboard.

## Recommended production extensions

1. Replace SQLite with PostgreSQL.
2. Add pgvector for real semantic search.
3. Add Microsoft SSO and role based access.
4. Add LangSmith or OpenTelemetry tracing.
5. Add PDF evidence packet export.
6. Add CI CD deployment to AWS ECS or Azure Container Apps.
7. Add human feedback based evaluation dataset.
