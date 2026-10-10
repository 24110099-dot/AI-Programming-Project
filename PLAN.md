# PLAN — Final Project AIPR · Đề tài T1: Trợ lý quy chế + hành động

> **Sản phẩm:** Hỏi quy chế → làm thủ tục → xác nhận.
> Trọng tâm bắt buộc: RAG (W3–W4) + Agent loop & tool (W6) + MCP (W7), có đo lường (W5).
> Kiến thức nền từng tuần: xem [docs/00_tong_hop_kien_thuc.md](docs/00_tong_hop_kien_thuc.md).

---

## 0. Những điểm cần chốt ngay (D1)

| # | Vấn đề | Đề xuất |
|---|---|---|
| 1 | Số thành viên | **Đã chốt: 3 người (A/B/C)**. Hướng dẫn từng bước: [docs/01_huong_dan_tung_buoc.md](docs/01_huong_dan_tung_buoc.md). |
| 2 | File hybrid w4 | **Đã có:** `src/policy_agent/rag/hybrid_search.py` (bản gốc, chỉ thêm 3 dòng header ghi nguồn). SV A cần 2 chỉnh sửa nhỏ khi ghép — xem mục 3.2. |
| 3 | Máy hiện tại **không có `make`** (Windows) | Vẫn viết `Makefile` (GV chạy `make setup && make demo`) + file `tasks.ps1` chạy y hệt trên Windows. Mọi lệnh đi qua `uv run` để không phụ thuộc đường dẫn venv. |
| 4 | LLM provider | Groq (đã có key, lớp dùng suốt khóa), model mặc định `openai/gpt-oss-20b`, đổi qua biến `MODEL` trong `.env`. |
| 5 | Embedding | Local `sentence-transformers`. Corpus chủ yếu tiếng Anh nhưng GV có thể hỏi tiếng Việt → dùng model **đa ngôn ngữ** `paraphrase-multilingual-MiniLM-L12-v2` (so sánh với `all-MiniLM-L6-v2` của W4 = 1 cấu hình phụ, được +1). |
| 6 | Kiểu agent | ReAct dạng text, `Action: tool_name {json args}` — vì đề chấm "parse action an toàn (thiếu dấu ngoặc không làm chết run)". Danh sách tool nhét vào prompt **lấy từ `list_tools()`**, không hard-code. |
| 7 | Bảo mật | `resource week 2/test_api.py` có Groq key thật trong comment → **không copy vào repo**, nên rotate key. `.env` chỉ ở máy, repo chỉ có `.env.example`. |

---

## 1. Phạm vi bài toán (để viết mục 1 của report)

**Người dùng:** nhân viên Acme/Northwind cần làm thủ tục nội bộ (làm việc từ xa, làm việc ở văn phòng nước khác, mua thiết bị, hoàn ứng chi phí, xin security review).

**Hệ thống làm:**
1. **(a) Tra cứu** — trả lời quy chế kèm `[doc_id]` đúng phiên bản; từ chối khi corpus không có.
2. **(b) Biến đổi** — suy ra điều không viết sẵn:
   - tổng hợp ≥2 tài liệu (VD: đi HCM 2 tuần → cần duyệt line manager + HR (DOC0005) + APAC-VPN, security review (DOC0004)…);
   - chọn **bản mới nhất** khi 2 phiên bản mâu thuẫn (DOC0005 v1.0 vs tài liệu mới v2.0);
   - tính toán: số ngày làm việc, hạn nộp đơn, tổng chi phí thiết bị → ngưỡng $1,000 → ai duyệt;
   - từ chối vì **thiếu dữ liệu để suy luận** (VD: hỏi "có được hoàn tiền không" mà không có số tiền/hoá đơn).
3. **(c) Hành động** — tạo hồ sơ thủ tục thật (`create_request` ghi vào `data/state/requests.json`) **rồi bắt buộc** gọi `get_request` đọc lại để chứng minh trạng thái đã đổi.

**Hệ thống KHÔNG làm:** không gửi email/không duyệt thay người có thẩm quyền; không trả lời ngoài corpus (lương, stock option, dress code…); không sửa/xoá quy chế; không xác thực danh tính người dùng; không xử lý dữ liệu cá nhân thật.

---

## 2. Kiến trúc

```
User ─► scripts/demo.py | scripts/chat.py           (HOST 1)
          │
          ▼
   agent/loop.py  ── ReAct, MAX_STEPS, parse an toàn, trace JSONL, USAGE
          │  call_llm()  ──► llm/client.py ──► Groq API (retry/timeout/log HTTP)
          │  tools = list_tools()  (discover động)
          ▼
   mcp_client/client.py ══ stdio JSON-RPC ══►  mcp_server/server.py   (MCP boundary)
                                                 ├─ search_policy      (read)  ─► rag/retriever.py (dense | hybrid + metadata filter)
                                                 ├─ get_document       (read)
                                                 ├─ calc_business_days (read, tính toán tất định)
                                                 ├─ create_request     (WRITE) ─► mcp_server/request_store.py ─► data/state/requests.json
                                                 └─ get_request        (read, VERIFY)
   scripts/second_host.py (HOST 2) ═══════════════╝   (+ Cline trong VS Code = host thứ 3, tuỳ chọn)
```

**Luồng mẫu** — "Tôi ở Singapore, muốn làm ở văn phòng HCM từ 2026-11-02 đến 2026-11-13, tạo đơn giúp tôi":
1. `search_policy("work from another country approval")` → DOC0005 v1.0 và DOC0101 v2.0 → chọn v2.0 (mới hơn).
2. `search_policy("Ho Chi Minh City office requirements")` → DOC0004 (APAC-VPN, desk booking, security review).
3. `calc_business_days("2026-10-12","2026-11-02")` → kiểm tra đủ hạn nộp trước N ngày làm việc.
4. `create_request({...})` → `REQ-0007, status=submitted`.
5. `get_request("REQ-0007")` → thấy bản ghi → Final Answer có `[doc_id]` + mã hồ sơ.

---

## 3. Thiết kế chi tiết

### 3.1 Corpus (`data/corpus/` + `data/corpus/manifest.json`)

Mỗi tài liệu có metadata bắt buộc: `doc_id, title, version, date, owner` (+ `category`, `supersedes`, `lang`).

| doc_id | Nguồn | Vai trò trong đề tài |
|---|---|---|
| DOC0001 | Lớp — Company Policy (remote work, leave, travel, expense) | quy chế gốc |
| DOC0002 | Lớp — IT Helpdesk | thủ tục IT |
| DOC0003 | Lớp — IT Procurement | ngưỡng mua sắm |
| DOC0004 | Lớp — Global Office Directory | yêu cầu văn phòng HCM |
| DOC0005 | Lớp — International Work Policy **v1.0** | bản cũ |
| DOC0006 | Lớp — Equipment Catalog | phụ cấp, duyệt thiết bị |
| DOC0101 | **Nhóm viết** — International Work Policy **v2.0** (supersedes DOC0005) | tạo mâu thuẫn phiên bản: đổi số ngày tối đa, hạn nộp, người duyệt |
| DOC0102 | **Nhóm viết** — Sổ tay thủ tục (Request Procedures) + bảng giá thiết bị | định nghĩa loại đơn, trường bắt buộc, SLA, ai duyệt → tool `create_request` bám theo; bảng giá cần cho câu tính toán (DOC0006 ghi rõ giá **không** có trong tài liệu) |
| DOC0103 | **Nhóm viết** (tuỳ chọn) — FAQ/quy định văn phòng HCM bằng tiếng Việt | test truy vấn tiếng Việt |

> Không dùng `07_security_remote_access.txt` (ngoài DOC0001–0006 được phép). Không dùng dữ liệu nhóm khác.

### 3.2 RAG (`src/policy_agent/rag/`)
- **Chunking:** recursive theo heading/đoạn (`## Section ...`) với `chunk_size≈400`, `overlap≈60`. Lý do (viết vào docstring + report): mỗi section là 1 điều khoản trọn vẹn; cắt theo heading giữ nguyên điều khoản + số liệu đi kèm; overlap chống mất câu ở biên; chunk nhỏ để citation trỏ đúng điều khoản.
- Mỗi chunk mang metadata của tài liệu (`version, date, owner, category`) → prompt in ra `[DOC0101 v2.0 2026-09-01]` để LLM chọn bản mới.
- **Tái dùng `hybrid_search.py` (w4):** commit bản gốc trước, rồi 1 commit riêng chỉ sửa 2 chỗ bắt buộc:
  1. Dòng `sys.path.append(r"../w3")` + `from vector_store import ...` → `from policy_agent.rag.vector_store import ...` (tên hàm `embed_text`, `cosine_similarity` phải khớp `vector_store.py` của A).
  2. Hai lệnh `print(...)` trong `hybrid_search()` → `logging` (ra stderr). Hàm này chạy **bên trong MCP server**, `print()` ra stdout sẽ làm hỏng kênh JSON-RPC (bài học W7).
  - Lưu ý khi vấn đáp: file gốc chỉ normalize BM25, còn cosine giữ nguyên (đã nằm trong [-1, 1]); trọng số 0.3/0.7.
- **2 chế độ truy vấn:** `dense` (cosine) và `hybrid` (BM25 + dense, tái dùng w4) — chọn bằng `RETRIEVAL_MODE` trong `.env`/CLI, **không** để model chọn (bài học W7 KC1).
- **Metadata filter (+1):** lọc `category` / chỉ lấy bản `latest` trước khi chấm điểm.
- **Ngưỡng no_answer:** nếu điểm top-1 < `MIN_SCORE` → tool trả "No relevant passages…" → agent từ chối.
- Index build 1 lần (`make index`) → `data/index/`; server load 1 lần lúc khởi động.

### 3.3 Agent (`src/policy_agent/agent/`)
- Vòng lặp viết tay: `for step in range(MAX_STEPS)` (MAX_STEPS = 8).
- Prompt hệ thống ở `prompts/agent_system.txt`; mô tả tool sinh từ `list_tools()`.
- `parser.py`: tìm `Final Answer:` hoặc `Action: name {json}`; JSON hỏng (thiếu ngoặc, nháy đơn…) → thử sửa nhẹ → vẫn hỏng thì observation `"Error: could not parse action, use format ..."` (không crash). Viết unit test cho các ca hỏng.
- Tool lỗi → luôn trả chuỗi `"Error: ..."` (server bọc try/except, không raise).
- **Guard verify:** nếu đã gọi tool ghi thành công mà chưa gọi `get_request` cùng id, loop chặn `Final Answer` và nhắc agent verify.
- Trace: mỗi câu 1 bản ghi JSONL `{timestamp, question, steps:[{thought, action, args, observation}], final_answer, cited_doc_ids, usage:{calls, prompt_tokens, completion_tokens, max_prompt}}`.

### 3.4 MCP server (`src/policy_agent/mcp_server/`)

| Tool | Loại | Contract (tóm tắt) |
|---|---|---|
| `search_policy(query: str, top_k: int = 3, category: str \| None = None)` | read | trả `[doc_id vX date] (score) passage`, top_k ≤ 5, cắt độ dài |
| `get_document(doc_id: str)` | read | full text ≤ 4000 ký tự, kèm metadata |
| `calc_business_days(start_date: str, end_date: str)` | read | số ngày làm việc (T2–T6) giữa 2 ngày ISO |
| `create_request(request_type: str, employee: str, details: str, start_date: str = "", end_date: str = "")` | **write** | validate loại đơn theo DOC0102 → ghi `requests.json` → trả `request_id` |
| `get_request(request_id: str)` | read (**verify**) | trả bản ghi hoặc `Error: not found` |

- Transport stdio, `logging` ra stderr + `logs/server.log`; **không `print()`**.
- Không publish: `rebuild_index`, `delete_request`, tham số `mode`/`threshold`, đường dẫn file (giải thích ở report mục 5).
- `scripts/probe_server.py`: raw JSON-RPC (initialize → tools/list → tools/call) để chứng minh contract.
- Host thứ hai (+1): `scripts/second_host.py` — client Python khác, discover + gọi `get_request`; tuỳ chọn thêm cấu hình Cline.

### 3.5 Đánh giá (`src/policy_agent/eval/`, `tests/testset.jsonl`)

Schema mỗi dòng `testset.jsonl`:
```json
{"id": "Q01", "question": "...", "type": "direct|synthesis|version_conflict|calculation|action|insufficient|no_answer",
 "expected_doc_ids": ["DOC0101"], "reference_answer": "...", "expect_refusal": false, "expect_write": false}
```

Phân bổ đề xuất (14 câu, ≥4 no_answer):

| Loại | Số câu | Ví dụ |
|---|---|---|
| direct | 2 | Hoàn tiền ăn tối đa bao nhiêu/ngày? |
| synthesis (≥2 doc) | 2 | Làm ở văn phòng HCM 2 tuần cần những duyệt + thiết lập IT gì? |
| version_conflict | 2 | Được làm ở nước khác tối đa bao nhiêu ngày liên tiếp? (phải lấy v2.0) |
| calculation | 1 | Mua laptop + dock + headset thì ai duyệt? (cộng tiền → ngưỡng $1,000) |
| action (write + verify) | 2 | Tạo đơn work-from-abroad cho tôi… / Tạo đơn mua thiết bị… |
| insufficient (từ chối ở khâu suy luận) | 1 | Chi phí công tác của tôi có vượt hạn mức không? (không có hoá đơn) |
| no_answer (từ chối ở khâu truy vấn) | 4 | Lịch vesting stock option? Quy định dress code? Mức lương thử việc? Chính sách nghỉ thai sản? |

Metrics (`make eval`):
- **Faithfulness** (LLM judge W5, temp 0) cho câu không phải no_answer.
- **Tỉ lệ từ chối đúng** = no_answer + insufficient bị từ chối / tổng; kèm **tỉ lệ từ chối sai** (từ chối câu có đáp án).
- **Citation hit** = expected_doc_ids ⊆ doc_id được trích.
- **Action success** = có ghi + có verify + bản ghi tồn tại trong `requests.json`.
- **USAGE từng câu**: calls, prompt_tokens, completion_tokens, max_prompt.
- Chạy cả `dense` và `hybrid` (+1), xuất `results/eval_<ts>.csv` + biểu đồ PNG (+1).
- ≥3 lần chạy thật → `logs/run_<timestamp>.jsonl` (≥3 file).
- Chọn ≥1 ca thất bại thật để phân tích trong report.

---

## 4. Phân công

### 4.1 Nhóm 3 người

| | **SV A — RAG & dữ liệu** | **SV B — Agent & LLM** | **SV C — MCP & Eval/Reproducibility** |
|---|---|---|---|
| Code | `rag/*`, `data/corpus/*` (viết DOC0101–0103 + manifest), `rag/build_index.py` | `llm/client.py`, `prompts/*`, `agent/loop.py`, `agent/parser.py`, `agent/trace.py`, `models.py` | `mcp_server/*`, `mcp_client/*`, `scripts/*`, `eval/*`, `Makefile`, `tasks.ps1`, `README.md` |
| Test | test chunking/retrieval, so sánh dense vs hybrid | `tests/test_parser.py` (ca thiếu ngoặc…) | `tests/test_request_store.py`, probe server |
| Testset | soạn câu direct/synthesis/version_conflict/no_answer + `expected_doc_ids` | soạn câu action/calculation/insufficient | chạy eval, gom số liệu, biểu đồ |
| Report | mục 3 (RAG) | mục 4 (Agent & tool) | mục 5 (MCP), mục 6 (Đánh giá) |
| Chung | mục 1, 2, 7, 8, 9 + `ai-usage.md` — mỗi người tự khai phần mình |||

### 4.2 Quy tắc Git (được chấm)
- Mỗi người commit **bằng tài khoản của chính mình**, commit nhỏ, thường xuyên (≥1 commit/ngày làm việc), message rõ: `rag: add hybrid retriever`, `agent: safe action parser`.
- Nhánh theo phần: `feat/rag`, `feat/agent`, `feat/mcp` → merge vào `main` qua PR/review chéo.
- Không commit `.env`, `data/index/`, `.venv/`. Report mục 8 ghi commit hash từng phần.

---

## 5. Lịch 10 ngày & checkpoint

| Ngày | A — RAG | B — Agent | C — MCP/Eval | Checkpoint (Definition of Done) |
|---|---|---|---|---|
| D1 | Chốt mục 0; copy DOC0001–0006, lập `manifest.json` | `llm/client.py` (retry, timeout, log HTTP, USAGE) | `git init`, `pyproject.toml`, `Makefile`, `.env.example`, README khung | `make setup` chạy được trên 3 máy |
| D2 | Viết DOC0101, DOC0102 (+DOC0103); loader + chunking + lý do | `models.py` (dataclass), prompt files | `request_store.py` (create/get, JSON) + test | |
| D3 | Dense store + build_index; copy hybrid w4 | `parser.py` + test ca hỏng | `server.py` với `search_policy`, `get_document` (stdio, log stderr) | **CP1:** `make index` + probe thấy ≥2 tool |
| D4 | Retriever 2 chế độ + metadata filter + ngưỡng no_answer | `loop.py` (MAX_STEPS, Error strings) chạy với tool giả | thêm `create_request`, `get_request`, `calc_business_days`; `mcp_client` discover động | |
| D5 | Tinh chỉnh retrieval trên câu khó (version conflict) | Nối loop ↔ MCP client; guard verify; trace JSONL | `scripts/demo.py`, `chat.py` | **CP2:** `make demo` end-to-end 1 câu action có write + verify |
| D6 | Soạn testset phần A | Soạn testset phần B; sửa prompt | `eval/metrics.py`, `run_eval.py` | `tests/testset.jsonl` ≥12 câu, ≥4 no_answer |
| D7 | Hỗ trợ debug câu fail retrieval | Hỗ trợ debug câu fail agent | Chạy eval dense vs hybrid, CSV + chart, `second_host.py` | **CP3:** `make eval` tái lập được số liệu |
| D8 | Report mục 3 | Report mục 4 (trace thật 1 câu) | Report mục 5–6; ≥3 run logs | Report draft |
| D9 | Chạy cold start trên máy sạch (clone repo mới → `make setup && make demo`) | Viết `ai-usage.md` phần mình | README hoàn chỉnh, sửa lỗi cold start | **CP4:** cold start pass |
| D10 | Ôn vấn đáp + tập sửa code tại chỗ phần mình | như A | như A | Nộp: report.docx + repo (.git) + logs + testset + ai-usage + README |

---

## 6. Chuẩn bị bảo vệ (20 phút)
- **Cold start:** README chính xác, `.env.example` đủ biến, `data/` có sẵn corpus (index có thể build trong `make setup`).
- **Demo 3 phút/người** với 1 câu GV đưa tại chỗ → dùng `make chat` (terminal mở sẵn).
- **Sơ đồ in sẵn** (mục 2) — mỗi người trình bày ~1.5 phút phần mình.
- **Vấn đáp:** mỗi người nắm khái niệm W1–W7 + **số liệu eval của chính mình**.
- **Sửa code tại chỗ:** biết file/dòng mình viết. Bài tập thử: đổi MAX_STEPS, thêm 1 tool MCP mới, đổi trọng số hybrid, thêm 1 trường vào dataclass, đổi ngưỡng no_answer.

## 7. Việc làm thêm (+tối đa 6)
- [ ] Metadata filter dùng thật trong pipeline (+1)
- [ ] So sánh 1 cấu hình: dense vs hybrid (hoặc 2 model embedding / 2 chunk size) (+1)
- [ ] MCP server dùng được từ host thứ hai (`scripts/second_host.py`) (+1)
- [ ] Đồ thị + CSV log chi tiết theo từng câu (+1)
