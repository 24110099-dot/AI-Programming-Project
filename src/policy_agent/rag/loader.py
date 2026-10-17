"""Read corpus text and attach the shared DocumentMetadata contract.

The manifest is the source of document IDs and provenance, not file names alone.
Loading returns Document objects and performs no embedding or chunking.
Invalid metadata or a manifest/file mismatch must stop loading visibly.
"""

import json
from pathlib import Path
from typing import Any

from policy_agent.models import Document, DocumentMetadata


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys before a dictionary overwrites them."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_manifest(corpus_dir: Path) -> list[dict[str, Any]]:
    """Read manifest entries; semantic metadata is checked by load_documents."""
    text = (Path(corpus_dir) / "manifest.json").read_text(encoding="utf-8")
    entries = json.loads(text, object_pairs_hook=_unique_object)
    if not isinstance(entries, list):
        raise ValueError("Manifest must be a list")
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Each manifest entry must be a dictionary")
    return entries


def load_documents(corpus_dir: Path) -> list[Document]:

    corpus_dir = Path(corpus_dir).resolve()
    entries = load_manifest(corpus_dir)
    metadata_list = [_document_metadata(entry) for entry in entries]
    seen_ids = set()
    seen_paths = set()
    file_paths = []
    for metadata in metadata_list:
        if metadata.doc_id in seen_ids:
            raise ValueError(f"Duplicate doc_id: {metadata.doc_id}")
        relative_path = Path(metadata.file)
        if relative_path.is_absolute() or relative_path.drive:
            raise ValueError(f"Document file must be relative: {metadata.file}")
        file_path = (corpus_dir / relative_path).resolve()
        if not file_path.is_relative_to(corpus_dir):
            raise ValueError(f"Document file is outside corpus: {metadata.file}")
        if file_path in seen_paths:
            raise ValueError(f"Duplicate file: {metadata.file}")
        seen_ids.add(metadata.doc_id)
        seen_paths.add(file_path)
        file_paths.append(file_path)

    actual_paths = {path.resolve() for path in corpus_dir.rglob("*.txt") if path.is_file()}
    if seen_paths != actual_paths:
        missing = sorted(str(path) for path in seen_paths - actual_paths)
        unlisted = sorted(str(path) for path in actual_paths - seen_paths)
        raise ValueError(f"Manifest/corpus mismatch: missing={missing}; unlisted={unlisted}")

    documents = []
    for metadata, file_path in zip(metadata_list, file_paths):
        content = file_path.read_text(encoding="utf-8")
        if not content.strip():
            raise ValueError(f"Document {metadata.doc_id} is empty: {file_path}")
        documents.append(Document(content=content, metadata=metadata))
    return documents


def _document_metadata(entry: dict[str, Any]) -> DocumentMetadata:
    for field in ("doc_id", "title", "version", "date", "owner", "file"):
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip() or value.strip().upper() == "TODO":
            raise ValueError(f"Invalid metadata: {field} must be a nonblank string, not TODO")
    try:
        return DocumentMetadata(**entry)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid metadata for {entry.get('doc_id')}: {exc}") from exc
