"""Shared data contracts; no embedding, persistence, or agent execution."""
from dataclasses import dataclass, field
from datetime import date
from types import UnionType
from typing import Any, Literal, get_args, get_origin, get_type_hints


def _matches(value: Any, annotation: Any) -> bool:
    """Check annotated containers while leaving payload values opaque."""
    origin = get_origin(annotation)
    args = get_args(annotation)
    if annotation is Any:
        return True
    if origin is UnionType:
        return any(_matches(value, option) for option in args)
    if origin is Literal:
        return value in args
    if origin is list:
        return isinstance(value, list) and all(_matches(item, args[0]) for item in value)
    if origin is dict:
        return isinstance(value, dict) and all(_matches(k, args[0]) and _matches(v, args[1]) for k, v in value.items())
    if annotation is float:
        return type(value) in (int, float)
    if annotation in (int, str):
        return type(value) is annotation
    return isinstance(value, annotation)


class _Validated:
    """Validate constructor types, not later mutation or business policy."""

    def __post_init__(self) -> None:
        for name, annotation in get_type_hints(type(self)).items():
            if not _matches(getattr(self, name), annotation):
                if get_origin(annotation) is Literal:
                    raise ValueError(f"{name} has an unsupported value")
                raise TypeError(f"{name} must match {annotation}")


@dataclass
class DocumentMetadata(_Validated):
    """Manifest provenance; mandatory fields and ISO date are validated."""

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
        super().__post_init__()
        for name in ("doc_id", "title", "version", "date", "owner"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be blank")
        if date.fromisoformat(self.date).isoformat() != self.date:
            raise ValueError("date must use YYYY-MM-DD")


@dataclass
class Document(_Validated):
    """Source text plus typed provenance; doc_id is read from metadata."""

    content: str
    metadata: DocumentMetadata

    @property
    def doc_id(self) -> str:
        """Return the canonical manifest identifier."""
        return self.metadata.doc_id


@dataclass
class DocumentChunk(_Validated):
    """Retrieval unit; an empty embedding means not yet embedded."""

    chunk_id: str
    content: str
    metadata: DocumentMetadata
    embedding: list[float] = field(default_factory=list)


@dataclass
class ToolSpec(_Validated):
    """Normalized discovered tool; SDK inputSchema maps to input_schema."""

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedAction(_Validated):
    """Parser result: one tool call, final answer, or recoverable error."""

    kind: Literal["action", "final", "error"]
    tool_name: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    final_answer: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        selected = {"action": self.tool_name, "final": self.final_answer, "error": self.error}[self.kind]
        if selected is None or not selected.strip():
            raise ValueError(f"{self.kind} requires a nonblank payload")
        if self.kind != "action" and (self.tool_name is not None or self.args):
            raise ValueError("Only action may contain tool_name or args")
        if self.kind != "final" and self.final_answer is not None:
            raise ValueError("Only final may contain final_answer")
        if self.kind != "error" and self.error is not None:
            raise ValueError("Only error may contain error")


@dataclass
class StepTrace(_Validated):
    """One plan-compatible observation record, not a tool executor."""

    thought: str = ""
    action: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    observation: str = ""


@dataclass
class Usage(_Validated):
    """Explicit counters supplied by the future LLM client."""

    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    max_prompt: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        if any(value < 0 for value in (self.calls, self.prompt_tokens, self.completion_tokens, self.max_prompt)):
            raise ValueError("Usage counters must be nonnegative")


@dataclass
class RunTrace(_Validated):
    """Serializable run data matching PLAN.md; caller supplies timestamp."""

    timestamp: str
    question: str
    steps: list[StepTrace] = field(default_factory=list)
    final_answer: str = ""
    cited_doc_ids: list[str] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)


@dataclass
class ProcedureRequest(_Validated):
    """Proposed persisted record; C owns policy validation and write/verify."""

    request_id: str
    request_type: str
    employee: str
    details: str
    start_date: str = ""
    end_date: str = ""
    status: str = "submitted"
    created_at: str = ""
