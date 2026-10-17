import asyncio
import json
import sys
from pathlib import Path
from policy_agent.config import load_settings
from policy_agent.mcp_client.client import MCPToolClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


async def run_second_host():
    settings = load_settings()
    print("\n" + "=" * 65)
    print("      SECOND MCP HOST - DEMO GIAO TIEP VOI POLICY MCP SERVER")
    print("=" * 65)
    print("Khoi tao ket noi stdio toi MCP Server...")
    async with MCPToolClient(
        root=settings.project_root,
        requests_path=settings.requests_path,
        logs_dir=settings.logs_dir,
    ) as client:
        print("\n[1] Dynamic Tool Discovery (Kham pha cong cu dong):")
        tools = await client.list_tools()
        print(f"    => Tim thay {len(tools)} cong cu duoc dang ky tren MCP Server:")
        for t in tools:
            print(f"       - {t.name:<20}: {t.description[:60]}...")
        if len(tools) < 2:
            return False

        print("\n[2] Test goi tool tinh toan tat dinh: calc_business_days")
        start_d, end_d = "2026-11-02", "2026-11-06"
        days_resp = await client.call_tool("calc_business_days", {"start_date": start_d, "end_date": end_d})
        print(f"    => Tu {start_d} den {end_d}: {days_resp} ngay lam viec.")
        if days_resp != "5":
            return False

        print("\n[3] Test goi tool ghi du lieu: create_request")
        test_details = json.dumps(
            {"reason": "second host verification", "item": "Ergonomic Keyboard", "office": "HCM"},
            ensure_ascii=False,
        )
        create_resp = await client.call_tool(
            "create_request",
            {
                "request_type": "HARDWARE_PURCHASE",
                "employee": "SecondHostUser",
                "details": test_details,
            },
        )
        print(f"    => Ket qua tra ve: {create_resp}")
        created_record = json.loads(create_resp)
        req_id = created_record.get("request_id")
        if not req_id:
            return False

        print("\n[4] Test goi tool verify trang thai: get_request")
        get_resp = await client.call_tool("get_request", {"request_id": req_id})
        print(f"    => Du lieu doc lai tu store: {get_resp}")
        fetched_record = json.loads(get_resp)
        if fetched_record.get("request_id") != req_id or fetched_record.get("status") != "submitted":
            return False
        print("    => Xac thuc thanh cong: Ban ghi ton tai va dung trang thai 'submitted'!")
        print("\n" + "=" * 65)
        print("      HOST THU HAI HOAN THANH KIEM TRA KET NOI THANH CONG!")
        print("=" * 65 + "\n")
        return True


def main():
    if not asyncio.run(run_second_host()):
        sys.exit(1)


if __name__ == "__main__":
    main()
