# Khai báo sử dụng AI

> Bắt buộc theo mục 7 của *02-Yêu cầu thực hiện*: công cụ nào, cho phần nào, prompt chính, đoạn code nào do AI sinh.
> Mỗi thành viên tự ghi phần của mình, cập nhật theo từng lần dùng.

| Ngày | Thành viên | Công cụ | Phần | Prompt chính (tóm tắt) | Kết quả AI sinh ra | Đã sửa / kiểm chứng gì |
|---|---|---|---|---|---|---|
| 2026-10-10 | (người chạy) | Claude Code (Opus 5.5) | Lập kế hoạch | "Đọc 2 file đề, tổng hợp kiến thức W1–W8, tạo plan, chia phần, tạo cấu trúc thư mục" | `PLAN.md`, `docs/00_tong_hop_kien_thuc.md`, khung thư mục + file stub (chỉ docstring/TODO, chưa có code logic), `Makefile`, `tasks.ps1`, `pyproject.toml`, `.env.example`, `.gitignore`, `README.md`, `data/corpus/manifest.json` (copy DOC0001–0006 của lớp) | |
| 2026-10-13 | Huynh Nhat Bao (A; nhận hỗ trợ schema chung B) | Hermes Agent | Loader, chunking, schema dùng chung và tests | "Hướng dẫn tự viết loader; hoàn thiện loader và chunking có test; dùng schema B để làm tiếp" | Schema `models.py`/test từ gói B; bổ sung validation và `load_documents`; `chunking.py` với docstring 5 dòng; tests loader/chunking/models | SV luyện đọc manifest, list/dict, vòng lặp, return và chạy các test đầu. Hermes chạy toàn bộ 72 tests pass; đọc 8 tài liệu thật thành 59 chunks, max 400 ký tự. Chưa xác nhận SV tự giải thích/viết lại toàn bộ code bổ sung; chưa commit/push. |
