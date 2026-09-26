import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient, models
from app.main import app
from app.agents.analytics_agent import analytics_node
from app.agents import rag_agent
from app.agents.orchestrator import orchestrator_app

client = TestClient(app)


@pytest.mark.parametrize(
    ("content", "expected_severity"),
    [
        ("Security breach detected in production.", "critical"),
        ("Service degraded during deployment.", "medium"),
        ("Routine deployment completed.", "low"),
    ],
)
def test_analytics_severity_levels(content, expected_severity):
    result = analytics_node(
        {
            "event_type": "incident",
            "content": content,
            "agents_involved": [],
        }
    )

    assert result["analytics"]["severity"] == expected_severity

def test_healthcheck():
    """Verifica che l'endpoint root sia online."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_process_event_pipeline(monkeypatch):
    """Testa l'orchestrazione end-to-end con agenti MCP e LLM."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("QDRANT_URL", raising=False)
    payload = {
        "event_id": "TEST-2026",
        "source": "GitHubActions",
        "event_type": "build_failure",
        "content": "Pipeline failed during Docker image build step due to missing environment variable."
    }
    
    response = client.post("/process-event", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "TEST-2026"
    assert data["status"] == "success"
    assert "MCP_Log_Agent" in data["agents_involved"]
    assert "RAG_RetrievalAgent" in data["agents_involved"]
    assert "Analytics_Agent" in data["agents_involved"]
    assert "LLM_StandardizerAgent" in data["agents_involved"]
    assert len(data["standardized_context"]) > 0
    assert data["analytics"]["severity"] == "high"
    assert data["analytics"]["content_words"] > 0


def test_process_demo_event_fixture(monkeypatch):
    """Esegue un evento fittizio completo attraverso l'API."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("QDRANT_URL", raising=False)
    fixture_path = Path(__file__).parents[1] / "examples" / "demo_event.json"
    payload = json.loads(fixture_path.read_text())

    response = client.post("/process-event", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "DEMO-2026-001"
    assert data["status"] == "success"
    assert data["analytics"]["source"] == "CustomerSupport"
    assert data["analytics"]["event_type"] == "urgent_escalation"
    assert data["analytics"]["severity"] == "critical"
    assert "production outage" in data["analytics"]["risk_signals"]


def test_process_event_rejects_incomplete_fake_payload():
    response = client.post(
        "/process-event",
        json={
            "event_id": "DEMO-INVALID-001",
            "source": "SyntheticMonitoring",
            "event_type": "health_check",
        },
    )

    assert response.status_code == 422


def test_rag_retrieves_documents_from_qdrant(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "http://qdrant.test")
    monkeypatch.setenv("QDRANT_COLLECTION", "runbooks")

    class FakeQdrantClient:
        def __init__(self, url, api_key):
            assert url == "http://qdrant.test"

        def query_points(self, **kwargs):
            assert kwargs["collection_name"] == "runbooks"
            assert kwargs["query"] == [0.1, 0.2]
            return SimpleNamespace(
                points=[SimpleNamespace(payload={"text": "Docker build recovery steps"})]
            )

    monkeypatch.setattr(rag_agent, "QdrantClient", FakeQdrantClient)
    result = rag_agent.rag_retrieval_node(
        {
            "metadata": {"query_vector": [0.1, 0.2]},
            "agents_involved": [],
        }
    )

    assert result["retrieved_context"] == "Docker build recovery steps"
    assert result["agents_involved"] == ["RAG_RetrievalAgent"]


def test_orchestrator_uses_fake_qdrant_context(monkeypatch):
    query_vector = [0.1, 0.2, 0.3]
    qdrant = QdrantClient(":memory:")
    qdrant.create_collection(
        collection_name="test_runbooks",
        vectors_config=models.VectorParams(
            size=len(query_vector),
            distance=models.Distance.COSINE,
        ),
    )
    qdrant.upsert(
        collection_name="test_runbooks",
        points=[
            models.PointStruct(
                id=1,
                vector=query_vector,
                payload={"text": "Runbook fittizio: verificare la configurazione Docker."},
            )
        ],
    )

    monkeypatch.setenv("QDRANT_URL", "http://qdrant.test")
    monkeypatch.setenv("QDRANT_COLLECTION", "test_runbooks")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(rag_agent, "QdrantClient", lambda **kwargs: qdrant)

    result = orchestrator_app.invoke(
        {
            "event_id": "TEST-RAG-1",
            "source": "pytest",
            "event_type": "build_failure",
            "content": "Docker build failed.",
            "metadata": {"query_vector": query_vector},
            "mcp_logs": "",
            "retrieved_context": "",
            "analytics": {},
            "context": "",
            "agents_involved": [],
        }
    )

    assert result["retrieved_context"] == "Runbook fittizio: verificare la configurazione Docker."
    assert result["analytics"]["severity"] == "high"
    assert "RAG_RetrievalAgent" in result["agents_involved"]