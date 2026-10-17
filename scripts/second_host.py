"""Host thu hai (Second Host) ket noi toi MCP Server (+1 diem cong).

Chung minh tinh doc lap va tuong thich tieu chuan cua MCP Server:
- May chu MCP co the phuc vu nhieu client khac nhau qua giao thuc stdio JSON-RPC.
- Host thu 2 doc lap tu dong discover danh sach cong cu (list_tools) va thuc hien ghi/doc du lieu.
Nguoi phu trach: SV C (Khang).
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Them src vao PYTHONPATH neu chay truc tiep script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from policy_agent.config import load_settings
from policy_agent.mcp_client.client import MCPToolClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("second_host")


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
        # 1. Dynamic Tool Discovery
        print("\n[1] Dynamic Tool Discovery (Kham pha cong cu dong):")
        tools = await client.list_tools()
        print(f"    => Tim thay {len(tools)} cong cu duoc dang ky tren MCP Server:")
        for t in tools:
            print(f"       - {t.name:<20}: {t.description[:60]}...")

        if len(tools) < 2:
            print("Loi: So luong tool tim thay nho hon 2!")
            return False

        # 2. Goi cong cu tinh toan ngay lam viec (calc_business_days)
        print("\n[2] Test goi tool tinh toan tat dinh: calc_business_days")
        start_d, end_d = "2026-11-02", "2026-11-06"
        days_resp = await client.call_tool(
            "calc_business_days",
            {"start_date": start_d, "end_date": end_d},
        )
        print(f"    => Tu {start_d} den {end_d}: {days_resp} ngay lam viec.")
        assert days_resp == "5", f"Ket qua tinh ngay sai: {days_resp}"

        # 3. Goi cong cu ghi ho so thu tuc (create_request)
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

        try:
            created_record = json.loads(create_resp)
            req_id = created_record.get("request_id")
        except Exception:
            print("Loi: Ket qua tao don khong phai JSON hop le!")
            return False

        # 4. Goi cong cu verify (get_request)
        print("\n[4] Test goi tool verify trang thai: get_request")
        get_resp = await client.call_tool("get_request", {"request_id": req_id})
        print(f"    => Du lieu doc lai tu store: {get_resp}")

        try:
            fetched_record = json.loads(get_resp)
            assert fetched_record.get("request_id") == req_id
            assert fetched_record.get("status") == "submitted"
            print("    => Xac thuc thanh cong: Ban ghi ton tai va dung trang thai 'submitted'!")
        except Exception as e:
            print(f"Loi: Xac thuc ban ghi that bai: {e}")
            return False

        print("\n" + "=" * 65)
        print("      HOST THU HAI HOAN THANH KIEM TRA KET NOI THANH CONG!")
        print("=" * 65 + "\n")
        return True


def main():
    success = asyncio.run(run_second_host())
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
