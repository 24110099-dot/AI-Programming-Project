"""Script dich toan bo tieu luan AI_FinalProject - Copy.docx sang tieng Anh.
Bao toan 100% dinh dang, phong chu, hinh anh va bang bieu.
"""

from pathlib import Path
import docx

PARAGRAPH_TRANSLATIONS = {
    22: "Ho Chi Minh City, October 2026",
    29: "- Team Leader: Ngo Quang Truong – Phone: 0838282133",
    30: "Instructor's feedback: ...............................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................",
    32: "TABLE OF CONTENTS:",
    33: "I. PROBLEM SCOPE\t2",
    34: "1.1. Target Users and Context\t2",
    35: "1.2. In-scope System Capabilities\t2",
    36: "1.3. Out-of-scope System Boundaries\t2",
    37: "II. SYSTEM ARCHITECTURE\t3",
    38: "III. RAG AND DATA DESIGN (Student A)\t4",
    39: "3.1. Corpus Structure and Version Management\t4",
    40: "3.2. Chunking Strategy\t4",
    41: "3.3. Retrieval Mechanism and Hybrid Search\t4",
    42: "IV. AGENT AND LLM DESIGN (Student B)\t5",
    43: "4.1. Core Agent Loop and ReAct Prompting\t5",
    44: "4.2. Fault Tolerance & Safe Action Parser\t5",
    45: "4.3. Write + Verify Principle (Action Certification)\t5",
    46: "V. MCP SERVER PROTOCOL (Student C)\t5",
    47: "VI. SYSTEM EVALUATION (Student C)\t6",
    48: "6.1. Test Suite Configuration (Testset)\t6",
    49: "6.2. Evaluation Metrics and Results\t6",
    50: "6.3. Failure Case Analysis\t7",
    51: "VII. SYSTEM LIMITATIONS\t7",
    52: "VIII. TEAM CONTRIBUTION & GIT COMMITS\t7",
    53: "IX. APPENDIX\t7",
    55: "REPORT CONTENT",
    56: "I. PROBLEM SCOPE",
    57: "1.1. Target Users and Context.",
    58: "The \"Rules and Action Assistant\" system is developed for internal employees of Acme/Northwind Corporation. The assistant empowers employees to query internal policies and automates procedural request initiation for administrative workflows, including remote work, international office work, IT hardware procurement, expense reimbursement claims, and security review requests.",
    59: "1.2. In-scope System Capabilities",
    60: "The system is architected to address three primary functional groups:",
    61: "Policy Retrieval (Read/Retrieval): Accurately searches and extracts internal regulations with mandatory provenance attribution via document IDs (e.g., [DOC0101 v2.0]). The system reliably issues safe refusals (no_answer) whenever queries fall outside the corpus boundary.",
    62: "Reasoning and Information Transformation:",
    63: "Synthesizes multi-document information across separate policy sources (e.g., combining host office site protocols with remote access security policies).",
    64: "Recognizes and prioritizes the latest policy version (e.g., applying DOC0101 v2.0 over superseding DOC0005 v1.0) when version conflicts occur.",
    65: "Performs deterministic calculations: computing exact business days between two dates, or aggregating hardware equipment costs to determine approval thresholds based on company spending guidelines.",
    66: "Action Execution (Write & Verify): Generates formalized procedure requests (e.g., REQ-0007) committed to persistent state storage (requests.json), followed by a mandatory verification step that reads back the newly generated request ID to confirm transaction durability before responding to the user.",
    67: "1.3. Out-of-scope System Boundaries",
    68: "To ensure security and functional focus, the system explicitly excludes the following:",
    69: "Sending automated external emails or granting managerial approvals on behalf of authorized personnel.",
    70: "Answering out-of-corpus inquiries (such as compensation policies, stock option vesting schedules, dress code regulations).",
    71: "Modifying, overwriting, or deleting original company policy documents within the repository.",
    72: "II. SYSTEM ARCHITECTURE",
    73: "The system adopts a decoupled client-server architecture separating the decision-making Agent (Client) from tool execution (Server) via the Model Context Protocol (MCP).",
    75: "Figure 2.1: Overall architecture diagram of the Policy Agent system and MCP protocol boundary (stdio JSON-RPC).",
    76: "Data Flow Lifecycle:",
    77: "Host & Agent Loop: The user interacts via a terminal interface (Host 1 - scripts/demo.py or scripts/chat.py). Queries enter a custom hand-crafted Agent Loop. This loop enforces a strict step limit (MAX_STEPS = 8) to eliminate infinite loops and bound token expenditure.",
    78: "LLM Routing & ReAct: The LLM (Groq API — configured by default with openai/gpt-oss-20b and operated in production with qwen/qwen3.8-27b via the MODEL variable in .env) receives the system prompt and reasons through a ReAct cycle (Thought / Action / Action Input / Observation / Final Answer). Tool schemas are discovered dynamically via the list_tools() method from the MCP Server.",
    79: "MCP Boundary: The Agent Client dispatches execution requests over standard I/O (stdio JSON-RPC) to the MCP Server. To prevent protocol framing corruption, all server telemetry and logging are redirected to stderr and logs/server.log, ensuring stdout remains strictly pristine.",
    80: "Tool Execution: The MCP Server executes registered tools:",
    81: "Read Tools: Invokes the RAG module (Dense/Hybrid search, metadata filtering) to extract document chunks, or runs deterministic business day calculations.",
    82: "Write Tools: Persists state records into data/state/requests.json and reads back data to verify.",
    83: "Sample Query Execution Flow (Remote Work Procedure Request Scenario — Q08):",
    84: "• Step 1 (Policy Lookup): The user requests to calculate business days and create a REMOTE_WORK request for employee Alice from 2026-11-02 to 2026-11-06. The Agent reasons (Thought) and invokes search_policy(query=\"remote work policy guidelines\", top_k=3) -> retrieves DOC0001 Section 4.",
    85: "• Step 2 (Deterministic Calculation): The Agent calls calc_business_days(start_date=\"2026-11-02\", end_date=\"2026-11-06\") -> the MCP Server returns exactly 5 business days.",
    86: "• Step 3 (Side-Effect Action Execution): The Agent invokes create_request(request_type=\"REMOTE_WORK\", employee=\"Alice\", details='{\"reason\": \"family event\", \"location\": \"Home Office\"}', start_date=\"2026-11-02\", end_date=\"2026-11-06\") -> the server commits the record to data/state/requests.json and returns ticket ID REQ-3e5760ddfaff4ba18ee39467c88c7df9 with status submitted.",
    87: "• Step 4 (Mandatory Verification — Guard Verify): The is_forced_verify flag in the loop activates, mandating that the subsequent step execute get_request(request_id=\"REQ-3e5760ddfaff4ba18ee39467c88c7df9\") to corroborate all persisted fields on disk.",
    88: "• Step 5 (Synthesis & Final Answer): Following 100% validation match, the Agent outputs the Final Answer including confirmation code REQ-3e5760ddfaff4ba18ee39467c88c7df9 and attribution citation [DOC0001].",
    89: "III. RAG AND DATA DESIGN (Student A)",
    90: "3.1. Corpus Structure and Version Management",
    91: "The knowledge repository integrates the baseline policy corpus (DOC0001 - DOC0006) with custom-authored documents engineered for edge-case evaluation (DOC0101, DOC0102). In particular, DOC0101 (v2.0) intentionally introduces conflicting numerical parameters against DOC0005 (v1.0) to assess the LLM's capacity to resolve version discrepancies. Each document is bound to strict metadata: doc_id, version, date, owner, and category.",
    92: "3.2. Chunking Strategy",
    93: "Rather than applying fixed-character windowing which fractures semantic clauses, the system employs Recursive Chunking guided by markdown section headings (## Section...) and structural whitespace.",
    94: "Hyperparameters: chunk_size = 400 characters, with an overlap = 60 characters, inclusive of section header prefixes (## Heading) within length boundaries to preserve self-contained contextual provenance.",
    95: "Design Rationale: Heading-aligned partitioning guarantees that each text chunk contains a cohesive legal clause or procedure without separating numerical limits from governing rules. The overlap prevents boundary-spanning conditions from truncation. Document metadata is embedded directly into chunk text headers (e.g., [DOC0101 v2.0 2026-09-01]) providing the LLM with immediate provenance and temporal context for version comparisons.",
    96: "3.3. Retrieval Mechanism and Hybrid Search",
    97: "The pipeline supports dual retrieval configurations:",
    98: "Dense Search: Utilizes local multilingual sentence embeddings (paraphrase-multilingual) evaluated via Cosine Similarity.",
    99: "Hybrid Search: Integrates BM25 lexical keyword matching with Dense semantic vectors. To ensure mathematical parity during score fusion, both scoring spaces undergo Min-Max normalization prior to linear interpolation with weights: 0.3 BM25 + 0.7 Cosine.",
    100: "Metadata Filtering & Threshold Gating: Incorporates pre-scoring metadata filtering by category or latest-version tags. A MIN_SCORE threshold gate is enforced: if the top candidate chunk falls below this threshold, an empty result is returned, driving the Agent into a calibrated no_answer state to preempt hallucination.",
    101: "IV. AGENT AND LLM DESIGN (Student B)",
    102: "4.1. Core Agent Loop and ReAct Prompting.",
    103: "The Agent loop is implemented entirely from scratch without high-level framework abstraction. Lifecycle progression is bounded by the MAX_STEPS parameter. The ReAct cognitive framework compels the model to formulate thoughts (Thought:) prior to tool invocation (Action:). The system prompt strictly governs citation grounding, graceful refusals, and temporal version preference.",
    104: "4.2. Fault Tolerance & Safe Action Parser.",
    105: "Because unstructured LLM text generation is prone to syntax defects, the Parser (agent/parser.py) incorporates resilient parsing heuristics.",
    106: "If the LLM emits malformed JSON containing missing braces or single-quoted Python dict notation, the parser attempts safe repair via ast.literal_eval.",
    107: "Direct eval() calls are strictly prohibited to prevent arbitrary code injection vulnerabilities.",
    108: "If an error is unrecoverable, the runtime avoids crashing. Instead, it yields an observation: \"Error: could not parse action...\" prompting the LLM to self-correct its syntax in the following turn.",
    109: "4.3. Write + Verify Principle (Action Certification).",
    110: "To guarantee transaction durability, the loop enforces a Guard Verify gate. The Agent is blocked from concluding with a Final Answer after executing a mutating tool (create_request) until it explicitly invokes the read-back tool (get_request) using the returned identifier to corroborate disk persistence.",
    111: "4.4. Schema Declaration with Dataclasses & API Retry/Logging Mechanism (Weeks 1 & 2)",
    112: "All core data structures in src/policy_agent/models.py are explicitly defined using 9 typed @dataclass structures (eliminating raw dictionaries): DocumentMetadata, Document, DocumentChunk, ToolSpec, ParsedAction, StepTrace, Usage, RunTrace, and ProcedureRequest. The LLM dispatcher call_llm() in src/policy_agent/llm/client.py configures a 30.0s timeout and up to 6 retry attempts utilizing Exponential Backoff combined with retry-after header parsing upon encountering connection errors (APIConnectionError) or rate limits (429 RateLimitError, 5xx), while recording comprehensive HTTP error logs into logs/http_errors.jsonl. Final Answer responses are rendered with real-time character-by-character streaming (stream_print) adopted from Week 2 practicals.",
    113: "V. MCP SERVER PROTOCOL (Student C)",
    114: "Tool Design Philosophy and Architectural Contract.",
    115: "The system integrates an MCP Server built upon SDK v2. Decoupling via MCP abstracts filesystem structures and internal RAG/DB logic away from the LLM context, enhancing system security.",
    116: "Dynamic Discovery: The client queries tool availability dynamically via list_tools() rather than relying on hardcoded interfaces.",
    117: "Explicit Contract: Type annotations in models.py define the tool schemas. Tools include: search_policy, get_document, calc_business_days, create_request, and get_request. Output lengths and top_k bounds are strictly clamped to avoid context window overflow.",
    118: "Fault-Tolerant Exception Handling: Server tools never propagate unhandled exceptions across the JSON-RPC wire. All failures are intercepted and returned as structured strings: \"Error: [Reason]\".",
    119: "Table 5.1: Registered MCP Tools and Interface Contract on the MCP Server:",
    121: "Interprocess Interoperability Verification (Second Host): In addition to the primary Agent, the project features an independent script scripts/second_host.py (executable via make host2) acting as a secondary MCP Host that connects to the server over stdio, dynamically discovers 5 tools, calls calc_business_days, creates a request via create_request, and validates durability with get_request with 100% success.",
    122: "VI. SYSTEM EVALUATION (Student C)",
    123: "The system undergoes automated end-to-end evaluation via make eval (uv run python -m policy_agent.eval.run_eval --mode both), directly benchmarking Dense Search against Hybrid Search (0.3 BM25 + 0.7 Cosine) across all 14 benchmark scenarios in tests/testset.jsonl.",
    124: "6.1. Test Suite Configuration (Testset)",
    125: "The test dataset encompasses 14 scenarios spanning representative challenges: Direct queries, Multi-document Synthesis, Version_conflict resolution, Arithmetic Calculation, Action execution with Write+Verify, Insufficient data refusals, and out-of-scope No_answer inquiries.",
    126: "6.2. Evaluation Metrics and Results",
    127: "Based on experimental execution logs in logs/run_dense_20261018_054345.jsonl, logs/run_hybrid_20261018_054345.jsonl, and results/eval_latest.csv:",
    128: "• Overall Pass Rate & Faithfulness: Dense Search passes 12/14 questions (85.7%) with an average Faithfulness score of 97.68% (0.9768); Hybrid Search passes 13/14 questions (92.9%) with an average Faithfulness of 96.67% (0.9667) and an average Citation Hit rate of 82.14% (0.8214).",
    129: "• Refusal Accuracy: Achieves 100.0% in both Dense and Hybrid modes (correctly refusing all 5/5 no_answer and insufficient queries; false refusal rate across 9 valid queries is 0.0%).",
    130: "• Action Success (Write + Verify Pipeline): Dense Search achieves 50.0% (1/2 questions), whereas Hybrid Search achieves 100.0% (both Q08 and Q09 successfully complete the create_request -> get_request verification cycle with persistence in data/state/requests.json).",
    131: "• Token Consumption & LLM Invocations (Groq): Dense mode expends 70,865 total tokens (average 5,062 tokens/query, 4.5 calls/query); Hybrid mode expends 72,599 total tokens (average 5,186 tokens/query, 4.7 calls/query).",
    132: "Table 6.1: Comparative performance summary between Dense Search and Hybrid Search (BM25 + Dense):",
    135: "Figure 6.1: Performance and token expenditure benchmark comparison between Dense Search and Hybrid Search.",
    136: "Table 6.2: Granular query-by-query evaluation results and token metrics (Q01 – Q14):",
    138: "6.3. Failure Case Analysis",
    139: "• Representative Failure Case (Dense vs. Hybrid disparity on Action query Q09 and Direct query Q01): On Q09: \"I am Bob, needing to purchase a Dell UltraSharp 27-inch monitor for an AI project. Please create a HARDWARE_PURCHASE order for me.\"",
    140: "• Root Cause Analysis: (1) In Q09 under Dense Search (pure semantic cosine similarity with min_score = 0.35), the Agent query retrieved DOC0003 (governing the $1,000 threshold) but omitted DOC0006 (Equipment Catalog containing \"Dell UltraSharp 27-inch monitor: $480\"). Lacking price knowledge, the Agent conservatively halted to prompt Bob for unit pricing rather than triggering create_request (reducing Dense Action Success to 50%). Conversely, Hybrid Search (0.3 BM25 + 0.7 Cosine) leveraged lexical BM25 matching on the proper noun \"Dell UltraSharp 27\" in DOC0006, equipping the Agent with required budget figures to submit and verify the order (Action Success = 100%). (2) In Q01 (inquiring about maximum meal reimbursement of $50/day), the figure \"$50 per day\" appears simultaneously across DOC0001, DOC0003, and DOC0006. The retriever ranked DOC0006 (score=0.563) and DOC0003 above DOC0001; although the Agent correctly stated \"$50 per day\" citing [DOC0006] and [DOC0003], the rigid gold standard in testset.jsonl only accepted expected_doc_ids=[\"DOC0001\"], resulting in Citation Hit = 0.0.",
    141: "• Mitigations: (1) Standardize on RETRIEVAL_MODE=hybrid as the default configuration for queries involving proper nouns, model numbers, and technical catalog terms; (2) In the evaluation benchmark, allow equivalent citation sets (any-of matching) when rules are redundantly codified across interconnected policies.",
    142: "VII. SYSTEM LIMITATIONS",
    143: "1. Tabular Data Chunking and Cross-lingual Retrieval Limitations: Heading-based recursive partitioning (##) with chunk_size=400 performs robustly on prose policy sections, but degrades on multi-column tables or English technical jargon queried in colloquial Vietnamese, where Dense cosine similarity can drop near the min_score threshold (as demonstrated in Q09).",
    144: "2. Flat-file State Store Concurrency Limits: Persisting records in flat JSON files (data/state/requests.json) via RequestStore suffices for single-server MCP deployments, but lacks ACID transaction isolation and concurrency locking mechanisms (such as those in SQLite or PostgreSQL) required under concurrent multi-process architectures.",
    145: "3. Rate Limits (TPM/TPD) and Round-Trip Latency Constraints: Each multi-step ReAct trajectory exchanging 5 tool schemas consumes 3,000 – 8,000 tokens. On free-tier API quotas (e.g., 6,000 TPM on Groq), continuous benchmarking triggers backoff delays that extend response latencies. Future milestones include compacting JSON schemas in prompts, introducing semantic caching, and migrating the persistence layer to SQLite.",
    146: "VIII. TEAM CONTRIBUTION & GIT COMMITS",
    147: "The project was partitioned equitably among 3 members along architectural boundaries (RAG & Data / Agent & LLM / MCP Server & Evaluation). All development history is documented transparently in Git commits:",
    149: "IX. APPENDIX",
    150: "9.1. Complete Agent System Prompt (prompts/agent_system.txt):",
    151: """You are an internal Policy & Procedure Assistant (Policy & Procedure Agent). You are only permitted to use the tools in the list below; never invent tool names.

In each response turn, you MUST output in exactly one of the two formats:

Format 1 (When calling a tool):
Thought: brief reasoning on what to look up or execute next
Action: tool_name
Action Input: {"param": "value"}

Format 2 (When sufficient results are collected and verification is complete):
Thought: brief synthesis of collected results
Final Answer: comprehensive response for the user

Mandatory Rules:
1. Never output both Action and Final Answer in the same turn. Action Input must be a valid, non-empty JSON object.
2. Always call search_policy (or get_document) to retrieve documents before answering about policies, spending limits, or approval conditions.
3. Grounding Citations: Every statement, figure, and policy clause in Final Answer must include document IDs in square brackets, e.g., [DOC0001], [DOC0101].
4. Version Discrepancies: When multiple documents govern the same topic (e.g., older DOC0005 v1.0 and newer DOC0101 v2.0 superseding DOC0005), strictly prioritize the document with the latest version/date.
5. Calibrated Refusal (no_answer):
   - If search returns no relevant excerpts or queries fall outside policy scope (e.g., compensation, stock option vesting, maternity leave, dress code), decline to answer stating that the current corpus contains no information. Do not speculate and do not attach [DOCxxxx] when refusing.
   - If calculation queries lack required input parameters (e.g., asking if expenses exceed limits without providing amounts or receipts), decline conclusion and state what data is missing.
6. Action & Verification Protocol (Write + Verify):
   - Only call create_request when the user explicitly requests filing and all mandatory fields are provided.
   - In create_request, details must be a JSON string with mandatory fields by request type:
     + REMOTE_WORK: {"reason": "...", "location": "..."} (requires start_date, end_date in YYYY-MM-DD)
     + INTL_WORK: {"reason": "...", "country": "...", "office": "..."} (requires start_date, end_date in YYYY-MM-DD)
     + HARDWARE_PURCHASE: {"reason": "...", "item": "..."}
     + EXPENSE_CLAIM: {"reason": "...", "amount": 100, "currency": "USD", "receipt": "..."}
     + SECURITY_REVIEW: {"reason": "...", "system": "...", "scope": "..."}
   - Immediately upon successful create_request, the very next step MUST call get_request with the newly generated request_id to verify stored data before emitting Final Answer.
   - If unverified, explicitly notify that the request remains unverified.

Available Tools (dynamically discovered from MCP server):
{{TOOLS}}""",
    152: "9.2. Real JSONL Trace of a Write + Verify Execution (Extracted from logs/run_20261017T215430_940079Z_1608b859.jsonl):",
    154: "9.3. AI Usage Declaration Summary Table (Synchronized with ai-usage.md):",
    155: "Pursuant to Requirement 7 (\"Mandatory ai-usage.md submission: which tools, for which components, primary prompts, and code generated by AI\"), the table below summarizes AI integration milestones across all 3 team members designated by identifiers ([A1]–[A4], [B1]–[B6], [C1]–[C5]). The comprehensive audit detailing verbatim prompt texts and exact file/function/line boundaries is documented in ai-usage.md accompanying the source repository for the 20-minute oral defense.",
}

TABLE_TRANSLATIONS = {
    # Table 0: Member Table on cover page
    0: {
        (0, 0): "No.",
        (0, 1): "Full Name",
        (0, 2): "Student ID",
        (0, 3): "Role / Completion",
        (1, 0): "1", (1, 1): "Huynh Nhat Bao", (1, 2): "24110079", (1, 3): "Student A (RAG & Data)",
        (2, 0): "2", (2, 1): "Nguyen Quoc Bao Khang", (2, 2): "24110099", (2, 3): "Student C (MCP & Eval)",
        (3, 0): "3", (3, 1): "Ngo Quang Truong", (3, 2): "24110142", (3, 3): "Student B (Leader - Agent & LLM)",
    },
    # Table 1: MCP Server Tools Contract
    1: {
        (0, 0): "Tool Name",
        (0, 1): "Type",
        (0, 2): "Input Schema Parameters",
        (0, 3): "Bounds & Output Contract",
        (1, 0): "search_policy",
        (1, 1): "Read (RAG)",
        (1, 2): "query: str, top_k: int = 3 (1..5), category: str | None = None",
        (1, 3): "Returns up to top_k policy excerpts exceeding min_score with provenance [DOCxxxx vX YYYY-MM-DD].",
        (2, 0): "get_document",
        (2, 1): "Read (Doc)",
        (2, 2): "doc_id: str (non-blank)",
        (2, 3): "Returns JSON containing metadata and document full text, capped at 4,000 characters.",
        (3, 0): "calc_business_days",
        (3, 1): "Read (Compute)",
        (3, 2): "start_date: str (YYYY-MM-DD), end_date: str (YYYY-MM-DD)",
        (3, 3): "Deterministically calculates business working days (Monday–Friday) within [start_date, end_date].",
        (4, 0): "create_request",
        (4, 1): "Write (Side effect)",
        (4, 2): "request_type: str, employee: str, details: str (JSON), start_date: str, end_date: str",
        (4, 3): "Validates schema per request type, generates REQ-<uuid>, commits to data/state/requests.json.",
        (5, 0): "get_request",
        (5, 1): "Read (Verify)",
        (5, 2): "request_id: str (REQ-...)",
        (5, 3): "Reads record back from requests.json by request_id to verify submitted status.",
    },
    # Table 2: Benchmark Summary
    2: {
        (0, 0): "Evaluation Metric",
        (0, 1): "Dense Search (Cosine)",
        (0, 2): "Hybrid Search (0.3 BM25 + 0.7 Dense)",
        (0, 3): "Analysis / Variance",
        (1, 0): "Pass Rate",
        (1, 1): "12 / 14 (85.7%)",
        (1, 2): "13 / 14 (92.9%)",
        (1, 3): "+7.2% favoring Hybrid (solves Q09)",
        (2, 0): "Faithfulness",
        (2, 1): "97.68% (0.9768)",
        (2, 2): "96.67% (0.9667)",
        (2, 3): "Both configurations exceed 96% context grounding",
        (3, 0): "Citation Hit",
        (3, 1): "82.14% (0.8214)",
        (3, 2): "82.14% (0.8214)",
        (3, 3): "Hybrid achieves 1.00 on Q04 via keyword matching",
        (4, 0): "Refusal Accuracy",
        (4, 1): "100.0% (14/14)",
        (4, 2): "100.0% (14/14)",
        (4, 3): "Zero hallucination on 4 no_answer and 1 insufficient",
        (5, 0): "Action Success",
        (5, 1): "50.0% (1/2)",
        (5, 2): "100.0% (2/2)",
        (5, 3): "+50.0%: Hybrid retrieves DOC0006 catalog pricing for Q09",
        (6, 0): "Total Tokens / Avg per Query",
        (6, 1): "70,865 (5,062 tok/query)",
        (6, 2): "72,599 (5,186 tok/query)",
        (6, 3): "Comparable token expenditure (+2.4%)",
    },
    # Table 3: Detailed Q01-Q14 test results
    3: {
        (0, 0): "ID",
        (0, 1): "Category",
        (0, 2): "Dense Pass",
        (0, 3): "Hybrid Pass",
        (0, 4): "Faith (D/H)",
        (0, 5): "Cite (D/H)",
        (0, 6): "Tokens (D/H)",
        (0, 7): "Calls (D/H)",
    },
    # Table 4: Team Contributions
    4: {
        (0, 0): "Member & Student ID",
        (0, 1): "Assigned Subsystem",
        (0, 2): "Primary Source Files",
        (0, 3): "Representative Commit Hashes & Descriptions",
        (1, 0): "Huynh Nhat Bao (ID: 24110079) [Student A]",
        (1, 1): "RAG Pipeline, Corpus & Indexing",
        (1, 2): "src/policy_agent/rag/loader.py\nsrc/policy_agent/rag/chunking.py\nsrc/policy_agent/rag/embeddings.py\nsrc/policy_agent/rag/vector_store.py\nsrc/policy_agent/rag/hybrid_search.py\nsrc/policy_agent/rag/retriever.py\nsrc/policy_agent/rag/build_index.py\ndata/corpus/DOC0101, DOC0102",
        (1, 3): "• 285d580: rag: define metadata for DOC0101 and DOC0102\n• 4f1f822: chore: add shared data schemas for RAG\n• 999c4ce: rag: add validated corpus loader and heading-aware chunking\n• d264462: rag: add cached multilingual embedding wrapper\n• 6807794: rag: add dense vector store with JSON persistence\n• 8aac74c: rag: add reproducible corpus index build\n• 266ccd8: rag: adapt W4 hybrid imports and logging for MCP",
        (2, 0): "Ngo Quang Truong (ID: 24110142) [Student B - Team Leader]",
        (2, 1): "ReAct Agent Loop, Safe Parser, LLM Client & CLI Scripts",
        (2, 2): "src/policy_agent/agent/loop.py\nsrc/policy_agent/agent/parser.py\nsrc/policy_agent/agent/trace.py\nsrc/policy_agent/llm/client.py\nsrc/policy_agent/config.py\nsrc/policy_agent/models.py\nscripts/demo.py, scripts/chat.py\nprompts/agent_system.txt",
        (2, 3): "• 23c9505: first demo (agent loop & parser)\n• be58eb4: Merge branch feat/rag into main\n• 19454d3: Merge branch Trường into main\n• a5c8455: agent: refactor loop, parser, and llm client with clear structure\n• eb981ca: refactor: simplify agent, mcp, and tests to match W1-W7 lecture notes\n• 7f8323c: feat: add streaming from week2 to chat and demo",
        (3, 0): "Nguyen Quoc Bao Khang (ID: 24110099) [Student C]",
        (3, 1): "MCP Server, Request Store, Second Host & Evaluation Pipeline",
        (3, 2): "src/policy_agent/mcp_server/server.py\nsrc/policy_agent/mcp_server/request_store.py\nsrc/policy_agent/mcp_server/validation.py\nsrc/policy_agent/mcp_client/client.py\nsrc/policy_agent/eval/metrics.py\nsrc/policy_agent/eval/report.py\nsrc/policy_agent/eval/run_eval.py\nscripts/second_host.py, probe_server.py\ntests/testset.jsonl",
        (3, 3): "• 726d0d0: chore: project skeleton, plan and class corpus\n• 8c02662: docs: fix GitHub remote URL in setup guide\n• 8425dec / 1172249: MCP server stdio, RequestStore & probe_server\n• 1ff5fc5: Merge branch Khang into main (eval metrics, report, run_eval, second_host, testset.jsonl)",
    },
    # Table 5: AI Usage Table
    5: {
        (0, 0): "Milestone & Date",
        (0, 1): "Member",
        (0, 2): "AI Tool",
        (0, 3): "Applied Module & File",
        (0, 4): "Primary Prompt (Summary)",
        (0, 5): "Human Review, Verification & Custom Code",
        (1, 0): "[C1] 2026-10-10",
        (1, 1): "Nguyen Quoc Bao Khang (C)",
        (1, 2): "Claude 6.0 Opus",
        (1, 3): "Project skeleton, Makefile, tasks.ps1, pyproject.toml",
        (1, 4): "Read AIPR project briefs, architect standard directory tree, configure uv, cross-platform Makefile & tasks.ps1.",
        (1, 5): "Custom-designed setup/demo/chat/eval/probe/host2 targets; verified make setup passes.",
        (2, 0): "[A1] 2026-10-13",
        (2, 1): "Huynh Nhat Bao (A)",
        (2, 2): "ChatGPT",
        (2, 3): "Corpus loader & Chunking (loader.py, chunking.py)",
        (2, 4): "Write load_manifest, load_corpus and heading-aware chunking (##) with max 400 chars, overlap 60.",
        (2, 5): "Hand-wrote 5-line chunking design rationale docstring; pytest test_loader, test_chunking 100% pass.",
        (3, 0): "[C2] 2026-10-14",
        (3, 1): "Nguyen Quoc Bao Khang (C)",
        (3, 2): "Claude 6.0 Opus",
        (3, 3): "Request Store & Validation (request_store.py, validation.py)",
        (3, 4): "Write RequestStore with atomic write (.tmp -> rename) and validation.py verifying dates & 5 request types.",
        (3, 5): "Designed submitted status state lifecycle; pytest test_request_store verified crash-safety.",
        (4, 0): "[B1, B2] 2026-10-14",
        (4, 1): "Ngo Quang Truong (B)",
        (4, 2): "Gemini 3.8 Flash",
        (4, 3): "Dataclass Schema (models.py) & Fallback Parser (parser.py)",
        (4, 4): "Define 9 standard Week 1 @dataclasses; suggest ast.literal_eval for safe single-quoted JSON recovery.",
        (4, 5): "Authored ReAct regex parser; pytest test_parser (6 malformed edge cases) and test_models 100% pass.",
        (5, 0): "[A2] 2026-10-16",
        (5, 1): "Huynh Nhat Bao (A)",
        (5, 2): "ChatGPT",
        (5, 3): "Vector Store, Embeddings & Build Index (vector_store.py, embeddings.py)",
        (5, 4): "Write VectorStore JSON persistence, sentence-transformers embedding wrapper (384-d), numpy cosine similarity.",
        (5, 5): "Optimized embedding caching into JSON index; pytest test_vector_store, test_embeddings pass.",
        (6, 0): "[A3, A4] 2026-10-17",
        (6, 1): "Huynh Nhat Bao (A)",
        (6, 2): "ChatGPT",
        (6, 3): "RAG Retriever, Metadata Filter & Hybrid Search (retriever.py, hybrid_search.py)",
        (6, 4): "Write dual-mode retriever (dense/hybrid), filter_chunks_by_metadata filtering supersedes and category.",
        (6, 5): "Integrated legacy DOC0005 filtering when DOC0101 is present (+1 pt); pytest test_retriever verified min_score.",
        (7, 0): "[C3–C5] 2026-10-17",
        (7, 1): "Nguyen Quoc Bao Khang (C)",
        (7, 2): "Claude 6.0 Opus",
        (7, 3): "Second Host, Eval Pipeline & Metrics (second_host.py, report.py, metrics.py)",
        (7, 4): "Write second_host.py testing stdio interop; report.py exporting CSV & plotting charts; metrics.py evaluating 5 metrics.",
        (7, 5): "Completed second host (+1 pt); make eval generates eval_latest.csv & PNG comparison chart (+1 pt).",
        (8, 0): "[B3–B6] 2026-10-18",
        (8, 1): "Ngo Quang Truong (B)",
        (8, 2): "Gemini 3.8 Flash",
        (8, 3): "HTTP Retry, Streaming, CLI & Loop Guard (client.py, trace.py, loop.py, chat.py)",
        (8, 4): "Catch HTTP 429 logging http_errors.jsonl, compute retry-after; typing streaming; ReAct loop with is_forced_verify.",
        (8, 5): "Authored full ReAct loop by hand (W6); completed scripts/demo.py, scripts/chat.py; 112/112 tests pass.",
    },
}


def update_paragraph_text(p, new_text):
    """Cap nhat text cua doan van nhung giu nguyen runs co hinh anh."""
    # Kiem tra co hinh anh hay drawing khong
    if "w:drawing" in p._p.xml or "w:pict" in p._p.xml:
        # Giu nguyen run anh, chi cap nhat run chua text
        for r in p.runs:
            if "w:drawing" not in r._r.xml and "w:pict" not in r._r.xml:
                r.text = new_text
                return
        return

    # Khong co anh: cap nhat run dau tien va xoa text o cac run tiep theo
    if p.runs:
        p.runs[0].text = new_text
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(new_text)


def translate_document(input_path: Path, output_path: Path):
    print(f"Loading {input_path}...")
    doc = docx.Document(str(input_path))

    # 1. Dich cac Paragraphs
    print(f"Translating {len(doc.paragraphs)} paragraphs...")
    for idx, p in enumerate(doc.paragraphs):
        if idx in PARAGRAPH_TRANSLATIONS:
            new_text = PARAGRAPH_TRANSLATIONS[idx]
            update_paragraph_text(p, new_text)

    # 2. Dich cac Tables
    print(f"Translating {len(doc.tables)} tables...")
    for t_idx, table in enumerate(doc.tables):
        if t_idx in TABLE_TRANSLATIONS:
            cell_map = TABLE_TRANSLATIONS[t_idx]
            for (r_idx, c_idx), new_text in cell_map.items():
                if r_idx < len(table.rows) and c_idx < len(table.rows[r_idx].cells):
                    cell = table.cell(r_idx, c_idx)
                    if cell.paragraphs:
                        update_paragraph_text(cell.paragraphs[0], new_text)
                        for extra_p in cell.paragraphs[1:]:
                            update_paragraph_text(extra_p, "")
                    else:
                        cell.text = new_text

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"Saved translated document to: {output_path}")


def main():
    source_path = Path(r"D:\Year3\AI Programing with python\temp\AI_FinalProject - Copy.docx")
    if not source_path.exists():
        # Fallback neu file o thu muc project
        source_path = Path(r"D:\Year3\AI Programing with python\Project_AIPR\AI_FinalProject - Copy.docx")

    targets = [
        Path(r"D:\Year3\AI Programing with python\temp\AI_FinalProject - Copy.docx"),
        Path(r"D:\Year3\AI Programing with python\Project_AIPR\AI_FinalProject - Copy.docx"),
        Path(r"D:\Year3\AI Programing with python\Project_AIPR\report\report.docx"),
    ]

    for target in targets:
        translate_document(source_path, target)
        print(f"Successfully updated: {target} (Size: {target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
