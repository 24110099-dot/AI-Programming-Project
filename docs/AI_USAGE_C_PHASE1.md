# Khai báo AI — SV C, giai đoạn 1

AI được dùng để soạn hướng dẫn, đề xuất schema demo cho `details`, viết request store, MCP server/client, raw probe và test. Code dùng MCP SDK v2 được kiểm bằng introspection SDK thực tế và chạy subprocess stdio, không dựa vào API FastMCP v1.

Trong lúc chuẩn bị tài liệu đã thực thi 37 test C, raw JSON-RPC initialize/list/call, đối chiếu create/get/file và kiểm PowerShell target check-env/test/probe với environment sẵn có, cùng một lượt uv runtime nhẹ độc lập. Dữ liệu toàn bộ là demo. Không có cuộc gọi Groq/LLM hoặc retrieval RAG thật; không có kết quả eval hay commit tự động.

SV C phải tự đọc hiểu, chạy lại, ghi môi trường/kết quả của mình và khai báo phần sửa trước khi nộp. Không nhận phần chưa chạy là tự kiểm chứng, không gán commit hash chưa tồn tại, không nhận schema demo là policy được DOC0102 xác nhận.
