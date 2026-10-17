"""Truy van tai lieu quy che (RAG Retriever) ho tro 2 che do Dense va Hybrid.

Tich hop:
1. Metadata Filter TRUOC khi cham diem (+1 diem cong):
   - Loc theo danh muc (category) neu duoc chi dinh.
   - Loc bo phien ban cu bi thay the boi truong 'supersedes' (chi giu ban moi nhat).
2. Ho tro 2 che do truy van (+1 diem cong):
   - 'dense' : Cosine similarity tren vector embedding.
   - 'hybrid': Ket hop 0.3 * BM25_norm + 0.7 * Cosine (tai su dung hybrid_search.py Tuan 4).
3. Cong chan nguong MIN_SCORE (no_answer gate):
   - Loai bo cac ket qua co diem thap hon min_score de chong bia dat (hallucination).

Nguoi phu trach: SV A (Bao).
"""

import os
from pathlib import Path

from policy_agent.config import load_settings
from policy_agent.models import DocumentChunk
from policy_agent.rag.embeddings import embed_text
from policy_agent.rag.hybrid_search import build_bm25_index, hybrid_search
from policy_agent.rag.vector_store import VectorStore, cosine_similarity

# Bo nho dem (cache) VectorStore theo duong dan va thoi gian cap nhat file
_STORE_CACHE: dict[tuple[str, float], VectorStore] = {}


def load_cached_store(index_path: Path | None = None) -> VectorStore:
    """Doc file index.json va luu cache trong bo nho de tang toc truy van."""
    if index_path is None:
        settings = load_settings()
        index_path = settings.index_dir / "index.json"
    resolved = Path(index_path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Index file not found: {resolved}")

    mtime = resolved.stat().st_mtime
    cache_key = (str(resolved), mtime)
    if cache_key not in _STORE_CACHE:
        store = VectorStore()
        store.load(resolved)
        _STORE_CACHE.clear()
        _STORE_CACHE[cache_key] = store
    return _STORE_CACHE[cache_key]


def filter_chunks_by_metadata(
    chunks: list[DocumentChunk],
    category: str | None = None,
    latest_only: bool = True,
) -> list[DocumentChunk]:
    """Loc danh sach chunk theo metadata TRUOC khi tinh diem tuong dong.

    - Neu latest_only=True: Tu dong phat hien cac tai lieu cu bi thay the qua truong
      metadata.supersedes (VD: DOC0101 supersedes DOC0005 -> loai bo DOC0005).
    - Neu category duoc truyen vao: Chi giu cac chunk thuoc dung category do.
    """
    if not chunks:
        return []

    superseded_doc_ids: set[str] = set()
    if latest_only:
        for chunk in chunks:
            old_id = getattr(chunk.metadata, "supersedes", None)
            if isinstance(old_id, str) and old_id.strip():
                superseded_doc_ids.add(old_id.strip())

    target_cat = category.strip().lower() if isinstance(category, str) and category.strip() else None

    filtered: list[DocumentChunk] = []
    for chunk in chunks:
        if latest_only and chunk.metadata.doc_id in superseded_doc_ids:
            continue
        if target_cat is not None and (chunk.metadata.category or "").strip().lower() != target_cat:
            continue
        filtered.append(chunk)

    return filtered


def format_chunk_hit(chunk: DocumentChunk, score: float) -> str:
    """Dinh dang ket qua truy van kem provenance [doc_id vX date] cho Agent."""
    meta = chunk.metadata
    snippet = chunk.content.strip()
    return f"[{meta.doc_id} v{meta.version} {meta.date}] (score={score:.3f}) {snippet}"


def retrieve(
    query: str,
    mode: str | None = None,
    top_k: int = 3,
    category: str | None = None,
    *,
    min_score: float | None = None,
    latest_only: bool = True,
    store: VectorStore | None = None,
    index_path: Path | None = None,
) -> list[tuple[DocumentChunk, float]]:
    """Truy van top_k doan quy che phu hop nhat voi cau hoi.

    Tra ve danh sach tuple (DocumentChunk, score) da qua bo loc metadata va nguong min_score.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a nonblank string")
    if type(top_k) is not int or not (1 <= top_k <= 10):
        raise ValueError("top_k must be an integer between 1 and 10")

    settings = load_settings()
    selected_mode = (mode or os.getenv("RETRIEVAL_MODE") or settings.retrieval_mode).strip().lower()
    if selected_mode not in ("dense", "hybrid"):
        raise ValueError("mode must be 'dense' or 'hybrid'")

    threshold = settings.min_score if min_score is None else float(min_score)

    active_store = store if store is not None else load_cached_store(index_path=index_path)
    all_chunks = list(active_store.chunks.values())

    # Buoc 1: Loc metadata truoc khi cham diem
    candidates = filter_chunks_by_metadata(
        all_chunks,
        category=category,
        latest_only=latest_only,
    )
    if not candidates:
        return []

    # Buoc 2: Tinh diem theo che do dense hoac hybrid
    scored: list[tuple[DocumentChunk, float]] = []
    if selected_mode == "dense":
        query_vec = embed_text(query, model_name=active_store.model_name)
        for chunk in candidates:
            sim = cosine_similarity(query_vec, chunk.embedding)
            scored.append((chunk, float(sim)))
        scored.sort(key=lambda item: item[1], reverse=True)
    else:
        bm25_index = build_bm25_index(candidates)
        embeddings = [chunk.embedding for chunk in candidates]
        raw_bm25 = bm25_index.get_scores(query.lower().split())
        has_keyword_match = bool(len(raw_bm25) > 0 and max(raw_bm25) > 0.0)

        ranked = hybrid_search(
            query=query,
            chunks=candidates,
            bm25_index=bm25_index,
            embeddings=embeddings,
            top_k=len(candidates),
        )
        for chunk_idx, hyb_score in ranked:
            # Neu khong co bat ky tu khoa nao khop BM25, normalise_scores trong W4 tra ve 1.0
            # nen ta tru 0.3 de diem phan anh dung phan vector similarity (0.7 * cosine)
            effective_score = float(hyb_score) if has_keyword_match else float(hyb_score - 0.3)
            scored.append((candidates[chunk_idx], effective_score))
        scored.sort(key=lambda item: item[1], reverse=True)

    # Buoc 3: Loc theo nguong min_score (no_answer gate)
    passed = [(chunk, score) for chunk, score in scored if score >= threshold]
    return passed[:top_k]
