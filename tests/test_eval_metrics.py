from policy_agent.eval.metrics import (
    check_action_success,
    check_citation_hit,
    check_faithfulness,
    check_refusal,
)


def test_citation_and_refusal():
    assert check_citation_hit("Quy dinh tai [DOC0101].", ["DOC0101"]) == 1.0
    assert check_citation_hit("Khong co ma.", ["DOC0101"]) == 0.0
    ok, _ = check_refusal("Quy chế hiện tại không có thông tin về cổ phiếu.", expect_refusal=True)
    assert ok is True


def test_action_and_faithfulness():
    steps = [
        {"action": "create_request", "args": {}, "observation": '{"request_id": "REQ-abc123"}'},
        {"action": "get_request", "args": {"request_id": "REQ-abc123"}, "observation": '{"request_id": "REQ-abc123"}'},
    ]
    assert check_action_success(steps) is True
    score, _ = check_faithfulness(
        "Employees may work remotely up to three days per week.",
        ["Employees may work remotely up to three days per week with manager approval."],
    )
    assert score >= 0.8
