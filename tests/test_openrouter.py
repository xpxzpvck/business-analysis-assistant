import asyncio
import json

import httpx
import pytest
from pydantic import ValidationError

from ba_assistant.models import Analysis
from ba_assistant.openrouter import OpenRouter, ProviderConfig, ProviderError, retry_delay
from ba_assistant.session import Session

MESSAGES = [{"role": "user", "content": "Test brief"}]


def success(**extra):
    return {"choices": [{"finish_reason": "stop", "message": {"content": '{"facts":[],"issues":[],"questions":[]}'}}], **extra}


def run(responses, **config):
    requests, sleeps = [], []

    async def handler(request):
        requests.append(request)
        item = responses[min(len(requests) - 1, len(responses) - 1)]
        if isinstance(item, Exception):
            raise item
        return item

    async def sleep(delay):
        sleeps.append(delay)

    adapter = OpenRouter(ProviderConfig(api_key="test-only-key", model="example/fixed", **config),
                         transport=httpx.MockTransport(handler), sleep=sleep)
    return adapter, requests, sleeps


def test_success_payload_and_usage():
    adapter, requests, sleeps = run([httpx.Response(200, json=success(usage={"total_tokens": 12, "cost": 0.01, "private": "omit"}))])
    result = asyncio.run(adapter.complete(MESSAGES, Analysis))
    assert isinstance(result.value, Analysis) and result.attempts == 1
    assert result.usage == {"total_tokens": 12, "cost": 0.01}
    payload = json.loads(requests[0].content)
    assert payload["model"] == "example/fixed" and payload["provider"]["allow_fallbacks"] is False
    schema = payload["response_format"]["json_schema"]["schema"]
    assert set(schema["required"]) == {"facts", "issues", "questions", "resolutions"}
    assert schema["$defs"]["FactDraft"]["additionalProperties"] is False
    assert sleeps == []


@pytest.mark.parametrize("content, finish, kind", [
    ('{"facts":', "length", "output_truncated"),
    ("", "stop", "output_empty"),
    ("```json\n{}\n```", "stop", "output_not_json"),
    ('{"facts":"PRIVATE"}', "stop", "output_schema"),
    ('{"PRIVATE_SECRET":true}', "stop", "output_schema"),
    ("", "content_filter", "output_refused"),
])
def test_safe_output_failure_categories(content, finish, kind):
    body = {"choices": [{"finish_reason": finish, "message": {"content": content}}]}
    adapter, requests, sleeps = run([httpx.Response(200, json=body)])
    with pytest.raises(ProviderError) as caught:
        asyncio.run(adapter.complete(MESSAGES, Analysis))
    assert caught.value.kind == kind
    assert len(requests) == 1 and not sleeps
    assert "PRIVATE" not in str(caught.value.diagnostic)
    if content == '{"facts":"PRIVATE"}':
        assert caught.value.diagnostic == "facts: list_type"


@pytest.mark.parametrize("status", [429, 500, 502, 503])
def test_transient_status_retries_once(status):
    adapter, requests, sleeps = run([httpx.Response(status, headers={"Retry-After": "0"}), httpx.Response(200, json=success())])
    result = asyncio.run(adapter.complete(MESSAGES, Analysis))
    assert result.attempts == 2 and len(requests) == 2 and sleeps == [0]


@pytest.mark.parametrize("status", [400, 401, 402, 403, 404, 422, 302])
def test_permanent_errors_and_redirects_not_retried(status):
    adapter, requests, sleeps = run([httpx.Response(status, text="test-only-key PRIVATE BRIEF")])
    with pytest.raises(ProviderError) as caught:
        asyncio.run(adapter.complete(MESSAGES, Analysis))
    assert len(requests) == 1 and not sleeps
    assert "PRIVATE" not in str(caught.value) and "test-only-key" not in str(caught.value)


@pytest.mark.parametrize("error", [httpx.ReadTimeout("private"), httpx.ConnectError("private")])
def test_network_failure_exhausts_two_attempts(error):
    adapter, requests, sleeps = run([error])
    with pytest.raises(ProviderError) as caught:
        asyncio.run(adapter.complete(MESSAGES, Analysis))
    assert caught.value.attempts == 2 and len(requests) == 2 and sleeps == [1]
    assert "private" not in str(caught.value)


@pytest.mark.parametrize("body", [[], {}, {"choices": []}, {"choices": [None]},
    {"choices": [{"finish_reason": "stop", "message": None}]},
    {"choices": [{"finish_reason": "stop", "message": "malformed"}]},
    {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]},
    {"choices": [{"finish_reason": "stop", "message": {"content": "not JSON"}}]},
    {"choices": [{"finish_reason": "stop", "message": {"content": '{"confirmed":true}'}}]},
    {"choices": [{"finish_reason": "stop", "message": {"content": "{}", "refusal": "No"}}]},
])
def test_invalid_output_is_not_retried(body):
    adapter, requests, sleeps = run([httpx.Response(200, json=body)])
    with pytest.raises(ProviderError):
        asyncio.run(adapter.complete(MESSAGES, Analysis))
    assert len(requests) == 1 and not sleeps


def test_bad_outer_json():
    adapter, requests, _ = run([httpx.Response(200, text="<html>bad</html>")])
    with pytest.raises(ProviderError, match="invalid_json"):
        asyncio.run(adapter.complete(MESSAGES, Analysis))
    assert len(requests) == 1


def test_http_200_error_not_success():
    adapter, requests, _ = run([httpx.Response(200, json={"error": {"code": 503}}), httpx.Response(200, json=success())])
    assert asyncio.run(adapter.complete(MESSAGES, Analysis)).attempts == 2
    assert len(requests) == 2


def test_long_retry_after_stops_without_retrying_early():
    adapter, requests, sleeps = run([httpx.Response(429, headers={"Retry-After": "60"})])
    with pytest.raises(ProviderError):
        asyncio.run(adapter.complete(MESSAGES, Analysis))
    assert len(requests) == 1 and not sleeps
    assert retry_delay("nonsense") == 1 and retry_delay("nan") is None


def test_overall_deadline_cancels_attempt():
    calls = []

    async def handler(request):
        calls.append(request)
        await asyncio.sleep(1)
        return httpx.Response(200, json=success())

    adapter = OpenRouter(ProviderConfig(api_key="test-only-key", model="example/fixed", attempt_timeout=0.01, max_attempts=1), transport=httpx.MockTransport(handler))
    with pytest.raises(ProviderError, match="timeout"):
        asyncio.run(adapter.complete(MESSAGES, Analysis))
    assert len(calls) == 1


def test_missing_config_fails_before_network(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    with pytest.raises(ValidationError):
        ProviderConfig.from_env()


def test_provider_failure_preserves_pending_session():
    session = Session()
    session.user_message("Employee creates request.")
    before = session.state
    adapter, _, _ = run([httpx.Response(401)])

    async def analyze():
        result = await adapter.complete(MESSAGES, Analysis)
        session.apply_analysis(result.value.model_dump(), before.version)

    with pytest.raises(ProviderError):
        asyncio.run(analyze())
    assert session.state == before


def test_cancel_is_not_retried():
    async def handler(request):
        raise asyncio.CancelledError

    adapter = OpenRouter(ProviderConfig(api_key="test-only-key", model="example/fixed"), transport=httpx.MockTransport(handler))
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(adapter.complete(MESSAGES, Analysis))


def test_repeated_http_failure_stops_after_two_attempts():
    adapter, requests, sleeps = run([httpx.Response(503)])
    with pytest.raises(ProviderError) as caught:
        asyncio.run(adapter.complete(MESSAGES, Analysis))
    assert caught.value.attempts == 2 and len(requests) == 2 and sleeps == [1]


def test_missing_usage_stays_unknown_and_secret_repr_is_masked():
    adapter, _, _ = run([httpx.Response(200, json=success())])
    assert asyncio.run(adapter.complete(MESSAGES, Analysis)).usage is None
    assert "test-only-key" not in repr(adapter.config)


def test_invalid_messages_never_reach_transport():
    adapter, requests, _ = run([httpx.Response(200, json=success())])
    with pytest.raises(ValueError):
        asyncio.run(adapter.complete([{"role": "user", "content": "brief", "gold": []}], Analysis))
    assert not requests
