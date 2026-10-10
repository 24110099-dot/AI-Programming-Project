"""call_llm(): Groq chat completion with retry/backoff, timeout, HTTP error logging, USAGE counters.

Owner: SV B.  Reuse: W2 errh.py (retry taxonomy), W8 common.py (USAGE dict).
TODO:
- [ ] retry RateLimit / connection / 5xx with 2**attempt + jitter; no retry on auth / 4xx
- [ ] timeout on every request
- [ ] log every HTTP error to logs/http_errors.jsonl
- [ ] update Usage per call (calls, prompt_tokens, completion_tokens, max_prompt)
"""
