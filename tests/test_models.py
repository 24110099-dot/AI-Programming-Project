"""Contract tests for the proposed shared dataclasses."""
import importlib
from pathlib import Path


def test_document_contract_preserves_metadata():
    package = importlib.import_module("policy_agent")
    assert (Path(package.__file__).resolve().parent / "models.py").exists(), "D1 models.py is missing"
    models = importlib.import_module("policy_agent.models")
    metadata = models.DocumentMetadata(doc_id="DOC0101", title="Policy", version="2.0", date="2026-09-01", owner="HR", supersedes="DOC0005")
    document = models.Document(content="Policy text", metadata=metadata)
    chunk = models.DocumentChunk(chunk_id="DOC0101:0", content=document.content, metadata=metadata)
    assert document.metadata is metadata
    assert chunk.metadata is metadata
    assert chunk.metadata.supersedes == "DOC0005"
    assert chunk.embedding == []
    assert document.doc_id == "DOC0101"
    assert Path(models.__file__).resolve().parents[2] == Path(__file__).resolve().parents[1]


import json
from dataclasses import asdict
import pytest
from policy_agent import models


def metadata():
    return models.DocumentMetadata("DOC0101", "Policy", "2.0", "2026-09-01", "HR")


def test_agent_trace_serializes_plan_fields():
    assert hasattr(models, "RunTrace"), "Shared agent schemas are missing"
    action = models.ParsedAction(kind="action", tool_name="search_policy", args={"query": "leave"})
    tool = models.ToolSpec(name="search_policy", description="Search", input_schema={"type": "object"})
    step = models.StepTrace(thought="Look up policy", action=action.tool_name, args=action.args, observation="[DOC0101] result")
    run = models.RunTrace(timestamp="2026-10-13T10:00:00+07:00", question="leave?", steps=[step], final_answer="[DOC0101]", cited_doc_ids=["DOC0101"], usage=models.Usage(calls=1, prompt_tokens=12, completion_tokens=4, max_prompt=12))
    data = json.loads(json.dumps(asdict(run)))
    assert data["steps"][0]["action"] == tool.name
    assert data["usage"] == {"calls": 1, "prompt_tokens": 12, "completion_tokens": 4, "max_prompt": 12}


def test_mutable_defaults_are_independent():
    a = models.DocumentChunk("a", "text", metadata())
    b = models.DocumentChunk("b", "text", metadata())
    a.embedding.append(0.5)
    assert b.embedding == []
    x = models.RunTrace("now", "q")
    y = models.RunTrace("now", "q")
    x.steps.append(models.StepTrace())
    x.cited_doc_ids.append("DOC0101")
    x.usage.calls = 1
    assert y.steps == [] and y.cited_doc_ids == [] and y.usage.calls == 0
    action = models.ParsedAction(kind="action", tool_name="get_request")
    other = models.ParsedAction(kind="action", tool_name="get_request")
    action.args["id"] = "REQ-1"
    assert other.args == {}
    assert models.ToolSpec("one", "desc").input_schema is not models.ToolSpec("two", "desc").input_schema
    assert models.StepTrace().args is not models.StepTrace().args


@pytest.mark.parametrize("factory", [
    lambda: models.Document(content=123, metadata=metadata()),
    lambda: models.Document(content="x", metadata={"doc_id": "x"}),
    lambda: models.DocumentChunk("c", "x", metadata(), embedding=[True]),
    lambda: models.DocumentChunk("c", "x", metadata(), embedding=["0.5"]),
    lambda: models.ToolSpec("x", "desc", input_schema=[]),
    lambda: models.Usage(calls=True),
    lambda: models.RunTrace("now", "q", steps=[{}]),
])
def test_constructor_rejects_wrong_types(factory):
    with pytest.raises(TypeError):
        factory()


@pytest.mark.parametrize("changes", [{"doc_id": ""}, {"date": "2026-02-30"}, {"owner": "  "}])
def test_metadata_rejects_invalid_provenance(changes):
    data = asdict(metadata())
    data.update(changes)
    with pytest.raises(ValueError):
        models.DocumentMetadata(**data)


@pytest.mark.parametrize("field", ["calls", "prompt_tokens", "completion_tokens", "max_prompt"])
def test_usage_rejects_negative_counters(field):
    with pytest.raises(ValueError):
        models.Usage(**{field: -1})


def test_action_variants_validate():
    assert models.ParsedAction(kind="final", final_answer="answer").final_answer == "answer"
    assert models.ParsedAction(kind="error", error="bad JSON").error == "bad JSON"
    for kwargs in [{"kind": "unknown"}, {"kind": "action"}, {"kind": "final"}, {"kind": "error"}]:
        with pytest.raises(ValueError):
            models.ParsedAction(**kwargs)
    with pytest.raises(ValueError):
        models.ParsedAction(kind="action", tool_name="x", final_answer="contradiction")


def test_request_matches_store_boundary_without_enforcing_policy():
    request = models.ProcedureRequest(request_id="REQ-0001", request_type="work_from_abroad", employee="Demo", details="HCM", start_date="2026-11-02", end_date="2026-11-13", created_at="2026-10-13T00:00:00Z")
    assert request.status == "submitted"
    assert asdict(request)["details"] == "HCM"
    with pytest.raises(TypeError):
        models.ProcedureRequest(request_id="r", request_type="x", employee=1, details="x")


def test_empty_embedding_is_not_computed_and_numeric_values_are_preserved():
    chunk = models.DocumentChunk("c", "", metadata(), embedding=[1, 0.5])
    assert chunk.embedding == [1, 0.5]
    assert models.DocumentChunk("c", "", metadata()).embedding == []

