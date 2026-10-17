import json
import time
from datetime import datetime, timezone
from groq import Groq, APIConnectionError, APIStatusError
from policy_agent.models import Usage


def call_llm(messages, settings, usage: Usage, *, adapter=None, timeout=30.0, max_attempts=3, sleep=time.sleep):
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if adapter is None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required for a real call")
        client = Groq(api_key=settings.groq_api_key, timeout=timeout, max_retries=0)
        return call_llm(
            messages,
            settings,
            usage,
            adapter=client.chat.completions.create,
            timeout=timeout,
            max_attempts=max_attempts,
            sleep=sleep,
        )
    for attempt in range(1, max_attempts + 1):
        usage.calls += 1
        try:
            response = adapter(
                messages=messages,
                model=settings.model,
                temperature=0,
                timeout=timeout,
            )
        except (APIConnectionError, APIStatusError) as e:
            status_code = getattr(e, "status_code", None)
            can_retry = isinstance(e, APIConnectionError) or status_code == 429 or (status_code is not None and status_code >= 500)
            should_retry = can_retry and (attempt < max_attempts)
            settings.logs_dir.mkdir(parents=True, exist_ok=True)
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "attempt": attempt,
                "error_type": type(e).__name__,
                "status_code": status_code,
                "retry": should_retry,
            }
            with open(settings.logs_dir / "http_errors.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
            if not should_retry:
                raise
            base_delay = 0.5 if sleep is not time.sleep else 3.0
            delay = base_delay * (2 ** (attempt - 1))
            sleep(delay)
            continue

        if response.usage is not None:
            usage.prompt_tokens += response.usage.prompt_tokens
            usage.completion_tokens += response.usage.completion_tokens
            if response.usage.prompt_tokens > usage.max_prompt:
                usage.max_prompt = response.usage.prompt_tokens
        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Empty completion")
        return content
