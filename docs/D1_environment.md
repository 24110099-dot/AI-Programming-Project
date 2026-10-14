# Môi trường SV C — chỉ giai đoạn 1 (D1–D4)

- Dùng Python >=3.11, uv và MCP SDK v2; bản kiểm thử thực tế: Python 3.11.16 / mcp 2.3.0.
- `uv lock` tạo/kiểm tra lock; `uv sync --locked` cài toàn bộ dependency chung của nhóm, có thể tải torch nặng. Không chạy build_index khi A chưa bàn giao.
- `tasks.ps1 setup` / `make setup` trong gói này chỉ chuẩn bị môi trường; không gọi module tương lai.
- `tasks.ps1 test` kiểm tra bốn file test C; `tasks.ps1 probe` dùng thư mục tạm, không đụng state dùng thật.
- `scripts/check_environment.py` chỉ import, không đọc key, không gọi Groq, không tải model embedding.
- Server mặc định FAKE và không tự nạp `.env`. Không cần API key ở giai đoạn này. Muốn đổi nơi lưu state: đặt REQUESTS_PATH/LOGS_DIR trong môi trường subprocess.
- Khi ghép Makefile/tasks.ps1 vào repo chung: giữ target tương lai của nhóm, chỉ sửa target C đã thống nhất. Không ghi đè models.py/config.py của B nếu khác bản hỗ trợ trong gói.
- Không đưa `.env`, `.venv`, requests.json, cache hoặc log cá nhân vào Git.
