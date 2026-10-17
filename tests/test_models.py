from dataclasses import asdict
import pytest
from policy_agent.models import (
    Document,
    DocumentChunk,
    DocumentMetadata,
    ParsedAction,
    ProcedureRequest,
    RunTrace,
    StepTrace,
    ToolSpec,
    Usage,
)


def test_document_and_chunk_models():
    meta = DocumentMetadata(
        doc_id="DOC0001",
        title="Company Policy",
        version="1.0",
        date="2026-09-01",
        owner="HR",
        category="policy",
    )
    doc = Document(content="Remote work allowed", metadata=meta)
    chunk = DocumentChunk(chunk_id="DOC0001:0", content="Remote work", metadata=meta, embedding=[0.1, 0.2])
    assert doc.doc_id == "DOC0001"
    assert asdict(chunk)["chunk_id"] == "DOC0001:0"


def test_invalid_metadata_date():
    with pytest.raises(ValueError):
        DocumentMetadata(
            doc_id="DOC0001",
            title="Policy",
            version="1.0",
            date="2026/09/01",
            owner="HR",
        )


def test_agent_and_request_dataclasses():
    tool = ToolSpec(name="search_policy", description="Search policy")
    act = ParsedAction(kind="action", tool_name="search_policy", args={"query": "remote"})
    trace = RunTrace(timestamp="2026-10-18T00:00:00Z", question="Test?", steps=[StepTrace(thought="t")], usage=Usage(calls=1))
    req = ProcedureRequest(request_id="REQ-1", request_type="REMOTE_WORK", employee="An", details="{}")
    assert tool.name == "search_policy"
    assert act.tool_name == "search_policy"
    assert trace.usage.calls == 1
    assert req.status == "submitted"
