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


from policy_agent.agent.trace import stream_print


def print_run_trace(trace) -> None:
    print("\n" + "=" * 70)
    print(f"Question: {trace.question}")
    print("-" * 70)
    for idx, step in enumerate(trace.steps, start=1):
        print(f"[Step {idx}]")
        if step.thought:
            print(f"  Thought     : {step.thought}")
        if step.action:
            print(f"  Action      : {step.action}")
            print(f"  Action Input: {json.dumps(step.args, ensure_ascii=False)}")
        if step.observation:
            obs_preview = step.observation.replace("\n", " ")
            if len(obs_preview) > 220:
                obs_preview = obs_preview[:220] + "..."
            print(f"  Observation : {obs_preview}")
    print("-" * 70)
    sys.stdout.write("Final Answer  : ")
    sys.stdout.flush()
    stream_print(trace.final_answer, delay=0.015)
    print(f"Cited Docs    : {trace.cited_doc_ids}")
    print(
        f"USAGE         : calls={trace.usage.calls}, "
        f"prompt_tokens={trace.usage.prompt_tokens}, "
        f"completion_tokens={trace.usage.completion_tokens}, "
        f"max_prompt={trace.usage.max_prompt}"
    )
    print("=" * 70 + "\n")


async def run_chat_session(tool_client=None, provider=None, settings=None) -> None:
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
            await run_chat_session(tool_client=mcp_client, provider=provider, settings=settings)
            return

    # Nếu truyền câu hỏi trực tiếp qua tham số dòng lệnh thì chạy 1 lượt rồi thoát
    cli_args = [arg for arg in sys.argv[1:] if arg.strip()]
    if cli_args:
        question = " ".join(cli_args)
        trace = await run_agent(question, tool_client, provider, settings)
        print_run_trace(trace)
        return

    print("Policy Agent CLI (gõ 'exit' hoặc 'quit' để thoát)")
    while True:
        try:
            question = input("\nBạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nĐã thoát phiên hỏi đáp.")
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit", "q"):
            print("Đã thoát phiên hỏi đáp.")
            break

        trace = await run_agent(question, tool_client, provider, settings)
        print_run_trace(trace)


def main() -> None:
    asyncio.run(run_chat_session())


if __name__ == "__main__":
    main()
