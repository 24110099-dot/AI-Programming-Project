# SV C — Phase 1 standalone

Bản chạy độc lập D1–D4, MCP stdio SDK v2, 5 tool. Retrieval là **FAKE keyword fixture**, không phải RAG, không dùng tài liệu corpus và không chứng minh CP1 của A.

`details` là **chuỗi JSON object theo schema demo do dự án định nghĩa**, không phải mô tả ngôn ngữ tự nhiên đã được validate theo policy. DOC0102 gốc được kiểm tra đang trống; chưa thể xác nhận trường bắt buộc, SLA, người duyệt, ngưỡng hoặc lịch lễ từ corpus. Không tự bịa các giá trị đó.

Chạy `uv lock`, `uv sync --locked`, sau đó `./tasks.ps1 test` và `./tasks.ps1 probe` trong PowerShell; Unix có `make test`, `make probe`. Gói có `uv.lock` dependency chung từ D1_C, được kiểm lại bằng `uv lock`; sync toàn bộ môi trường chưa được chạy lại ở thư mục độc lập để tránh torch.

Thay thế nhẹ được kiểm thử: đặt PYTHONPATH bằng đường dẫn tuyệt đối `src`, rồi `uv run --no-project --python 3.11 --with mcp==2.3.0 --with pytest --with python-dotenv python -m pytest -q`.

Server: `python -m policy_agent.mcp_server.server` (chỉ giao tiếp stdio với host). Probe: `python scripts/probe_server.py`; muốn giữ proof dùng `--state-dir <thư mục mới>`. Probe không xoá hoặc ghi đè state đã tồn tại. Mỗi lần tạo đơn sinh id mới, không chống tạo trùng khi retry.

Request store là **single-writer**: dùng tempfile cùng thư mục + flush/fsync + os.replace, đọc file hỏng thì từ chối và không ghi đè. Không có khóa liên-process; không khẳng định chống lost update khi hai server ghi cùng file, cũng không khẳng định crash-durability tuyệt đối trên mọi filesystem.

B nhận `async with MCPToolClient()`, `await list_tools()` -> list[ToolSpec], `await call_tool(name,args)` -> str. create/get thành công trả JSON string đầy đủ ProcedureRequest; lỗi vận hành trả `Error:`. Đối số sai schema có thể bị SDK chặn trước hàm tool; client chuyển is_error/exception thành Error string.

Ngày tính inclusive [start_date,end_date], chỉ thứ Hai–thứ Sáu, không trừ ngày lễ. Schema details: REMOTE_WORK reason/location; INTL_WORK reason/country/office; HARDWARE_PURCHASE reason/item; EXPENSE_CLAIM reason/currency/receipt và amount số hữu hạn >0; SECURITY_REVIEW reason/system/scope. Các field chữ phải không rỗng. Remote/international bắt buộc hai ngày ISO. Loại khác có thể bỏ cả hai, nếu có thì phải đủ hai và start<=end. Field phụ được giữ nguyên, không được tuyên bố đã validate.

Đọc GIAI_DOAN_1_C.md bên ngoài gói để có toàn bộ code, placement, ngày làm việc, lệnh Git và giới hạn kiểm chứng. evidence/ là kết quả thực thi với dữ liệu demo, không phải log LLM/RAG thật.
