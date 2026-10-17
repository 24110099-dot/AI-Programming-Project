import pytest
from policy_agent.mcp_server import server


def test_fake_retrieval():
    assert hasattr(server, "search_policy"), "search_policy missing"
    assert "FAKE" in server.search_policy("remote")
    assert "DEMO_REMOTE" in server.search_policy("remote")
    assert "No relevant passages" in server.search_policy("stock vesting")
    assert "FAKE" in server.get_document("DEMO_REMOTE")
    assert server.get_document("missing").startswith("Error:")
    assert server.search_policy("", 3).startswith("Error:")
    assert server.search_policy("remote", 6).startswith("Error:")


@pytest.mark.parametrize("start,end,expected", [("2026-11-02","2026-11-06","5"), ("2026-11-07","2026-11-08","0"), ("2026-11-02","2026-11-02","1")])
def test_business_days(start, end, expected):
    assert hasattr(server, "calc_business_days"), "calc_business_days missing"
    assert server.calc_business_days(start, end) == expected


@pytest.mark.parametrize("start,end", [("20261102","2026-11-06"), ("2026-02-30","2026-11-06"), ("2026-11-06","2026-11-02")])
def test_bad_dates(start, end):
    assert hasattr(server, "calc_business_days"), "calc_business_days missing"
    assert server.calc_business_days(start, end).startswith("Error:")


def test_tool_write_verify(tmp_path, monkeypatch):
    assert hasattr(server, "create_request"), "create_request missing"
    monkeypatch.setenv("REQUESTS_PATH", str(tmp_path / "requests.json"))
    details = '{"reason":"demo","location":"home"}'
    record = __import__("json").loads(server.create_request("REMOTE_WORK", "Demo", details, "2026-11-02", "2026-11-03"))
    assert __import__("json").loads(server.get_request(record["request_id"])) == record
    assert server.get_request("missing").startswith("Error:")
    assert server.create_request("INVALID", "Demo", details).startswith("Error:")
