"""Split by headings to keep each policy section in its original context.
Prefer paragraph and sentence boundaries when a section exceeds 400 characters.
Count heading text inside the size limit so retrieved chunks remain bounded.
Use 60-character overlap within long sections to retain boundary context.
Keep source metadata on every chunk for citations and version selection.
"""

import re

from policy_agent.models import Document, DocumentChunk


def chunk_document(
    document: Document, chunk_size: int = 400, overlap: int = 60
) -> list[DocumentChunk]:
    """Return heading-aware chunks; size and overlap are measured in characters."""
    if type(chunk_size) is not int or type(overlap) is not int:
        raise TypeError("chunk_size and overlap must be integers, not bool")
    if chunk_size <= 0 or not 0 <= overlap < chunk_size:
        raise ValueError("Require chunk_size > 0 and 0 <= overlap < chunk_size")
    if not document.content.strip():
        raise ValueError(f"Document {document.doc_id} is empty")
    sections = re.split(r"(?m)(?=^##[ \t]+)", document.content)
    chunks = []
    for section in sections:
        if not section.strip():
            continue
        for content in _split_section(section, chunk_size, overlap):
            chunks.append(DocumentChunk(
                chunk_id=f"{document.doc_id}:{len(chunks)}",
                content=content,
                metadata=document.metadata,
            ))
    return chunks


def _split_section(section: str, chunk_size: int, overlap: int) -> list[str]:
    if len(section) <= chunk_size:
        return [section]
    prefix = ""
    body = section
    if re.match(r"^##[ \t]+", section):
        heading, newline, body = section.partition("\n")
        prefix = heading + newline
    budget = chunk_size - len(prefix)
    if budget <= overlap:
        raise ValueError("Heading leaves insufficient body space; increase chunk_size or reduce overlap")
    pieces = []
    start = 0
    while start < len(body):
        limit = min(start + budget, len(body))
        end = _end_boundary(body, start, limit, budget, overlap)
        pieces.append(prefix + body[start:end])
        if end == len(body):
            break
        start = end - overlap
    return pieces


def _end_boundary(text: str, start: int, limit: int, budget: int, overlap: int) -> int:
    if limit == len(text):
        return limit
    window = text[start:limit]
    minimum = max(budget // 2, overlap + 1)
    for pattern in (r"\n[ \t]*\n", r"(?<=[.!?])\s+", r"\s+"):
        ends = [match.end() for match in re.finditer(pattern, window) if match.end() >= minimum]
        if ends:
            return start + ends[-1]
    return limit


def chunk_documents(
    documents: list[Document], chunk_size: int = 400, overlap: int = 60
) -> list[DocumentChunk]:
    """Apply the same strategy to each document while preserving corpus order."""
    chunks = []
    for document in documents:
        chunks.extend(chunk_document(document, chunk_size=chunk_size, overlap=overlap))
    return chunks
