# Policy Agent — Trợ lý quy chế + hành động (Final Project AIPR, T1)

Hỏi quy chế → làm thủ tục → xác nhận. RAG (dense + hybrid BM25) + agent loop tự viết + MCP server (stdio).

> 🚧 Khung README — hoàn thiện ở D9 (cold start test). Kế hoạch: [PLAN.md](PLAN.md).

## Yêu cầu
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`uv --version`)
- Groq API key

## Chạy (1 lệnh)
```bash
cp .env.example .env      # rồi điền GROQ_API_KEY
make setup && make demo
```
Windows không có `make`: `.\tasks.ps1 setup; .\tasks.ps1 demo`

| Lệnh | Việc |
|---|---|
| `make setup` | cài dependency + build index |
| `make demo` | 3 câu mẫu (tra cứu, tạo đơn + verify, no_answer) |
| `make chat` | hỏi tự do |
| `make eval` | chạy `tests/testset.jsonl` (dense + hybrid) → `logs/`, `results/` |
| `make probe` | kiểm tra MCP server bằng JSON-RPC thô |
| `make host2` | client MCP thứ hai |
| `make test` | unit test |

## Cấu trúc
```
data/corpus/        DOC0001–0006 (lớp) + DOC0101–0103 (nhóm viết) + manifest.json
src/policy_agent/   llm/ rag/ agent/ mcp_server/ mcp_client/ eval/ prompts/
scripts/            demo, chat, probe_server, second_host
tests/              testset.jsonl + unit tests
logs/ results/      trace JSONL, CSV, biểu đồ
report/             report.docx, sơ đồ kiến trúc
```

## Thành viên
| SV | MSSV | Phần phụ trách |
|---|---|---|
| A | | RAG & dữ liệu |
| B | | Agent & LLM |
| C | | MCP & Eval |
