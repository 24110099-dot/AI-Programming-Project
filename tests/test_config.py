from pathlib import Path
import pytest
from policy_agent.config import Settings, load_settings


def test_default_settings():
    settings = load_settings(environ={})
    root = Path(__file__).resolve().parents[1]
    assert settings.project_root == root
    assert settings.model == "openai/gpt-oss-20b"
    assert settings.retrieval_mode == "dense"
    assert settings.max_steps == 8
    assert settings.min_score == 0.35


def test_env_overrides():
    env = {
        "MODEL": "qwen/qwen3.8-27b",
        "GROQ_API_KEY": "test-key",
        "RETRIEVAL_MODE": "hybrid",
        "MAX_STEPS": "5",
        "MIN_SCORE": "0.25",
    }
    settings = load_settings(environ=env)
    assert settings.model == "qwen/qwen3.8-27b"
    assert settings.retrieval_mode == "hybrid"
    assert settings.max_steps == 5
    assert settings.min_score == 0.25
    assert "test-key" not in repr(settings)


def test_invalid_settings(tmp_path):
    with pytest.raises(ValueError):
        Settings(project_root=tmp_path, retrieval_mode="invalid")
    with pytest.raises(ValueError):
        Settings(project_root=tmp_path, max_steps=0)
