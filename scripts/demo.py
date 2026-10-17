import asyncio
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from policy_agent.config import load_settings
from policy_agent.llm.client import call_llm
from policy_agent.agent.loop import run_agent

DEMO_QUESTIONS = [
    (
        "1. Tra cứu & Xử lý phiên bản (Lookup + Version Conflict)",
        "According to the latest international work policy, how many consecutive days can an employee work from another country and how many business days in advance must the request be submitted?",
    ),
    (
        "2. Làm thủ tục & Xác minh trạng thái (Write + Verify)",
        "Please submit a REMOTE_WORK request for employee Nguyen Van An from 2026-11-02 to 2026-11-05 at location Home Office with reason sprint planning, and verify that the request is saved.",
    ),
    (
        "3. Từ chối câu hỏi ngoài phạm vi (Calibration / no_answer)",
        "What is the company policy on employee stock option vesting schedules and cryptocurrency bonuses?",
    ),
]


def print_demo_result(title: str, trace) -> None:
    print("\n" + "=" * 76)
    print(f"DEMO CASE: {title}")
    print(f"Question : {trace.question}")
    print("-" * 76)
    for idx, step in enumerate(trace.steps, start=1):
        print(f"  Step {idx}:")
        if step.thought:
            print(f"    Thought     : {step.thought}")
        if step.action:
            print(f"    Action      : {step.action}")
            print(f"    Action Input: {json.dumps(step.args, ensure_ascii=False)}")
        if step.observation:
            obs = step.observation.replace("\n", " ")
            if len(obs) > 240:
                obs = obs[:240] + "..."
            print(f"    Observation : {obs}")
    print("-" * 76)
    print(f"Final Answer : {trace.final_answer}")
    print(f"Cited Docs   : {trace.cited_doc_ids}")
    print(
        f"USAGE        : calls={trace.usage.calls}, "
        f"prompt_tokens={trace.usage.prompt_tokens}, "
        f"completion_tokens={trace.usage.completion_tokens}, "
        f"max_prompt={trace.usage.max_prompt}"
    )
    print("=" * 76)


async def run_demo(tool_client=None, provider=None, settings=None) -> list:
    if settings is None:
        root = Path(__file__).resolve().parents[1]
        dotenv_file = root / ".env"
        settings = load_settings(
            project_root=root,
            dotenv_path=dotenv_file if dotenv_file.is_file() else None,
        )

    if provider is None:
        def default_provider(messages, usage):
            return call_llm(messages, settings, usage)
        provider = default_provider

    if tool_client is None:
        from policy_agent.mcp_client.client import MCPToolClient
        async with MCPToolClient(
            root=settings.project_root,
            requests_path=settings.requests_path,
            logs_dir=settings.logs_dir,
        ) as mcp_client:
            return await run_demo(tool_client=mcp_client, provider=provider, settings=settings)

    traces = []
    for idx_q, (title, question) in enumerate(DEMO_QUESTIONS):
        if idx_q > 0:
            await asyncio.sleep(2.0)
        trace = await run_agent(question, tool_client, provider, settings)
        print_demo_result(title, trace)
        traces.append(trace)

    return traces


def main() -> None:
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
