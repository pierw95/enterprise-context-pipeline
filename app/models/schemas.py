from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class EventPayload(BaseModel):
    event_id: str
    source: str
    event_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class ContextResponse(BaseModel):
    event_id: str
    status: str
    standardized_context: str
    agents_involved: List[str]
    analytics: Dict[str, Any]