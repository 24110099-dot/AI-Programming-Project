import ast
import json
import re
from policy_agent.models import ParsedAction


def _check_unique_keys(pairs):
    # Hook kiểm tra phát hiện trùng lặp key trong JSON
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate key")
        result[key] = value
    return result


def _parse_action_input(raw_json_str: str) -> dict:
    # Bước 1: Thử parse bằng json.loads chuẩn
    try:
        return json.loads(raw_json_str, object_pairs_hook=_check_unique_keys)
    except json.JSONDecodeError:
        # Bước 2 (Fallback): Khi LLM dùng nháy đơn thay vì nháy kép
        # Dùng AST để parse an toàn, không dùng eval() trực tiếp
        tree = ast.parse(raw_json_str, mode="eval")
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                keys = [ast.literal_eval(key) for key in node.keys]
                if len(keys) != len(set(keys)):
                    raise ValueError("Duplicate key")
        return ast.literal_eval(tree)


def parse_response(text: str) -> ParsedAction:
    try:
        if not isinstance(text, str) or len(text) > 50000:
            raise ValueError("Response must be a bounded string")

        # Tìm các dòng Action và Final Answer trong câu trả lời
        action_matches = re.findall(r"^Action:\s*(.*)$", text, re.MULTILINE)
        final_matches = re.findall(r"^Final Answer:\s*(.*)$", text, re.MULTILINE)

        # Bắt buộc phải có đúng 1 Action HOẶC đúng 1 Final Answer
        if len(action_matches) + len(final_matches) != 1:
            raise ValueError("Expected exactly one Action or Final Answer")

        # Trường hợp 1: LLM đưa ra câu trả lời cuối cùng
        if final_matches:
            answer = text.split("Final Answer:", 1)[1].strip()
            return ParsedAction(kind="final", final_answer=answer)

        # Trường hợp 2: LLM muốn gọi tool
        input_matches = re.findall(r"^Action Input:\s*", text, re.MULTILINE)
        if len(input_matches) != 1:
            raise ValueError("Expected one Action Input")

        raw_input = text.split("Action Input:", 1)[1].strip()
        args = _parse_action_input(raw_input)

        # Kiểm tra tham số phải là dict không rỗng và các key là chuỗi
        if not isinstance(args, dict) or not args or not all(isinstance(k, str) for k in args):
            raise ValueError("Action Input must be a nonempty object")

        # Chặn các giá trị NaN/Infinity
        json.dumps(args, allow_nan=False)

        tool_name = action_matches[0].strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tool_name):
            raise ValueError("Invalid tool name")

        return ParsedAction(kind="action", tool_name=tool_name, args=args)

    except (ValueError, TypeError, SyntaxError, RecursionError, MemoryError):
        # Không làm crash chương trình khi output lỗi, trả về ParsedAction dạng error
        return ParsedAction(
            kind="error",
            error="Invalid ReAct response; supply one Action with object input, or one Final Answer"
        )
