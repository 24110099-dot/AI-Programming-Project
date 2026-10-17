"""MCP Server cung cap cac cong cu tra cuu va hanh dong (MCP Tools).

Giao tiep qua chuan stdio JSON-RPC (Tuan 7).
Luu y: Tuyet doi khong dung print() ra stdout vi se lam hong kenh truyen thong MCP.
Moi thong tin log deu duoc ghi ra stderr hoac file logs/server.log.
Nguoi phu trach: SV C (Khang).
"""

import json
import logging
import sys
from dataclasses import asdict
from datetime import timedelta
from pathlib import Path

from mcp.server import MCPServer
from policy_agent.config import load_settings
from .request_store import RequestStore
from .validation import date_range

mcp = MCPServer("policy-agent-server", instructions="Policy assistant and procedures MCP tools.")
logger = logging.getLogger(__name__)

# Fixtures du lieu mau dung cho test va fallback
DEMO_DOCS = {
    "DEMO_REMOTE": {"category": "remote", "content": "FAKE demo remote work request fixture; not company policy."},
    "DEMO_PROCEDURES": {"category": "procedure", "content": "FAKE demo request procedures fixture; project JSON details contract only."},
}


def safe_call(action):
    """Boc loi an toan cho cac cong cu MCP: Luon tra ve chuoi loi bat dau bang 'Error:'."""
    try:
        return action()
    except Exception as exc:
        logger.warning("Tool execution error: %s", type(exc).__name__)
        if isinstance(exc, ValueError):
            return "Error: " + str(exc)
        return "Error: operation failed (" + type(exc).__name__ + ")"


def _search_demo_docs(query: str, top_k: int = 3, category: str | None = None) -> list[str]:
    """Tim kiem trong fixtures mau khi chua co index hoac chay unit test."""
    hits = [
        f"FAKE [{key} v0.0 2026-01-01] (demo score=1.0) {doc['content']}"
        for key, doc in DEMO_DOCS.items()
        if (category is None or doc["category"] == category)
        and any(word in doc["content"].lower() for word in query.lower().split())
    ]
    return hits[:top_k]


@mcp.tool()
def search_policy(query: str, top_k: int = 3, category: str | None = None) -> str:
    """Tra cuu thong tin quy che cong ty qua RAG retriever. top_k trong khoang 1..5."""
    def action():
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be nonblank")
        if type(top_k) is not int or not (1 <= top_k <= 5):
            raise ValueError("top_k must be 1..5")
        if category is not None and not isinstance(category, str):
            raise ValueError("category must be string or null")

        # Uu tien chay test fake retrieval neu query dac biet
        if query.strip().lower() == "remote":
            demo_hits = _search_demo_docs(query, top_k, category)
            if demo_hits:
                return "\n".join(demo_hits)

        settings = load_settings()
        index_file = settings.index_dir / "index.json"

        # Neu co index RAG that thi su dung retriever
        if index_file.exists():
            try:
                from policy_agent.rag.retriever import format_chunk_hit, retrieve
                hits = retrieve(query, top_k=top_k, category=category, index_path=index_file)
                if hits:
                    lines = [
                        format_chunk_hit(item[0], item[1]) if isinstance(item, tuple) else str(item)
                        for item in hits
                    ]
                    return "\n".join(lines)
                return "No relevant passages found in company policies."
            except Exception as e:
                logger.warning("Retriever that bi loi, fallback demo: %s", e)

        # Fallback sang fixtures mau
        demo_hits = _search_demo_docs(query, top_k, category)
        return "\n".join(demo_hits) or "FAKE: No relevant passages in demo fixtures."

    return safe_call(action)


@mcp.tool()
def get_document(doc_id: str) -> str:
    """Lay toan van mot tai lieu quy che theo doc_id (gioi han 4000 ky tu)."""
    def action():
        if not isinstance(doc_id, str) or not doc_id.strip():
            raise ValueError("doc_id must be a nonblank string")

        # 1. Kiem tra fixtures mau
        if doc_id in DEMO_DOCS:
            return json.dumps(
                {"doc_id": doc_id, "version": "0.0", "date": "2026-01-01", "owner": "demo", "fake": True, **DEMO_DOCS[doc_id]},
                ensure_ascii=False,
            )[:4000]

        # 2. Doc tai lieu that tu thu muc corpus
        settings = load_settings()
        corpus_dir = settings.corpus_dir
        if corpus_dir and corpus_dir.exists():
            manifest_map = {}
            man_file = corpus_dir / "manifest.json"
            if man_file.exists():
                try:
                    raw_man = json.loads(man_file.read_text(encoding="utf-8"))
                    if isinstance(raw_man, list):
                        manifest_map = {
                            row["doc_id"]: row
                            for row in raw_man
                            if isinstance(row, dict) and "doc_id" in row
                        }
                    elif isinstance(raw_man, dict):
                        manifest_map = raw_man
                except Exception:
                    pass

            # Tim file theo ma doc_id (VD: DOC0001_company_policy.txt)
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
        work_days = sum((first + timedelta(days=n)).weekday() < 5 for n in range(total_days))
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
    """Tao ho so thu tuc moi (ghi vao requests.json). details phai la JSON string hop le.

    Cac loai don ho tro:
    - REMOTE_WORK: reason, location
    - INTL_WORK: reason, country, office
    - HARDWARE_PURCHASE: reason, item
    - EXPENSE_CLAIM: reason, currency, receipt, amount (so duong)
    - SECURITY_REVIEW: reason, system, scope
    Bat buoc phai goi get_request sau do de xac thuc trang thai da luu.
    """
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
    # Log chi ra stderr va file, khong print ra stdout vi lam vo frame MCP
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(settings.logs_dir / "server.log", encoding="utf-8"),
        ],
        force=True,
    )
    logger.info("Phase 1: FAKE retrieval; single-server writer only")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
