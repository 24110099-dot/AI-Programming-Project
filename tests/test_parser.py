from policy_agent.agent.parser import parse_response


def test_parse_valid_action():
    text = 'Thought: Can tim quy che\nAction: search_policy\nAction Input: {"query": "remote"}'
    res = parse_response(text)
    assert res.kind == "action"
    assert res.tool_name == "search_policy"
    assert res.args == {"query": "remote"}


def test_parse_valid_final_answer():
    text = "Thought: Da du thong tin\nFinal Answer: Nhan vien duoc lam tu xa 3 ngay [DOC0001]."
    res = parse_response(text)
    assert res.kind == "final"
    assert "DOC0001" in res.final_answer


def test_parse_malformed_returns_error_without_crash():
    for bad in [
        'Action: search_policy\nAction Input: {"query": "missing_brace"',
        "Thought: thinking only",
        "Action: a\nAction Input: {}\nFinal Answer: both",
        "",
    ]:
        res = parse_response(bad)
        assert res.kind == "error"
