import asyncio
import json
from policy_agent.config import Settings
from policy_agent.models import ToolSpec
from policy_agent.agent.loop import run_agent


class FakeTools:
    """Test-only tool transport, not a running MCP server."""
    def __init__(self):
        self.calls = []
        self.record = None

    async def list_tools(self):
        return [ToolSpec(name, "test tool", {"type": "object"}) for name in ("search_policy", "create_request", "get_request")]

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        if name == "search_policy":
            return "[DOC0101] version 2.0: 21 days"
        if name == "create_request":
            self.record = {"request_id": "REQ-test", "status": "submitted", "start_date": "", "end_date": "", **args}
            return json.dumps(self.record)
        return json.dumps(self.record)


class FakeLLM:
    """Test-only scripted completions, not API evidence."""
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.messages = []

    def __call__(self, messages, usage):
        self.messages.append(list(messages))
        usage.calls += 1
        return next(self.outputs)


def run(tmp_path, outputs, tools=None, max_steps=8):
    tools = tools or FakeTools()
    provider = FakeLLM(outputs)
    result = asyncio.run(run_agent("test question", tools, provider, Settings(tmp_path, max_steps=max_steps)))
    return result, tools, provider


def test_search_final_dynamic_prompt_and_trace(tmp_path):
    result, tools, provider = run(tmp_path, ['Action: search_policy\nAction Input: {"query":"abroad"}', 'Final Answer: 21 days [DOC0101]'])
    assert result.final_answer == "21 days [DOC0101]"
    assert len(result.steps) == 2
    assert result.cited_doc_ids == ["DOC0101"]
    assert result.usage.calls == 2
    assert '"name": "search_policy"' in provider.messages[0][0]["content"]
    rows = [json.loads(line) for line in next((tmp_path / "logs").glob("run_*.jsonl")).read_text(encoding="utf-8").splitlines()]
    assert rows[-1]["event"] == "USAGE"


CREATE = 'Action: create_request\nAction Input: {"request_type":"REMOTE_WORK","employee":"An","details":"two days"}'


def test_write_forces_immediate_verify_before_final(tmp_path):
    result, tools, provider = run(tmp_path, [CREATE, "Final Answer: saved"])
    assert [name for name, args in tools.calls] == ["create_request", "get_request"]
    assert tools.calls[1][1] == {"request_id": "REQ-test"}
    assert len(result.steps) == 3
    assert "Đã xác minh REQ-test" in result.final_answer
    assert provider.messages[-1][-1]["content"].startswith("Observation:")


def test_write_not_allowed_without_verify_budget(tmp_path):
    result, tools, _ = run(tmp_path, [CREATE], max_steps=1)
    assert tools.calls == []
    assert "MAX_STEPS" in result.final_answer


class BadGet(FakeTools):
    async def call_tool(self, name, args):
        output = await super().call_tool(name, args)
        if name == "get_request":
            record = json.loads(output)
            record["details"] = "wrong"
            return json.dumps(record)
        return output


def test_wrong_record_cannot_claim_success(tmp_path):
    result, tools, _ = run(tmp_path, [CREATE, "Final Answer: saved"], tools=BadGet())
    assert [name for name, args in tools.calls] == ["create_request", "get_request"]
    assert "chưa xác minh" in result.final_answer
    assert "saved" not in result.final_answer


class BrokenTools(FakeTools):
    def __init__(self, failure):
        super().__init__()
        self.failure = failure

    async def call_tool(self, name, args):
        if name == self.failure:
            raise RuntimeError("do not log secret exception text")
        return await super().call_tool(name, args)


def test_tool_exception_is_safe_observation(tmp_path):
    result, _, _ = run(tmp_path, ['Action: search_policy\nAction Input: {"query":"x"}', 'Final Answer: no evidence'], tools=BrokenTools("search_policy"))
    assert result.steps[0].observation == "Error: tool exception RuntimeError"
    assert result.final_answer == "no evidence"


def test_unknown_tool_and_parser_error_recover(tmp_path):
    result, tools, _ = run(tmp_path, ['Action: invented\nAction Input: {"q":"x"}', 'bad', 'Final Answer: no evidence'])
    assert tools.calls == []
    assert len(result.steps) == 3
    assert result.steps[0].observation == "Error: Unknown tool"
    assert result.steps[1].observation.startswith("Error:")


def test_verify_exception_cannot_claim_success(tmp_path):
    result, _, _ = run(tmp_path, [CREATE, 'Final Answer: saved'], tools=BrokenTools("get_request"))
    assert "chưa xác minh" in result.final_answer


class NoCreate(FakeTools):
    async def list_tools(self):
        return [ToolSpec("get_request", "test", {})]


def test_undiscovered_create_cannot_claim_success(tmp_path):
    result, tools, _ = run(tmp_path, [CREATE, 'Final Answer: saved'], tools=NoCreate())
    assert tools.calls == []
    assert "chưa xác minh" in result.final_answer


class NoGet(FakeTools):
    async def list_tools(self):
        return [ToolSpec("create_request", "test", {})]


def test_missing_get_blocks_write_and_success_final(tmp_path):
    result, tools, _ = run(tmp_path, [CREATE, 'Final Answer: saved'], tools=NoGet())
    assert tools.calls == []
    assert "chưa xác minh" in result.final_answer
    assert "saved" not in result.final_answer


def test_last_step_verify_does_not_exceed_budget(tmp_path):
    result, tools, provider = run(tmp_path, [CREATE], max_steps=2)
    assert [name for name, args in tools.calls] == ["create_request", "get_request"]
    assert len(result.steps) == 2
    assert result.usage.calls == 1
    assert "MAX_STEPS" in result.final_answer


class ChangedRecord(FakeTools):
    def __init__(self, field):
        super().__init__()
        self.field = field

    async def call_tool(self, name, args):
        output = await super().call_tool(name, args)
        if name == "get_request":
            value = json.loads(output)
            value[self.field] = "wrong"
            return json.dumps(value)
        return output


def test_each_record_field_is_checked(tmp_path):
    for field in ("request_id", "status", "request_type", "employee", "details", "start_date", "end_date"):
        result, _, _ = run(tmp_path, [CREATE, 'Final Answer: saved'], tools=ChangedRecord(field))
        assert "chưa xác minh" in result.final_answer


class ErrorCreate(FakeTools):
    async def call_tool(self, name, args):
        self.calls.append((name, args))
        return "Error: refused"


def test_error_create_stops_without_false_success(tmp_path):
    result, tools, _ = run(tmp_path, [CREATE, 'Final Answer: saved'], tools=ErrorCreate())
    assert [name for name, args in tools.calls] == ["create_request"]
    assert "chưa xác minh" in result.final_answer


def test_create_exception_never_retries_write(tmp_path):
    result, _, _ = run(tmp_path, [CREATE, CREATE], tools=BrokenTools("create_request"))
    assert len(result.steps) == 1
    assert "chưa xác minh" in result.final_answer


