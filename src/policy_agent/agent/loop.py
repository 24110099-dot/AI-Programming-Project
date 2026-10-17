"""Async tool orchestration with an immediate write/read verification guard."""
import asyncio
import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from policy_agent.models import ParsedAction, RunTrace, StepTrace, ToolSpec
from policy_agent.agent.parser import parse_response
from policy_agent.agent.trace import save_trace


_FIELDS = ("request_type", "employee", "details", "start_date", "end_date")
_UNVERIFIED = "Đơn chưa xác minh; không thể xác nhận đã lưu thành công."


def _record(text):
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("Expected a request record object")
    if not isinstance(value.get("request_id"), str) or not value["request_id"].strip():
        raise ValueError("Missing request_id")
    if value.get("status") != "submitted":
        raise ValueError("Request is not submitted")
    return value


def _matches(record, expected):
    return all(isinstance(record.get(field), str) and record[field] == expected.get(field, "") for field in _FIELDS)


async def run_agent(question, tool_client, provider, settings, *, prompt_path=None):
    """Accept async list_tools/call_tool and sync provider(messages, usage) -> str.

    Each decision or forced verification consumes one MAX_STEPS slot.
    Tool errors end ambiguous writes rather than retrying a non-idempotent write.
    """
    stamp = datetime.now(timezone.utc)
    run = RunTrace(timestamp=stamp.isoformat(), question=question)
    filename = "run_" + stamp.strftime("%Y%m%dT%H%M%S_%fZ") + "_" + uuid4().hex[:8] + ".jsonl"
    pending, verified = None, []
    write_attempted = False
    try:
        tools = await tool_client.list_tools()
        if not isinstance(tools, list) or not all(isinstance(tool, ToolSpec) for tool in tools):
            raise TypeError("list_tools must return list[ToolSpec]")
        names = {tool.name for tool in tools}
        path = Path(prompt_path) if prompt_path else Path(__file__).resolve().parents[3] / "prompts/agent_system.txt"
        system = path.read_text(encoding="utf-8").replace("{{TOOLS}}", json.dumps([asdict(tool) for tool in tools], ensure_ascii=False))
        messages = [{"role": "system", "content": system}, {"role": "user", "content": question}]
        for number in range(settings.max_steps):
            forced = pending is not None
            if forced:
                decision = ParsedAction(kind="action", tool_name="get_request", args={"request_id": pending[0]})
                messages.append({"role": "assistant", "content": "Action: get_request\nAction Input: " + json.dumps(decision.args)})
            else:
                text = await asyncio.to_thread(provider, list(messages), run.usage)
                decision = parse_response(text)
                messages.append({"role": "assistant", "content": text})
            step = StepTrace()
            run.steps.append(step)
            if decision.kind == "final":
                run.final_answer = decision.final_answer
                if verified:
                    run.final_answer = "Đã xác minh " + ", ".join(verified) + ". " + run.final_answer
                break
            if decision.kind == "error":
                step.observation = "Error: " + decision.error
            else:
                step.action, step.args = decision.tool_name, decision.args
                if step.action == "create_request" and (step.action not in names or "get_request" not in names or settings.max_steps - number < 2):
                    step.observation = "Error: write blocked; need discovered create/get and one remaining verification step"
                    run.final_answer = "Đơn chưa xác minh; MAX_STEPS hoặc tool create/get không đủ để thực hiện ghi."
                    break
                elif step.action not in names:
                    step.observation = "Error: Unknown tool"
                else:
                    if step.action == "create_request":
                        write_attempted = True
                    try:
                        observation = await tool_client.call_tool(step.action, step.args)
                        if not isinstance(observation, str):
                            raise TypeError("call_tool must return string")
                        step.observation = observation
                    except Exception as exc:
                        step.observation = "Error: tool exception " + type(exc).__name__
                    if step.action == "create_request":
                        try:
                            record = _record(step.observation)
                            pending = (record["request_id"], dict(step.args), record)
                        except (ValueError, TypeError):
                            run.final_answer = _UNVERIFIED
                            break
                    elif forced:
                        try:
                            record = _record(step.observation)
                            if record["request_id"] != pending[0] or not _matches(record, pending[1]) or not _matches(pending[2], pending[1]):
                                raise ValueError("Verification mismatch")
                            verified.append(record["request_id"])
                            pending = None
                        except (ValueError, TypeError):
                            step.observation = "Error: verification failed; " + step.observation
                            run.final_answer = _UNVERIFIED
                            break
            messages.append({"role": "user", "content": "Observation: " + step.observation})
        if not run.final_answer:
            run.final_answer = "Đã đạt MAX_STEPS; chưa có câu trả lời được xác nhận."
    except Exception as exc:
        run.steps.append(StepTrace(observation="Error: run exception " + type(exc).__name__))
        run.final_answer = _UNVERIFIED if write_attempted else "Không hoàn tất lượt chạy; hãy kiểm tra trace lỗi."
    run.cited_doc_ids = sorted(set(re.findall(r"\[(DOC[A-Za-z0-9_-]+)\]", run.final_answer)))
    save_trace(run, settings.logs_dir / filename)
    return run
