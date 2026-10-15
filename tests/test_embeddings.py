import pytest

from policy_agent.rag import embeddings


def must_not_load_model(*args, **kwargs):
    raise AssertionError("Input validation must happen before loading the model")


def test_empty_input_returns_empty_list_without_loading_model(monkeypatch):
    monkeypatch.setattr(embeddings, "get_model", must_not_load_model)
    assert embeddings.embed_texts([]) == []


@pytest.mark.parametrize("texts", ["plain string", None, [42]])
def test_invalid_input_type_is_rejected_before_model_load(monkeypatch, texts):
    monkeypatch.setattr(embeddings, "get_model", must_not_load_model)
    with pytest.raises(TypeError):
        embeddings.embed_texts(texts)


@pytest.mark.parametrize("texts", [[""], ["  \n\t"]])
def test_blank_text_is_rejected_before_model_load(monkeypatch, texts):
    monkeypatch.setattr(embeddings, "get_model", must_not_load_model)
    with pytest.raises(ValueError):
        embeddings.embed_texts(texts)


@pytest.mark.parametrize("explicit_model,expected_model", [
    (None, "test/environment-model"),
    ("test/explicit-model", "test/explicit-model"),
])
def test_model_selection_uses_environment_unless_explicit(monkeypatch, explicit_model, expected_model):
    import numpy as np

    requested = []

    class FakeModel:
        def encode(self, texts, normalize_embeddings):
            assert normalize_embeddings is True
            return np.array([[1.0, 0.0] for _ in texts])

    def fake_get_model(name):
        requested.append(name)
        return FakeModel()

    monkeypatch.setenv("EMBEDDING_MODEL", "test/environment-model")
    monkeypatch.setattr(embeddings, "get_model", fake_get_model)
    kwargs = {} if explicit_model is None else {"model_name": explicit_model}
    embeddings.embed_texts(["Policy"], **kwargs)
    assert requested == [expected_model]

