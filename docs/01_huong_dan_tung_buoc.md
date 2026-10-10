# Hướng dẫn từng bước — nhóm 3 người

> **A** = RAG & dữ liệu · **B** = Agent & LLM · **C** = MCP & Eval/Reproducibility (README, Makefile)
> Mỗi bước có dòng **✅ Xong khi** — chưa đạt thì chưa sang bước sau.
> Lệnh viết cho PowerShell trên Windows.

---

## Giai đoạn 0 — Khởi động (D1, cả nhóm, ~2 giờ)

### Bước 0.1 — Họp 30 phút, chốt 4 việc
1. Ai là A, B, C (điền tên + MSSV vào bảng cuối `README.md`).
2. Một người (khuyên **C**) làm "chủ repo".
3. Đọc chung `PLAN.md` mục 1–3, thống nhất tên tool và schema (bước 0.4).

### Bước 0.2 — Chủ repo (C) tạo repo Git
```powershell
cd "C:\Users\Admin\UTE\AI Programing with Python\AI Project"
git init -b main
git config user.name  "Ten That Cua C"
git config user.email "email-github-cua-C@..."
git status            # KIỂM TRA: không được thấy file .env trong danh sách
git add .
git commit -m "chore: project skeleton, plan and class corpus"
```
Lên GitHub tạo repo **Private** (không tick "Add README"), rồi:
```powershell
git remote add origin https://github.com/<C>/policy-agent.git
git push -u origin main
```
GitHub → Settings → Collaborators → mời A và B.

### Bước 0.3 — Mỗi người (A, B, C) cài môi trường trên máy mình
```powershell
git clone https://github.com/<C>/policy-agent.git     # A và B làm; C đã có sẵn
cd policy-agent
git config user.name  "Ten That Cua Ban"              # BẮT BUỘC đúng tên mình — GV đối chiếu commit
git config user.email "email-github-cua-ban@..."
uv --version                                           # chưa có: irm https://astral.sh/uv/install.ps1 | iex
uv sync                                                # lần đầu tải torch ~vài trăm MB, chờ
Copy-Item .env.example .env                            # mở .env, dán GROQ_API_KEY của CHÍNH MÌNH
```
Mỗi người dùng key Groq riêng để không ăn chung rate limit.

✅ **Xong khi:** cả 3 máy chạy `uv run python -c "import policy_agent, groq, mcp, rank_bm25; print('ok')"` in ra `ok`.

### Bước 0.4 — Chốt "hợp đồng" giữa 3 phần (quan trọng nhất)
Ba người code song song được là nhờ thống nhất trước **chữ ký hàm**. B viết vào `src/policy_agent/models.py`, cả nhóm review rồi commit:

| Ranh giới | Hợp đồng |
|---|---|
| A → C | `retrieve(query: str, mode: str, top_k: int, category: str \| None) -> list[tuple[DocumentChunk, float]]` |
| C → B | `MCPToolClient.list_tools() -> list[ToolSpec]` và `call_tool(name: str, args: dict) -> str` (luôn trả chuỗi, lỗi là `"Error: ..."`) |
| B → C | `run_agent(question: str) -> RunTrace` (C dùng trong demo + eval) |
| Chung | dataclass `Document`, `DocumentChunk`, `ToolSpec`, `ParsedAction`, `StepTrace`, `RunTrace`, `Usage`, `ProcedureRequest` |

Trước khi ghép, mỗi người dùng **bản giả** của phần người khác (VD: B dùng fake client trả chuỗi cố định; C dùng fake retriever) → không ai phải chờ ai.

✅ **Xong khi:** `models.py` có đủ dataclass ở trên, được merge vào `main`.

---

## Quy trình Git hằng ngày (cả 3 người, mọi ngày)

```powershell
git checkout main ; git pull                 # đầu buổi: lấy code mới nhất
git checkout -b feat/rag                     # chỉ lần đầu (A: feat/rag, B: feat/agent, C: feat/mcp)
git checkout feat/rag ; git merge main       # các buổi sau: cập nhật nhánh mình

# ... code ...
uv run pytest -q                             # chạy test trước khi commit
git add <file của mình>                      # KHÔNG dùng "git add ." nếu chưa xem git status
git commit -m "rag: add section-based chunking"
git push -u origin feat/rag
```
- Xong 1 việc → mở **Pull Request** trên GitHub → **một người khác review** → merge vào `main`.
- Commit nhỏ, mỗi ngày ≥1 commit. Không dồn commit cuối kỳ (bị trừ điểm).
- Mỗi khi nhờ AI viết đoạn nào → ghi ngay 1 dòng vào `ai-usage.md`.

---

## Giai đoạn 1 — Làm từng phần song song (D2–D4)

### SV A — RAG & dữ liệu
1. **Viết tài liệu mới** (D2) trong `data/corpus/`:
   - `DOC0101_international_work_v2.txt`: bản 2.0 thay DOC0005, **đổi một vài con số** (VD: tối đa 30 → 21 ngày, nộp trước 10 → 15 ngày làm việc, thêm bước security review).
   - `DOC0102_request_procedures.txt`: các loại đơn (`REMOTE_WORK`, `INTL_WORK`, `HARDWARE_PURCHASE`, `EXPENSE_CLAIM`, `SECURITY_REVIEW`), trường bắt buộc, ai duyệt, SLA, **bảng giá thiết bị**.
   - (tuỳ chọn) `DOC0103_...` tiếng Việt.
   - Điền đủ `version, date, owner, category, file` trong `manifest.json` (bỏ hết `TODO`).
2. `rag/loader.py` + `rag/chunking.py` (D2): viết 3–5 dòng **lý do chunking** trong docstring.
3. `rag/embeddings.py`, `rag/vector_store.py`, `rag/build_index.py` (D3) — tái dùng `resource week 4/vector_store.py`.
4. `rag/hybrid_search.py` đã có sẵn (file của thầy). D3: làm 1 commit riêng sửa đúng 2 chỗ ghi ở `PLAN.md` mục 3.2 (đổi import, đổi `print` → `logging`), ghi lý do trong commit message.
5. `rag/retriever.py` (D4): 2 chế độ `dense|hybrid`, metadata filter, ngưỡng `MIN_SCORE`.

✅ **Xong khi:** `uv run python -m policy_agent.rag.build_index` chạy OK, và một script nhỏ hỏi *"how many consecutive days can I work abroad"* trả chunk của **DOC0101** đứng đầu ở cả 2 chế độ.

### SV B — Agent & LLM
1. `models.py` (D1–D2, bước 0.4) + `config.py`.
2. `llm/client.py` (D2): `call_llm()` có retry/backoff (tái dùng `resource week 2/errh.py`), `timeout`, ghi lỗi HTTP vào `logs/http_errors.jsonl`, đếm `Usage` (tái dùng `resource week 8/common.py`).
3. `agent/parser.py` + `tests/test_parser.py` (D3): ít nhất 6 ca hỏng (thiếu ngoặc, nháy đơn, JSON rỗng, 2 Action, không có Action, có cả Action lẫn Final Answer) → không ca nào làm crash.
4. `prompts/agent_system.txt` (D3): format ReAct, luật trích `[doc_id]`, ưu tiên bản mới nhất, từ chối khi không có, **ghi xong phải gọi `get_request`**.
5. `agent/loop.py` + `agent/trace.py` (D4): chạy với **fake client**; có `MAX_STEPS`, guard verify, ghi `logs/run_<timestamp>.jsonl`.

✅ **Xong khi:** `uv run pytest -q tests/test_parser.py` pass hết, và loop với fake client in ra trace có ≥2 bước + dòng USAGE.

### SV C — MCP server/client & hạ tầng
1. `uv lock` → commit `uv.lock` (D1). Hoàn thiện `Makefile`, `tasks.ps1`.
2. `mcp_server/request_store.py` + `tests/test_request_store.py` (D2): `create()` rồi `get()` thấy bản ghi; ghi file an toàn.
3. `mcp_server/server.py` (D3): bắt đầu bằng `search_policy`, `get_document` dùng **fake retriever**; log ra stderr, **không `print()`**. Tái dùng `resource week 7/create_mcp.py`, `rag_server.py`.
4. `scripts/probe_server.py` (D3): JSON-RPC thô — tái dùng `resource week 7/probe_fetch_mcp.py`.
5. (D4) Thêm `calc_business_days`, `create_request` (ghi), `get_request` (đọc/verify); `mcp_client/client.py` discover động bằng `list_tools()`.

✅ **Xong khi:** `.\tasks.ps1 probe` in ra 5 tool + kết quả 1 lần gọi `create_request` rồi `get_request` thấy đúng bản ghi.

### 🚩 Checkpoint CP1 (cuối D3) — 15 phút họp
Mỗi người demo phần mình chạy độc lập. Ai trễ thì 2 người còn lại hỗ trợ ngay.

---

## Giai đoạn 2 — Ghép hệ thống (D5)

Thứ tự ghép (theo từng PR, merge xong mới làm bước sau):
1. **A + C:** server thay fake retriever bằng `retrieve()` thật → `probe` thấy kết quả có `[DOC0xxx]`.
2. **B + C:** loop thay fake client bằng `MCPToolClient` thật.
3. **C:** viết `scripts/demo.py` (3 câu: tra cứu, tạo đơn + verify, no_answer) và `scripts/chat.py` cùng B.

✅ **CP2:** `.\tasks.ps1 demo` chạy hết 3 câu; câu tạo đơn có trace `create_request → get_request`, file `data/state/requests.json` có bản ghi mới.

---

## Giai đoạn 3 — Testset & đánh giá (D6–D7)

1. **D6 – soạn `tests/testset.jsonl`** theo schema trong `PLAN.md` mục 3.5:
   - A: 2 direct, 2 synthesis, 2 version_conflict, 4 no_answer.
   - B: 1 calculation, 2 action, 1 insufficient.
   - Mỗi câu ghi `expected_doc_ids` + `reference_answer` **do người soạn tự kiểm bằng cách đọc tài liệu**.
2. **D6 – C viết** `eval/metrics.py` (faithfulness kiểu W5, tỉ lệ từ chối đúng/sai, citation hit, action success) và `eval/run_eval.py`.
3. **D7 – C chạy** `make eval` ở cả `dense` và `hybrid` → `results/eval_<ts>.csv` + biểu đồ; chạy ≥3 lần thật → ≥3 file `logs/run_*.jsonl`.
4. **D7 – cả nhóm** xem câu sai: lỗi retrieval → A sửa; lỗi suy luận/format → B sửa; lỗi tool → C sửa. **Mỗi lần chỉ đổi 1 thứ** rồi chạy lại.
5. C viết `scripts/second_host.py` (+1 điểm).

✅ **CP3:** người khác trong nhóm chạy `make eval` trên máy mình ra cùng bảng số liệu (sai số do LLM chấp nhận được).

---

## Giai đoạn 4 — Report, README, cold start (D8–D9)

1. **D8 – Report Word** (8–9 trang, đúng khung 9 mục): A viết mục 3, B mục 4 (dán trace thật 1 câu), C mục 5 + 6 (bảng kết quả, chi phí token từng câu, ≥1 ca thất bại + phân tích). Chung: mục 1, 2 (sơ đồ), 7 (≥2 hạn chế thật), 8 (ai làm gì + **commit hash**: `git log --author="Ten" --oneline`), 9 (phụ lục prompt, trace dài, ai-usage).
2. **D9 – Cold start:** A clone repo vào **thư mục mới tinh**, làm đúng theo README (`Copy-Item .env.example .env`, điền key, `make setup && make demo`). Lỗi gì → ghi lại → C sửa README/Makefile.
3. **D9 – mỗi người** hoàn thiện dòng của mình trong `ai-usage.md`.

✅ **CP4:** cold start pass trên máy sạch; `git status` không có `.env`; `git log` có commit của cả 3 người rải đều các ngày.

---

## Giai đoạn 5 — Nộp & ôn bảo vệ (D10)

**Nộp:** `report.docx` · repo (zip có thư mục `.git` hoặc link) · `logs/` · `tests/testset.jsonl` · `ai-usage.md` · `README.md`.

**Ôn (mỗi người tự làm):**
- Giải thích được **từng dòng** file mình viết; mở file đúng dòng trong 10 giây.
- Thuộc số liệu eval của mình (faithfulness, tỉ lệ từ chối đúng, token/câu).
- Tập sửa nhanh: đổi `MAX_STEPS`; thêm 1 tool MCP; đổi trọng số hybrid; thêm trường vào dataclass; đổi `MIN_SCORE`.
- Ôn khái niệm W1–W7 ([docs/00_tong_hop_kien_thuc.md](00_tong_hop_kien_thuc.md)), nhất là: mutable default, retry vs không retry, overlap, normalize trước khi fuse, faithfulness ≠ đúng, tại sao cần MAX_STEPS, tại sao stdout phải sạch, tools/list vs tools/call.
- In sẵn sơ đồ kiến trúc; mở sẵn terminal ở `make chat`.
