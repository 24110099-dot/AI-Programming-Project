import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping
from dotenv import dotenv_values


@dataclass
class Settings:
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
        self.project_root = Path(self.project_root).resolve()
        if not self.model or not self.model.strip():
            raise ValueError("MODEL must not be blank")
        if self.retrieval_mode not in ("dense", "hybrid"):
            raise ValueError("RETRIEVAL_MODE must be dense or hybrid")
        if self.max_steps < 1:
            raise ValueError("MAX_STEPS must be positive")
        if self.corpus_dir is None:
            self.corpus_dir = (self.project_root / "data/corpus").resolve()
        else:
            p = Path(self.corpus_dir)
            self.corpus_dir = p.resolve() if p.is_absolute() else (self.project_root / p).resolve()
        if self.index_dir is None:
            self.index_dir = (self.project_root / "data/index").resolve()
        else:
            p = Path(self.index_dir)
            self.index_dir = p.resolve() if p.is_absolute() else (self.project_root / p).resolve()
        if self.requests_path is None:
            self.requests_path = (self.project_root / "data/state/requests.json").resolve()
        else:
            p = Path(self.requests_path)
            self.requests_path = p.resolve() if p.is_absolute() else (self.project_root / p).resolve()
        if self.logs_dir is None:
            self.logs_dir = (self.project_root / "logs").resolve()
        else:
            p = Path(self.logs_dir)
            self.logs_dir = p.resolve() if p.is_absolute() else (self.project_root / p).resolve()


def load_settings(
    *,
    project_root: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    dotenv_path: str | Path | None = None,
) -> Settings:
    root = Path(project_root).resolve() if project_root is not None else Path(__file__).resolve().parents[2]
    values = {}
    if dotenv_path is not None:
        path = Path(dotenv_path)
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            raise FileNotFoundError("Explicit dotenv file was not found")
        values.update(dotenv_values(path, encoding="utf-8", interpolate=False))
    if environ is None:
        values.update(os.environ)
    else:
        values.update(environ)
    mode = values.get("RETRIEVAL_MODE", "dense")
    max_steps = int(values.get("MAX_STEPS", "8"))
    default_score = "0.35" if mode == "dense" else "0.25"
    min_score = float(values.get("MIN_SCORE", default_score))
    key = values.get("GROQ_API_KEY")
    groq_key = key if key and key.strip() else None
    return Settings(
        project_root=root,
        model=values.get("MODEL", "openai/gpt-oss-20b"),
        groq_api_key=groq_key,
        retrieval_mode=mode,
        max_steps=max_steps,
        min_score=min_score,
        corpus_dir=Path(values["CORPUS_DIR"]) if "CORPUS_DIR" in values else None,
        index_dir=Path(values["INDEX_DIR"]) if "INDEX_DIR" in values else None,
        requests_path=Path(values["REQUESTS_PATH"]) if "REQUESTS_PATH" in values else None,
        logs_dir=Path(values["LOGS_DIR"]) if "LOGS_DIR" in values else None,
    )
