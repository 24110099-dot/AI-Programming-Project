"""Configuration tests use injected environment, never the real .env/key."""
import importlib
from pathlib import Path


def test_defaults_use_module_root_without_creating_state():
    package = importlib.import_module("policy_agent")
    assert (Path(package.__file__).resolve().parent / "config.py").exists(), "D1 config.py is missing"
    config = importlib.import_module("policy_agent.config")
    settings = config.load_settings(environ={})
    root = Path(__file__).resolve().parents[1]
    assert settings.project_root == root
    assert settings.model == "openai/gpt-oss-20b"
    assert settings.retrieval_mode == "dense"
    assert settings.max_steps == 8
    assert settings.min_score == 0.35
    assert settings.groq_api_key is None
    assert settings.corpus_dir == root / "data/corpus"
    assert settings.index_dir == root / "data/index"
    assert settings.requests_path == root / "data/state/requests.json"
    assert settings.logs_dir == root / "logs"
    isolated = config.load_settings(project_root=root / ".uncreated-config-root", environ={})
    assert not isolated.project_root.exists()
    assert not isolated.index_dir.exists()
    assert not isolated.requests_path.exists()
    assert Path(config.__file__).resolve().parents[2] == root


import os
from dataclasses import asdict
import pytest
from policy_agent import config


def test_environment_overrides_and_secret_repr():
    settings = config.load_settings(environ={"MODEL": "demo/model", "GROQ_API_KEY": "synthetic-test-only", "RETRIEVAL_MODE": "hybrid", "MAX_STEPS": "3", "MIN_SCORE": "0.2"})
    assert (settings.model, settings.retrieval_mode, settings.max_steps, settings.min_score) == ("demo/model", "hybrid", 3, 0.2)
    assert settings.groq_api_key == "synthetic-test-only"
    assert "synthetic-test-only" not in repr(settings)
    assert "groq_api_key" not in repr(settings)
    assert "synthetic-test-only" in asdict(settings).values()


def test_mode_specific_threshold_defaults_and_boundaries():
    assert config.load_settings(environ={"RETRIEVAL_MODE": "hybrid"}).min_score == 0.25
    assert config.load_settings(environ={"MIN_SCORE": "-1"}).min_score == -1
    assert config.load_settings(environ={"RETRIEVAL_MODE": "hybrid", "MIN_SCORE": "-0.7"}).min_score == -0.7
    assert config.load_settings(environ={"MIN_SCORE": "1"}).min_score == 1


@pytest.mark.parametrize("env", [
    {"MODEL": " "}, {"RETRIEVAL_MODE": "bm25"}, {"MAX_STEPS": "0"},
    {"MAX_STEPS": "-1"}, {"MAX_STEPS": "8.0"}, {"MAX_STEPS": "eight"},
    {"MIN_SCORE": "NaN"}, {"MIN_SCORE": "inf"}, {"MIN_SCORE": "-1.01"},
    {"MIN_SCORE": "1.01"}, {"MIN_SCORE": ""},
    {"RETRIEVAL_MODE": "hybrid", "MIN_SCORE": "-0.71"},
    {"INDEX_DIR": " "},
])
def test_invalid_environment_values_fail_fast(env):
    with pytest.raises(ValueError):
        config.load_settings(environ=env)


@pytest.mark.parametrize("env", [{"MAX_STEPS": True}, {"MODEL": 42}, {"GROQ_API_KEY": None}])
def test_non_string_environment_values_are_rejected(env):
    with pytest.raises(TypeError):
        config.load_settings(environ=env)


@pytest.mark.parametrize("changes", [
    {"max_steps": True}, {"max_steps": 1.5}, {"model": 123},
    {"groq_api_key": 123}, {"min_score": True}, {"min_score": "0.4"},
    {"project_root": "root"}, {"index_dir": 1},
])
def test_direct_settings_reject_wrong_types(changes):
    kwargs = {"project_root": Path(__file__).resolve().parents[1]}
    kwargs.update(changes)
    with pytest.raises(TypeError):
        config.Settings(**kwargs)


@pytest.mark.parametrize("changes", [{"max_steps": 0}, {"retrieval_mode": "oops"}, {"min_score": float("nan")}, {"min_score": 2}])
def test_direct_settings_reject_invalid_values(changes):
    with pytest.raises(ValueError):
        config.Settings(project_root=Path(__file__).resolve().parents[1], **changes)


def test_paths_follow_supplied_root_even_after_chdir(tmp_path, monkeypatch):
    root = tmp_path / "project"
    monkeypatch.chdir(tmp_path)
    settings = config.load_settings(project_root=root, environ={"CORPUS_DIR": "fixtures/corpus", "INDEX_DIR": str(tmp_path / "external-index"), "REQUESTS_PATH": "state/requests.json", "LOGS_DIR": "output/logs"})
    assert settings.project_root == root
    assert settings.corpus_dir == root / "fixtures/corpus"
    assert settings.index_dir == tmp_path / "external-index"
    assert settings.requests_path == root / "state/requests.json"
    assert settings.logs_dir == root / "output/logs"
    assert not root.exists()
    assert config.load_settings(environ={}).project_root == Path(__file__).resolve().parents[1]


def test_explicit_dotenv_has_lower_priority_without_mutating_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "environ", {})
    env_file = tmp_path / ".env.fixture"
    env_file.write_text('MODEL=file/model\nMAX_STEPS=4\nGROQ_API_KEY=synthetic-file-key\n', encoding="utf-8")
    settings = config.load_settings(dotenv_path=env_file, environ={"MODEL": "injected/model"})
    assert settings.model == "injected/model" and settings.max_steps == 4
    assert settings.groq_api_key == "synthetic-file-key"
    assert dict(os.environ) == {}
    assert config.load_settings(environ={}).groq_api_key is None
    with pytest.raises(FileNotFoundError):
        config.load_settings(dotenv_path=tmp_path / "missing", environ={})


def test_process_environment_is_read_only_when_explicitly_loading(monkeypatch):
    monkeypatch.setattr(os, "environ", {"MODEL": "process/model", "MAX_STEPS": "2"})
    assert config.load_settings().model == "process/model"
    assert config.load_settings(environ={}).model == "openai/gpt-oss-20b"
    assert dict(os.environ) == {"MODEL": "process/model", "MAX_STEPS": "2"}


def test_import_has_no_settings_or_io(tmp_path):
    import subprocess
    import sys
    script = '''
import builtins, os, pathlib, socket

def blocked(*args, **kwargs):
    raise AssertionError("import must not perform application I/O")

builtins.open = blocked
pathlib.Path.open = blocked
pathlib.Path.read_text = blocked
pathlib.Path.mkdir = blocked
socket.socket = blocked
os.getenv = blocked
import policy_agent.models
import policy_agent.config
assert not hasattr(policy_agent.config, "settings")
print(policy_agent.config.__file__)
'''
    result = subprocess.run([sys.executable, "-B", "-c", script], cwd=tmp_path, env={"SYSTEMROOT": "C:/Windows", "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"), "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert str(Path(__file__).resolve().parents[1] / "src/policy_agent/config.py") in result.stdout
