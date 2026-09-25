from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# Definiamo lo Stato del Grafo
class AgentState(TypedDict):
    event_id: str
    source: str
    event_type: str
    content: str
    context: str
    agents_involved: List[str]

# Nodo 1: Agente di Analisi e Routing
def router_agent(state: AgentState) -> AgentState:
    agents = state.get("agents_involved", [])
    agents.append("RouterAgent")
    
    # Esempio di routing condizionale basato sul tipo di evento
    content_upper = state["content"].upper()
    return {
        **state,
        "agents_involved": agents
    }

# Nodo 2: Agente RAG / Documentale
def rag_agent(state: AgentState) -> AgentState:
    agents = state.get("agents_involved", [])
    agents.append("RAGAgent")
    
    context = f"[RAG Enriched]: Standardized document context for event '{state['event_id']}'."
    return {
        **state,
        "context": context,
        "agents_involved": agents
    }

# Costruzione del Grafo LangGraph
def build_orchestrator():
    workflow = StateGraph(AgentState)
    
    # Aggiunta dei Nodi
    workflow.add_node("router", router_agent)
    workflow.add_node("rag", rag_agent)
    
    # Definizione del Flusso (Edges)
    workflow.set_entry_point("router")
    workflow.add_edge("router", "rag")
    workflow.add_edge("rag", END)
    
    return workflow.compile()

# Istanza compilata della pipeline
orchestrator_app = build_orchestrator()