# Tổng hợp kiến thức W1–W8 → dùng cho Final Project (T1: Trợ lý quy chế + hành động)

> Nguồn: slide `week1..week7/index.html` (+ `deck.pdf` W5–W7), code `resource week 1..8`.
> Cột "Dùng trong project" chỉ ra file nào trong repo sẽ tái dùng kiến thức/code đó.

---

## W1 — Python Data Structures for AI

| Khái niệm | Điểm cần nhớ (vấn đáp hay hỏi) |
|---|---|
| list / dict / set / tuple | list = chuỗi có thể đổi; dict = record (API response, metadata); set = dedup O(1); tuple = key bất biến, hashable (cache key) |
| Truy cập an toàn | `d.get("k", default)`, idiom `resp.get("choices", [{}])[0].get(...)` |
| JSON | chỉ 6 kiểu; `datetime`/`set` cần `CustomEncoder.default()` |
| `@dataclass` | sinh `__init__/__repr__/__eq__`; **mutable default phải dùng `field(default_factory=list)`** |
| `asdict` + `DataclassEncoder` | dataclass → JSON (dùng ghi trace JSONL) |
| Type hints / TypedDict | không ép kiểu runtime; phục vụ IDE/mypy và **là schema** của tool MCP (W7) |

Code tham khảo: `resource week 1/codeAlong3.py`, `ex1.py` (DataclassEncoder, load/save chunks).
**Dùng trong project:** `src/policy_agent/models.py` (mọi schema = dataclass, đề bắt `grep -n "@dataclass"`), `agent/trace.py`.

## W2 — LLM API Access & Integration

| Khái niệm | Điểm cần nhớ |
|---|---|
| Chat completion | `messages=[{role, content}]`, đọc `choices[0].message.content`, `usage.prompt_tokens/completion_tokens` |
| Tham số | `temperature=0` cho output ổn định/judge; `max_tokens` → `finish_reason="length"` |
| Streaming | ghép `delta.content`, chunk cuối `content=None` + `finish_reason="stop"` |
| Error handling | **Retry**: RateLimit, APIConnection, 5xx · **Không retry**: Auth (sai key), BadRequest; backoff `2**attempt + jitter` |
| Prompt template | `string.Template.safe_substitute`, validate input rỗng; **prompt là code → tách ra file** |
| Bảo mật key | `.env` + `load_dotenv()`, `.env` vào `.gitignore` |
| Logging/cost | ghi JSONL mỗi call (timestamp, tokens, cost, finish_reason) |

Code: `resource week 2/errh.py` (retry đầy đủ taxonomy), `api_helpers.py` (PRICING, `log_api_call` JSONL), `ex2_3_chat_assistant.py` (sliding window history). Stack lớp dùng: **Groq**, model `openai/gpt-oss-20b` / `qwen/qwen3.8-27b`.
**Dùng trong project:** `llm/client.py` (call_llm có retry/timeout + log lỗi HTTP), `prompts/*.txt`.

> ⚠️ `resource week 2/test_api.py` dòng 1 đang chứa một Groq API key thật dạng comment. **Không copy file này vào repo project**, và nên vào console Groq thu hồi (rotate) key đó.

## W3 — RAG Foundations: Documents & Embeddings

| Khái niệm | Điểm cần nhớ |
|---|---|
| `Document` / `DocumentChunk` | `doc_id` liên kết chunk → document cha; `chunk_id` để truy vết trích dẫn |
| DocumentStore | add/get/delete(cascade chunks)/list — khung của mọi vector DB |
| Chunking | fixed-size + overlap (nhanh) · recursive `\n\n → \n → . → space` (giữ đoạn) · semantic (tốn API) |
| Overlap | để câu nằm ở biên không bị cắt đôi |
| Embedding | vector đã normalize → cosine = dot; `jina-embeddings-v3` (API) hoặc `all-MiniLM-L6-v2` (local) |
| Cosine | `dot(a,b)/(‖a‖‖b‖)`, ∈ [-1, 1]; **threshold cấu hình được** (KC2) |

Code: `resource week 3/recursive_chunking.py`, `jina_embeddings.py`, `ex2_2_similarity_research.py`.
**Dùng trong project:** `rag/chunking.py` (+ 3–5 dòng lý do chunking), `rag/embeddings.py`.

## W4 — Building the RAG Pipeline

| Khái niệm | Điểm cần nhớ |
|---|---|
| Grounding prompt | "Answer based ONLY on the context… nếu thiếu, nói *I cannot find…*" → chống hallucination |
| Pipeline 5 bước | embed query → search → build prompt → LLM (temp 0) → trả `{query, answer, sources, num_chunks, context_tokens}` |
| Citation | format context `[i] (Source: doc_id/title)` → câu trả lời trích được nguồn |
| Edge cases | không có chunk liên quan · query rỗng · context quá dài (token budget) |
| **Hybrid search** | BM25 (`rank_bm25`) + cosine, **normalize min-max trước khi fuse**, `0.3·BM25 + 0.7·vector` |
| Re-ranking | cross-encoder trên top-N → tăng precision (recall do stage 1 quyết định) |
| Metadata filter | lọc theo `source/date/...` **trước** khi chấm điểm |

Code: `resource week 4/ex1_3_document_loader.py` (fixed vs recursive + thống kê), `vector_store.py` (dense + save/load JSON), `ex1_3_rag_v1.py` (RAG v1 + bảng quan sát 3 loại câu: direct/partial/none), `company_policy.txt`.
**Dùng trong project:** `rag/vector_store.py` (dense), `rag/hybrid_search.py`, `rag/retriever.py`.

> Đề bắt **tái dùng `w4/ex2_1_hybrid_search.py`, không viết lại** → đã đặt tại `src/policy_agent/rag/hybrid_search.py` (bản gốc + header ghi nguồn). Nội dung: `normalise_scores()` (min-max), `build_bm25_index()` (tách từ bằng khoảng trắng), `hybrid_search()` trả `(chunk_index, score)` với `0.3·BM25_norm + 0.7·cosine`.

## W5 — RAG Evaluation & Groundedness

| Metric | Hỏi gì | Cách đo |
|---|---|---|
| Faithfulness | answer có bám context không? | tách answer thành claim → LLM judge YES/NO từng claim (temp 0) → supported/total |
| Answer relevance | answer có trả lời đúng câu hỏi? | LLM judge YES/NO (không nhìn context → có blind spot) |
| Context precision | chunk lấy về có liên quan? | relevant chunks / retrieved |
| Context recall | có lấy đủ chunk cần? | cần ground truth (expected doc_ids) |

- Test set phải có phổ câu: **direct / synthesis / unknown (no_answer)** — câu unknown bắt hallucination.
- Chẩn đoán theo pattern metric, **mỗi lần chỉ đổi MỘT biến** rồi đo lại.
- Failure modes: missing context, lost-in-the-middle, hallucination, over-reliance, irrelevant retrieval.

Code: `resource week 5/lab5_sheet_for_student (1).md` (check_faithfulness, answer_relevance, context_precision, detect_failure_modes, Evaluator).
**Dùng trong project:** `eval/metrics.py`, `eval/run_eval.py`, `tests/testset.jsonl`.

## W6 — Agent Loop, ReAct & Memory

| Khái niệm | Điểm cần nhớ |
|---|---|
| Function calling | khai báo schema → model trả `tool_calls` → **code của mình** validate + chạy → append assistant msg **trước** tool msg, kèm `tool_call_id` |
| Agent loop | call → execute → observe → repeat, **có `MAX_STEPS`** (vừa chặn vòng lặp vô hạn vừa chặn chi phí) |
| ReAct | `Thought / Action / Observation / Final Answer`; parse bằng regex → **dễ vỡ → parse lỗi phải xử lý êm** (retry/nhắc format/dừng sạch) |
| Memory | history, tool results, sliding window / summary / external store |
| An toàn | **không bao giờ `eval()`** tool args/output; tool output = input không tin cậy (prompt injection) |
| Write + verify | `ex2_1_react_2_unfinished.py`: `cleanup_logs()` đổi trạng thái nhưng **không báo số mới → phải gọi lại `disk_usage()` để verify** — đúng khuôn tầng (c) của đề |

Code: `resource week 6/ex1_1_tc1_unfinished.py` (function calling 2 vòng), `ex2_1_react.py` (`parse_reply`, `run_action`, `react_agent`), `ex2_1_react_2_unfinished.py` (read/write/verify).
**Dùng trong project:** `agent/loop.py`, `agent/parser.py`. Buổi bảo vệ đọc code "bài C2/C3" ≈ Concept 2 (agent loop) & Concept 3 (memory) của W6.

## W7 — Model Context Protocol (MCP)

| Khái niệm | Điểm cần nhớ |
|---|---|
| Host / Client / Server | host = app; 1 client / 1 server; server khai báo capability |
| 3 primitives | Tools (model quyết định gọi) · Resources (app gắn vào) · Prompts (user gọi) |
| Transport | **stdio** (client spawn server, stdout = kênh JSON-RPC) · Streamable HTTP (remote) · SSE (legacy) |
| 2 động từ | `tools/list` (discover) · `tools/call` |
| **stdout sạch** | `print()` trong server làm hỏng stream → log ra **stderr** / file |
| Thiết kế tool | 1 tool = 1 ý định, tên là động từ; trả text có provenance `[doc_id]`; **bound** output; không lộ path; type hints **là** schema |
| Registry biến mất | agent không hard-code danh sách tool: `tools = await client.list_tools()` → adapter `mcp_tools_to_openai()` |
| Server nợ client | declaration đúng, tên ổn định, lỗi mô tả được, output có giới hạn, không bẩn stdout; load store 1 lần ở module level |
| Raw probe | debug server bằng JSON-RPC stdlib trước khi debug agent |
| SDK version | lớp dùng **v2**: `from mcp.server import MCPServer`, `from mcp import Client, StdioServerParameters`; spawn bằng `sys.executable` + đường dẫn tuyệt đối |

Code: `resource week 7/create_mcp.py` (server + logging stderr), `rag_server.py` (5 tool: search_documents, get_document, list_documents, remember, recall), `mcp_client.py` (discover), `probe-mcp.py` / `probe_fetch_mcp.py` (raw probe), `student_mcp_setup.md` (Cline = host thứ hai).
**Dùng trong project:** `mcp_server/server.py`, `mcp_client/client.py`, `scripts/probe_server.py`, `scripts/second_host.py`.

## W8 — Multi-Agent (tham khảo, không bắt buộc)

- `resource week 8/common.py`: **`call_llm` + `USAGE = {calls, prompt_tokens, completion_tokens, max_prompt}`** — đúng 4 trường đề yêu cầu log từng câu → tái dùng pattern này.
- `Tool` dataclass (name, description, parameters, fn) + `schema()`.
- `case1_tools.py`: `draft_email` = tool có side effect (ghi `./drafts`).
- `data/01..06_*.txt` = **DOC0001–DOC0006 của lớp** (Company Policy, IT Helpdesk, IT Procurement, Global Offices, International Work, Equipment Catalog) → được phép tái dùng.
- 4 pattern: pipeline, orchestrator-worker, router, critic. **Critic/verifier phải là context khác producer** (không thì là "rubber stamp") — có thể dùng làm ý tưởng cho bước verify câu trả lời.

---

## Ánh xạ: yêu cầu bắt buộc → tuần → file trong repo

| # | Yêu cầu (02-Yeu-cau) | Tuần | File chính |
|---|---|---|---|
| 2.1 | Python 3.11+, `make setup && make demo` | — | `Makefile`, `pyproject.toml`, `README.md` |
| 2.2 | Agent loop tự viết (không framework) | W6 | `agent/loop.py` |
| 2.3 | Tool schema = dataclass/TypedDict có type hint | W1 | `models.py` |
| 2.4 | retry/timeout, log lỗi HTTP, prompt tách file | W2 | `llm/client.py`, `prompts/*.txt` |
| 2.5 | dense + hybrid BM25 (tái dùng w4), chunking có lý do | W3–W4 | `rag/*` |
| 2.6 | MAX_STEPS, tool lỗi trả `"Error: ..."`, parse action an toàn | W6 | `agent/loop.py`, `agent/parser.py` |
| 2.7 | ≥1 tool ghi + verify bằng tool đọc | W6 | `mcp_server/request_store.py`, `agent/loop.py` |
| 2.8 | MCP server tự viết, ≥2 tool (≥1 ghi), stdio, stdout sạch, client discover động | W7 | `mcp_server/server.py`, `mcp_client/client.py` |
| Eval | ≥12 câu, ≥4 no_answer, faithfulness + tỉ lệ từ chối đúng, USAGE từng câu | W5, W8 | `tests/testset.jsonl`, `eval/*`, `logs/` |
