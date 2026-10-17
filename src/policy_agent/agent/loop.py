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

# Các trường cần đối chiếu khi kiểm tra đơn
REQUEST_FIELDS = ("request_type", "employee", "details", "start_date", "end_date")
UNVERIFIED_MESSAGE = "Đơn chưa xác minh; không thể xác nhận đã lưu thành công."


def _parse_request_record(text: str) -> dict:
    # Đọc bản ghi JSON trả về từ tool create_request hoặc get_request
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Expected a request record object")
    if not isinstance(data.get("request_id"), str) or not data["request_id"].strip():
        raise ValueError("Missing request_id")
    if data.get("status") != "submitted":
        raise ValueError("Request is not submitted")
    return data


def _match_request_fields(record: dict, expected: dict) -> bool:
    # So sánh xem dữ liệu đọc lại có khớp với dữ liệu lúc gửi tạo đơn không
    for field in REQUEST_FIELDS:
        if not isinstance(record.get(field), str):
            return False
        if record[field] != expected.get(field, ""):
            return False
    return True


def _extract_thought(text: str) -> str:
    if not isinstance(text, str):
        return ""
    match = re.search(r"^Thought:\s*(.*)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


async def run_agent(question: str, tool_client=None, provider=None, settings=None, *, prompt_path=None) -> RunTrace:
    # Tự động nạp cấu hình, LLM provider và MCP client nếu người gọi chỉ truyền question
    if settings is None:
        from policy_agent.config import load_settings
        root = Path(__file__).resolve().parents[3]
        dotenv_file = root / ".env"
        settings = load_settings(
            project_root=root,
            dotenv_path=dotenv_file if dotenv_file.is_file() else None,
        )

    if provider is None:
        from policy_agent.llm.client import call_llm
        def default_provider(msgs, usage):
            return call_llm(msgs, settings, usage)
        provider = default_provider

    if tool_client is None:
        from policy_agent.mcp_client.client import MCPToolClient
        async with MCPToolClient(
            root=settings.project_root,
            requests_path=settings.requests_path,
            logs_dir=settings.logs_dir,
        ) as mcp_client:
            return await run_agent(
                question,
                mcp_client,
                provider,
                settings,
                prompt_path=prompt_path,
            )

    # Khởi tạo đối tượng lưu vết (trace) cho lượt chạy
    now = datetime.now(timezone.utc)
    run_trace = RunTrace(timestamp=now.isoformat(), question=question)
    trace_filename = f"run_{now.strftime('%Y%m%dT%H%M%S_%fZ')}_{uuid4().hex[:8]}.jsonl"

    pending_record = None  # Lưu tạm đơn vừa tạo để ép buộc bước sau phải verify
    verified_requests = []
    write_attempted = False

    try:
        # Bước 1: Khám phá danh sách tool động từ MCP server
        discovered_tools = await tool_client.list_tools()
        if not isinstance(discovered_tools, list) or not all(isinstance(t, ToolSpec) for t in discovered_tools):
            raise TypeError("list_tools must return list[ToolSpec]")

        available_tool_names = {t.name for t in discovered_tools}

        # Nạp system prompt và điền danh sách công cụ vào {{TOOLS}}
        prompt_file = Path(prompt_path) if prompt_path else Path(__file__).resolve().parents[3] / "prompts/agent_system.txt"
        tools_json = json.dumps([asdict(t) for t in discovered_tools], ensure_ascii=False)
        system_prompt = prompt_file.read_text(encoding="utf-8").replace("{{TOOLS}}", tools_json)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        # Bước 2: Vòng lặp ReAct chính (tối đa max_steps bước)
        for step_idx in range(settings.max_steps):
            is_forced_verify = pending_record is not None
            thought_text = ""

            if is_forced_verify:
                # Cơ chế Guard: Nếu vừa tạo đơn, bước tiếp theo BẮT BUỘC gọi get_request để verify
                thought_text = f"Kiểm tra lại đơn {pending_record[0]} vừa tạo bằng get_request"
                decision = ParsedAction(
                    kind="action",
                    tool_name="get_request",
                    args={"request_id": pending_record[0]},
                )
                messages.append({
                    "role": "assistant",
                    "content": f"Action: get_request\nAction Input: {json.dumps(decision.args)}",
                })
            else:
                # Gọi LLM để sinh Thought và Action tiếp theo
                llm_response = await asyncio.to_thread(provider, list(messages), run_trace.usage)
                thought_text = _extract_thought(llm_response)
                decision = parse_response(llm_response)
                messages.append({"role": "assistant", "content": llm_response})

            current_step = StepTrace(thought=thought_text)
            run_trace.steps.append(current_step)

            # Trường hợp LLM đưa ra Final Answer -> Kết thúc
            if decision.kind == "final":
                run_trace.final_answer = decision.final_answer
                if verified_requests:
                    verified_ids = ", ".join(verified_requests)
                    run_trace.final_answer = f"Đã xác minh {verified_ids}. {run_trace.final_answer}"
                break

            # Trường hợp LLM sinh output bị lỗi format
            if decision.kind == "error":
                current_step.observation = f"Error: {decision.error}"
            else:
                current_step.action = decision.tool_name
                current_step.args = dict(decision.args)

                # Nếu LLM truyền details dạng dict khi gọi create_request thì chuyển sang chuỗi JSON
                if current_step.action == "create_request" and isinstance(current_step.args.get("details"), dict):
                    current_step.args["details"] = json.dumps(current_step.args["details"], ensure_ascii=False)

                # Ràng buộc an toàn: Không cho phép tạo đơn nếu không đủ bước để verify
                remaining_steps = settings.max_steps - step_idx
                if current_step.action == "create_request" and (
                    current_step.action not in available_tool_names
                    or "get_request" not in available_tool_names
                    or remaining_steps < 2
                ):
                    current_step.observation = "Error: write blocked; need discovered create/get and one remaining verification step"
                    run_trace.final_answer = "Đơn chưa xác minh; MAX_STEPS hoặc tool create/get không đủ để thực hiện ghi."
                    break

                if current_step.action not in available_tool_names:
                    current_step.observation = "Error: Unknown tool"
                else:
                    if current_step.action == "create_request":
                        write_attempted = True

                    # Gọi tool qua MCP client
                    try:
                        observation_str = await tool_client.call_tool(current_step.action, current_step.args)
                        if not isinstance(observation_str, str):
                            raise TypeError("call_tool must return string")
                        current_step.observation = observation_str
                    except Exception as err:
                        current_step.observation = f"Error: tool exception {type(err).__name__}"

                    # Nếu là lệnh tạo đơn, lưu lại bản ghi để bước sau kiểm chứng
                    if current_step.action == "create_request":
                        try:
                            record = _parse_request_record(current_step.observation)
                            pending_record = (record["request_id"], dict(current_step.args), record)
                        except (ValueError, TypeError):
                            run_trace.final_answer = UNVERIFIED_MESSAGE
                            break

                    # Nếu là bước verify bắt buộc, đối chiếu dữ liệu đọc lại
                    elif is_forced_verify:
                        try:
                            record = _parse_request_record(current_step.observation)
                            if (
                                record["request_id"] != pending_record[0]
                                or not _match_request_fields(record, pending_record[1])
                                or not _match_request_fields(pending_record[2], pending_record[1])
                            ):
                                raise ValueError("Verification mismatch")
                            verified_requests.append(record["request_id"])
                            pending_record = None
                        except (ValueError, TypeError):
                            current_step.observation = f"Error: verification failed; {current_step.observation}"
                            run_trace.final_answer = UNVERIFIED_MESSAGE
                            break

            # Cung cấp Observation làm phản hồi cho Agent ở bước sau
            messages.append({"role": "user", "content": f"Observation: {current_step.observation}"})

        # Nếu chạy hết số bước quy định mà chưa có kết luận
        if not run_trace.final_answer:
            run_trace.final_answer = "Đã đạt MAX_STEPS; chưa có câu trả lời được xác nhận."

    except Exception as err:
        run_trace.steps.append(StepTrace(observation=f"Error: run exception {type(err).__name__}"))
        run_trace.final_answer = UNVERIFIED_MESSAGE if write_attempted else "Không hoàn tất lượt chạy; hãy kiểm tra trace lỗi."

    # Trích xuất các doc_id được trích dẫn trong Final Answer
    run_trace.cited_doc_ids = sorted(set(re.findall(r"\[(DOC[A-Za-z0-9_-]+)\]", run_trace.final_answer)))

    # Lưu trace ra file log JSONL
    save_trace(run_trace, settings.logs_dir / trace_filename)
    return run_trace
