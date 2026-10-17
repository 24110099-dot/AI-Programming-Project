import asyncio
import json
from policy_agent.config import Settings
from policy_agent.models import ToolSpec
from policy_agent.agent.loop import run_agent


class FakeClient:
    def __init__(self, tools=None, outputs=None):
        self.tools = tools or [
            ToolSpec("search_policy", "Search", {}),
            ToolSpec("create_request", "Create", {}),
            ToolSpec("get_request", "Get", {}),
        ]
        self.outputs = outputs or {}
        self.called = []

    async def list_tools(self):
        return self.tools

    async def call_tool(self, name, args):
        self.called.append((name, args))
        return self.outputs.get(name, "ok")


def test_agent_lookup_and_citation(tmp_path):
    responses = iter([
        'Thought: Tim quy che\nAction: search_policy\nAction Input: {"query": "remote"}',
        "Thought: Xong\nFinal Answer: Duoc lam tu xa 3 ngay [DOC0001].",
    ])
    client = FakeClient(outputs={"search_policy": "[DOC0001] 3 days per week"})
    trace = asyncio.run(run_agent("Remote?", client, lambda m, u: next(responses), Settings(tmp_path)))
    assert "DOC0001" in trace.cited_doc_ids
    assert len(trace.steps) == 2


def test_agent_write_forces_verify_step(tmp_path):
    rec = json.dumps({
        "request_id": "REQ-123",
        "request_type": "REMOTE_WORK",
        "employee": "An",
        "details": '{"reason": "test", "location": "home"}',
        "start_date": "2026-11-02",
        "end_date": "2026-11-03",
        "status": "submitted",
    })
    responses = iter([
        'Thought: Tao don\nAction: create_request\nAction Input: {"request_type": "REMOTE_WORK", "employee": "An", "details": {"reason": "test", "location": "home"}, "start_date": "2026-11-02", "end_date": "2026-11-03"}',
        "Thought: Da xac minh\nFinal Answer: Don REQ-123 da tao thanh cong.",
    ])
    client = FakeClient(outputs={"create_request": rec, "get_request": rec})
    trace = asyncio.run(run_agent("Create request", client, lambda m, u: next(responses), Settings(tmp_path)))
    assert [c[0] for c in client.called] == ["create_request", "get_request"]
    assert "REQ-123" in trace.final_answer


def test_agent_max_steps_guard(tmp_path):
    client = FakeClient(outputs={"search_policy": "hit"})
    trace = asyncio.run(
        run_agent(
            "Loop?",
            client,
            lambda m, u: 'Action: search_policy\nAction Input: {"query": "x"}',
            Settings(tmp_path, max_steps=2),
        )
    )
    assert len(trace.steps) == 2
    assert "MAX_STEPS" in trace.final_answer
