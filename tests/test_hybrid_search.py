import importlib
import logging
from types import SimpleNamespace

import numpy as np
import pytest


def load_hybrid_module():
    try:
        return importlib.import_module("policy_agent.rag.hybrid_search")
    except ImportError as exc:
        pytest.fail(f"Hybrid must import project modules by package path: {exc}")


def test_hybrid_uses_project_cosine():
    module = load_hybrid_module()
    assert module.cosine_similarity.__module__ == "policy_agent.rag.vector_store"


def test_hybrid_preserves_weighted_fusion_without_stdout(monkeypatch, capsys, caplog):
    module = load_hybrid_module()
    monkeypatch.setattr(module, "embed_text", lambda query: [1.0, 0.0])
    chunks = [SimpleNamespace(content="remote policy"), SimpleNamespace(content="expense policy")]
    bm25 = SimpleNamespace(get_scores=lambda tokens: np.array([0.0, 10.0]))

    with caplog.at_level(logging.DEBUG, logger=module.__name__):
        results = module.hybrid_search(
            "remote", chunks, bm25, [[1.0, 0.0], [0.0, 1.0]], top_k=2
        )

    assert [index for index, _ in results] == [0, 1]
    assert [score for _, score in results] == pytest.approx([0.7, 0.3])
    assert capsys.readouterr().out == ""
    assert "Tokenized query" in caplog.text
    assert "BM25 scores" in caplog.text


def test_original_bm25_normalisation_behavior_is_preserved():
    module = load_hybrid_module()
    assert module.normalise_scores([]) == []
    assert module.normalise_scores([0.0, 10.0]) == [0.0, 1.0]
    assert module.normalise_scores([0.0, 0.0]) == [1.0, 1.0]
