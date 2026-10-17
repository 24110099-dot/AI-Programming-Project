import httpx
import pytest
from types import SimpleNamespace as NS
from groq import APIStatusError
from policy_agent.config import Settings
from policy_agent.models import Usage
from policy_agent.llm.client import call_llm


def fake_resp(text="ok", prompt=10, completion=5):
    return NS(choices=[NS(message=NS(content=text))], usage=NS(prompt_tokens=prompt, completion_tokens=completion))


def test_call_llm_tracks_usage(tmp_path):
    usage = Usage()
    res = call_llm([], Settings(tmp_path), usage, adapter=lambda **kw: fake_resp("hello", 12, 6))
    assert res == "hello"
    assert usage.calls == 1
    assert usage.prompt_tokens == 12
    assert usage.completion_tokens == 6


def test_call_llm_retries_on_429(tmp_path):
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    err_429 = APIStatusError("rate limit", response=httpx.Response(429, request=req), body=None)
    items = iter([err_429, fake_resp("recovered")])

    def adapter(**kw):
        val = next(items)
        if isinstance(val, Exception):
            raise val
        return val

    usage = Usage()
    sleeps = []
    res = call_llm([], Settings(tmp_path), usage, adapter=adapter, sleep=sleeps.append)
    assert res == "recovered"
    assert usage.calls == 2
    assert sleeps == [0.5]
    assert (tmp_path / "logs/http_errors.jsonl").exists()


def test_call_llm_requires_api_key(tmp_path):
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        call_llm([], Settings(tmp_path), Usage())
