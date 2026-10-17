"""Unit tests cho module danh gia (metrics.py va report.py) cua SV C (Khang)."""

import json
from pathlib import Path
from policy_agent.eval import metrics, report


def test_refusal_detection():
    # Truong hop tu choi dung
    ans_refusal = "Khong tim thay thong tin ve co phieu ESOP trong tai lieu quy che."
    ok, reason = metrics.check_refusal(ans_refusal, expect_refusal=True)
    assert ok is True

    # Truong hop ky vong tu choi nhung lai tra loi
    ans_hallucination = "Co phieu ESOP se vest sau 1 nam lam viec voi ti le 25%."
    ok, reason = metrics.check_refusal(ans_hallucination, expect_refusal=True)
    assert ok is False

    # Truong hop cau hoi binh thuong, tra loi dung (khong tu choi)
    ans_normal = "Nhan vien duoc hoan toi da $50/ngay theo DOC0001."
    ok, reason = metrics.check_refusal(ans_normal, expect_refusal=False)
    assert ok is True

    # Truong hop tu choi sai (false refusal)
    ans_false_refusal = "Toi khong the tra loi cau hoi nay."
    ok, reason = metrics.check_refusal(ans_false_refusal, expect_refusal=False)
    assert ok is False


def test_citation_hit():
    ans = "Theo quy dinh tai [DOC0001] va DOC0102, muc chi tieu la $50."
    assert metrics.check_citation_hit(ans, ["DOC0001"]) == 1.0
    assert metrics.check_citation_hit(ans, ["DOC0001", "DOC0102"]) == 1.0
    assert metrics.check_citation_hit(ans, ["DOC0001", "DOC9999"]) == 0.5
    assert metrics.check_citation_hit(ans, []) == 1.0


def test_action_success(tmp_path):
    req_file = tmp_path / "requests.json"
    req_id = "REQ-abcdef123456"
    req_file.write_text(json.dumps([{"request_id": req_id, "status": "submitted"}]), encoding="utf-8")

    # Trace day du: create_request -> get_request
    good_steps = [
        {"action": "create_request", "args": {}, "observation": f'{{"request_id": "{req_id}"}}'},
        {"action": "get_request", "args": {"request_id": req_id}, "observation": f'{{"request_id": "{req_id}", "status": "submitted"}}'},
    ]
    assert metrics.check_action_success(good_steps, requests_path=req_file) is True

    # Trace thieu verify (chua goi get_request)
    unverified_steps = [
        {"action": "create_request", "args": {}, "observation": f'{{"request_id": "{req_id}"}}'},
    ]
    assert metrics.check_action_success(unverified_steps, requests_path=req_file) is False


def test_check_faithfulness_heuristic():
    context = "Nhan vien duoc lam viec tu xa toi da 2 ngay moi tuan."
    good_answer = "Theo quy dinh, duoc lam viec tu xa 2 ngay mot tuan."
    bad_answer = "Nhan vien duoc nghi phep 30 ngay va thuong xe oto."

    score_good, details_good = metrics.check_faithfulness(good_answer, context, client=None)
    score_bad, details_bad = metrics.check_faithfulness(bad_answer, context, client=None)

    assert score_good > score_bad
    assert score_good >= 0.5


def test_report_csv_and_plot(tmp_path):
    records = [
        {
            "id": "Q01",
            "type": "direct",
            "question": "Q1?",
            "passed": True,
            "faithfulness": 1.0,
            "citation_hit": 1.0,
            "refusal_correct": True,
            "action_success": True,
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "llm_calls": 2,
            "refusal_reason": "",
            "final_answer": "Answer 1",
        },
        {
            "id": "Q02",
            "type": "no_answer",
            "question": "Q2?",
            "passed": True,
            "faithfulness": 1.0,
            "citation_hit": 1.0,
            "refusal_correct": True,
            "action_success": True,
            "prompt_tokens": 80,
            "completion_tokens": 30,
            "total_tokens": 110,
            "llm_calls": 1,
            "refusal_reason": "Correct refusal",
            "final_answer": "Khong tim thay thong tin",
        },
    ]

    csv_out = tmp_path / "eval.csv"
    report.write_csv(records, csv_out)
    assert csv_out.exists()

    png_out = tmp_path / "chart.png"
    report.plot_comparison_chart(records, records, png_out)
    assert png_out.exists()
