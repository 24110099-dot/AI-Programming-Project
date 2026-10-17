import pytest
from policy_agent.agent.parser import parse_response


@pytest.mark.parametrize("text", [
    'Thought: find\nAction: search_policy\nAction Input: {"query":"remote"}',
    "Action: search_policy\nAction Input: {'query': 'remote'}",
])
def test_action_json_and_safe_literal(text):
    result = parse_response(text)
    assert result.kind == "action"
    assert result.tool_name == "search_policy"
    assert result.args == {"query": "remote"}


def test_final():
    result = parse_response("Thought: done\nFinal Answer: 21 days [DOC0101]")
    assert result.kind == "final"
    assert result.final_answer == "21 days [DOC0101]"


@pytest.mark.parametrize("text", [
    'Action: search_policy\nAction Input: {"query":"x"',
    'Action: search_policy\nAction Input: {}',
    'Action: a\nAction Input: {"x":1}\nAction: b\nAction Input: {"y":2}',
    'Thought: nothing',
    'Action: a\nAction Input: {"x":1}\nFinal Answer: done',
    'Action: a\nAction Input: {"x":1,"x":2}',
    "Action: a\nAction Input: {'x':1,'x':2}",
    "Action: a\nAction Input: {'x': __import__('os').system('BAD')}",
    'Action: a\nAction Input: []',
    'Action: a\nAction Input: {"x":NaN}',
    'Final Answer: ',
    None,
])
def test_malformed_never_crashes(text):
    result = parse_response(text)
    assert result.kind == "error"
    assert result.error

