"""Safe ReAct parsing: 'Final Answer:' or 'Action: tool_name {json args}'.

Owner: SV B.  Reuse: W6 ex2_1_react.py parse_reply().
TODO:
- [ ] never raise: malformed JSON / missing brackets -> ParsedAction(kind="error", message=...)
- [ ] never eval() anything
- [ ] unit tests in tests/test_parser.py
"""
