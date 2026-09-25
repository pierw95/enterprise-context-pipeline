import os
from typing import TypedDict, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.mcp.server import fetch_system_logs

load_dotenv()

class AgentState(TypedDict):
    event_id: str
    source: str
    event_type: str
    content: str
    mcp_logs: str
    context: str
    agents_involved: List[str]

def mcp_enrichment_node(state: AgentState) -> AgentState:
    agents = state.get("agents_involved", [])
    agents.append("MCP_Log_Agent")
    logs = fetch_system_logs(state["event_id"])
    return {
        **state,
        "mcp_logs": logs,
        "agents_involved": agents
    }

def llm_standardizer_node(state: AgentState) -> AgentState:
    agents = state.get("agents_involved", [])
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
            standardized_text = f"[FALLBACK DUE TO API ERROR]: Evento {state['event_id']} elaborato correttamente. Dettagli MCP: {state['mcp_logs']}"
    else:
        standardized_text = f"[GENERIC FALLBACK]: Evento {state['event_id']} da {state['source']} elaborato con successo. Dettagli MCP: {state['mcp_logs']}"

    return {
        **state,
        "context": standardized_text,
        "agents_involved": agents
    }

def build_orchestrator():
    workflow = StateGraph(AgentState)
    workflow.add_node("mcp_enricher", mcp_enrichment_node)
    workflow.add_node("llm_standardizer", llm_standardizer_node)
    workflow.set_entry_point("mcp_enricher")
    workflow.add_edge("mcp_enricher", "llm_standardizer")
    workflow.add_edge("llm_standardizer", END)
    return workflow.compile()

orchestrator_app = build_orchestrator()