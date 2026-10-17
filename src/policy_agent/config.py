import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    # Cấu hình chung của hệ thống; ẩn groq_api_key khi in ra màn hình
    project_root: Path
    model: str = "openai/gpt-oss-20b"
    groq_api_key: str | None = field(default=None, repr=False)
    retrieval_mode: str = "dense"
    max_steps: int = 8
    min_score: float = 0.35
    corpus_dir: Path | None = None
    index_dir: Path | None = None
    requests_path: Path | None = None
    logs_dir: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.project_root, Path):
            raise TypeError("project_root must be pathlib.Path")
        if type(self.model) is not str or type(self.retrieval_mode) is not str:
            raise TypeError("model and retrieval_mode must be strings")
        if self.groq_api_key is not None and type(self.groq_api_key) is not str:
            raise TypeError("groq_api_key must be a string or None")
        if type(self.max_steps) is not int:
            raise TypeError("max_steps must be an integer, not bool")
        if type(self.min_score) not in (int, float):
            raise TypeError("min_score must be a number, not bool")
        if not self.model.strip():
            raise ValueError("MODEL must not be blank")
        if self.retrieval_mode not in ("dense", "hybrid"):
            raise ValueError("RETRIEVAL_MODE must be dense or hybrid")
        if self.max_steps < 1:
            raise ValueError("MAX_STEPS must be positive")
        lower = -1.0 if self.retrieval_mode == "dense" else -0.7
        if not math.isfinite(self.min_score) or not lower <= self.min_score <= 1.0:
            raise ValueError(f"MIN_SCORE must be finite and in [{lower}, 1.0]")
        root = self.project_root.resolve()
        object.__setattr__(self, "project_root", root)
        defaults = {
            "corpus_dir": "data/corpus",
            "index_dir": "data/index",
            "requests_path": "data/state/requests.json",
            "logs_dir": "logs",
        }
        for name, relative in defaults.items():
            value = getattr(self, name)
            if value is not None and not isinstance(value, Path):
                raise TypeError(f"{name} must be pathlib.Path or None")
            value = root / relative if value is None else value
            resolved = value.resolve() if value.is_absolute() else (root / value).resolve()
            object.__setattr__(self, name, resolved)


def load_settings(
    *,
    project_root: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    dotenv_path: str | Path | None = None,
) -> Settings:
    # Đọc biến môi trường từ file .env (nếu có truyền vào) và os.environ
    if project_root is not None and not isinstance(project_root, (str, Path)):
        raise TypeError("project_root must be a path or string")
    root = Path(project_root).resolve() if project_root is not None else Path(__file__).resolve().parents[2]
    values: dict[str, str | None] = {}
    if dotenv_path is not None:
        from dotenv import dotenv_values

        path = Path(dotenv_path)
        path = path if path.is_absolute() else root / path
        if not path.is_file():
            raise FileNotFoundError("Explicit dotenv file was not found")
        values.update(dotenv_values(path, encoding="utf-8", interpolate=False))
    values.update(os.environ if environ is None else environ)
    known = (
        "MODEL",
        "GROQ_API_KEY",
        "RETRIEVAL_MODE",
        "MAX_STEPS",
        "MIN_SCORE",
        "CORPUS_DIR",
        "INDEX_DIR",
        "REQUESTS_PATH",
        "LOGS_DIR",
    )
    for name in known:
        if name in values and type(values[name]) is not str:
            raise TypeError(f"{name} must be a string")
    mode = values.get("RETRIEVAL_MODE", "dense")
    try:
        max_steps = int(values.get("MAX_STEPS", "8"))
    except ValueError:
        raise ValueError("MAX_STEPS must be an integer") from None
    try:
        min_score = float(values.get("MIN_SCORE", "0.35" if mode == "dense" else "0.25"))
    except ValueError:
        raise ValueError("MIN_SCORE must be a number") from None
    paths = {}
    for env_name, field_name in (
        ("CORPUS_DIR", "corpus_dir"),
        ("INDEX_DIR", "index_dir"),
        ("REQUESTS_PATH", "requests_path"),
        ("LOGS_DIR", "logs_dir"),
    ):
        if env_name in values:
            if not values[env_name].strip():
                raise ValueError(f"{env_name} must not be blank")
            paths[field_name] = Path(values[env_name])
    key = values.get("GROQ_API_KEY")
    return Settings(
        project_root=root,
        model=values.get("MODEL", "openai/gpt-oss-20b"),
        groq_api_key=key if key and key.strip() else None,
        retrieval_mode=mode,
        max_steps=max_steps,
        min_score=min_score,
        **paths,
    )
