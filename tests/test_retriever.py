"""Unit tests cho module RAG retriever (dense, hybrid, metadata filter, min_score gate)."""

import pytest

from policy_agent.models import DocumentChunk, DocumentMetadata
from policy_agent.rag import retriever
from policy_agent.rag.vector_store import VectorStore


def _make_chunk(
    chunk_id: str,
    doc_id: str,
    content: str,
    embedding: list[float],
    *,
    version: str = "1.0",
    category: str = "policy",
    supersedes: str | None = None,
) -> DocumentChunk:
    meta = DocumentMetadata(
        doc_id=doc_id,
        title=f"Title {doc_id}",
        version=version,
        date="2026-09-01",
        owner="HR",
        category=category,
        supersedes=supersedes,
    )
    return DocumentChunk(
        chunk_id=chunk_id,
        content=content,
        metadata=meta,
        embedding=embedding,
    )


def _sample_store() -> VectorStore:
    store = VectorStore(model_name="fake-test-model")
    c1 = _make_chunk(
        "DOC0005:0",
        "DOC0005",
        "Employees may work from another country up to 30 consecutive days.",
        [1.0, 0.0, 0.0],
        version="1.0",
        category="policy",
    )
    c2 = _make_chunk(
        "DOC0101:0",
        "DOC0101",
        "Employees may work from another country up to 21 consecutive days under v2.0.",
        [0.95, 0.31, 0.0],
        version="2.0",
        category="policy",
        supersedes="DOC0005",
    )
    c3 = _make_chunk(
        "DOC0003:0",
        "DOC0003",
        "Hardware purchases over 1000 dollars require department head approval.",
        [0.0, 1.0, 0.0],
        version="1.0",
        category="procurement",
    )
    store.chunks = {c.chunk_id: c for c in (c1, c2, c3)}
    return store


def test_metadata_filter_removes_superseded_and_filters_category():
    store = _sample_store()
    all_chunks = list(store.chunks.values())

    # Mac dinh latest_only=True se loai DOC0005 vi DOC0101 supersedes DOC0005
    latest_chunks = retriever.filter_chunks_by_metadata(all_chunks, latest_only=True)
    doc_ids = [c.metadata.doc_id for c in latest_chunks]
    assert "DOC0005" not in doc_ids
    assert "DOC0101" in doc_ids
    assert "DOC0003" in doc_ids

    # Loc theo category='procurement'
    proc_chunks = retriever.filter_chunks_by_metadata(all_chunks, category="procurement", latest_only=True)
    assert [c.metadata.doc_id for c in proc_chunks] == ["DOC0003"]


def test_retrieve_dense_respects_supersedes_and_min_score(monkeypatch):
    store = _sample_store()
    monkeypatch.setattr(retriever, "embed_text", lambda q, model_name=None: [1.0, 0.0, 0.0])

    # Query huong ve vector [1, 0, 0] nhung DOC0005 bi superseded nen DOC0101 duoc chon
    hits = retriever.retrieve(
        "international work consecutive days",
        mode="dense",
        top_k=3,
        min_score=0.5,
        store=store,
    )
    assert len(hits) == 1
    chunk, score = hits[0]
    assert chunk.metadata.doc_id == "DOC0101"
    assert score > 0.9

    # Neu tat latest_only=False thi ca DOC0005 va DOC0101 deu xuat hien
    both_hits = retriever.retrieve(
        "international work consecutive days",
        mode="dense",
        top_k=3,
        min_score=0.5,
        latest_only=False,
        store=store,
    )
    assert [c.metadata.doc_id for c, _ in both_hits] == ["DOC0005", "DOC0101"]


def test_retrieve_min_score_gate_triggers_no_answer(monkeypatch):
    store = _sample_store()
    # Vector truc giao [0, 0, 1] -> cosine similarity = 0.0 < min_score (0.35)
    monkeypatch.setattr(retriever, "embed_text", lambda q, model_name=None: [0.0, 0.0, 1.0])

    hits = retriever.retrieve(
        "cryptocurrency stock option vesting",
        mode="dense",
        top_k=3,
        min_score=0.35,
        store=store,
    )
    assert hits == []


def test_retrieve_hybrid_mode_combines_bm25_and_vector(monkeypatch):
    store = _sample_store()
    monkeypatch.setattr("policy_agent.rag.hybrid_search.embed_text", lambda q: [0.0, 1.0, 0.0])

    hits = retriever.retrieve(
        "hardware purchases approval",
        mode="hybrid",
        top_k=2,
        min_score=0.3,
        store=store,
    )
    assert len(hits) >= 1
    top_chunk, top_score = hits[0]
    assert top_chunk.metadata.doc_id == "DOC0003"
    assert top_score >= 0.7

    formatted = retriever.format_chunk_hit(top_chunk, top_score)
    assert "[DOC0003 v1.0 2026-09-01]" in formatted
    assert "Hardware purchases" in formatted
