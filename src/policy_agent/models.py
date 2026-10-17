from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class DocumentMetadata:
    doc_id: str
    title: str
    version: str
    date: str
    owner: str
    category: str = ""
    supersedes: str | None = None
    lang: str = "en"
    source: str = ""
    file: str = ""

    def __post_init__(self) -> None:
        for name in ("doc_id", "title", "version", "date", "owner"):
            val = getattr(self, name)
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"{name} must not be blank")
        if not isinstance(self.date, str) or date.fromisoformat(self.date).isoformat() != self.date:
            raise ValueError("date must use YYYY-MM-DD")


@dataclass
class Document:
    content: str
    metadata: DocumentMetadata

    @property
    def doc_id(self) -> str:
        return self.metadata.doc_id


@dataclass
class DocumentChunk:
    chunk_id: str
    content: str
    metadata: DocumentMetadata
    embedding: list[float] = field(default_factory=list)


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedAction:
    kind: str
    tool_name: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    final_answer: str | None = None
    error: str | None = None


@dataclass
class StepTrace:
    thought: str = ""
    action: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    observation: str = ""


@dataclass
class Usage:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    max_prompt: int = 0


@dataclass
class RunTrace:
    timestamp: str
    question: str
    steps: list[StepTrace] = field(default_factory=list)
    final_answer: str = ""
    cited_doc_ids: list[str] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)


@dataclass
class ProcedureRequest:
    request_id: str
    request_type: str
    employee: str
    details: str
    start_date: str = ""
    end_date: str = ""
    status: str = "submitted"
    created_at: str = ""
