import json

from policy_agent.rag import build_index, vector_store


def test_build_index_connects_loader_chunking_embeddings_and_save(tmp_path, monkeypatch):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    metadata = {
        "doc_id": "DOC_TEST", "file": "policy.txt", "title": "Test Policy",
        "version": "1.0", "date": "2026-09-01", "owner": "Test HR",
        "category": "policy",
    }
    (corpus_dir / "manifest.json").write_text(json.dumps([metadata]), encoding="utf-8")
    (corpus_dir / "policy.txt").write_text("Remote work requires approval.", encoding="utf-8")

    def fake_embed_texts(texts, model_name=None):
        assert model_name == "test/build-model"
        return [[1.0, 0.0] for _ in texts]

    monkeypatch.setattr(vector_store, "embed_texts", fake_embed_texts)
    output_path = tmp_path / "index" / "index.json"
    assert callable(getattr(build_index, "build_index", None)), "build_index function is missing"
    store = build_index.build_index(corpus_dir, output_path, model_name="test/build-model")

    assert isinstance(store, vector_store.VectorStore)
    assert output_path.is_file()
    restored = vector_store.VectorStore()
    restored.load(output_path)
    assert restored.model_name == "test/build-model"
    assert list(restored.chunks) == list(store.chunks)
    assert len(restored.chunks) == 1
    chunk = next(iter(restored.chunks.values()))
    assert chunk.metadata.doc_id == "DOC_TEST"
    assert chunk.content == "Remote work requires approval."
    assert chunk.embedding == [1.0, 0.0]


def test_main_uses_project_paths_independent_of_working_directory(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace

    calls = []
    module_path = tmp_path / "src" / "policy_agent" / "rag" / "build_index.py"
    monkeypatch.setattr(build_index, "__file__", str(module_path))
    monkeypatch.chdir(tmp_path.parent)

    def fake_build_index(corpus_dir, output_path):
        calls.append((corpus_dir, output_path))
        return SimpleNamespace(model_name="test/main-model", chunks={"DOC_TEST:0": None})

    monkeypatch.setattr(build_index, "build_index", fake_build_index)
    assert callable(getattr(build_index, "main", None)), "main is missing"
    build_index.main()

    assert calls == [(tmp_path / "data" / "corpus", tmp_path / "data" / "index" / "index.json")]
    assert str(tmp_path / "data" / "index" / "index.json") in capsys.readouterr().out

