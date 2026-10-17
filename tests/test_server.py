import json
from policy_agent.mcp_server import server


def test_search_and_get_document():
    assert "FAKE [DEMO_REMOTE" in server.search_policy("remote")
    assert "No relevant passages" in server.search_policy("stock vesting")
    doc = json.loads(server.get_document("DEMO_REMOTE"))
    assert doc["doc_id"] == "DEMO_REMOTE"


def test_calc_business_days():
    assert server.calc_business_days("2026-11-02", "2026-11-06") == "5"
    assert server.calc_business_days("2026-11-07", "2026-11-08") == "0"
    assert server.calc_business_days("2026-11-06", "2026-11-02").startswith("Error:")


def test_create_and_verify_request_tool(tmp_path, monkeypatch):
    monkeypatch.setenv("REQUESTS_PATH", str(tmp_path / "requests.json"))
    raw = server.create_request(
        "REMOTE_WORK",
        "An",
        '{"reason": "demo", "location": "home"}',
        "2026-11-02",
        "2026-11-03",
    )
    created = json.loads(raw)
    verified = json.loads(server.get_request(created["request_id"]))
    assert created == verified
