import asyncio
import json
from pathlib import Path
from policy_agent.mcp_client import client as module
from policy_agent.models import ToolSpec


def test_real_stdio_dynamic_client(tmp_path):
    assert hasattr(module, "MCPToolClient"), "MCPToolClient missing"
    async def scenario():
        root = Path(__file__).resolve().parents[1]
        async with module.MCPToolClient(root=root, requests_path=tmp_path / "requests.json", logs_dir=tmp_path / "logs") as client:
            tools = await client.list_tools()
            assert len(tools) == 5
            assert all(isinstance(tool, ToolSpec) and tool.input_schema for tool in tools)
            assert {tool.name for tool in tools} == {"search_policy","get_document","calc_business_days","create_request","get_request"}
            assert "FAKE" in await client.call_tool("search_policy", {"query":"remote"})
            assert await client.call_tool("calc_business_days", {"start_date":"2026-11-02", "end_date":"2026-11-06"}) == "5"
            details = '{"reason":"demo","location":"home"}'
            record = json.loads(await client.call_tool("create_request", {"request_type":"REMOTE_WORK","employee":"Demo","details":details,"start_date":"2026-11-02","end_date":"2026-11-03"}))
            assert json.loads(await client.call_tool("get_request", {"request_id":record["request_id"]})) == record
            assert json.loads((tmp_path / "requests.json").read_text(encoding="utf-8")) == [record]
            assert (await client.call_tool("get_request", {"request_id":"missing"})).startswith("Error:")
            assert (await client.call_tool("calc_business_days", {})).startswith("Error:")
            assert (await client.call_tool("not_a_tool", {})).startswith("Error:")
        assert client._client is None
    asyncio.run(scenario())
