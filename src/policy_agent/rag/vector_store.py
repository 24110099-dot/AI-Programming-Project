"""Store document chunks and retrieve them by cosine similarity."""
import json
import os
from dataclasses import asdict
from pathlib import Path

import numpy as np

from policy_agent.models import Document, DocumentChunk, DocumentMetadata
from policy_agent.rag.embeddings import DEFAULT_MODEL, embed_text, embed_texts

def cosine_similarity(a: list[float], b: list[float]) -> float:
    vector_a = np.asarray(a, dtype=float)
    vector_b = np.asarray(b, dtype=float)

    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)

    if norm_a == 0 or norm_b == 0:
        raise ValueError("Cannot compare zero-length vectors")

    score = np.dot(vector_a, vector_b) / (norm_a * norm_b)
    return float(score)


class VectorStore:

    def __init__(self, model_name: str | None = None):
        self.model_name = (
            model_name
            if model_name is not None
            else os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)
        )
        self.chunks: dict[str, DocumentChunk] = {}

    def add(self, chunks: list[DocumentChunk]) -> list[str]:
        if not chunks:
            return []

        chunk_ids = [chunk.chunk_id for chunk in chunks]

        if len(set(chunk_ids)) != len(chunk_ids):
            raise ValueError("Duplicate chunk IDs in input")

        for chunk_id in chunk_ids:
            if chunk_id in self.chunks:
                raise ValueError(f"Duplicate chunk ID: {chunk_id}")

        texts = [chunk.content for chunk in chunks]
        vectors = embed_texts(texts, model_name=self.model_name)
        if len(vectors) != len(chunks):
            raise ValueError("Embedding count does not match chunk count")
        for chunk, vector in zip(chunks, vectors):
            chunk.embedding = vector
            self.chunks[chunk.chunk_id] = chunk

        return chunk_ids

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[tuple[DocumentChunk, float]]:
        if not self.chunks:
            return []

        query_vector = embed_text(query, model_name=self.model_name)
        results = []

        for chunk in self.chunks.values():
            score = cosine_similarity(query_vector, chunk.embedding)
            results.append((chunk, score))

        results.sort(key=lambda item: item[1], reverse=True)
        return results[:top_k]

    def save(self, path: Path) -> None:
        path = Path(path)

        payload = {
            "format_version": 1,
            "model_name": self.model_name,
            "chunks": [
                asdict(chunk)
                for chunk in self.chunks.values()
            ],
        }

        text = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


    def load(self, path: Path) -> None:
        text = Path(path).read_text(encoding="utf-8")
        payload = json.loads(text)

        if payload.get("format_version") != 1:
            raise ValueError("Unsupported index format")

        restored_chunks = {}

        for item in payload["chunks"]:
            metadata = DocumentMetadata(**item["metadata"])

            chunk = DocumentChunk(
                chunk_id=item["chunk_id"],
                content=item["content"],
                metadata=metadata,
                embedding=item["embedding"],
            )

            if chunk.chunk_id in restored_chunks:
                raise ValueError(f"Duplicate chunk ID: {chunk.chunk_id}")

            restored_chunks[chunk.chunk_id] = chunk

        self.model_name = payload["model_name"]
        self.chunks = restored_chunks
