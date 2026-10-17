import json

import pytest

from policy_agent.rag import loader


def test_load_manifest_returns_document_entries(tmp_path):
    expected = [
        {"doc_id": "DOC_TEST", "file": "policy.txt", "title": "Test Policy"}
    ]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(expected), encoding="utf-8")

    assert callable(getattr(loader, "load_manifest", None)), (
        "loader.py needs a load_manifest(corpus_dir) function"
    )
    actual = loader.load_manifest(tmp_path)

    assert actual == expected
    assert isinstance(actual, list)


def test_load_manifest_rejects_non_list_root(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"doc_id": "DOC_TEST"}', encoding="utf-8")

    with pytest.raises(ValueError, match="Manifest must be a list"):
        loader.load_manifest(tmp_path)


def test_load_manifest_rejects_non_dictionary_entry(tmp_path):
    (tmp_path / "manifest.json").write_text('["hello"]', encoding="utf-8")

    with pytest.raises(ValueError, match="Each manifest entry must be a dictionary"):
        loader.load_manifest(tmp_path)

def corpus_entry():
    return {
        "doc_id": "DOC_TEST", "file": "policy.txt", "title": "Test Policy",
        "version": "1.0", "date": "2026-09-01", "owner": "Test HR",
        "category": "policy", "lang": "en", "supersedes": None,
        "source": "synthetic test fixture"
    }


def write_corpus(tmp_path, entries):
    (tmp_path / "manifest.json").write_text(json.dumps(entries), encoding="utf-8")


def test_load_documents_preserves_typed_metadata_and_text(tmp_path):
    from policy_agent.models import Document

    entry = corpus_entry()
    write_corpus(tmp_path, [entry])
    content = "## Quy định\nLàm việc từ xa.\n"
    (tmp_path / entry["file"]).write_text(content, encoding="utf-8")

    assert callable(getattr(loader, "load_documents", None)), "load_documents is missing"
    documents = loader.load_documents(tmp_path)

    assert len(documents) == 1
    assert isinstance(documents[0], Document)
    assert documents[0].content == content
    assert documents[0].metadata.doc_id == entry["doc_id"]
    assert documents[0].metadata.title == entry["title"]
    assert documents[0].metadata.version == entry["version"]
    assert documents[0].metadata.date == entry["date"]
    assert documents[0].metadata.owner == entry["owner"]
    assert documents[0].metadata.category == entry["category"]
    assert documents[0].metadata.file == entry["file"]


@pytest.mark.parametrize("field", ["doc_id", "title", "version", "date", "owner", "file"])
@pytest.mark.parametrize("bad_value", [None, "", "TODO"])
def test_load_documents_rejects_invalid_required_metadata(tmp_path, field, bad_value):
    entry = corpus_entry()
    if bad_value is None:
        del entry[field]
    else:
        entry[field] = bad_value
    write_corpus(tmp_path, [entry])
    (tmp_path / "policy.txt").write_text("Policy", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid metadata"):
        loader.load_documents(tmp_path)

@pytest.mark.parametrize("content", ["", "   \n\t"])
def test_load_documents_rejects_empty_text(tmp_path, content):
    entry = corpus_entry()
    write_corpus(tmp_path, [entry])
    (tmp_path / entry["file"]).write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        loader.load_documents(tmp_path)

@pytest.mark.parametrize("mismatch", ["missing_file", "unlisted_file", "duplicate_id", "duplicate_file"])
def test_load_documents_rejects_manifest_file_mismatch(tmp_path, mismatch):
    entry = corpus_entry()
    entries = [entry]
    if mismatch != "missing_file":
        (tmp_path / "policy.txt").write_text("Policy", encoding="utf-8")
    if mismatch == "unlisted_file":
        (tmp_path / "extra.txt").write_text("Extra", encoding="utf-8")
    if mismatch == "duplicate_id":
        entries.append(dict(entry, file="other.txt"))
        (tmp_path / "other.txt").write_text("Other", encoding="utf-8")
    if mismatch == "duplicate_file":
        entries.append(dict(entry, doc_id="DOC_OTHER"))
    write_corpus(tmp_path, entries)
    with pytest.raises(ValueError, match="mismatch|Duplicate"):
        loader.load_documents(tmp_path)

@pytest.mark.parametrize("file_name", ["../outside.txt", "ABSOLUTE"])
def test_load_documents_rejects_paths_outside_corpus(tmp_path, file_name):
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("Do not read this file", encoding="utf-8")
    entry = corpus_entry()
    entry["file"] = str(outside) if file_name == "ABSOLUTE" else file_name
    write_corpus(tmp_path, [entry])
    with pytest.raises(ValueError, match="relative|outside"):
        loader.load_documents(tmp_path)

@pytest.mark.parametrize("invalid_json", ['[{', '[{"doc_id":"A","doc_id":"B"}]', '[NaN]'])
def test_load_manifest_rejects_invalid_or_ambiguous_json(tmp_path, invalid_json):
    (tmp_path / "manifest.json").write_text(invalid_json, encoding="utf-8")
    with pytest.raises(ValueError):
        loader.load_manifest(tmp_path)

