"""Hand-written agent loop (no framework).

Owner: SV B.  Reuse: W6 react_agent(), W8 Agent.run().
TODO:
- [ ] tools discovered via mcp_client (no hard-coded registry)
- [ ] MAX_STEPS guard
- [ ] tool error -> observation "Error: ..."
- [ ] verify guard: after a successful write, require get_request(<same id>) before Final Answer
- [ ] write one RunTrace per question via agent/trace.py
"""
