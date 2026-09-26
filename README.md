# Enterprise Context-Aware Multi-Agent Pipeline

A Python service that accepts enterprise events, enriches them with system-log and knowledge-base context, calculates deterministic event analytics, and returns a standardized summary. The request workflow uses **FastAPI**, **LangGraph**, **Qdrant**, and optionally **Groq**.

## Architecture

`POST /process-event` validates an event with Pydantic and passes its fields into a compiled LangGraph workflow. The workflow runs four nodes in sequence:

1. **MCP log enrichment** calls `fetch_system_logs(event_id)` and adds the returned log text to the graph state.
2. **RAG retrieval** searches a configured Qdrant collection when the request includes `metadata.query_vector`; retrieved text is passed to the summarizer.
3. **Analytics** calculates content length, word count, detected risk signals, and a rule-based severity (`low`, `medium`, `high`, or `critical`).
4. **LLM standardization** invokes Groq's `llama-3.1-70b-versatile` model to produce a concise Italian summary using the event, MCP logs, retrieved context, and analytics. If `GROQ_API_KEY` is missing or the Groq request fails, the node returns a deterministic fallback summary.

```text
Event JSON -> FastAPI/Pydantic -> LangGraph -> MCP logs -> Qdrant RAG
                                              -> analytics -> Groq/fallback
                                              -> JSON response
```

### Integration notes

The repository exposes `fetch_system_logs` through a local Python wrapper that currently returns a sample response; it demonstrates the tool boundary but is not a networked MCP server or an external log integration.

RAG is optional. It requires a populated Qdrant collection and a query vector in `metadata.query_vector`, generated upstream with the same embedding model and vector dimensions used to index the collection. Set `QDRANT_URL`; optional settings are `QDRANT_API_KEY`, `QDRANT_COLLECTION` (default `enterprise_knowledge`), and `QDRANT_TEXT_FIELD` (default `text`). If Qdrant or a query vector is unavailable, the pipeline continues without retrieved documents.

Analytics severity is a simple keyword heuristic, not a calibrated risk model. Validate it against your event taxonomy before using it for operational decisions. This repository is a portfolio implementation, not a production-hardened service.

## Requirements

- Python 3.10 or newer
- A Groq API key for live LLM summaries (optional; fallback mode works without one)
- A Qdrant instance and populated collection for retrieval (optional)

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

The application loads this file with `python-dotenv`. Keep `.env` out of version control and never expose API keys in logs or source code. To enable Qdrant retrieval, configure these values as well:

```dotenv
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=enterprise_knowledge
QDRANT_TEXT_FIELD=text
```

Send the precomputed query vector with an event in `metadata.query_vector`. The vector must match the embedding model and dimensions used by the collection. This service does not currently embed text or ingest documents.

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

A reproducible fictional CustomerSupport event is available at `examples/demo_event.json`:

```bash
curl -X POST http://localhost:8000/process-event \
    -H 'Content-Type: application/json' \
    --data @examples/demo_event.json
```

Without `GROQ_API_KEY` or Qdrant, the request still completes using the deterministic fallback and returns `status: "success"`.

The response includes `event_id`, `status`, `standardized_context`, `agents_involved`, and an `analytics` object. The endpoint returns `status: "success"` when the workflow completes, including when optional retrieval or the LLM uses its fallback.

## Tests

Run the API and pipeline tests from the repository root:

```bash
pytest tests/
```

## Docker

Build and run the API container (without Groq, the deterministic fallback is used):

```bash
docker build -t enterprise-context-pipeline .
docker run --rm -p 8000:8000 enterprise-context-pipeline
```

Pass `GROQ_API_KEY` and the Qdrant settings to the container at runtime when needed; do not bake secrets into the image.

## Repository layout

```text
app/
agents/orchestrator.py  LangGraph workflow and Groq/fallback behavior
agents/rag_agent.py     Optional Qdrant retrieval node
agents/analytics_agent.py  Deterministic event metrics and severity
main.py                 FastAPI application and endpoints
mcp/server.py           Local system-log tool stub
models/schemas.py       Pydantic request and response models
Dockerfile              Container image definition
tests/test_pipeline.py  Health endpoint and event pipeline tests
requirements.txt        Python dependencies
```
