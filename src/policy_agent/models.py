"""All schemas as @dataclass with type hints (requirement 2.3 — no raw dicts).

Owner: SV B (Document/DocumentChunk agreed with SV A).  Reuse: W1 dataclass, W3 Document model.
TODO:
- [ ] Document, DocumentChunk (doc_id, title, version, date, owner, category)
- [ ] ToolSpec (name, description, input_schema) built from MCP list_tools()
- [ ] ParsedAction, StepTrace, RunTrace, Usage(calls, prompt_tokens, completion_tokens, max_prompt)
- [ ] ProcedureRequest (request_id, request_type, employee, details, start_date, end_date, status, created_at)
"""
