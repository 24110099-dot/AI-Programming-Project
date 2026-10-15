"""Smoke-check real embeddings and vector-store persistence, not an agent evaluation."""

from dataclasses import asdict
from math import isclose
from pathlib import Path
from tempfile import TemporaryDirectory

from policy_agent.rag.chunking import chunk_documents
from policy_agent.rag.loader import load_documents
from policy_agent.rag.vector_store import VectorStore


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    documents = load_documents(root / "data" / "corpus")
    chunks = chunk_documents(documents)
    if not chunks:
        raise ValueError("No corpus chunks to check")

    store = VectorStore()
    print(f"Embedding {len(chunks)} chunks with {store.model_name}", flush=True)
    store.add(chunks)
    query = "How many business days before arrival must visitor desks be booked?"
    before = store.search(query, top_k=3)
    assert before, "Search returned no results"

    with TemporaryDirectory(prefix="policy-vector-smoke-") as directory:
        path = Path(directory) / "index.json"
        store.save(path)
        restored = VectorStore()
        restored.load(path)

        assert restored.model_name == store.model_name
        assert list(restored.chunks) == list(store.chunks)
        for chunk_id, original in store.chunks.items():
            assert asdict(restored.chunks[chunk_id]) == asdict(original)

        after = restored.search(query, top_k=3)
        assert [chunk.chunk_id for chunk, _ in after] == [chunk.chunk_id for chunk, _ in before]
        assert all(
            isclose(old_score, new_score, rel_tol=1e-6, abs_tol=1e-6)
            for (_, old_score), (_, new_score) in zip(before, after)
        )

    print(f"Documents: {len(documents)}")
    print(f"Chunks: {len(store.chunks)}")
    print(f"Embedding dimensions: {sorted({len(chunk.embedding) for chunk in store.chunks.values()})}")
    print(f"Query: {query}")
    for chunk, score in after:
        print(f"{chunk.chunk_id} | {chunk.metadata.title} | score={score:.6f}")
    print("PASS: typed chunks, metadata, vectors, model and search results survive save/load")
    print("Temporary index removed; data/index was not changed")


if __name__ == "__main__":
    main()
