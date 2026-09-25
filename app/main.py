from fastapi import FastAPI
from app.models.schemas import EventPayload, ContextResponse
from app.agents.orchestrator import orchestrator_app

app = FastAPI(title="Enterprise Context-Aware Pipeline")

@app.get("/")
def read_root():
    return {"status": "online", "system": "Multi-Agent Context Pipeline"}

@app.post("/process-event", response_model=ContextResponse)
def process_event(payload: EventPayload):
    # Inizializziamo lo stato per il grafo LangGraph
    initial_state = {
        "event_id": payload.event_id,
        "source": payload.source,
        "event_type": payload.event_type,
        "content": payload.content,
        "context": "",
        "agents_involved": []
    }
    
    # Esecuzione del Grafo Multi-Agente
    result = orchestrator_app.invoke(initial_state)
    
    return ContextResponse(
        event_id=result["event_id"],
        status="success",
        standardized_context=result["context"],
        agents_involved=result["agents_involved"]
    )