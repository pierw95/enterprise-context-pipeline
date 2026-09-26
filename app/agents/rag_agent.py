import logging
import os
from typing import Any, Dict, List, TypedDict

from qdrant_client import QdrantClient


logger = logging.getLogger(__name__)


class RagState(TypedDict, total=False):
	metadata: Dict[str, Any]
	retrieved_context: str
	agents_involved: List[str]


def rag_retrieval_node(state: RagState) -> RagState:
	agents = list(state.get("agents_involved", []))
	agents.append("RAG_RetrievalAgent")

	qdrant_url = os.getenv("QDRANT_URL", "").strip()
	metadata = state.get("metadata") or {}
	query_vector = metadata.get("query_vector")
	if not qdrant_url or not isinstance(query_vector, list) or not query_vector:
		return {
			**state,
			"retrieved_context": "",
			"agents_involved": agents,
		}

	try:
		client = QdrantClient(
			url=qdrant_url,
			api_key=os.getenv("QDRANT_API_KEY") or None,
		)
		response = client.query_points(
			collection_name=os.getenv("QDRANT_COLLECTION", "enterprise_knowledge"),
			query=query_vector,
			limit=3,
			with_payload=True,
		)
		text_field = os.getenv("QDRANT_TEXT_FIELD", "text")
		documents = [
			str(point.payload[text_field]).strip()
			for point in response.points
			if point.payload and point.payload.get(text_field)
		]
		retrieved_context = "\n".join(documents)
	except Exception:
		logger.exception("Qdrant retrieval failed for event %s", state.get("event_id"))
		retrieved_context = ""

	return {
		**state,
		"retrieved_context": retrieved_context,
		"agents_involved": agents,
	}
