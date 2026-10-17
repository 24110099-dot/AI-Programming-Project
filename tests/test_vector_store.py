import pytest

from policy_agent.rag import vector_store


@pytest.mark.parametrize("a,b,expected", [
    ([1.0, 0.0], [1.0, 0.0], 1.0),
    ([1.0, 0.0], [0.0, 1.0], 0.0),
    ([1.0, 0.0], [-1.0, 0.0], -1.0),
])
def test_cosine_similarity(a, b, expected):
    assert callable(getattr(vector_store, "cosine_similarity", None)), (
        "cosine_similarity is missing"
    )
    assert vector_store.cosine_similarity(a, b) == pytest.approx(expected)


def test_vector_store_starts_empty_with_independent_storage():
    assert callable(getattr(vector_store, "VectorStore", None)), "VectorStore is missing"
    first = vector_store.VectorStore()
    second = vector_store.VectorStore()
    assert first.chunks == {}
    assert second.chunks == {}
    assert first.chunks is not second.chunks


def test_add_embeds_texts_and_keeps_chunk_metadata(monkeypatch):
    from policy_agent.models import DocumentChunk, DocumentMetadata

    metadata = DocumentMetadata(
        doc_id="DOC_TEST", title="Policy", version="1.0",
        date="2026-09-01", owner="Test HR",
    )
    chunks = [
        DocumentChunk("DOC_TEST:0", "Remote policy", metadata),
        DocumentChunk("DOC_TEST:1", "Expense policy", metadata),
    ]

    def fake_embed_texts(texts, model_name=None):
        assert texts == ["Remote policy", "Expense policy"]
        return [[1.0, 0.0], [0.0, 1.0]]

    monkeypatch.setattr(vector_store, "embed_texts", fake_embed_texts)
    store = vector_store.VectorStore()
    assert callable(getattr(store, "add", None)), "VectorStore.add is missing"
    ids = store.add(chunks)

    assert ids == ["DOC_TEST:0", "DOC_TEST:1"]
    assert store.chunks["DOC_TEST:0"] is chunks[0]
    assert store.chunks["DOC_TEST:1"] is chunks[1]
    assert chunks[0].embedding == [1.0, 0.0]
    assert chunks[1].embedding == [0.0, 1.0]
    assert all(chunk.metadata is metadata for chunk in store.chunks.values())


def test_search_returns_best_matching_chunk_and_score(monkeypatch):
    from policy_agent.models import DocumentChunk, DocumentMetadata

    metadata = DocumentMetadata("DOC_TEST", "Policy", "1.0", "2026-09-01", "Test HR")
    chunks = [
        DocumentChunk("DOC_TEST:0", "Remote policy", metadata),
        DocumentChunk("DOC_TEST:1", "Expense policy", metadata),
    ]
    monkeypatch.setattr(vector_store, "embed_texts", lambda texts, model_name=None: [[1.0, 0.0], [0.0, 1.0]])

    def fake_embed_text(query, model_name=None):
        assert query == "expense claim"
        return [0.0, 1.0]

    monkeypatch.setattr(vector_store, "embed_text", fake_embed_text)
    store = vector_store.VectorStore()
    store.add(chunks)
    assert callable(getattr(store, "search", None)), "VectorStore.search is missing"
    results = store.search("expense claim", top_k=1)

    assert len(results) == 1
    chunk, score = results[0]
    assert chunk is chunks[1]
    assert score == pytest.approx(1.0)


@pytest.mark.parametrize("already_stored", [False, True])
def test_add_rejects_duplicate_chunk_ids_before_embedding(monkeypatch, already_stored):
    from policy_agent.models import DocumentChunk, DocumentMetadata

    metadata = DocumentMetadata("DOC_TEST", "Policy", "1.0", "2026-09-01", "Test HR")
    first = DocumentChunk("DOC_TEST:0", "Original", metadata)
    second = DocumentChunk("DOC_TEST:0", "Different text", metadata)
    store = vector_store.VectorStore()
    if already_stored:
        store.chunks[first.chunk_id] = first
        batch = [second]
    else:
        batch = [first, second]
    previous = dict(store.chunks)

    def must_not_embed(texts, model_name=None):
        pytest.fail("Duplicate IDs must be rejected before embedding")

    monkeypatch.setattr(vector_store, "embed_texts", must_not_embed)
    with pytest.raises(ValueError, match="Duplicate"):
        store.add(batch)
    assert store.chunks == previous






def test_store_keeps_the_same_model_for_documents_and_queries(monkeypatch):
    from policy_agent.models import DocumentChunk, DocumentMetadata

    metadata = DocumentMetadata("DOC_TEST", "Policy", "1.0", "2026-09-01", "Test HR")
    chunk = DocumentChunk("DOC_TEST:0", "Policy", metadata)
    requested_models = []

    def fake_batch(texts, model_name=None):
        requested_models.append(model_name)
        return [[1.0, 0.0]]

    def fake_query(query, model_name=None):
        requested_models.append(model_name)
        return [1.0, 0.0]

    monkeypatch.setattr(vector_store, "embed_texts", fake_batch)
    monkeypatch.setattr(vector_store, "embed_text", fake_query)
    monkeypatch.setenv("EMBEDDING_MODEL", "test/original-model")
    store = vector_store.VectorStore()
    store.add([chunk])
    monkeypatch.setenv("EMBEDDING_MODEL", "test/different-model")
    store.search("Policy")

    assert requested_models == ["test/original-model", "test/original-model"]


def test_save_writes_model_chunks_vectors_and_metadata(tmp_path):
    import json
    from dataclasses import asdict
    from policy_agent.models import DocumentChunk, DocumentMetadata

    metadata = DocumentMetadata("DOC_TEST", "Quy định", "2.0", "2026-09-01", "Test HR")
    chunk = DocumentChunk("DOC_TEST:0", "Làm việc từ xa", metadata, embedding=[1.0, 0.0])
    store = vector_store.VectorStore(model_name="test/persisted-model")
    store.chunks[chunk.chunk_id] = chunk
    path = tmp_path / "nested" / "index.json"
    assert callable(getattr(store, "save", None)), "VectorStore.save is missing"

    store.save(path)

    content = path.read_text(encoding="utf-8")
    payload = json.loads(content)
    assert payload["format_version"] == 1
    assert payload["model_name"] == "test/persisted-model"
    assert payload["chunks"] == [asdict(chunk)]
    assert "Quy định" in content


def test_load_restores_typed_chunks_and_model_without_embedding(tmp_path, monkeypatch):
    from dataclasses import asdict
    from policy_agent.models import DocumentChunk, DocumentMetadata

    metadata = DocumentMetadata("DOC_TEST", "Quy định", "2.0", "2026-09-01", "Test HR")
    chunk = DocumentChunk("DOC_TEST:0", "Làm việc từ xa", metadata, embedding=[1.0, 0.0])
    source = vector_store.VectorStore(model_name="test/saved-model")
    source.chunks[chunk.chunk_id] = chunk
    path = tmp_path / "index.json"
    source.save(path)

    def must_not_embed(*args, **kwargs):
        pytest.fail("Loading saved vectors must not embed again")

    monkeypatch.setattr(vector_store, "embed_texts", must_not_embed)
    monkeypatch.setattr(vector_store, "embed_text", must_not_embed)
    restored = vector_store.VectorStore(model_name="test/different-model")
    assert callable(getattr(restored, "load", None)), "VectorStore.load is missing"
    restored.load(path)

    assert restored.model_name == "test/saved-model"
    assert list(restored.chunks) == [chunk.chunk_id]
    loaded = restored.chunks[chunk.chunk_id]
    assert isinstance(loaded, DocumentChunk)
    assert isinstance(loaded.metadata, DocumentMetadata)
    assert loaded is not chunk
    assert asdict(loaded) == asdict(chunk)


@pytest.mark.parametrize("vectors", [
    [],
    [[1.0, 0.0]],
    [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]],
])
def test_add_rejects_wrong_embedding_count_without_partial_write(monkeypatch, vectors):
    from policy_agent.models import DocumentChunk, DocumentMetadata

    metadata = DocumentMetadata("DOC_TEST", "Policy", "1.0", "2026-09-01", "Test HR")
    chunks = [
        DocumentChunk("DOC_TEST:0", "Remote policy", metadata),
        DocumentChunk("DOC_TEST:1", "Expense policy", metadata),
    ]
    monkeypatch.setattr(vector_store, "embed_texts", lambda texts, model_name=None: vectors)
    store = vector_store.VectorStore()
    with pytest.raises(ValueError, match="count"):
        store.add(chunks)
    assert store.chunks == {}
    assert all(chunk.embedding == [] for chunk in chunks)



