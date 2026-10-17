import json
from policy_agent.models import RunTrace, StepTrace, Usage
from policy_agent.agent.trace import save_trace


def test_jsonl_trace(tmp_path):
    run = RunTrace(timestamp="test", question="q", steps=[StepTrace(action="search", observation="found")], final_answer="a", usage=Usage(calls=1))
    path = save_trace(run, tmp_path / "logs/run_test.jsonl")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [row["event"] for row in rows] == ["START", "STEP", "FINAL", "USAGE"]
    assert rows[1]["action"] == "search"
    assert rows[-1]["calls"] == 1
