"""Synchronous Groq completion boundary with explicit attempt accounting."""
import json
import math
import time
from datetime import datetime, timezone
from groq import APIConnectionError, APIStatusError
from policy_agent.models import Usage


def call_llm(messages, settings, usage: Usage, *, adapter=None, timeout=30.0, max_attempts=3, sleep=time.sleep):
    """Retry transport, 429 and 5xx errors; never log request/response bodies."""
    if type(max_attempts) is not int or max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    if adapter is None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required for a real call")
        from groq import Groq
        with Groq(api_key=settings.groq_api_key, timeout=timeout, max_retries=0) as client:
            return call_llm(messages, settings, usage, adapter=client.chat.completions.create, timeout=timeout, max_attempts=max_attempts, sleep=sleep)
    for attempt in range(1, max_attempts + 1):
        usage.calls += 1
        try:
            result = adapter(messages=messages, model=settings.model, temperature=0, timeout=timeout)
        except (APIConnectionError, APIStatusError) as exc:
            status = getattr(exc, "status_code", None)
            retry = isinstance(exc, APIConnectionError) or status == 429 or (status is not None and status >= 500)
            settings.logs_dir.mkdir(parents=True, exist_ok=True)
            event = {"timestamp": datetime.now(timezone.utc).isoformat(), "attempt": attempt, "error_type": type(exc).__name__, "status_code": status, "retry": retry and attempt < max_attempts}
            with (settings.logs_dir / "http_errors.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(event) + "\n")
            if not retry or attempt == max_attempts:
                raise
            sleep(0.5 * 2 ** (attempt - 1))
            continue
        if result.usage is not None:
            usage.prompt_tokens += result.usage.prompt_tokens
            usage.completion_tokens += result.usage.completion_tokens
            usage.max_prompt = max(usage.max_prompt, result.usage.prompt_tokens)
        text = result.choices[0].message.content
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Empty completion")
        return text
