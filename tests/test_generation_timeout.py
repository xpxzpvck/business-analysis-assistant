import asyncio
import json

import httpx
import pytest

from ba_assistant.models import Analysis, ArtifactBundle
from ba_assistant.openrouter import FreeProviderConfig, OpenRouter, ProviderError
from ba_assistant.workflow import Workflow, WorkflowError
from test_domain import ready_session, bundle
from test_openrouter import MESSAGES


def test_generation_has_separate_deadline_from_analysis():
    session = ready_session()
    calls = []

    async def handler(request):
        calls.append(request.extensions["timeout"])
        await asyncio.sleep(0.03)
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps(bundle(session))}}]})

    config = FreeProviderConfig(api_key="dummy", attempt_timeout=0.005, generation_timeout=1)
    adapter = OpenRouter(config, transport=httpx.MockTransport(handler))
    with pytest.raises(ProviderError, match="^OpenRouter timeout"):
        asyncio.run(adapter.complete(MESSAGES, Analysis))
    result = asyncio.run(adapter.complete(MESSAGES, ArtifactBundle))
    assert isinstance(result.value, ArtifactBundle)
    assert calls[0]["read"] == 0.005 and calls[1]["read"] == 1
    assert config.model == "openrouter/free"


def test_generation_deadline_preserves_confirmations_and_existing_documents():
    session = ready_session()
    session.request_generation()
    session.accept_artifacts(bundle(session))
    before = session.state
    calls = []

    async def handler(request):
        calls.append(request)
        await asyncio.sleep(0.1)
        raise AssertionError("Should have been cancelled by deadline")

    provider = OpenRouter(FreeProviderConfig(api_key="dummy", generation_timeout=0.005),
                          transport=httpx.MockTransport(handler))
    flow = Workflow(session, provider)
    with pytest.raises(WorkflowError, match="generation_timeout"):
        asyncio.run(flow.generate())
    assert session.state == before
    assert len(calls) == 1
    assert flow.records[-1].outcome == "generation_timeout"
