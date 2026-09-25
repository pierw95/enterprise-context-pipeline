# Enterprise Context-Aware Multi-Agent Pipeline

A Python service that accepts enterprise events, enriches them with system-log context, and returns a standardized summary. The current request workflow uses **FastAPI**, **LangGraph**, **LangChain**, and **Groq**; it can also run without a Groq API key using a deterministic fallback.

## Architecture

`POST /process-event` validates an event with Pydantic and passes its fields into a compiled LangGraph workflow. The workflow runs two nodes in sequence:

1. **MCP log enrichment** calls `fetch_system_logs(event_id)` and adds the returned log text to the graph state.
2. **LLM standardization** invokes Groq's `llama-3.1-70b-versatile` model to produce a concise Italian summary. If `GROQ_API_KEY` is missing or the Groq request fails, the node returns a fallback summary containing the event and MCP log details.

```text
Event JSON -> FastAPI/Pydantic -> LangGraph -> MCP log enrichment
                                              -> Groq summary or fallback
                                              -> JSON response
```

### MCP integration status

The repository currently exposes `fetch_system_logs` through a local Python wrapper whose implementation returns a sample response. It demonstrates the tool boundary used by the graph, but it is not yet a networked MCP server or a connection to an external log system. Configure a real MCP transport and backend before using it for production data.

RAG, analytics, Qdrant persistence, and container deployment are not part of the currently implemented request path. They are not required to run the API. This repository is a portfolio implementation, not a production-hardened service.

## Requirements

- Python 3.10 or newer
- A Groq API key for live LLM summaries (optional; fallback mode works without one)

## Setup and run

```bash
git clone https://github.com/pieru95/enterprise-context-pipeline.git
cd enterprise-context-pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To enable Groq, create a `.env` file in the repository root:

```dotenv
GROQ_API_KEY=your_groq_api_key
```

The application loads this file with `python-dotenv`. Keep `.env` out of version control and never expose API keys in logs or source code.

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`; interactive OpenAPI documentation is at `http://localhost:8000/docs`.

## API

`GET /` returns a health response. `POST /process-event` accepts the following JSON fields (`metadata` is optional):

```json
{"event_id":"EVT-9921","source":"CustomerSupport","event_type":"escalation","content":"Customer requests an urgent review of API rate-limit charges."}
```

Example request:

```bash
curl -X POST http://localhost:8000/process-event -H 'Content-Type: application/json' -d '{"event_id":"EVT-9921","source":"CustomerSupport","event_type":"escalation","content":"Customer requests an urgent review of API rate-limit charges."}'
```

The response includes `event_id`, `status`, `standardized_context`, and `agents_involved`. The endpoint currently returns `status: "success"` when the workflow completes, including when the LLM node uses its fallback.

## Tests

Run the API and pipeline tests from the repository root:

```bash
pytest tests/
```

## Repository layout

```text
app/
agents/orchestrator.py  LangGraph workflow and Groq/fallback behavior
main.py                 FastAPI application and endpoints
mcp/server.py           Local system-log tool stub
models/schemas.py       Pydantic request and response models
tests/test_pipeline.py  Health endpoint and event pipeline tests
requirements.txt        Python dependencies
```
