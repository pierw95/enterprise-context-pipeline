# Enterprise Context-Aware Multi-Agent Pipeline

**A scalable, event-driven multi-agent architecture for standardizing enterprise context across heterogeneous data sources.** Built with **LangGraph**, **FastAPI**, **Qdrant Vector DB** and **Docker**.

---

## Overview

In modern enterprise environments, raw context (logs, support tickets, emails, customer interactions) arrives in unstructured and fragmented formats. This repository provides a production-grade, event-driven pipeline that ingests event payloads, routes them through specialized LLM agents via **LangGraph**, enriches the context using a Vector Database (RAG), and produces standardized JSON outputs for executive decision-making and downstream consumption.

---

## Key Features

- **Multi-Agent Orchestration:** Powered by LangGraph for deterministic state management and agent routing (`RouterAgent`, `RAGAgent`, `AnalyticsAgent`).
- **High-Performance REST API:** Built with FastAPI and Pydantic v2 for schema validation and async request handling.
- **Vector Search Integration:** Native integration with Qdrant Vector DB for sub-second context retrieval and semantic search.
- **Production-Ready CI/CD:** GitHub Actions automated workflow running test suites (`pytest`) and code quality checks on every push.
- **Containerized Deployment:** Fully Dockerized application ready for cloud-native deployment (GCP Vertex AI / Azure App Service / AWS ECS).

---

## System Architecture

The system ingests raw event payloads via a FastAPI endpoint, converts them into a shared `AgentState`, and routes them through a compiled LangGraph workflow:

```text
[Incoming Event Payload]
          │
          ▼
   [FastAPI Endpoint]
          │
          ▼
   [LangGraph State]
          │
          ├─────────────────────────┐
          ▼                         ▼
   [Router Agent] ───────► [RAG / Vector DB Agent]
          │                         │
          └─────────────────────────┘
          │
          ▼
[Standardized Context Response]

Category,Technologies
Orchestration & AI,"LangGraph, LangChain, Groq API (Llama 3), OpenAI APIs"
Backend API,"FastAPI, Uvicorn, Pydantic v2"
Vector Database,Qdrant Cloud / Local Cluster
DevOps & Testing,"Docker, Pytest, GitHub Actions (CI/CD), GitHub Codespaces"

Project Structure
enterprise-context-pipeline/
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # GitHub Actions CI/CD Pipeline
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI Application & Endpoints
│   ├── core/                  # Configurations & DB Connections
│   │   ├── config.py
│   │   └── database.py
│   ├── agents/                # LangGraph Agent Nodes & Workflows
│   │   ├── orchestrator.py    # Main LangGraph Graph Definition
│   │   ├── rag_agent.py       # RAG Retrieval Node
│   │   └── analytics_agent.py # Analytics / Metric Node
│   └── models/                # Pydantic Schemas
│       └── schemas.py
├── tests/                     # Unit & Integration Tests
│   └── test_pipeline.py
├── Dockerfile
├── requirements.txt
└── README.md

Quick Start
1. Clone & Set Up Environment
git clone [https://github.com/pieru95/enterprise-context-pipeline.git](https://github.com/pieru95/enterprise-context-pipeline.git)
cd enterprise-context-pipeline
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

2. Run Local Server
uvicorn app.main:app --reload

Access the interactive Swagger API documentation at http://localhost:8000/docs.

3. Sample API Request
curl -X 'POST' \
  'http://localhost:8000/process-event' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "event_id": "EVT-9921",
  "source": "CustomerSupport",
  "event_type": "escalation",
  "content": "Customer requesting urgent refund for API rate limit overages."
}'

Testing
Run the test suite using pytest: pytest tests/

Author & License
Developed as an enterprise-grade AI Architecture portfolio project.
