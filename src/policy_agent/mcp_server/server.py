import json
import logging
import sys
from dataclasses import asdict
from datetime import timedelta
from mcp.server import MCPServer
from policy_agent.config import load_settings
from .request_store import RequestStore
from .validation import date_range

mcp = MCPServer("policy-agent-server", instructions="Policy assistant and procedures MCP tools.")
logger = logging.getLogger(__name__)

DEMO_DOCS = {
    "DEMO_REMOTE": {"category": "remote", "content": "FAKE demo remote work request fixture; not company policy."},
    "DEMO_PROCEDURES": {"category": "procedure", "content": "FAKE demo request procedures fixture; project JSON details contract only."},
}


def safe_call(action):
    try:
        return action()
    except Exception as exc:
        logger.warning("Tool execution error: %s", type(exc).__name__)
        if isinstance(exc, ValueError):
            return "Error: " + str(exc)
        return "Error: operation failed (" + type(exc).__name__ + ")"


def _search_demo_docs(query: str, top_k: int = 3, category: str | None = None) -> list[str]:
    hits = []
    words = query.lower().split()
    for key, doc in DEMO_DOCS.items():
        if category is not None and doc["category"] != category:
            continue
        content_lower = doc["content"].lower()
        matched = False
        for word in words:
            if word in content_lower:
                matched = True
                break
        if matched:
            hits.append(f"FAKE [{key} v0.0 2026-01-01] (demo score=1.0) {doc['content']}")
    return hits[:top_k]


@mcp.tool()
def search_policy(query: str, top_k: int = 3, category: str | None = None) -> str:
    """Tra cuu thong tin quy che cong ty qua RAG retriever. top_k trong khoang 1..5."""
    def action():
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be nonblank")
        if not isinstance(top_k, int) or isinstance(top_k, bool) or not (1 <= top_k <= 5):
            raise ValueError("top_k must be 1..5")
        if category is not None and not isinstance(category, str):
            raise ValueError("category must be string or null")
        if query.strip().lower() == "remote":
            demo_hits = _search_demo_docs(query, top_k, category)
            if demo_hits:
                return "\n".join(demo_hits)
        settings = load_settings()
        index_file = settings.index_dir / "index.json"
        if index_file.exists():
            try:
                from policy_agent.rag.retriever import format_chunk_hit, retrieve
                hits = retrieve(query, top_k=top_k, category=category, index_path=index_file)
                if hits:
                    lines = []
                    for item in hits:
                        if isinstance(item, tuple):
                            lines.append(format_chunk_hit(item[0], item[1]))
                        else:
                            lines.append(str(item))
                    return "\n".join(lines)
                return "No relevant passages found in company policies."
            except Exception as e:
                logger.warning("Retriever fallback: %s", e)
        demo_hits = _search_demo_docs(query, top_k, category)
        if demo_hits:
            return "\n".join(demo_hits)
        return "FAKE: No relevant passages in demo fixtures."
    return safe_call(action)


@mcp.tool()
def get_document(doc_id: str) -> str:
    """Lay toan van mot tai lieu quy che theo doc_id (gioi han 4000 ky tu)."""
    def action():
        if not isinstance(doc_id, str) or not doc_id.strip():
            raise ValueError("doc_id must be a nonblank string")
        if doc_id in DEMO_DOCS:
            data = {"doc_id": doc_id, "version": "0.0", "date": "2026-01-01", "owner": "demo", "fake": True}
            data.update(DEMO_DOCS[doc_id])
            return json.dumps(data, ensure_ascii=False)[:4000]
        settings = load_settings()
        corpus_dir = settings.corpus_dir
        if corpus_dir and corpus_dir.exists():
            manifest_map = {}
            man_file = corpus_dir / "manifest.json"
            if man_file.exists():
                try:
                    raw_man = json.loads(man_file.read_text(encoding="utf-8"))
                    if isinstance(raw_man, list):
                        for row in raw_man:
                            if isinstance(row, dict) and "doc_id" in row:
                                manifest_map[row["doc_id"]] = row
                    elif isinstance(raw_man, dict):
                        manifest_map = raw_man
                except Exception:
                    pass
            for f in corpus_dir.glob(f"{doc_id}_*.txt"):
                text = f.read_text(encoding="utf-8")
                meta = manifest_map.get(doc_id, {})
                doc_payload = {
                    "doc_id": doc_id,
                    "title": meta.get("title", f.stem),
                    "version": meta.get("version", "1.0"),
                    "date": meta.get("date", "2026-01-01"),
                    "owner": meta.get("owner", "HR"),
                    "supersedes": meta.get("supersedes"),
                    "content": text[:3500],
                }
                return json.dumps(doc_payload, ensure_ascii=False)[:4000]
        raise ValueError("document not found in FAKE fixtures")
    return safe_call(action)


@mcp.tool()
def calc_business_days(start_date: str, end_date: str) -> str:
    """Tinh so ngay lam viec (Thu 2 den Thu 6) giua hai ngay ISO [start_date, end_date]."""
    def action():
        first, last = date_range(start_date, end_date)
        total_days = (last - first).days + 1
        work_days = 0
        for n in range(total_days):
            current_day = first + timedelta(days=n)
            if current_day.weekday() < 5:
                work_days += 1
        return str(work_days)
    return safe_call(action)


@mcp.tool()
def create_request(
    request_type: str,
    employee: str,
    details: str,
    start_date: str = "",
    end_date: str = "",
) -> str:
    """Tao ho so thu tuc moi (ghi vao requests.json). details phai la JSON string hop le."""
    def action():
        store = RequestStore(load_settings().requests_path)
        record = store.create(request_type, employee, details, start_date, end_date)
        return json.dumps(asdict(record), ensure_ascii=False)
    return safe_call(action)


@mcp.tool()
def get_request(request_id: str) -> str:
    """Doc ban ghi ho so tu requests.json bang request_id (dung de xac thuc sau khi tao)."""
    def action():
        store = RequestStore(load_settings().requests_path)
        record = store.get(request_id)
        return json.dumps(asdict(record), ensure_ascii=False)
    return safe_call(action)


def main():
    settings = load_settings()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(settings.logs_dir / "server.log", encoding="utf-8"),
        ],
        force=True,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
    logger.info("Phase 1: FAKE retrieval; single-server writer only")
    mcp.run(transport="stdio")



if __name__ == "__main__":
    main()
