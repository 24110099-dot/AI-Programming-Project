"""One-time build step: corpus -> chunks -> embeddings -> data/index/.  Run: make index

Owner: SV A.  Reuse: W7/W8 build_index.py.
"""
from pathlib import Path

from policy_agent.rag.loader import load_documents
from policy_agent.rag.chunking import chunk_documents
from policy_agent.rag.vector_store import VectorStore
from dotenv import load_dotenv
def build_index(
    corpus_dir: Path,
    output_path: Path,
    chunk_size: int = 400,
    overlap: int = 60,
    model_name: str | None = None,
) -> VectorStore:
    documents = load_documents(corpus_dir)

    chunks = chunk_documents(
        documents,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    if not chunks:
        raise ValueError("No chunks to index")

    store = VectorStore(model_name=model_name)
    store.add(chunks)
    store.save(output_path)

    return store
def main() -> None:
    root = Path(__file__).resolve().parents[3]
    load_dotenv(root / ".env", override=False)

    corpus_dir = root / "data" / "corpus"
    output_path = root / "data" / "index" / "index.json"

    store = build_index(corpus_dir, output_path)

    print("Model:", store.model_name)
    print("Chunks:", len(store.chunks))
    print("Index saved:", output_path)

if __name__ == "__main__":
    main()