import asyncio
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

from policy_agent.config import Settings
from policy_agent.models import ToolSpec


def _load_script(name: str):
    root = Path(__file__).resolve().parents[1]
    script_path = root / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_demo_is_offline_and_prints_verify_usage(tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("GROQ_API_KEY", None)
    result = subprocess.run(
        [sys.executable, str(root / "scripts/demo_agent_fake.py"), str(tmp_path)],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    assert "TEST-ONLY" in result.stdout
    assert '"action": "create_request"' in result.stdout
    assert '"action": "get_request"' in result.stdout
    assert '"event": "USAGE"' in result.stdout


def test_demo_script_runs_all_three_questions(tmp_path, capsys):
    demo_mod = _load_script("demo.py")
    chat_mod = _load_script("chat.py")

    class DemoFakeTools:
        def __init__(self):
            self.record = None

        async def list_tools(self):
            return [
                ToolSpec(name, "tool", {"type": "object"})
                for name in ("search_policy", "create_request", "get_request")
            ]

        async def call_tool(self, name, args):
            if name == "search_policy":
                if "stock" in args.get("query", "").lower():
                    return "No relevant passages found."
                return "[DOC0101 v2.0 2026-09-01] Up to 21 consecutive days; submit 15 business days in advance."
            if name == "create_request":
                self.record = {
                    "request_id": "REQ-demo01",
                    "status": "submitted",
                    "start_date": args.get("start_date", ""),
                    "end_date": args.get("end_date", ""),
                    "request_type": args["request_type"],
                    "employee": args["employee"],
                    "details": args["details"],
                }
                return json.dumps(self.record)
            return json.dumps(self.record)

    scripted_outputs = iter([
        # Question 1: lookup
        'Thought: Tra cứu quy định làm việc quốc tế\nAction: search_policy\nAction Input: {"query": "international work policy consecutive days"}',
        'Thought: Đã có thông tin từ DOC0101\nFinal Answer: Tối đa 21 ngày liên tiếp và nộp trước 15 ngày làm việc [DOC0101].',
        # Question 2: write + verify
        'Thought: Tạo đơn REMOTE_WORK\nAction: create_request\nAction Input: {"request_type": "REMOTE_WORK", "employee": "Nguyen Van An", "details": "{\\"reason\\":\\"sprint planning\\",\\"location\\":\\"Home Office\\"}", "start_date": "2026-11-02", "end_date": "2026-11-05"}',
        'Thought: Đã xác minh đơn\nFinal Answer: Đã tạo và xác minh đơn làm việc từ xa thành công [DOC0102].',
        # Question 3: no_answer
        'Thought: Kiểm tra quy định stock option\nAction: search_policy\nAction Input: {"query": "stock option vesting cryptocurrency"}',
        'Thought: Không có trong tài liệu\nFinal Answer: Xin lỗi, quy chế hiện tại không có thông tin về stock option hay thưởng tiền mã hóa.',
    ])

    def fake_provider(messages, usage):
        usage.calls += 1
        return next(scripted_outputs)

    settings = Settings(tmp_path)
    traces = asyncio.run(
        demo_mod.run_demo(tool_client=DemoFakeTools(), provider=fake_provider, settings=settings)
    )
    assert len(traces) == 3
    assert traces[0].cited_doc_ids == ["DOC0101"]
    assert "Đã xác minh REQ-demo01" in traces[1].final_answer
    assert traces[2].cited_doc_ids == []

    chat_mod.print_run_trace(traces[0])
    captured = capsys.readouterr().out
    assert "DEMO CASE:" in captured
    assert "USAGE" in captured
