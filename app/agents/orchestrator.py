import os
from typing import Any, Dict, List, TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.mcp.server import fetch_system_logs
from app.agents.rag_agent import rag_retrieval_node
from app.agents.analytics_agent import analytics_node

load_dotenv()

class AgentState(TypedDict):
    event_id: str
    source: str
    event_type: str
    content: str
    metadata: Dict[str, Any]
    mcp_logs: str
    retrieved_context: str
    analytics: Dict[str, Any]
    context: str
    agents_involved: List[str]

def mcp_enrichment_node(state: AgentState) -> AgentState:
    agents = list(state.get("agents_involved", []))
    agents.append("MCP_Log_Agent")
    logs = fetch_system_logs(state["event_id"])
    return {
        **state,
        "mcp_logs": logs,
        "agents_involved": agents
    }

def llm_standardizer_node(state: AgentState) -> AgentState:
    agents = list(state.get("agents_involved", []))
    agents.append("LLM_StandardizerAgent")
    
    groq_api_key = os.getenv("GROQ_API_KEY")

    if groq_api_key and groq_api_key.strip() != "":
        try:
            llm = ChatGroq(
                model_name="llama-3.1-70b-versatile",
                groq_api_key=groq_api_key,
                temperature=0.1
            )

            prompt = f"""
            Sei un AI Assistant enterprise specializzato nel normalizzare gli eventi aziendali.

            Dati dell'evento:
            - Event ID: {state['event_id']}
            - Fonte: {state['source']}
            - Tipo Evento: {state['event_type']}
            - Contenuto Grezzo: {state['content']}
            - Dettagli MCP: {state['mcp_logs']}
            - Contesto recuperato da RAG: {state['retrieved_context'] or 'Nessun documento disponibile.'}
            - Analisi deterministica: {state['analytics']}

            Fornisci una sintesi del contesto in formato chiaro, professionale e in lingua italiana (max 3 frasi).
            """

            response = llm.invoke([
                SystemMessage(content="Sei un sistema di arricchimento ed elaborazione contesto Enterprise."),
                HumanMessage(content=prompt)
            ])
            standardized_text = str(response.content)
        except Exception as e:
            # In caso di errore API Groq, usa il fallback e mostra l'errore nei log
            print(f"[GROQ ERROR]: {e}")
            standardized_text = (
                f"[FALLBACK DUE TO API ERROR]: Evento {state['event_id']} elaborato. "
                f"Severità stimata: {state['analytics']['severity']}. "
                f"Dettagli MCP: {state['mcp_logs']}"
            )
    else:
        standardized_text = (
            f"[GENERIC FALLBACK]: Evento {state['event_id']} da {state['source']} elaborato. "
            f"Severità stimata: {state['analytics']['severity']}. "
            f"Dettagli MCP: {state['mcp_logs']}"
        )

    return {
        **state,
        "context": standardized_text,
        "agents_involved": agents
    }

def build_orchestrator():
    workflow = StateGraph(AgentState)
    workflow.add_node("mcp_enricher", mcp_enrichment_node)
    workflow.add_node("rag_retriever", rag_retrieval_node)
    workflow.add_node("analytics", analytics_node)
    workflow.add_node("llm_standardizer", llm_standardizer_node)
    workflow.set_entry_point("mcp_enricher")
    workflow.add_edge("mcp_enricher", "rag_retriever")
    workflow.add_edge("rag_retriever", "analytics")
    workflow.add_edge("analytics", "llm_standardizer")
    workflow.add_edge("llm_standardizer", END)
    return workflow.compile()

orchestrator_app = build_orchestrator()