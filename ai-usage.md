# Khai báo sử dụng AI (ai-usage.md)

> **Căn cứ quy định tại Mục 7 tài liệu *02-Yêu cầu thực hiện*:**  
> *"Bắt buộc nộp ai-usage.md: dùng công cụ nào, cho phần nào, prompt chính, đoạn code nào do AI sinh."*  
>
> **Mối quan hệ đồng bộ & bổ trợ với Báo cáo Word (`report.docx` / `AI_FinalProject.docx`):**  
> * **Báo cáo Word (Phụ lục 9.3):** Cung cấp **Bảng tổng hợp đối chiếu** cô đọng, hệ thống hóa theo dòng thời gian và các mốc phát triển W1–W7 để đảm bảo giới hạn dung lượng 8–9 trang của toàn bộ tài liệu.  
> * **Tệp `ai-usage.md` này:** Cung cấp **Bằng chứng kỹ thuật chuyên sâu**, lưu trữ toàn văn các câu prompt gốc, phân định ranh giới từng file/hàm/dòng code do AI sinh so với phần do sinh viên tự code, và các lệnh kiểm chứng tự động phục vụ trực tiếp cho **20 phút vấn đáp bảo vệ và sửa code trực tiếp (Mục 9)**.

---

## BẢNG TỔNG HỢP ĐỐI CHIẾU SỬ DỤNG AI (ĐỒNG BỘ VỚI PHỤ LỤC 9.3 CỦA REPORT.DOCX)

Bảng dưới đây đồng bộ 100% với **Bảng 5 (Phụ lục 9.3)** trong Báo cáo Word. Mỗi dòng được đánh mã định danh (`[A1]–[A4]`, `[B1]–[B6]`, `[C1]–[C5]`) để đối chiếu trực tiếp xuống các phần mô tả chi tiết bên dưới:

| Mã mục | Ngày | Thành viên | Công cụ AI | Phần áp dụng & File mã nguồn | Prompt chính (Tóm tắt) | Đã sửa, Tự viết & Kiểm chứng thực tế |
| :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **[C1]** | 2026-10-10 | Nguyễn Quốc Bảo Khang (C) | Claude 6.0 Opus | Khung dự án, Makefile, tasks.ps1, pyproject.toml | Đọc 2 file đề AIPR, thiết kế cây thư mục chuẩn, cấu hình uv, Makefile và tasks.ps1 đa nền tảng. | Tự thiết kế các target `setup`, `demo`, `chat`, `eval`, `probe`, `host2`, `test`. Chạy thử `make setup` pass. |
| **[A1]** | 2026-10-13 | Huỳnh Nhật Bảo (A) | ChatGPT (GPT-4o) | Nạp corpus & Chunking (`loader.py`, `chunking.py`) | Viết `load_manifest`, `load_corpus` và `chunk_document` cắt theo heading `##` max 400 ký tự, overlap 60 ký tự. | Tự viết docstring 5 dòng giải thích lý do chunking; viết `tests/test_loader.py`, `tests/test_chunking.py` đạt 100% pass. |
| **[C2]** | 2026-10-14 | Nguyễn Quốc Bảo Khang (C) | Claude 6.0 Opus | Request Store & Validation (`request_store.py`, `validation.py`) | Viết `RequestStore` lưu JSON qua atomic write (.tmp -> rename) và `validation.py` kiểm tra ngày YYYY-MM-DD, 5 loại đơn. | Tự thiết kế khóa trạng thái `submitted`; viết `tests/test_request_store.py` kiểm tra crash-safe và validate dữ liệu. |
| **[B1, B2]** | 2026-10-14 | Ngô Quang Trường (B) | Gemini 3.8 Flash | Schema Dataclass (`models.py`) & Fallback Parser (`parser.py`) | Định nghĩa 9 `@dataclass` có type hint theo Tuần 1; gợi ý `ast.literal_eval` để cứu nguy JSON nháy đơn không crash. | Tự viết ReAct parser an toàn bằng regex; viết `tests/test_parser.py` (6 ca biên thiếu ngoặc/nháy đơn) và `tests/test_models.py`. |
| **[A2]** | 2026-10-16 | Huỳnh Nhật Bảo (A) | ChatGPT (GPT-4o) | Vector Store, Embeddings & Build Index (`vector_store.py`, `embeddings.py`) | Viết `VectorStore` lưu/đọc JSON, nhúng vector bằng sentence-transformers (384 chiều) và tính cosine similarity bằng numpy. | Tự tối ưu cache embedding vào file JSON; viết `tests/test_vector_store.py`, `tests/test_embeddings.py` kiểm tra vector chuẩn. |
| **[A3, A4]** | 2026-10-17 | Huỳnh Nhật Bảo (A) | ChatGPT (GPT-4o) | RAG Retriever, Metadata Filter & Hybrid Search (`retriever.py`, `hybrid_search.py`) | Viết `retriever.py` hỗ trợ 2 chế độ dense/hybrid (tái dùng W4), hàm `filter_chunks_by_metadata` lọc supersedes và category. | Tự tích hợp lọc bản cũ DOC0005 khi có DOC0101 (+1đ cộng); viết `tests/test_retriever.py` kiểm tra gating `min_score`. |
| **[C3–C5]** | 2026-10-17 | Nguyễn Quốc Bảo Khang (C) | Claude 6.0 Opus | Second Host, Eval Pipeline & Metrics (`second_host.py`, `report.py`, `metrics.py`) | Viết `second_host.py` kiểm thử interop stdio; module `report.py` xuất CSV và vẽ biểu đồ cột; `metrics.py` đo 5 chỉ số. | Tự hoàn thiện kịch bản host thứ hai (+1đ); chạy `make eval` sinh `eval_latest.csv` và biểu đồ PNG (+1đ cộng). |
| **[B3–B6]** | 2026-10-18 | Ngô Quang Trường (B) | Gemini 3.8 Flash | HTTP Retry, Streaming, CLI & Loop Guard (`client.py`, `trace.py`, `loop.py`, `chat.py`) | Bắt HTTP 429 ghi `http_errors.jsonl`, tính retry-after; streaming gõ phím; ReAct loop có `is_forced_verify` chống đơn rác. | Tự viết toàn bộ Agent ReAct Loop tay (W6); hoàn thiện `scripts/demo.py`, `scripts/chat.py`; 112/112 tests pass. |

---

## PHẦN I: SINH VIÊN A — HUỲNH NHẬT BẢO (MSSV: 24110079)
**Phần phụ trách:** RAG Pipeline, Quản lý Corpus & Bộ chỉ mục Vector / Hybrid Search  
**Mục đối chiếu trong Report:** Mục III (Thiết kế RAG và Dữ liệu) & Mục VIII (Phân công)

### [A1] Nạp Corpus và Phân đoạn văn bản (Chunking) theo Heading
* **Ngày thực hiện:** 2026-10-13
* **Công cụ AI:** ChatGPT (GPT-4o)
* **Phần áp dụng:** Nạp corpus, kiểm tra tính toàn vẹn metadata và phân mảnh tài liệu.
* **Prompt chính (Nguyên văn):**
  ```text
  "Viết hàm load_corpus đọc tất cả file .txt trong data/corpus/ và nạp metadata từ manifest.json. 
  Viết hàm chunk_document chia nhỏ văn bản theo các đề mục markdown (##) với kích thước tối đa 400 ký tự và overlap 60 ký tự, giữ nguyên tiêu đề mục vào đầu mỗi chunk để đảm bảo ngữ cảnh."
  ```
* **Phân định code do AI sinh vs Sinh viên tự viết:**
  - **File:** `src/policy_agent/rag/loader.py` (Dòng 20 – 80): Hàm `load_manifest`, `load_corpus` do AI đề xuất khung; sinh viên bổ sung phần validate chặt chẽ kiểu dữ liệu của các trường bắt buộc (`doc_id`, `title`, `version`, `date`, `owner`).
  - **File:** `src/policy_agent/rag/chunking.py` (Dòng 13 – 80): AI sinh hàm chia tách `_split_section`; sinh viên tự viết docstring 5 dòng giải thích lý do kỹ thuật (khống chế token, giữ tiêu đề mục, overlap 60 ký tự bảo toàn câu) theo đúng yêu cầu Mục 2.5 của đề bài.
* **Kiểm chứng thực tế:** Viết và chạy `pytest tests/test_loader.py tests/test_chunking.py` xác nhận 100% chunk không vượt quá 400 ký tự và giữ đúng metadata gốc.

---

### [A2] Quản lý Vector Store, Nhúng Embeddings & Build Index
* **Ngày thực hiện:** 2026-10-16
* **Công cụ AI:** ChatGPT (GPT-4o)
* **Phần áp dụng:** Lưu trữ vector nhúng và tìm kiếm tương đồng Cosine.
* **Prompt chính (Nguyên văn):**
  ```text
  "Viết class VectorStore hỗ trợ nhúng danh sách DocumentChunk bằng thư viện sentence-transformers (model paraphase-multilingual hoặc minilm), lưu trữ và khôi phục index từ file JSON phẳng. 
  Viết hàm cosine_similarity dùng numpy để tính điểm tương đồng giữa vector query và ma trận vector chunk."
  ```
* **Phân định code do AI sinh vs Sinh viên tự viết:**
  - **File:** `src/policy_agent/rag/vector_store.py` (Dòng 12 – 126): AI sinh thuật toán cosine bằng numpy và hàm lưu/đọc file JSON. Sinh viên tự tối ưu cấu trúc lưu trữ `chunks` dạng dictionary với key là `chunk_id`.
  - **File:** `src/policy_agent/rag/embeddings.py` (Dòng 15 – 45): Đóng gói model sentence-transformers với bộ nhớ cache in-memory.
  - **File:** `src/policy_agent/rag/build_index.py` (Dòng 10 – 40): Script build toàn bộ corpus thành `data/index/index.json`.
* **Kiểm chứng thực tế:** Chạy `python -m policy_agent.rag.build_index` sinh thành công file chỉ mục 384 chiều; chạy `pytest tests/test_vector_store.py tests/test_embeddings.py` pass 100%.

---

### [A3] Bộ truy vấn RAG Retriever, Lọc Metadata & Tái dùng Hybrid Search Tuần 4
* **Ngày thực hiện:** 2026-10-17
* **Công cụ AI:** ChatGPT (GPT-4o)
* **Phần áp dụng:** Module truy vấn hợp nhất (`retriever.py`) hỗ trợ 2 chế độ Dense / Hybrid và bộ lọc Metadata (+1 điểm cộng).
* **Prompt chính (Nguyên văn):**
  ```text
  "Viết module retriever.py hỗ trợ 2 chế độ truy vấn: 'dense' (Cosine thuần túy) và 'hybrid' (kết hợp 0.3 * BM25_norm + 0.7 * Cosine từ bài tập Tuần 4). 
  Đặc biệt, viết hàm filter_chunks_by_metadata để tự động phát hiện các tài liệu cũ bị thay thế qua trường metadata 'supersedes' (ví dụ DOC0101 thay thế DOC0005) để loại bỏ tài liệu cũ trước khi chấm điểm, đồng thời lọc theo category nếu có."
  ```
* **Phân định code do AI sinh vs Sinh viên tự viết:**
  - **File:** `src/policy_agent/rag/retriever.py` (Dòng 48 – 79): Hàm `filter_chunks_by_metadata` do AI đề xuất thuật toán; sinh viên tự liên kết với trường `supersedes` trong `manifest.json`.
  - **File:** `src/policy_agent/rag/retriever.py` (Dòng 89 – 159): Hàm `retrieve` và `format_chunk_hit` tích hợp gating `min_score` tự động loại bỏ kết quả dưới ngưỡng để chống ảo giác (hallucination).
  - **File:** `src/policy_agent/rag/hybrid_search.py`: Tái sử dụng trực tiếp mã nguồn bài tập Tuần 4 (`rank_bm25` và chuẩn hóa Min-Max).
* **Kiểm chứng thực tế:** Chạy `pytest tests/test_retriever.py`, kiểm chứng câu hỏi về làm việc từ xa tự động lấy nội dung từ `DOC0101 v2.0` và loại bỏ hoàn toàn `DOC0005 v1.0`.

---

### [A4] Bộ kiểm thử Unit Tests RAG Pipeline
* **Ngày thực hiện:** 2026-10-17
* **Công cụ AI:** ChatGPT (GPT-4o)
* **Phần áp dụng:** Kiểm thử tự động toàn diện tầng dữ liệu và truy vấn.
* **Prompt chính (Nguyên văn):**
  ```text
  "Viết các file unit test bằng pytest cho toàn bộ pipeline RAG gồm test_loader.py, test_chunking.py, test_vector_store.py, test_embeddings.py và test_retriever.py với các mock fixture đảm bảo không phụ thuộc internet."
  ```
* **Kiểm chứng thực tế:** Chạy `pytest tests/test_loader.py tests/test_chunking.py tests/test_vector_store.py tests/test_embeddings.py tests/test_retriever.py` — toàn bộ 42 bài test thuộc phần RAG đều vượt qua trong 4.1 giây.

---

## PHẦN II: SINH VIÊN B — NGÔ QUANG TRƯỜNG (MSSV: 24110142)
**Phần phụ trách:** ReAct Agent Loop, LLM Client (W2), Parser an toàn & Giao diện CLI  
**Mục đối chiếu trong Report:** Mục IV (Thiết kế Agent và LLM) & Mục VIII (Phân công)

### [B1] Định nghĩa Schema Dữ liệu Chuẩn Tuần 1 (@dataclass)
* **Ngày thực hiện:** 2026-10-14
* **Công cụ AI:** Gemini 3.8 Flash
* **Phần áp dụng:** Định nghĩa cấu trúc dữ liệu cho Agent, Trace và LLM Usage theo đúng quy chuẩn Tuần 1.
* **Prompt chính (Nguyên văn):**
  ```text
  "Giảng viên yêu cầu đồ án phải khai báo toàn bộ Tool Schema, Action, Trace và Usage bằng @dataclass của Python 3.11 có type hint đầy đủ, tuyệt đối không dùng dict thô. Hãy gợi ý định nghĩa chuẩn cho StepTrace, RunTrace, Usage, ParsedAction và ToolSpec."
  ```
* **Phân định code do AI sinh vs Sinh viên tự viết:**
  - **File:** `src/policy_agent/models.py` (Dòng 6 – 98): AI sinh cấu trúc mẫu cho 9 lớp `@dataclass`. Sinh viên tự bổ sung trường `max_prompt` vào `Usage` để giám sát cửa sổ ngữ cảnh và phương thức chuyển đổi `ToolSpec` tương thích chuẩn JSON-RPC của MCP.
* **Kiểm chứng thực tế:** Lệnh `grep -n "@dataclass" src/policy_agent/models.py` hiển thị đầy đủ 9 class; chạy `pytest tests/test_models.py` pass 100%.

---

### [B2] Bộ phân tích cú pháp an toàn (Safe ReAct Action Parser)
* **Ngày thực hiện:** 2026-10-14
* **Công cụ AI:** Gemini 3.8 Flash
* **Phần áp dụng:** Xử lý và trích xuất Action / Final Answer từ chuỗi sinh của LLM.
* **Prompt chính (Nguyên văn):**
  ```text
  "Trong bài toán Agent loop, khi LLM sinh Action Input, đôi khi mô hình sinh ra cú pháp dictionary dạng nháy đơn của Python kiểu {'query': 'remote'} thay vì chuẩn JSON nháy kép, dẫn đến json.loads() bị lỗi JSONDecodeError. 
  Hãy gợi ý hàm parse an toàn dùng ast.literal_eval làm fallback và bọc try-except toàn bộ để nếu LLM sinh lỗi thì trả về ParsedAction(kind='error') chứ không được làm sập chương trình."
  ```
* **Phân định code do AI sinh vs Sinh viên tự viết:**
  - **File:** `src/policy_agent/agent/parser.py` (Dòng 7 – 43): AI đề xuất hàm `_parse_action_input` với `ast.literal_eval`. Sinh viên tự viết toàn bộ biểu thức chính quy (Regex) bóc tách `Thought:`, `Action:`, `Action Input:`, `Final Answer:` và luật khống chế chỉ cho phép duy nhất 1 Action hoặc 1 Final Answer mỗi lượt.
* **Kiểm chứng thực tế:** Chạy `pytest tests/test_parser.py` kiểm chứng 6 kịch bản lỗi biên (chuỗi rỗng, thiếu ngoặc nhọn, nháy đơn, xuất hiện cả Action và Final Answer) đều được bẫy an toàn về `ParsedAction(kind='error')`.

---

### [B3] Client Gọi LLM có Retry, Exponential Backoff & Ghi Log Lỗi HTTP (W2)
* **Ngày thực hiện:** 2026-10-15
* **Công cụ AI:** Gemini 3.8 Flash
* **Phần áp dụng:** Gọi API Groq với cơ chế bảo vệ mạng và xử lý chạm ngưỡng (Rate Limit).
* **Prompt chính (Nguyên văn):**
  ```text
  "Trong hàm call_llm, hãy viết khối bắt APIConnectionError và APIStatusError (mã HTTP 429 hoặc >= 500). Ghi nhật ký lỗi vào file logs/http_errors.jsonl (gồm timestamp, attempt, error_type, status_code, retry) và tính thời gian chờ sleep theo header retry-after nếu có, hoặc tính exponential backoff 5.0 * (2 ** (attempt - 1))."
  ```
* **Phân định code do AI sinh vs Sinh viên tự viết:**
  - **File:** `src/policy_agent/llm/client.py` (Dòng 8 – 100): AI đề xuất khối `try...except` và cách trích xuất header `retry-after`. Sinh viên tự cấu hình adapter gọi Groq với `timeout=30.0`, cơ chế cộng dồn token `usage.prompt_tokens` và tính năng streaming `on_chunk`.
* **Kiểm chứng thực tế:** Chạy `pytest tests/test_llm.py` kiểm tra giả lập lỗi 429 kích hoạt retry chuẩn xác và ghi nhận lỗi vào `logs/http_errors.jsonl`.

---

### [B4] Ghi nhận Trace JSONL Chuẩn & Hiệu ứng Streaming Console
* **Ngày thực hiện:** 2026-10-16
* **Công cụ AI:** Gemini 3.8 Flash
* **Phần áp dụng:** Tuần tự hóa vết chạy và tạo trải nghiệm trực quan trên terminal.
* **Prompt chính (Nguyên văn):**
  ```text
  "Viết hàm save_trace(run, path) để serialize đối tượng RunTrace thành file .jsonl với các dòng event: START, STEP, FINAL, USAGE. Kèm hàm stream_print(text, delay=0.015) in từng ký tự ra sys.stdout có flush để tạo hiệu ứng gõ phím khi demo."
  ```
* **Phân định code do AI sinh vs Sinh viên tự viết:**
  - **File:** `src/policy_agent/agent/trace.py` (Dòng 8 – 35): AI cung cấp khung serialization. Sinh viên tự tinh chỉnh định dạng JSON đảm bảo tiếng Việt Unicode hiển thị nguyên bản (`ensure_ascii=False`).
* **Kiểm chứng thực tế:** Chạy `pytest tests/test_trace.py` kiểm tra sinh đúng 4 sự kiện chuẩn và ghi file thành công.

---

### [B5] Kịch bản Demo tự động (`demo.py`) & Terminal Chat (`chat.py`)
* **Ngày thực hiện:** 2026-10-18
* **Công cụ AI:** Gemini 3.8 Flash
* **Phần áp dụng:** Scripts giao tiếp người dùng và chạy kịch bản nghiệm thu.
* **Prompt chính (Nguyên văn):**
  ```text
  "Hãy viết giúp tôi 2 script Python:
  1. scripts/chat.py: Mở kết nối MCPToolClient qua stdio, chạy vòng lặp hỏi đáp tương tác trên terminal, in rõ từng bước Thought, Action, Observation, Final Answer và thống kê USAGE.
  2. scripts/demo.py: Chạy tự động 3 câu hỏi mẫu đại diện cho 3 tầng: Tra cứu + xử lý phiên bản mới nhất, Tạo đơn có verify, và Từ chối câu hỏi ngoài phạm vi."
  ```
* **Phân định code do AI sinh vs Sinh viên tự viết:**
  - **File:** `scripts/demo.py`: Sinh viên tự thiết kế 3 ca kiểm thử cốt lõi (DOC0101 version supersedes, tạo đơn Remote Work có xác thực, và câu hỏi từ chối về cổ phiếu stock option).
  - **File:** `scripts/chat.py`: Sinh viên tự tích hợp cờ `--question` để hỗ trợ cả chế độ hỏi 1 câu và chế độ hội thoại liên tục.
* **Kiểm chứng thực tế:** Chạy `make demo` hiển thị mượt mà 3 câu hỏi mẫu với hiệu ứng streaming ký tự; chạy `make chat` trả lời trơn tru các câu hỏi tự do.

---

### [B6] ReAct Agent Loop Viết Tay & Cơ chế Guard Bắt buộc Xác minh (Write + Verify)
* **Ngày thực hiện:** 2026-10-18
* **Công cụ AI:** Gemini 3.8 Flash (Trao đổi tư vấn thuật toán)
* **Phần áp dụng:** Trái tim điều phối ReAct Loop và cơ chế an toàn Write + Verify (Mục 2.6 và 2.7).
* **Phần do Sinh viên tự viết 100%:**
  - **File:** `src/policy_agent/agent/loop.py` (Dòng 41 – 182): Sinh viên tự tay thiết kế vòng lặp `for step_idx in range(settings.max_steps)`:
    + Cờ `is_forced_verify`: Khi `create_request` được gọi, hệ thống lập tức ép bước kế tiếp phải gọi `get_request` để kiểm tra bản ghi trên ổ đĩa.
    + Guard khống chế bước còn lại: Nếu số bước còn lại $< 2$, agent tự động chặn lệnh ghi và trả về thông báo lỗi, ngăn chặn hoàn toàn việc tạo đơn rác mà không kịp xác minh.
* **Kiểm chứng thực tế:** Chạy `pytest tests/test_loop.py` xác minh luồng tra cứu trích dẫn `[DOC0001]` và luồng tạo đơn bắt buộc hoàn tất xác minh trước khi đưa ra Final Answer.

---

## PHẦN III: SINH VIÊN C — NGUYỄN QUỐC BẢO KHANG (MSSV: 24110099)
**Phần phụ trách:** MCP Server (Stdio), Request Store, Pipeline Đánh giá (Eval) & Second Host  
**Mục đối chiếu trong Report:** Mục V (Giao thức MCP Server), Mục VI (Đánh giá) & Mục VIII (Phân công)

### [C1] Khởi tạo Khung dự án, Quản lý Gói và Tự động hóa (Makefile / Tasks)
* **Ngày thực hiện:** 2026-10-10
* **Công cụ AI:** Claude 6.0 Opus
* **Phần áp dụng:** Cấu trúc repository, cấu hình môi trường `uv` và script chạy 1 lệnh đa nền tảng.
* **Prompt chính (Nguyên văn):**
  ```text
  "Đọc 2 file tài liệu đề tài và yêu cầu thực hiện AIPR (W1–W7). Hãy thiết kế cấu trúc thư mục dự án chuẩn, file pyproject.toml với uv, Makefile và tasks.ps1 để chạy được trên cả Linux/macOS và Windows với đúng 1 lệnh 'make setup && make demo'."
  ```
* **Phân định code do AI sinh vs Sinh viên tự viết:**
  - **File:** `Makefile` & `tasks.ps1`: AI sinh các target cơ bản; sinh viên tự bổ sung các target chuyên biệt: `probe` (test JSON-RPC thô), `host2` (chạy host thứ hai), và `eval` (chạy song song Dense và Hybrid).
  - **File:** `pyproject.toml`: Sinh viên tự rà soát các gói thư viện được phép (mcp SDK, sentence-transformers, rank_bm25, groq, python-docx, matplotlib).
* **Kiểm chứng thực tế:** Khởi tạo môi trường ảo sạch sẽ, chạy `make setup` cài đặt thành công 100% dependencies.

---

### [C2] Quản lý Trạng thái Bền vững (Request Store) & Validation Đơn Thủ tục
* **Ngày thực hiện:** 2026-10-14
* **Công cụ AI:** Claude 6.0 Opus
* **Phần áp dụng:** Module lưu trữ hồ sơ thủ tục thay đổi trạng thái và xác thực trường dữ liệu.
* **Prompt chính (Nguyên văn):**
  ```text
  "Viết class RequestStore quản lý lưu trữ đơn thủ tục vào data/state/requests.json bằng cơ chế atomic write (ghi file .tmp rồi rename) để chống hỏng file khi crash. Viết module validation.py kiểm tra trường bắt buộc của 5 loại đơn và định dạng ngày ISO YYYY-MM-DD."
  ```
* **Phân định code do AI sinh vs Sinh viên tự viết:**
  - **File:** `src/policy_agent/mcp_server/request_store.py` (Dòng 12 – 91): AI sinh cơ chế atomic write; sinh viên tự hoàn thiện phương thức `create` tự động sinh mã UUID dạng `REQ-<hex>`, gán trạng thái mặc định `submitted` và timestamp UTC.
  - **File:** `src/policy_agent/mcp_server/validation.py` (Dòng 13 – 61): Sinh viên tự quy định danh sách các trường bắt buộc cho 5 loại đơn (`REMOTE_WORK`, `INTL_WORK`, `HARDWARE_PURCHASE`, `EXPENSE_CLAIM`, `SECURITY_REVIEW`).
* **Kiểm chứng thực tế:** Chạy `pytest tests/test_request_store.py` pass 100%, tạo thử và đọc lại dữ liệu toàn vẹn từ `requests.json`.

---

### [C3] Giao thức Máy khách Thứ hai (Second Host Client) & Probe Server
* **Ngày thực hiện:** 2026-10-16
* **Công cụ AI:** Claude 6.0 Opus
* **Phần áp dụng:** Chứng minh khả năng tương tác mở (Interoperability) của MCP Server qua kênh stdio (+1 điểm cộng).
* **Prompt chính (Nguyên văn):**
  ```text
  "Viết script độc lập scripts/second_host.py kết nối tới MCP server qua stdio JSON-RPC. Script tự động gọi list_tools để discover danh sách công cụ động, sau đó gọi thử calc_business_days và tạo đơn create_request + get_request để xác thực interoperability."
  ```
* **Phân định code do AI sinh vs Sinh viên tự viết:**
  - **File:** `scripts/second_host.py` (Dòng 27 – 105): AI sinh cấu trúc phiên làm việc MCP client độc lập; sinh viên tự viết luồng kịch bản kiểm thử 4 bước rõ ràng in ra terminal.
  - **File:** `scripts/probe_server.py` (Dòng 15 – 65): Script kiểm thử mức giao vận thấp, bắn bản tin JSON-RPC `tools/list` và `tools/call`.
* **Kiểm chứng thực tế:** Chạy `make host2` in ra thông báo kết nối thành công, tự động khám phá 5 công cụ và hoàn tất tạo/đọc đơn trên máy khách độc lập.

---

### [C4] Pipeline Đánh giá Tự động (Make Eval), Xuất CSV & Vẽ Biểu đồ So sánh
* **Ngày thực hiện:** 2026-10-17
* **Công cụ AI:** Claude 6.0 Opus
* **Phần áp dụng:** Đánh giá định lượng hệ thống theo bộ câu hỏi `testset.jsonl`, đo 5 metrics và vẽ biểu đồ so sánh (+1 điểm cộng).
* **Prompt chính (Nguyên văn):**
  ```text
  "Viết module report.py xuất kết quả đánh giá ra CSV chi tiết từng câu. Viết hàm plot_comparison_chart dùng matplotlib để vẽ biểu đồ so sánh giữa Dense và Hybrid (Pass Rate, Faithfulness, Citation Hit, Refusal, Token Cost). Viết metrics.py tính điểm Faithfulness bằng LLM Judge, Citation Hit và Action Success."
  ```
* **Phân định code do AI sinh vs Sinh viên tự viết:**
  - **File:** `src/policy_agent/eval/report.py` (Dòng 14 – 155): AI sinh mã vẽ đồ thị matplotlib; sinh viên tự căn chỉnh màu sắc, nhãn trục, lưu ảnh phân giải cao `results/benchmark_dense_vs_hybrid.png`.
  - **File:** `src/policy_agent/eval/metrics.py` (Dòng 30 – 160): Sinh viên tự thiết kế 2 prompt LLM Judge (`judge_claim.txt` và `judge_decompose.txt`) để chấm điểm Faithfulness theo phương pháp bóc tách luận điểm.
  - **File:** `src/policy_agent/eval/run_eval.py`: Tự viết luồng chạy tự động lần lượt 14 câu trên 2 chế độ, xuất bảng `results/eval_latest.csv`.
* **Kiểm chứng thực tế:** Chạy `make eval` hoàn tất thành công 28 lượt chạy, sinh ra báo cáo CSV chi tiết và biểu đồ so sánh trực quan đưa vào Báo cáo Word.

---

### [C5] Bộ kiểm thử MCP Server & Eval Metrics
* **Ngày thực hiện:** 2026-10-18
* **Công cụ AI:** Claude 6.0 Opus
* **Phần áp dụng:** Unit tests cho Server MCP, Request Store, Second Host và Metrics.
* **Prompt chính (Nguyên văn):**
  ```text
  "Viết các bài test pytest kiểm tra hàm safe_call của MCP server không bao giờ raise exception, kiểm tra bảo vệ stdout luôn sạch, test chạy tự động second host và kiểm tra tính toán các chỉ số metrics."
  ```
* **Kiểm chứng thực tế:** Chạy `pytest tests/test_server.py tests/test_request_store.py tests/test_second_host.py tests/test_eval_metrics.py` — toàn bộ bài test đều pass 100%.

---

## PHẦN IV: CAM KẾT LIÊM CHÍNH HỌC THUẬT & HƯỚNG DẪN VẤN ĐÁP (20 PHÚT)

1. **Nguyên tắc Liêm chính học thuật (Academic Integrity):**
   - Cả 3 sinh viên cam kết đã khai báo trung thực 100% các đoạn code có sự hỗ trợ của AI.
   - Các công cụ AI (ChatGPT, Gemini, Claude) được sử dụng đúng vai trò là trợ lý lập trình (Coding Assistant) để gợi ý cú pháp, sinh dữ liệu kiểm thử mẫu và viết các hàm tiện ích.
   - Toàn bộ tư duy kiến trúc hệ thống, việc tích hợp ranh giới MCP stdio, vòng lặp điều phối ReAct loop, cơ chế bảo vệ Write + Verify, và thiết kế 14 câu hỏi đánh giá đều do sinh viên trực tiếp thiết kế, làm chủ và kiểm thử thực tế.

2. **Sự sẵn sàng cho 20 phút bảo vệ cá nhân:**
   - **Sinh viên A (Huỳnh Nhật Bảo):** Nắm vững từng dòng code trong `rag/`, sẵn sàng giải thích cơ chế chunking 400 ký tự, thuật toán cosine similarity, công thức kết hợp Hybrid BM25, và hàm lọc `supersedes` metadata.
   - **Sinh viên B (Ngô Quang Trường):** Nắm vững từng dòng code trong `agent/` và `llm/`, sẵn sàng biểu diễn xử lý lỗi cú pháp bằng `ast.literal_eval`, luồng ReAct loop, cơ chế retry khi gặp lỗi mạng 429, và cờ kiểm soát `is_forced_verify`.
   - **Sinh viên C (Nguyễn Quốc Bảo Khang):** Nắm vững từng dòng code trong `mcp_server/` và `eval/`, sẵn sàng chứng minh tính sạch của kênh stdio, cơ chế atomic write chống hỏng file `requests.json`, giải thích công thức tính Faithfulness và phân tích sâu ca thất bại Q09.
