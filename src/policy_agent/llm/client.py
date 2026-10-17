import json
import math
import time
from datetime import datetime, timezone
from groq import APIConnectionError, APIStatusError
from policy_agent.models import Usage


def call_llm(messages, settings, usage: Usage, *, adapter=None, timeout=30.0, max_attempts=3, sleep=time.sleep):
    # Kiểm tra tính hợp lệ của tham số cấu hình
    if type(max_attempts) is not int or max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")

    # Nếu không truyền adapter giả lập (trong test), khởi tạo client Groq thật
    if adapter is None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required for a real call")
        from groq import Groq
        with Groq(api_key=settings.groq_api_key, timeout=timeout, max_retries=0) as client:
            return call_llm(
                messages,
                settings,
                usage,
                adapter=client.chat.completions.create,
                timeout=timeout,
                max_attempts=max_attempts,
                sleep=sleep,
            )

    # Vòng lặp retry: thử tối đa max_attempts lần nếu gặp lỗi mạng hoặc rate-limit
    for attempt in range(1, max_attempts + 1):
        usage.calls += 1
        try:
            result = adapter(
                messages=messages,
                model=settings.model,
                temperature=0,
                timeout=timeout,
            )
        except (APIConnectionError, APIStatusError) as exc:
            status_code = getattr(exc, "status_code", None)
            
            # Chỉ retry với lỗi kết nối mạng, HTTP 429 (rate limit) hoặc HTTP 5xx (server error)
            can_retry = isinstance(exc, APIConnectionError) or status_code == 429 or (status_code is not None and status_code >= 500)
            should_retry = can_retry and (attempt < max_attempts)

            # Ghi nhật ký lỗi HTTP để theo dõi
            settings.logs_dir.mkdir(parents=True, exist_ok=True)
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "attempt": attempt,
                "error_type": type(exc).__name__,
                "status_code": status_code,
                "retry": should_retry,
            }
            log_file = settings.logs_dir / "http_errors.jsonl"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

            if not should_retry:
                raise

            # Thời gian chờ tăng dần theo cấp số nhân: 0.5s, 1.0s...
            delay = 0.5 * (2 ** (attempt - 1))
            sleep(delay)
            continue

        # Cập nhật số lượng token đã tiêu thụ
        if result.usage is not None:
            usage.prompt_tokens += result.usage.prompt_tokens
            usage.completion_tokens += result.usage.completion_tokens
            usage.max_prompt = max(usage.max_prompt, result.usage.prompt_tokens)

        # Lấy nội dung câu trả lời của mô hình
        content = result.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Empty completion")

        return content
