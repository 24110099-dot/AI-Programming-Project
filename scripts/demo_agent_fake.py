"""Offline phase-1 demo only; not real Groq/MCP/RAG evidence."""
import asyncio
import json
import sys
from pathlib import Path
from policy_agent.config import load_settings
from policy_agent.models import ToolSpec
from policy_agent.agent.loop import run_agent


class FakeTools:
    """Keep one synthetic request in memory only."""
    def __init__(self):
        self.record = None

    async def list_tools(self):
        return [ToolSpec(name, "TEST-ONLY in-memory tool", {"type": "object"}) for name in ("create_request", "get_request")]

    async def call_tool(self, name, args):
        if name == "create_request":
            self.record = {"request_id": "REQ-test", "status": "submitted", "start_date": "", "end_date": "", **args}
        elif name != "get_request" or args["request_id"] != self.record["request_id"]:
            return "Error: unknown request"
        return json.dumps(self.record)


class FakeLLM:
    """Scripted answers and synthetic call counts; zero measured API tokens."""
    def __init__(self):
        self.outputs = iter([
            'Action: create_request\nAction Input: {"request_type":"REMOTE_WORK","employee":"An","details":"two days"}',
            'Final Answer: Đã đọc lại đúng bản ghi thử nghiệm.',
        ])

    def __call__(self, messages, usage):
        usage.calls += 1
        return next(self.outputs)


async def main():
    root = Path(__file__).resolve().parents[1]
    log_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root
    settings = load_settings(project_root=log_root, environ={})
    print("TEST-ONLY: fake Groq + fake tools; no network, no real request store")
    run = await run_agent("Tạo đơn thử nghiệm", FakeTools(), FakeLLM(), settings, prompt_path=root / "prompts/agent_system.txt")
    files = sorted(settings.logs_dir.glob("run_*.jsonl"), key=lambda path: path.stat().st_mtime_ns)
    print(files[-1].read_text(encoding="utf-8"), end="")
    if len(run.steps) < 2 or not run.final_answer.startswith("Đã xác minh"):
        raise RuntimeError("Fake demo failed")


if __name__ == "__main__":
    asyncio.run(main())
