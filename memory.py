"""Thin wrapper around Hindsight: retain incidents + feedback, recall similar ones."""
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "incident-response")

_client = None


def client() -> Hindsight:
    global _client
    if _client is None:
        kwargs = {"base_url": os.environ["HINDSIGHT_BASE_URL"]}
        if os.getenv("HINDSIGHT_API_KEY"):
            kwargs["api_key"] = os.environ["HINDSIGHT_API_KEY"]
        _client = Hindsight(**kwargs)
    return _client


def _format_incident(inc: dict) -> str:
    return (
        f"Incident {inc['id']} on service '{inc['service']}' (severity {inc.get('severity', 'n/a')}).\n"
        f"Symptoms: {inc['symptoms']}\n"
        f"Log snippet: {inc.get('log', 'n/a')}\n"
        f"Root cause: {inc['root_cause']}\n"
        f"Fix applied: {inc['fix']}\n"
        f"Outcome: {inc.get('outcome', 'resolved')}. "
        f"Time to resolve: {inc.get('minutes_to_resolve', 'n/a')} minutes."
    )


def retain_incident(inc: dict) -> None:
    """Store a resolved incident."""
    client().retain(
        bank_id=BANK_ID,
        content=_format_incident(inc),
        context="resolved production incident",
        timestamp=inc.get("timestamp") or datetime.now(timezone.utc).isoformat(),
    )


def retain_feedback(incident_id: str, service: str, suggested_fix: str, worked: bool, note: str = "") -> None:
    """Store whether a suggested fix worked, so future recalls favour proven fixes."""
    verdict = "WORKED" if worked else "FAILED"
    client().retain(
        bank_id=BANK_ID,
        content=(
            f"Feedback for incident {incident_id} on service '{service}': "
            f"the suggested fix '{suggested_fix}' {verdict}. {note}"
        ).strip(),
        context="engineer feedback on suggested fix",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def recall_similar(alert_text: str, limit: int = 5) -> list[str]:
    """Return the most relevant past incident/feedback memories for a new alert."""
    res = client().recall(bank_id=BANK_ID, query=alert_text)
    return [r.text for r in res.results[:limit]]


def reflect_patterns(question: str = "What recurring patterns or risky changes appear across our past incidents?") -> str:
    """Ask Hindsight to synthesise patterns across all stored incidents."""
    ans = client().reflect(bank_id=BANK_ID, query=question)
    return getattr(ans, "text", str(ans))
