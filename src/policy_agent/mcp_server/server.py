"""MCP server (stdio). Tools: search_policy, get_document, calc_business_days, create_request (WRITE), get_request (VERIFY).

Owner: SV C.  Reuse: W7 create_mcp.py (logging to stderr), rag_server.py (tool design).
Rules: no print() (stdout is the JSON-RPC channel); every tool returns "Error: ..." instead of raising;
bounded output; load the index once at module level.
"""
