"""Phase 1 FAKE retrieval only. No RAG import; stdout is MCP transport."""
import json
import logging
import sys
from dataclasses import asdict
from datetime import timedelta
from mcp.server import MCPServer
from policy_agent.config import load_settings
from .request_store import RequestStore
from .validation import date_range

mcp = MCPServer("policy-agent-phase1", instructions="FAKE retrieval demo; not real policy.")
logger = logging.getLogger(__name__)
DEMO_DOCS = {
    "DEMO_REMOTE": {"category": "remote", "content": "FAKE demo remote work request fixture; not company policy."},
    "DEMO_PROCEDURES": {"category": "procedure", "content": "FAKE demo request procedures fixture; project JSON details contract only."},
}


def safe(action):
    """Operational errors are strings; log only the exception class."""
    try:
        return action()
    except Exception as exc:
        logger.warning("tool failed: %s", type(exc).__name__)
        if isinstance(exc, ValueError):
            return "Error: " + str(exc)
        return "Error: operation failed (" + type(exc).__name__ + ")"


@mcp.tool()
def search_policy(query: str, top_k: int = 3, category: str | None = None) -> str:
    """FAKE keyword fixtures only, not semantic retrieval. top_k is 1..5."""
    def action():
        if type(query) is not str or not query.strip():
            raise ValueError("query must be nonblank")
        if type(top_k) is not int or not 1 <= top_k <= 5:
            raise ValueError("top_k must be 1..5")
        if category is not None and type(category) is not str:
            raise ValueError("category must be string or null")
        hits = [f"FAKE [{key} v0.0 2026-01-01] (demo score=1.0) {doc['content']}" for key, doc in DEMO_DOCS.items() if (category is None or doc["category"] == category) and any(word in doc["content"].lower() for word in query.lower().split())]
        return "\n".join(hits[:top_k]) or "FAKE: No relevant passages in demo fixtures."
    return safe(action)


@mcp.tool()
def get_document(doc_id: str) -> str:
    """FAKE full demo document with fixture metadata, bounded to 4000 chars."""
    def action():
        if type(doc_id) is not str or doc_id not in DEMO_DOCS:
            raise ValueError("document not found in FAKE fixtures")
        return json.dumps({"doc_id": doc_id, "version": "0.0", "date": "2026-01-01", "owner": "demo", "fake": True, **DEMO_DOCS[doc_id]}, ensure_ascii=False)[:4000]
    return safe(action)


@mcp.tool()
def calc_business_days(start_date: str, end_date: str) -> str:
    """Count Mon-Fri inclusive [start_date,end_date]; no public holidays."""
    def action():
        first, last = date_range(start_date, end_date)
        return str(sum((first + timedelta(days=n)).weekday() < 5 for n in range((last - first).days + 1)))
    return safe(action)


@mcp.tool()
def create_request(request_type: str, employee: str, details: str, start_date: str = "", end_date: str = "") -> str:
    """WRITE demo request. details is a JSON-object string, not free text.

    Required string fields: REMOTE_WORK reason/location; INTL_WORK
    reason/country/office; HARDWARE_PURCHASE reason/item; EXPENSE_CLAIM
    reason/currency/receipt and positive numeric amount; SECURITY_REVIEW
    reason/system/scope. Remote/international require ISO start/end dates.
    Project demo schema only, not validated DOC0102 policy. Read back with get_request.
    """
    def action():
        store = RequestStore(load_settings().requests_path)
        return json.dumps(asdict(store.create(request_type, employee, details, start_date, end_date)), ensure_ascii=False)
    return safe(action)


@mcp.tool()
def get_request(request_id: str) -> str:
    """Read the complete persisted JSON record; use after each successful write."""
    def action():
        return json.dumps(asdict(RequestStore(load_settings().requests_path).get(request_id)), ensure_ascii=False)
    return safe(action)


def main():
    settings = load_settings()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stderr), logging.FileHandler(settings.logs_dir / "server.log", encoding="utf-8")], force=True)
    logger.info("Phase 1: FAKE retrieval; single-server writer only")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
