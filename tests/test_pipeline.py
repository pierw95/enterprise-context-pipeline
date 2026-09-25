from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_healthcheck():
    """Verifica che l'endpoint root sia online."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_process_event_pipeline():
    """Testa l'orchestrazione end-to-end con agenti MCP e LLM."""
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
    assert "LLM_StandardizerAgent" in data["agents_involved"]
    assert len(data["standardized_context"]) > 0