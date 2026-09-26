from typing import Any, Dict, List, TypedDict


class AnalyticsState(TypedDict, total=False):
	source: str
	event_type: str
	content: str
	analytics: Dict[str, Any]
	agents_involved: List[str]


SIGNAL_LEVELS = {
	"critical": ("security breach", "data loss", "ransomware", "production outage"),
	"high": ("failure", "failed", "error", "urgent", "escalation"),
	"medium": ("warning", "degraded", "delay"),
}


def analytics_node(state: AnalyticsState) -> AnalyticsState:
	agents = list(state.get("agents_involved", []))
	agents.append("Analytics_Agent")

	content = state.get("content", "")
	searchable_text = f"{state.get('event_type', '')} {content}".lower()
	risk_signals = [
		signal
		for signals in SIGNAL_LEVELS.values()
		for signal in signals
		if signal in searchable_text
	]
	severity = next(
		(
			level
			for level, signals in SIGNAL_LEVELS.items()
			if any(signal in searchable_text for signal in signals)
		),
		"low",
	)

	return {
		**state,
		"analytics": {
			"source": state.get("source", ""),
			"event_type": state.get("event_type", ""),
			"severity": severity,
			"content_characters": len(content),
			"content_words": len(content.split()),
			"risk_signals": risk_signals,
		},
		"agents_involved": agents,
	}
