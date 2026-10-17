import ast
import json
import re
from policy_agent.models import ParsedAction


def _parse_action_input(raw_json_str: str) -> dict:
    try:
        return json.loads(raw_json_str)
    except json.JSONDecodeError:
        return ast.literal_eval(raw_json_str)


def parse_response(text: str) -> ParsedAction:
    try:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Empty response")
        action_matches = re.findall(r"^Action:\s*(.*)$", text, re.MULTILINE)
        final_matches = re.findall(r"^Final Answer:\s*(.*)$", text, re.MULTILINE)
        if len(action_matches) + len(final_matches) != 1:
            raise ValueError("Expected one Action or one Final Answer")
        if final_matches:
            answer = text.split("Final Answer:", 1)[1].strip()
            if not answer:
                raise ValueError("Empty Final Answer")
            return ParsedAction(kind="final", final_answer=answer)
        input_matches = re.findall(r"^Action Input:\s*", text, re.MULTILINE)
        if len(input_matches) != 1:
            raise ValueError("Expected one Action Input")
        raw_input = text.split("Action Input:", 1)[1].strip()
        args = _parse_action_input(raw_input)
        if not isinstance(args, dict) or not args:
            raise ValueError("Action Input must be a non-empty dictionary")
        tool_name = action_matches[0].strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tool_name):
            raise ValueError("Invalid tool name")
        return ParsedAction(kind="action", tool_name=tool_name, args=args)
    except Exception:
        return ParsedAction(
            kind="error",
            error="Invalid ReAct response; supply one Action with object input, or one Final Answer",
        )
