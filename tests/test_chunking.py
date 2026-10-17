import pytest

from policy_agent.models import Document, DocumentMetadata
from policy_agent.rag import chunking


def make_document(content, doc_id="DOC_TEST"):
    metadata = DocumentMetadata(
        doc_id=doc_id, title="Test Policy", version="2.0",
        date="2026-09-01", owner="Test HR", category="policy"
    )
    return Document(content=content, metadata=metadata)


def test_chunks_follow_headings_and_preserve_metadata():
    document = make_document("## Remote Work\nRemote policy.\n\n## Expenses\nExpense policy.")
    assert callable(getattr(chunking, "chunk_document", None)), "chunk_document is missing"
    chunks = chunking.chunk_document(document)
    assert len(chunks) == 2
    assert chunks[0].content == "## Remote Work\nRemote policy.\n\n"
    assert chunks[1].content == "## Expenses\nExpense policy."
    assert [chunk.chunk_id for chunk in chunks] == ["DOC_TEST:0", "DOC_TEST:1"]
    assert all(chunk.metadata is document.metadata for chunk in chunks)
    assert all(chunk.embedding == [] for chunk in chunks)

@pytest.mark.parametrize("prefix", ["", "## Long Policy\n"])
def test_long_section_has_bounded_chunks_overlap_and_no_lost_text(prefix):
    body = "abcdefghij" * 100
    document = make_document(prefix + body)
    chunks = chunking.chunk_document(document, chunk_size=100, overlap=12)
    assert len(chunks) > 1
    assert all(0 < len(chunk.content) <= 100 for chunk in chunks)
    assert all(chunk.content.startswith(prefix) for chunk in chunks)
    pieces = [chunk.content[len(prefix):] for chunk in chunks]
    for previous, following in zip(pieces, pieces[1:]):
        assert previous[-12:] == following[:12]
    reconstructed = pieces[0] + "".join(piece[12:] for piece in pieces[1:])
    assert reconstructed == body

@pytest.mark.parametrize("content,expected_end", [
    ("A" * 40 + "\n\n" + "B" * 100, "\n\n"),
    ("Remote work requires approval. " * 10, ". "),
])
def test_long_sections_prefer_paragraph_then_sentence_boundaries(content, expected_end):
    document = make_document(content)
    size = 80 if expected_end == "\n\n" else 100
    chunks = chunking.chunk_document(document, chunk_size=size, overlap=10)
    assert chunks[0].content.endswith(expected_end)
    reconstructed = chunks[0].content + "".join(chunk.content[10:] for chunk in chunks[1:])
    assert reconstructed == content

@pytest.mark.parametrize("size,overlap", [(0, 0), (-1, 0), (100, -1), (100, 100), (100, 101), (True, 0), (100.5, 10), (100, False)])
def test_invalid_parameters_fail_before_splitting(monkeypatch, size, overlap):
    def must_not_split(*args):
        raise AssertionError("Invalid parameters reached the splitter")
    monkeypatch.setattr(chunking, "_split_section", must_not_split)
    with pytest.raises((ValueError, TypeError)):
        chunking.chunk_document(make_document("Policy"), chunk_size=size, overlap=overlap)


def test_heading_that_exhausts_size_budget_is_rejected():
    document = make_document("## " + "H" * 150 + "\n")
    with pytest.raises(ValueError, match="heading|Heading"):
        chunking.chunk_document(document, chunk_size=100, overlap=10)


def test_empty_document_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        chunking.chunk_document(make_document("  \n\t"))


def test_preface_is_preserved_and_overlap_does_not_cross_sections():
    document = make_document("# Policy Title\nIntro.\n\n## Remote\nRemote.\n\n## Expenses\nExpenses.")
    chunks = chunking.chunk_document(document)
    assert len(chunks) == 3
    assert chunks[0].content.startswith("# Policy Title")
    assert chunks[1].content.startswith("## Remote")
    assert chunks[2].content.startswith("## Expenses")
    assert "Remote." not in chunks[2].content
    assert "Expenses." not in chunks[1].content
    assert "".join(chunk.content for chunk in chunks) == document.content


def test_overlap_must_fit_body_after_repeated_heading():
    document = make_document("## " + "H" * 60 + "\n" + "x" * 300)
    with pytest.raises(ValueError, match="Heading"):
        chunking.chunk_document(document, chunk_size=100, overlap=60)


def test_zero_overlap_preserves_long_unicode_text():
    content = "Quy định làm việc từ xa. " * 50
    chunks = chunking.chunk_document(make_document(content), chunk_size=80, overlap=0)
    assert all(0 < len(chunk.content) <= 80 for chunk in chunks)
    assert "".join(chunk.content for chunk in chunks) == content


def test_chunk_documents_flattens_results_with_distinct_ids():
    documents = [make_document("One policy", "DOC_A"), make_document("Other policy", "DOC_B")]
    assert callable(getattr(chunking, "chunk_documents", None)), "chunk_documents is missing"
    chunks = chunking.chunk_documents(documents)
    assert [chunk.chunk_id for chunk in chunks] == ["DOC_A:0", "DOC_B:0"]
    assert chunks[0].metadata is documents[0].metadata
    assert chunks[1].metadata is documents[1].metadata

