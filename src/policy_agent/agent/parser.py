"""Parse one ReAct decision; never execute text from a model."""
import ast
import json
import re
from policy_agent.models import ParsedAction


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate key")
        result[key] = value
    return result


def parse_response(text):
    """Recover single-quoted dictionaries safely; report malformed input."""
    try:
        if not isinstance(text, str) or len(text) > 50000:
            raise ValueError("Response must be a bounded string")
        actions = re.findall(r"^Action:\s*(.*)$", text, re.MULTILINE)
        finals = re.findall(r"^Final Answer:\s*(.*)$", text, re.MULTILINE)
        if len(actions) + len(finals) != 1:
            raise ValueError("Expected exactly one Action or Final Answer")
        if finals:
            answer = text.split("Final Answer:", 1)[1].strip()
            return ParsedAction(kind="final", final_answer=answer)
        inputs = re.findall(r"^Action Input:\s*", text, re.MULTILINE)
        if len(inputs) != 1:
            raise ValueError("Expected one Action Input")
        raw = text.split("Action Input:", 1)[1].strip()
        try:
            args = json.loads(raw, object_pairs_hook=_unique)
        except json.JSONDecodeError:
            tree = ast.parse(raw, mode="eval")
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    keys = [ast.literal_eval(key) for key in node.keys]
                    if len(keys) != len(set(keys)):
                        raise ValueError("Duplicate key")
            args = ast.literal_eval(tree)
        if not isinstance(args, dict) or not args or not all(isinstance(key, str) for key in args):
            raise ValueError("Action Input must be a nonempty object")
        json.dumps(args, allow_nan=False)
        name = actions[0].strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError("Invalid tool name")
        return ParsedAction(kind="action", tool_name=name, args=args)
    except (ValueError, TypeError, SyntaxError, RecursionError, MemoryError):
        return ParsedAction(kind="error", error="Invalid ReAct response; supply one Action with object input, or one Final Answer")
