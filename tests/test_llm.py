import json
import pytest
import httpx
from groq import APIStatusError, APITimeoutError
from types import SimpleNamespace as NS
from policy_agent.config import Settings
from policy_agent.models import Usage
from policy_agent.llm.client import call_llm


def response(text="ok", prompt=4, completion=2):
    return NS(choices=[NS(message=NS(content=text))], usage=NS(prompt_tokens=prompt, completion_tokens=completion))


def test_success_counts_usage(tmp_path):
    usage = Usage()
    seen = []
    def adapter(**kwargs):
        seen.append(kwargs)
        return response()
    assert call_llm([], Settings(tmp_path), usage, adapter=adapter) == "ok"
    assert usage == Usage(calls=1, prompt_tokens=4, completion_tokens=2, max_prompt=4)
    assert seen[0]["timeout"] == 30.0
    assert seen[0]["model"] == "openai/gpt-oss-20b"


def http_error(status):
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": "Bearer SECRET"})
    return APIStatusError("SECRET body", response=httpx.Response(status, request=request), body={"key": "SECRET"})


@pytest.mark.parametrize("failure", [http_error(429), http_error(503), APITimeoutError(request=httpx.Request("POST", "https://example.test"))])
def test_retry_redacts_logs_and_counts_failed_attempts(tmp_path, failure):
    outcomes = iter([failure, response()])
    def adapter(**kwargs):
        item = next(outcomes)
        if isinstance(item, Exception):
            raise item
        return item
    usage, sleeps = Usage(), []
    assert call_llm([], Settings(tmp_path), usage, adapter=adapter, sleep=sleeps.append) == "ok"
    assert usage.calls == 2
    assert usage.prompt_tokens == 4
    assert sleeps == [0.5]
    raw = (tmp_path / "logs/http_errors.jsonl").read_text()
    assert "SECRET" not in raw and "Authorization" not in raw
    assert json.loads(raw)["attempt"] == 1


@pytest.mark.parametrize("status,expected", [(401, 1), (500, 3)])
def test_retry_stops(tmp_path, status, expected):
    def adapter(**kwargs):
        raise http_error(status)
    usage = Usage()
    with pytest.raises(APIStatusError):
        call_llm([], Settings(tmp_path), usage, adapter=adapter, sleep=lambda _: None)
    assert usage.calls == expected
    assert usage.prompt_tokens == 0


def test_no_key_fails_before_network(tmp_path):
    usage = Usage()
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        call_llm([], Settings(tmp_path), usage)
    assert usage.calls == 0


def test_real_sdk_interface_with_mock_http_transport(tmp_path, monkeypatch):
    import groq
    original = groq.Groq
    calls = []
    def handle(request):
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            return httpx.Response(429, json={"error": {"message": "synthetic limit"}})
        return httpx.Response(200, json={
            "id": "mock", "object": "chat.completion", "created": 1,
            "model": "openai/gpt-oss-20b",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
        })
    options = []
    def factory(**kwargs):
        options.append(kwargs)
        return original(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(handle)))
    monkeypatch.setattr(groq, "Groq", factory)
    usage = Usage()
    settings = Settings(tmp_path, groq_api_key="synthetic-not-a-real-key")
    assert call_llm([{"role": "user", "content": "test"}], settings, usage, sleep=lambda _: None) == "ok"
    assert options[0]["max_retries"] == 0
    assert options[0]["timeout"] == 30.0
    assert len(calls) == usage.calls == 2
    assert usage.prompt_tokens == 4


